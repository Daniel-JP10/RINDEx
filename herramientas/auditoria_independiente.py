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
# Tolerancia relativa para comparar estimacion puntual vs p50 de suma replica a replica (D10)
TOLERANCIA_S1_RELATIVA_PCT = 3.0
TOLERANCIA_COMBINADO_RELATIVA_PCT = 3.0
TOLERANCIA_PORCENTAJE_DESC = 0.1


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

    # 5. Ganancia regional puntual de S1 en maiz sin bootstrap frente a p50 y rango [p10; p90]
    anual_mpio_sis_todos = (
        df.loc[df["area_cosechada"] > 0]
        .groupby(["cod_depto", "cod_mpio", "cultivo", "sistema", "anio"], as_index=False)
        .agg(
            area_cosechada=("area_cosechada", "sum"),
            produccion=("produccion", "sum"),
        )
    )
    per_sis_todos = anual_mpio_sis_todos.groupby(
        ["cod_depto", "cod_mpio", "cultivo", "sistema"], as_index=False
    ).agg(
        area_cosechada=("area_cosechada", "sum"),
        produccion=("produccion", "sum"),
        anios_con_dato=("anio", "nunique"),
    )
    per_sis_todos["rendimiento"] = per_sis_todos["produccion"] / per_sis_todos["area_cosechada"]
    eleg_sis_todos = per_sis_todos.loc[
        (per_sis_todos["area_cosechada"] >= 500.0) & (per_sis_todos["anios_con_dato"] >= 4)
    ].copy()

    s1_puntual_mpio: dict[tuple[str, str], float] = {}
    for (cult_s, _sis_s), sub_sis in eleg_sis_todos.groupby(["cultivo", "sistema"]):
        p75_reg = float(np.percentile(sub_sis["rendimiento"], 75.0))
        conteos_dep = sub_sis.groupby("cod_depto")["cod_mpio"].count().to_dict()
        p75_dep = {
            dep: float(np.percentile(g["rendimiento"], 75.0))
            for dep, g in sub_sis.groupby("cod_depto")
        }
        for fila_s in sub_sis.to_dict(orient="records"):
            dep = str(fila_s["cod_depto"])
            mpio = str(fila_s["cod_mpio"])
            y_ref = p75_dep[dep] if int(conteos_dep.get(dep, 0)) >= 5 else p75_reg
            brecha_u = max(0.0, y_ref - float(fila_s["rendimiento"]))
            area_media = float(fila_s["area_cosechada"]) / float(fila_s["anios_con_dato"])
            s1_puntual_mpio[(mpio, str(cult_s))] = (
                s1_puntual_mpio.get((mpio, str(cult_s)), 0.0) + brecha_u * area_media
            )

    ganancia_puntual_s1_maiz = sum(
        val for (_, c_k), val in s1_puntual_mpio.items() if c_k == "Maíz"
    )
    tar_s1_maiz = mapa_tarjetas["s1_maiz"]
    s1_p50_pub = float(tar_s1_maiz["cifra"])
    s1_ic = tar_s1_maiz["intervalo"]
    dif_rel_s1_pct = abs(ganancia_puntual_s1_maiz - s1_p50_pub) / s1_p50_pub * 100.0
    dentro_rango_s1 = float(s1_ic[0]) <= ganancia_puntual_s1_maiz <= float(s1_ic[1])
    filas_comparacion.append(
        {
            "categoria": "Escenario S1 Maiz (puntual vs p50)",
            "metrica": "Ganancia regional anual S1 Maiz (t/anio, dif. relativa %)",
            "valor_auditoria": round(ganancia_puntual_s1_maiz, 2),
            "valor_publicado": s1_p50_pub,
            "diferencia": round(dif_rel_s1_pct, 4),
            "tolerancia": f"<= {TOLERANCIA_S1_RELATIVA_PCT} % y en [p10; p90]",
            "cumple": (dif_rel_s1_pct <= TOLERANCIA_S1_RELATIVA_PCT) and dentro_rango_s1,
        }
    )

    # 6. Verificacion independiente del total regional combinado (3 cultivos y evidencia alta, D10)
    per_cul_tot = anual_mpio_cult.groupby(["cod_depto", "cod_mpio", "cultivo"], as_index=False).agg(
        area_sembrada=("area_sembrada", "sum"),
        area_cosechada=("area_cosechada", "sum"),
        produccion=("produccion", "sum"),
    )
    anios_cul_pos = (
        anual_pos.groupby(["cod_depto", "cod_mpio", "cultivo"])["anio"]
        .nunique()
        .reset_index(name="anios_con_dato")
    )
    per_cul_tot = per_cul_tot.merge(
        anios_cul_pos, on=["cod_depto", "cod_mpio", "cultivo"], how="left"
    )
    per_cul_tot["anios_con_dato"] = per_cul_tot["anios_con_dato"].fillna(0).astype(int)
    eleg_cul_tot = per_cul_tot.loc[
        (per_cul_tot["area_cosechada"] >= 500.0) & (per_cul_tot["anios_con_dato"] >= 4)
    ].copy()

    mapa_per_sis_aud = {
        (str(f["cod_mpio"]), str(f["cultivo"]), str(f["sistema"])): f
        for f in per_sis_todos.to_dict(orient="records")
    }
    hl_por_id = {
        str(fila_c["metrica"]).split(" ", maxsplit=1)[0]: float(fila_c["valor_auditoria"])
        for fila_c in filas_comparacion
        if fila_c["categoria"] == "Razon Hodges-Lehmann (H2/H3)"
    }
    razon_h2_aud = hl_por_id["h2_maiz_tecnificado"]
    razon_h3_aud = hl_por_id["h3_arroz_mecanizado_vs_manual"]

    comb_puntual_cult: dict[str, float] = {"Arroz": 0.0, "Maíz": 0.0, "Yuca": 0.0}
    for fila_e in eleg_cul_tot.to_dict(orient="records"):
        mpio_e = str(fila_e["cod_mpio"])
        cult_e = str(fila_e["cultivo"])
        s1_u = s1_puntual_mpio.get((mpio_e, cult_e), 0.0)
        s2_u = 0.0
        if cult_e in {"Maíz", "Arroz"}:
            sis_o = "tradicional" if cult_e == "Maíz" else "secano_manual"
            sis_d = "tecnificado" if cult_e == "Maíz" else "secano_mecanizado"
            info_o = mapa_per_sis_aud.get((mpio_e, cult_e, sis_o))
            if info_o is not None and float(info_o["area_cosechada"]) > 0.0:
                area_o_m = float(info_o["area_cosechada"]) / float(info_o["anios_con_dato"])
                info_d = mapa_per_sis_aud.get((mpio_e, cult_e, sis_d))
                if (
                    info_d is not None
                    and float(info_d["area_cosechada"]) > 0.0
                    and int(info_d["anios_con_dato"]) >= 2
                ):
                    delta_r = max(0.0, float(info_d["rendimiento"]) - float(info_o["rendimiento"]))
                else:
                    razon_u = razon_h2_aud if cult_e == "Maíz" else razon_h3_aud
                    delta_r = float(info_o["rendimiento"]) * (razon_u - 1.0)
                s2_u = area_o_m * delta_r

        s3_u = 0.0
        if (
            cult_e in {"Arroz", "Maíz"}
            and float(fila_e["area_sembrada"]) >= float(fila_e["area_cosechada"])
            and float(fila_e["area_cosechada"]) > 0.0
        ):
            no_cos_m = (float(fila_e["area_sembrada"]) - float(fila_e["area_cosechada"])) / float(
                fila_e["anios_con_dato"]
            )
            rend_m = float(fila_e["produccion"]) / float(fila_e["area_cosechada"])
            s3_u = no_cos_m * rend_m

        comb_puntual_cult[cult_e] += max(s1_u, s2_u) + s3_u

    comb_puntual_ev_alta = comb_puntual_cult["Arroz"] + comb_puntual_cult["Maíz"]
    comb_puntual_total = comb_puntual_ev_alta + comb_puntual_cult["Yuca"]

    for id_tar_comb, val_puntual, ids_componentes, etiqueta_comb in [
        (
            "combinado_region_total",
            comb_puntual_total,
            ("combinado_arroz", "combinado_maiz", "combinado_yuca"),
            "Total regional combinado (3 cultivos, dif. relativa %)",
        ),
        (
            "combinado_region_evidencia_alta",
            comb_puntual_ev_alta,
            ("combinado_arroz", "combinado_maiz"),
            "Total regional combinado evidencia alta (Arroz y Maiz, dif. relativa %)",
        ),
    ]:
        tar_c = mapa_tarjetas[id_tar_comb]
        p50_pub = float(tar_c["cifra"])
        p10_pub, p90_pub = float(tar_c["intervalo"][0]), float(tar_c["intervalo"][1])
        suma_p10_comp = sum(float(mapa_tarjetas[k]["intervalo"][0]) for k in ids_componentes)
        suma_p90_comp = sum(float(mapa_tarjetas[k]["intervalo"][1]) for k in ids_componentes)
        dif_rel_c = abs(val_puntual - p50_pub) / p50_pub * 100.0
        acotado_ok = (
            p10_pub >= suma_p10_comp
            and p90_pub <= suma_p90_comp
            and p10_pub <= val_puntual <= p90_pub
        )
        filas_comparacion.append(
            {
                "categoria": "Total regional combinado (D10)",
                "metrica": etiqueta_comb,
                "valor_auditoria": round(val_puntual, 2),
                "valor_publicado": p50_pub,
                "diferencia": round(dif_rel_c, 4),
                "tolerancia": (
                    f"<= {TOLERANCIA_COMBINADO_RELATIVA_PCT} % y acotado vs suma percentiles"
                ),
                "cumple": (dif_rel_c <= TOLERANCIA_COMBINADO_RELATIVA_PCT) and acotado_ok,
            }
        )

    # 7. Participacion del area cosechada de maiz tradicional
    maiz_sis_tot = (
        per_sis_todos.loc[per_sis_todos["cultivo"] == "Maíz"]
        .groupby("sistema")["area_cosechada"]
        .sum()
    )
    pct_maiz_trad_calc = round(
        float(maiz_sis_tot["tradicional"]) / float(maiz_sis_tot.sum()) * 100.0, 1
    )
    pct_maiz_trad_pub = float(mapa_tarjetas["pct_area_maiz_tradicional"]["cifra"])
    dif_maiz_trad = abs(pct_maiz_trad_calc - pct_maiz_trad_pub)
    filas_comparacion.append(
        {
            "categoria": "Estructura sistemas Maiz",
            "metrica": "Porcentaje area cosechada Maiz tradicional (%)",
            "valor_auditoria": pct_maiz_trad_calc,
            "valor_publicado": pct_maiz_trad_pub,
            "diferencia": round(dif_maiz_trad, 4),
            "tolerancia": f"<= {TOLERANCIA_PORCENTAJE_DESC}",
            "cumple": dif_maiz_trad <= TOLERANCIA_PORCENTAJE_DESC,
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
        es_rel = fila["categoria"] in {
            "Escenario S1 Maiz (puntual vs p50)",
            "Total regional combinado (D10)",
        }
        dif_txt = (
            f"{float(fila['diferencia']):.4f} %" if es_rel else f"{float(fila['diferencia']):.6f}"
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
