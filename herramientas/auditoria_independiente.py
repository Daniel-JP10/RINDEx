"""Auditoria independiente desde el archivo crudo xlsx sin importar ningun modulo de rindex."""

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

DEPARTAMENTOS_CARIBE: set[str] = {"08", "13", "20", "23", "44", "47", "70"}
CULTIVOS_CARIBE: set[str] = {"Maíz", "Yuca", "Arroz"}
MAPEO_SISTEMAS: dict[str, tuple[str, str]] = {
    "Arroz riego": ("Arroz", "riego"),
    "Arroz secano manual": ("Arroz", "secano_manual"),
    "Arroz secano mecanizado": ("Arroz", "secano_mecanizado"),
    "Maíz amarillo tecnificado": ("Maíz", "tecnificado"),
    "Maíz amarillo tradicional": ("Maíz", "tradicional"),
    "Maíz blanco tecnificado": ("Maíz", "tecnificado"),
    "Maíz blanco tradicional": ("Maíz", "tradicional"),
    "Maíz tecnificado": ("Maíz", "tecnificado"),
    "Maíz tradicional": ("Maíz", "tradicional"),
    "Yuca consumo en fresco": ("Yuca", "fresco"),
    "Yuca industrial": ("Yuca", "industrial"),
}

TOLERANCIA_TOTALES = 1e-6
TOLERANCIA_ESTADISTICOS = 0.01
TOLERANCIA_S1_RELATIVA_PCT = 2.0


def _hodges_lehmann_razon(diffs_log: np.ndarray) -> float:
    n = len(diffs_log)
    i_idx, j_idx = np.triu_indices(n)
    walsh = 0.5 * (diffs_log[i_idx] + diffs_log[j_idx])
    return float(math.exp(float(np.median(walsh))))


def _cargar_y_limpiar_xlsx_independiente(ruta_xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(ruta_xlsx)
    df["cod_depto"] = (
        pd.to_numeric(df["Código Dane departamento"], errors="coerce")
        .fillna(-1)
        .astype(int)
        .astype(str)
        .str.zfill(2)
    )
    df["cod_mpio"] = (
        pd.to_numeric(df["Código Dane municipio"], errors="coerce")
        .fillna(-1)
        .astype(int)
        .astype(str)
        .str.zfill(5)
    )
    df["cultivo"] = df["Cultivo"].astype(str).str.strip()
    df["desagregacion"] = df["Desagregación cultivo"].astype(str).str.strip()
    df["periodo"] = df["Periodo"].astype(str).str.strip()
    df["anio"] = pd.to_numeric(df["Año"], errors="coerce").fillna(-1).astype(int)

    mascara = (
        df["cod_depto"].isin(DEPARTAMENTOS_CARIBE)
        & df["cultivo"].isin(CULTIVOS_CARIBE)
        & (df["anio"] >= 2019)
        & (df["anio"] <= 2025)
    )
    df = df.loc[mascara].copy()

    df["area_sembrada"] = pd.to_numeric(df["Área sembrada"], errors="coerce")
    df["area_cosechada"] = pd.to_numeric(df["Área cosechada"], errors="coerce")
    df["produccion"] = pd.to_numeric(df["Producción"], errors="coerce")

    validas = (
        df["area_sembrada"].notna()
        & df["area_cosechada"].notna()
        & df["produccion"].notna()
        & (df["area_sembrada"] >= 0)
        & (df["area_cosechada"] >= 0)
        & (df["produccion"] >= 0)
        & (~((df["area_cosechada"] == 0) & (df["produccion"] > 0)))
    )
    df = df.loc[validas].copy()
    df = df.drop_duplicates(
        subset=["cod_mpio", "desagregacion", "anio", "periodo"],
        keep="first",
    ).copy()
    df["sistema"] = [MAPEO_SISTEMAS[d][1] for d in df["desagregacion"]]
    return df


def ejecutar_auditoria_independiente(
    ruta_xlsx: str | Path = "data/raw/eva_2019_2025.xlsx",
    dir_web_data: str | Path = "web/public/data",
    ruta_reporte: str | Path = "docs/auditoria_independiente.md",
) -> tuple[pd.DataFrame, bool]:
    xlsx_path = Path(ruta_xlsx)
    web_path = Path(dir_web_data)
    md_path = Path(ruta_reporte)

    df = _cargar_y_limpiar_xlsx_independiente(xlsx_path)

    regional_json = json.loads((web_path / "regional.json").read_text(encoding="utf-8"))
    hallazgos_json = json.loads((web_path / "hallazgos.json").read_text(encoding="utf-8"))
    mapa_tarjetas = {str(t["id"]): t for t in hallazgos_json["tarjetas"]}

    filas_comparacion: list[dict[str, Any]] = []

    # 1. Totales regionales por cultivo y anio y rendimiento regional ponderado
    reg_calc = (
        df.groupby(["cultivo", "anio"], as_index=False)
        .agg(
            area_sembrada=("area_sembrada", "sum"),
            area_cosechada=("area_cosechada", "sum"),
            produccion=("produccion", "sum"),
        )
        .sort_values(["cultivo", "anio"])
    )
    reg_calc["rendimiento"] = reg_calc["produccion"] / reg_calc["area_cosechada"]
    reg_calc["tasa_no_cosechada_pct"] = (
        (reg_calc["area_sembrada"] - reg_calc["area_cosechada"]) / reg_calc["area_sembrada"] * 100.0
    )

    mapa_reg_json = {(str(r["cultivo"]), int(r["anio"])): r for r in regional_json["registros"]}

    for f in reg_calc.to_dict(orient="records"):
        c = str(f["cultivo"])
        a = int(f["anio"])
        rj = mapa_reg_json[(c, a)]

        for campo_nom, val_calc_int, val_pub_int in [
            ("area_sembrada_ha", round(float(f["area_sembrada"])), int(rj["area_sembrada_ha"])),
            ("area_cosechada_ha", round(float(f["area_cosechada"])), int(rj["area_cosechada_ha"])),
            ("produccion_t", round(float(f["produccion"])), int(rj["produccion_t"])),
        ]:
            dif = abs(float(val_calc_int) - float(val_pub_int))
            ok = dif <= TOLERANCIA_TOTALES
            filas_comparacion.append(
                {
                    "categoria": "Totales regionales",
                    "metrica": f"{c} {a} - {campo_nom}",
                    "valor_auditoria": float(val_calc_int),
                    "valor_publicado": float(val_pub_int),
                    "diferencia": dif,
                    "tolerancia": f"<= {TOLERANCIA_TOTALES}",
                    "cumple": ok,
                }
            )

        rend_calc = round(float(f["rendimiento"]), 2)
        rend_pub = float(rj["rendimiento_tha"])
        dif_r = abs(rend_calc - rend_pub)
        filas_comparacion.append(
            {
                "categoria": "Rendimiento regional ponderado",
                "metrica": f"{c} {a} - rendimiento_tha",
                "valor_auditoria": rend_calc,
                "valor_publicado": rend_pub,
                "diferencia": dif_r,
                "tolerancia": f"<= {TOLERANCIA_TOTALES}",
                "cumple": dif_r <= TOLERANCIA_TOTALES,
            }
        )

    # 2. Tasa de area no cosechada de arroz en 2021
    fila_arroz_21 = reg_calc.loc[
        (reg_calc["cultivo"] == "Arroz") & (reg_calc["anio"] == 2021)
    ].iloc[0]
    tasa_a21_calc = round(float(fila_arroz_21["tasa_no_cosechada_pct"]), 1)
    tasa_a21_pub = float(mapa_reg_json[("Arroz", 2021)]["tasa_area_no_cosechada_pct"])
    dif_t21 = abs(tasa_a21_calc - tasa_a21_pub)
    filas_comparacion.append(
        {
            "categoria": "Arroz 2021",
            "metrica": "Tasa area no cosechada Arroz 2021 (%)",
            "valor_auditoria": tasa_a21_calc,
            "valor_publicado": tasa_a21_pub,
            "diferencia": dif_t21,
            "tolerancia": f"<= {TOLERANCIA_ESTADISTICOS}",
            "cumple": dif_t21 <= TOLERANCIA_ESTADISTICOS,
        }
    )

    # Elegibilidad municipal por cultivo (>= 500 ha y >= 4 anios con cosecha > 0)
    anual_mpio_cult = df.groupby(["cod_depto", "cod_mpio", "cultivo", "anio"], as_index=False).agg(
        area_sembrada=("area_sembrada", "sum"),
        area_cosechada=("area_cosechada", "sum"),
        produccion=("produccion", "sum"),
    )
    anual_pos = anual_mpio_cult.loc[anual_mpio_cult["area_cosechada"] > 0]
    per_mpio_cult = anual_pos.groupby(["cod_depto", "cod_mpio", "cultivo"], as_index=False).agg(
        area_cosechada=("area_cosechada", "sum"),
        produccion=("produccion", "sum"),
        anios_con_dato=("anio", "nunique"),
    )
    per_mpio_cult["rendimiento"] = per_mpio_cult["produccion"] / per_mpio_cult["area_cosechada"]
    per_eleg = per_mpio_cult.loc[
        (per_mpio_cult["area_cosechada"] >= 500.0) & (per_mpio_cult["anios_con_dato"] >= 4)
    ].copy()

    # 3. Razon de Hodges-Lehmann de H2 y de los pares de H3
    anual_sis = (
        df.loc[df["area_cosechada"] > 0]
        .groupby(["cod_mpio", "cultivo", "sistema", "anio"], as_index=False)
        .agg(
            area_cosechada=("area_cosechada", "sum"),
            produccion=("produccion", "sum"),
        )
    )
    anual_sis["rendimiento"] = anual_sis["produccion"] / anual_sis["area_cosechada"]

    pares_auditoria = [
        ("Maíz", "tecnificado", "tradicional", "h2_maiz_tecnificado"),
        ("Arroz", "riego", "secano_manual", "h3_arroz_riego_vs_manual"),
        ("Arroz", "secano_mecanizado", "secano_manual", "h3_arroz_mecanizado_vs_manual"),
        ("Arroz", "riego", "secano_mecanizado", "h3_arroz_riego_vs_mecanizado"),
    ]
    for cult, sis_a, sis_b, id_tar in pares_auditoria:
        mpios_el = set(per_eleg.loc[per_eleg["cultivo"] == cult, "cod_mpio"])
        sub_s = anual_sis.loc[
            (anual_sis["cultivo"] == cult)
            & (anual_sis["cod_mpio"].isin(mpios_el))
            & (anual_sis["sistema"].isin([sis_a, sis_b]))
        ]
        piv = (
            sub_s.pivot_table(
                index=["cod_mpio", "anio"],
                columns="sistema",
                values="rendimiento",
                aggfunc="first",
            )[[sis_a, sis_b]]
            .dropna()
            .reset_index()
        )
        piv["diff_log"] = np.log(piv[sis_a] / piv[sis_b])
        diffs_m = piv.groupby("cod_mpio")["diff_log"].mean().to_numpy(dtype=float)
        hl_calc = _hodges_lehmann_razon(diffs_m)
        hl_pub = float(mapa_tarjetas[id_tar]["cifra"])
        dif_hl = abs(hl_calc - hl_pub)
        filas_comparacion.append(
            {
                "categoria": "Razon Hodges-Lehmann (H2/H3)",
                "metrica": f"{id_tar} ({sis_a} vs {sis_b}, n={len(diffs_m)})",
                "valor_auditoria": round(hl_calc, 4),
                "valor_publicado": hl_pub,
                "diferencia": dif_hl,
                "tolerancia": f"<= {TOLERANCIA_ESTADISTICOS}",
                "cumple": dif_hl <= TOLERANCIA_ESTADISTICOS,
            }
        )

    # 4. Kruskal-Wallis de H4 por cultivo
    for cult, id_tar in [
        ("Arroz", "h4_arroz"),
        ("Maíz", "h4_maiz"),
        ("Yuca", "h4_yuca"),
    ]:
        sub_c = per_eleg.loc[per_eleg["cultivo"] == cult]
        grupos = [
            g["rendimiento"].to_numpy(dtype=float)
            for _, g in sub_c.groupby("cod_depto")
            if len(g) > 0
        ]
        res_kw = stats.kruskal(*grupos)
        n_tot = len(sub_c)
        eps2_calc = float(res_kw.statistic) / float(n_tot - 1)
        eps2_pub = float(mapa_tarjetas[id_tar]["cifra"])
        dif_kw = abs(eps2_calc - eps2_pub)
        filas_comparacion.append(
            {
                "categoria": "Kruskal-Wallis (H4)",
                "metrica": f"{id_tar} epsilon_cuadrado (H={res_kw.statistic:.2f}, n={n_tot})",
                "valor_auditoria": round(eps2_calc, 4),
                "valor_publicado": eps2_pub,
                "diferencia": dif_kw,
                "tolerancia": f"<= {TOLERANCIA_ESTADISTICOS}",
                "cumple": dif_kw <= TOLERANCIA_ESTADISTICOS,
            }
        )

    # 5. Ganancia regional puntual de S1 en maiz sin bootstrap frente a p50
    anual_mpio_sis_maiz = (
        df.loc[(df["cultivo"] == "Maíz") & (df["area_cosechada"] > 0)]
        .groupby(["cod_depto", "cod_mpio", "sistema", "anio"], as_index=False)
        .agg(
            area_cosechada=("area_cosechada", "sum"),
            produccion=("produccion", "sum"),
        )
    )
    per_sis_maiz = anual_mpio_sis_maiz.groupby(
        ["cod_depto", "cod_mpio", "sistema"], as_index=False
    ).agg(
        area_cosechada=("area_cosechada", "sum"),
        produccion=("produccion", "sum"),
        anios_con_dato=("anio", "nunique"),
    )
    per_sis_maiz["rendimiento"] = per_sis_maiz["produccion"] / per_sis_maiz["area_cosechada"]
    eleg_sis_maiz = per_sis_maiz.loc[
        (per_sis_maiz["area_cosechada"] >= 500.0) & (per_sis_maiz["anios_con_dato"] >= 4)
    ].copy()

    ganancia_puntual_s1_maiz = 0.0
    for _, sub_sis in eleg_sis_maiz.groupby("sistema"):
        p75_reg = float(np.percentile(sub_sis["rendimiento"], 75.0))
        conteos_dep = sub_sis.groupby("cod_depto")["cod_mpio"].count().to_dict()
        p75_dep = {
            dep: float(np.percentile(g["rendimiento"], 75.0))
            for dep, g in sub_sis.groupby("cod_depto")
        }
        for fila_s in sub_sis.to_dict(orient="records"):
            dep = str(fila_s["cod_depto"])
            y_ref = p75_dep[dep] if int(conteos_dep.get(dep, 0)) >= 5 else p75_reg
            brecha_u = max(0.0, y_ref - float(fila_s["rendimiento"]))
            area_media = float(fila_s["area_cosechada"]) / float(fila_s["anios_con_dato"])
            ganancia_puntual_s1_maiz += brecha_u * area_media

    s1_p50_pub = float(mapa_tarjetas["s1_maiz"]["cifra"])
    dif_rel_s1_pct = abs(ganancia_puntual_s1_maiz - s1_p50_pub) / s1_p50_pub * 100.0
    filas_comparacion.append(
        {
            "categoria": "Escenario S1 Maiz (puntual vs p50)",
            "metrica": "Ganancia regional anual S1 Maiz (t/anio, dif. relativa %)",
            "valor_auditoria": round(ganancia_puntual_s1_maiz, 2),
            "valor_publicado": s1_p50_pub,
            "diferencia": round(dif_rel_s1_pct, 4),
            "tolerancia": f"<= {TOLERANCIA_S1_RELATIVA_PCT} %",
            "cumple": dif_rel_s1_pct <= TOLERANCIA_S1_RELATIVA_PCT,
        }
    )

    df_res = pd.DataFrame(filas_comparacion)
    todo_ok = bool(df_res["cumple"].all())

    lineas: list[str] = [
        "# Auditoría independiente de cifras publicadas — RINDEx (Región Caribe 2019-2025)",
        "",
        "- **Fuente leída directamente**: `data/raw/eva_2019_2025.xlsx`",
        (
            "- **Dependencias utilizadas**: `pandas`, `numpy`, `scipy` "
            "(sin importar ningún módulo de `rindex`)"
        ),
        f"- **Total de verificaciones ejecutadas**: `{len(df_res)}`",
        f"- **Verificaciones aprobadas**: `{int(df_res['cumple'].sum())} / {len(df_res)}`",
        f"- **Estado global de la auditoría**: **{'APROBADA' if todo_ok else 'FALLIDA'}**",
        "",
        "## Detalle de comparaciones contra `regional.json` y `hallazgos.json`",
        "",
        (
            "| Categoría | Métrica | Valor auditoría independiente "
            "| Valor publicado (JSON) | Diferencia | Tolerancia | Estado |"
        ),
        "| :--- | :--- | ---: | ---: | ---: | :---: | :---: |",
    ]

    for fila in df_res.to_dict(orient="records"):
        estado_txt = "OK" if bool(fila["cumple"]) else "FALLO"
        es_s1 = fila["categoria"] == "Escenario S1 Maiz (puntual vs p50)"
        dif_txt = (
            f"{float(fila['diferencia']):.4f} %" if es_s1 else f"{float(fila['diferencia']):.6f}"
        )
        lineas.append(
            f"| {fila['categoria']} | {fila['metrica']} | "
            f"{float(fila['valor_auditoria']):.4f} | "
            f"{float(fila['valor_publicado']):.4f} | {dif_txt} | "
            f"`{fila['tolerancia']}` | **{estado_txt}** |"
        )

    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(lineas) + "\n", encoding="utf-8")

    if not todo_ok:
        fallos = df_res.loc[~df_res["cumple"]]
        raise ValueError(
            f"La auditoria independiente detecto {len(fallos)} cifras fuera de tolerancia."
        )

    return df_res, todo_ok


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ejecuta la auditoria independiente desde el xlsx crudo contra los JSON web."
    )
    parser.add_argument(
        "--xlsx",
        default="data/raw/eva_2019_2025.xlsx",
        help="Ruta al archivo Excel crudo de EVA.",
    )
    parser.add_argument(
        "--web-data",
        default="web/public/data",
        help="Directorio de JSON exportados para la web.",
    )
    parser.add_argument(
        "--reporte",
        default="docs/auditoria_independiente.md",
        help="Ruta de salida para el reporte de auditoria independiente.",
    )
    args = parser.parse_args()
    ejecutar_auditoria_independiente(
        ruta_xlsx=args.xlsx,
        dir_web_data=args.web_data,
        ruta_reporte=args.reporte,
    )


if __name__ == "__main__":
    main()
