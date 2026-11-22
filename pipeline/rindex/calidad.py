"""Diagnostico de valores repetidos, rachas, redondeo y series poco informativas."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from rindex.config import ConfiguracionEdicion, cargar_configuracion
from rindex.estadistica import calcular_pendientes_municipales, prueba_wilcoxon_pareada
from rindex.limpieza import limpiar_eva

TOLERANCIA_IGUALDAD = 1e-9
UMBRAL_SERIE_POCO_INFORMATIVA = 0.5


def DiagnosticarSerieResultado(
    proporcion_repetidos: float,
    serie_poco_informativa: bool,
    racha_maxima: int,
    todos_identicos: bool,
    pares_consecutivos: int,
    pares_identicos: int,
) -> dict[str, object]:
    return {
        "proporcion_repetidos": proporcion_repetidos,
        "serie_poco_informativa": serie_poco_informativa,
        "racha_maxima": racha_maxima,
        "todos_identicos": todos_identicos,
        "pares_consecutivos": pares_consecutivos,
        "pares_identicos": pares_identicos,
    }


def diagnosticar_vector_rendimiento(valores: np.ndarray | list[float]) -> dict[str, object]:
    arr = np.asarray(valores, dtype=float)
    arr = arr[~np.isnan(arr)]
    k = len(arr)
    if k == 0:
        return DiagnosticarSerieResultado(
            proporcion_repetidos=0.0,
            serie_poco_informativa=True,
            racha_maxima=0,
            todos_identicos=False,
            pares_consecutivos=0,
            pares_identicos=0,
        )
    if k == 1:
        return DiagnosticarSerieResultado(
            proporcion_repetidos=0.0,
            serie_poco_informativa=True,
            racha_maxima=1,
            todos_identicos=True,
            pares_consecutivos=0,
            pares_identicos=0,
        )

    diffs = np.abs(arr[1:] - arr[:-1])
    iguales = diffs <= TOLERANCIA_IGUALDAD
    pares_totales = int(k - 1)
    pares_iguales = int(np.sum(iguales))
    proporcion = float(pares_iguales / pares_totales)
    todos_iguales = bool((np.max(arr) - np.min(arr)) <= TOLERANCIA_IGUALDAD)

    racha_max = 1
    racha_actual = 1
    for es_igual in iguales:
        if es_igual:
            racha_actual += 1
            if racha_actual > racha_max:
                racha_max = racha_actual
        else:
            racha_actual = 1

    return DiagnosticarSerieResultado(
        proporcion_repetidos=proporcion,
        serie_poco_informativa=bool(proporcion > UMBRAL_SERIE_POCO_INFORMATIVA),
        racha_maxima=int(racha_max),
        todos_identicos=todos_iguales,
        pares_consecutivos=pares_totales,
        pares_identicos=pares_iguales,
    )


def calcular_metricas_repeticion_series(
    df_anual: pd.DataFrame,
    llaves_serie: list[str],
) -> pd.DataFrame:
    df_ord = df_anual.sort_values(llaves_serie + ["anio"])
    df_pos = df_ord.loc[df_ord["area_cosechada"] > 0]

    todas_llaves = df_ord[llaves_serie].drop_duplicates().reset_index(drop=True)
    if df_pos.empty:
        todas_llaves["proporcion_repetidos"] = 0.0
        todas_llaves["serie_poco_informativa"] = True
        todas_llaves["racha_maxima"] = 0
        todas_llaves["todos_identicos"] = False
        todas_llaves["pares_consecutivos"] = 0
        todas_llaves["pares_identicos"] = 0
        return todas_llaves

    mat_llaves = df_pos[llaves_serie].to_numpy()
    rend_arr = df_pos["rendimiento"].to_numpy(dtype=float)

    cambio = np.nonzero((mat_llaves[1:] != mat_llaves[:-1]).any(axis=1))[0] + 1
    inicios = np.concatenate(([0], cambio))
    fines = np.concatenate((cambio, [len(df_pos)]))

    registros: list[dict[str, object]] = []
    for ini, fin in zip(inicios, fines, strict=True):
        diag = diagnosticar_vector_rendimiento(rend_arr[ini:fin])
        fila_llave = {col: mat_llaves[ini, idx] for idx, col in enumerate(llaves_serie)}
        fila_llave.update(diag)
        registros.append(fila_llave)

    df_diag = pd.DataFrame(registros)
    res = todas_llaves.merge(df_diag, on=llaves_serie, how="left")
    res["proporcion_repetidos"] = res["proporcion_repetidos"].fillna(0.0).astype(float)
    res["serie_poco_informativa"] = res["serie_poco_informativa"].fillna(True).astype(bool)
    res["racha_maxima"] = res["racha_maxima"].fillna(0).astype(int)
    res["todos_identicos"] = res["todos_identicos"].fillna(False).astype(bool)
    res["pares_consecutivos"] = res["pares_consecutivos"].fillna(0).astype(int)
    res["pares_identicos"] = res["pares_identicos"].fillna(0).astype(int)
    return res


def _fmt_ent(valor: int | float) -> str:
    return f"{int(valor):,}".replace(",", ".")


def _fmt_dec(valor: float, decimales: int = 2) -> str:
    texto = f"{float(valor):,.{decimales}f}"
    partes = texto.split(".")
    entero = partes[0].replace(",", ".")
    return f"{entero},{partes[1]}" if len(partes) > 1 else entero


def _resumir_repeticion_por_grupo(
    df_anual: pd.DataFrame,
    llaves_serie: list[str],
    cols_agrupacion: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    diag = calcular_metricas_repeticion_series(df_anual, llaves_serie)
    conteos_anios = (
        df_anual.loc[df_anual["area_cosechada"] > 0]
        .groupby(llaves_serie, as_index=False)["anio"]
        .count()
        .rename(columns={"anio": "anios_con_dato"})
    )
    diag = diag.merge(conteos_anios, on=llaves_serie, how="left")
    diag["anios_con_dato"] = diag["anios_con_dato"].fillna(0).astype(int)

    # Series con al menos 2 anios para evaluar pares consecutivos y series constantes
    diag_2 = diag.loc[diag["anios_con_dato"] >= 2].copy()
    diag_2["poco_inf_int"] = diag_2["serie_poco_informativa"].astype(int)
    diag_2["ident_int"] = diag_2["todos_identicos"].astype(int)

    resumen = (
        diag_2.groupby(cols_agrupacion, as_index=False)
        .agg(
            series_evaluadas=("anios_con_dato", "count"),
            series_constantes=("ident_int", "sum"),
            series_poco_inf=("poco_inf_int", "sum"),
            pares_consecutivos=("pares_consecutivos", "sum"),
            pares_identicos=("pares_identicos", "sum"),
            racha_mediana=("racha_maxima", "median"),
            racha_max=("racha_maxima", "max"),
        )
        .sort_values(cols_agrupacion)
    )
    resumen["pct_series_constantes"] = (
        resumen["series_constantes"] / resumen["series_evaluadas"] * 100.0
    )
    resumen["pct_series_poco_inf"] = (
        resumen["series_poco_inf"] / resumen["series_evaluadas"] * 100.0
    )
    resumen["pct_pares_identicos"] = np.where(
        resumen["pares_consecutivos"] > 0,
        resumen["pares_identicos"] / resumen["pares_consecutivos"] * 100.0,
        0.0,
    )

    dist_rachas = (
        diag_2.groupby(cols_agrupacion + ["racha_maxima"], as_index=False)["anios_con_dato"]
        .count()
        .rename(columns={"anios_con_dato": "num_series"})
    )
    return resumen, dist_rachas


def generar_reporte_calidad_series(
    df_limpio: pd.DataFrame,
    anual_mpio_cultivo: pd.DataFrame,
    anual_mpio_sistema: pd.DataFrame,
    periodo_mpio_cultivo: pd.DataFrame,
    cfg: ConfiguracionEdicion,
    ruta_salida: str | Path = "docs/calidad_series.md",
) -> Path:
    ruta_md = Path(ruta_salida)
    ruta_md.parent.mkdir(parents=True, exist_ok=True)

    res_cul, rachas_cul = _resumir_repeticion_por_grupo(
        anual_mpio_cultivo,
        llaves_serie=["codigo_dane_municipio", "cultivo"],
        cols_agrupacion=["cultivo"],
    )
    res_sis, rachas_sis = _resumir_repeticion_por_grupo(
        anual_mpio_sistema,
        llaves_serie=["codigo_dane_municipio", "cultivo", "sistema"],
        cols_agrupacion=["cultivo", "sistema"],
    )

    lineas: list[str] = [
        f"# Diagnóstico de calidad de series y valores repetidos — {cfg.nombre_visible}",
        "",
        f"- **Edición**: `{cfg.id_edicion}`",
        f"- **Región**: {cfg.region}",
        "- **Criterio de `serie_poco_informativa`**: `proporcion_repetidos > 0,50` "
        "(más del 50 % de los pares de años consecutivos con rendimiento idéntico).",
        "",
        "## 1. Repetición interanual en `anual_municipio_cultivo` (por cultivo)",
        "",
        "| Cultivo | Series (>= 2 años) | Series 100 % constantes (%) "
        "| Pares consecutivos | Pares idénticos (%) | Series poco informativas (> 50 % rep.) |",
        "| :--- | ---: | ---: | ---: | ---: | ---: |",
    ]

    for f in res_cul.to_dict(orient="records"):
        const_txt = f"{_fmt_ent(f['series_constantes'])} ({_fmt_dec(f['pct_series_constantes'])} %)"
        pares_txt = f"{_fmt_ent(f['pares_identicos'])} ({_fmt_dec(f['pct_pares_identicos'])} %)"
        poco_txt = f"{_fmt_ent(f['series_poco_inf'])} ({_fmt_dec(f['pct_series_poco_inf'])} %)"
        lineas.append(
            f"| {f['cultivo']} | {_fmt_ent(f['series_evaluadas'])} | {const_txt} | "
            f"{_fmt_ent(f['pares_consecutivos'])} | {pares_txt} | {poco_txt} |"
        )

    lineas.extend(
        [
            "",
            "## 2. Repetición interanual en `anual_municipio_sistema` (por cultivo y sistema)",
            "",
            "| Cultivo | Sistema | Series (>= 2 años) | Series 100 % constantes (%) "
            "| Pares consecutivos | Pares idénticos (%) | Series poco informativas (> 50 % rep.) |",
            "| :--- | :--- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    for f in res_sis.to_dict(orient="records"):
        const_txt = f"{_fmt_ent(f['series_constantes'])} ({_fmt_dec(f['pct_series_constantes'])} %)"
        pares_txt = f"{_fmt_ent(f['pares_identicos'])} ({_fmt_dec(f['pct_pares_identicos'])} %)"
        poco_txt = f"{_fmt_ent(f['series_poco_inf'])} ({_fmt_dec(f['pct_series_poco_inf'])} %)"
        lineas.append(
            f"| {f['cultivo']} | `{f['sistema']}` | {_fmt_ent(f['series_evaluadas'])} | "
            f"{const_txt} | {_fmt_ent(f['pares_consecutivos'])} | {pares_txt} | {poco_txt} |"
        )

    lineas.extend(
        [
            "",
            "## 3. Distribución de la longitud máxima de rachas de valor repetido por serie",
            "",
            "### 3.1. En `anual_municipio_cultivo`",
            "",
            "| Cultivo | Racha máx. = 1 | Racha = 2 | Racha = 3 | Racha = 4 "
            "| Racha = 5 | Racha = 6 | Racha = 7 |",
            "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    piv_rc = rachas_cul.pivot_table(
        index="cultivo",
        columns="racha_maxima",
        values="num_series",
        fill_value=0,
    )
    for r_len in range(1, 8):
        if r_len not in piv_rc.columns:
            piv_rc[r_len] = 0
    for cultivo in sorted(piv_rc.index):
        vals = " | ".join(_fmt_ent(piv_rc.loc[cultivo, r_len]) for r_len in range(1, 8))
        lineas.append(f"| {cultivo} | {vals} |")

    lineas.extend(
        [
            "",
            "### 3.2. En `anual_municipio_sistema`",
            "",
            "| Cultivo | Sistema | Racha máx. = 1 | Racha = 2 | Racha = 3 "
            "| Racha = 4 | Racha = 5 | Racha = 6 | Racha = 7 |",
            "| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    piv_rs = rachas_sis.pivot_table(
        index=["cultivo", "sistema"],
        columns="racha_maxima",
        values="num_series",
        fill_value=0,
    )
    for r_len in range(1, 8):
        if r_len not in piv_rs.columns:
            piv_rs[r_len] = 0
    for cultivo, sistema in piv_rs.index:
        vals = " | ".join(_fmt_ent(piv_rs.loc[(cultivo, sistema), r_len]) for r_len in range(1, 8))
        lineas.append(f"| {cultivo} | `{sistema}` | {vals} |")

    # 4. Pendientes Theil-Sen exactamente iguales a cero en H1 y tratamiento de ceros en Wilcoxon
    per_eleg = periodo_mpio_cultivo.loc[periodo_mpio_cultivo["elegible_500"]].copy()
    anual_eleg = anual_mpio_cultivo.merge(
        per_eleg[["codigo_dane_municipio", "cultivo"]],
        on=["codigo_dane_municipio", "cultivo"],
        how="inner",
    )
    df_pend = calcular_pendientes_municipales(
        anual_eleg,
        anios_minimos=cfg.parametros.anios_minimos_con_dato,
    )

    lineas.extend(
        [
            "",
            "## 4. Pendientes Theil-Sen iguales a cero en H1 y tratamiento en Wilcoxon",
            "",
            (
                "- **Método de tratamiento de ceros en `scipy.stats.wilcoxon`**: "
                "`zero_method='wilcox'` (descarta las diferencias exactamente iguales "
                "a cero antes de asignar rangos)."
            ),
            "",
            (
                "| Cultivo | Municipios elegibles (`n`) | Pendientes Theil-Sen = 0 "
                "| % Pendientes = 0 | `n` efectivo en Wilcoxon (`n != 0`) "
                "| Estadístico `W` | Valor `p` |"
            ),
            "| :--- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    for cultivo in sorted(cfg.cultivos):
        sub_p = df_pend.loc[df_pend["cultivo"] == cultivo, "pendiente_theil_sen"].to_numpy(
            dtype=float
        )
        n_tot = len(sub_p)
        n_ceros = int(np.sum(np.abs(sub_p) <= TOLERANCIA_IGUALDAD))
        n_ef = n_tot - n_ceros
        pct_ceros = (n_ceros / n_tot * 100.0) if n_tot > 0 else 0.0
        w_res = prueba_wilcoxon_pareada(sub_p)
        lineas.append(
            f"| {cultivo} | {_fmt_ent(n_tot)} | {_fmt_ent(n_ceros)} | "
            f"{_fmt_dec(pct_ceros)} % | {_fmt_ent(n_ef)} | "
            f"{_fmt_dec(w_res.estadistico)} | {_fmt_dec(w_res.valor_p, 4)} |"
        )

    # 5. Repeticion a nivel de fila semestral (semestre A vs semestre B del mismo anio)
    df_sem_pos = df_limpio.loc[df_limpio["area_cosechada"] > 0].copy()
    df_sem_pos["semestre"] = np.where(
        df_sem_pos["periodo"].str.endswith("A"),
        "A",
        np.where(df_sem_pos["periodo"].str.endswith("B"), "B", "anual"),
    )
    piv_ab = df_sem_pos.loc[df_sem_pos["semestre"].isin(["A", "B"])].pivot_table(
        index=["codigo_dane_municipio", "cultivo", "sistema", "desagregacion_cultivo", "anio"],
        columns="semestre",
        values="rendimiento",
        aggfunc="first",
    )
    pares_ab = piv_ab[["A", "B"]].dropna().reset_index()
    pares_ab["id_ab"] = (pares_ab["A"] - pares_ab["B"]).abs() <= TOLERANCIA_IGUALDAD

    res_ab = (
        pares_ab.groupby(["cultivo", "sistema"], as_index=False)
        .agg(
            pares_ab=("id_ab", "count"),
            identicos_ab=("id_ab", "sum"),
        )
        .sort_values(["cultivo", "sistema"])
    )
    res_ab["pct_identicos_ab"] = np.where(
        res_ab["pares_ab"] > 0,
        res_ab["identicos_ab"] / res_ab["pares_ab"] * 100.0,
        0.0,
    )

    lineas.extend(
        [
            "",
            "## 5. Repetición semestral: rendimiento idéntico entre semestres A y B del mismo año",
            "",
            "| Cultivo | Sistema | Pares A-B en el mismo municipio-año "
            "| Pares con `rendimiento_A == rendimiento_B` | Porcentaje idéntico A vs. B |",
            "| :--- | :--- | ---: | ---: | ---: |",
        ]
    )
    for f in res_ab.to_dict(orient="records"):
        lineas.append(
            f"| {f['cultivo']} | `{f['sistema']}` | {_fmt_ent(f['pares_ab'])} | "
            f"{_fmt_ent(f['identicos_ab'])} | {_fmt_dec(f['pct_identicos_ab'])} % |"
        )

    # 6. Concentracion en valores redondos (enteros ,00 y multiplos de 0,5 terminados en ,0 o ,5)
    lineas.extend(
        [
            "",
            "## 6. Concentración en valores redondos frente a distribución uniforme",
            "",
            "- **Referencia uniforme en 2 decimales (`0,00` a `0,99`)**: "
            "`1,00 %` enteros exactos (`,00`); `2,00 %` terminados en `,00` o `,50`; "
            "`10,00 %` terminados en un decimal exacto (`,X0`, incluidos `,00` y `,50`).",
            "- **Referencia uniforme en 1 decimal (`,0` a `,9`)**: "
            "`10,00 %` enteros exactos (`,0`); `20,00 %` terminados en `,0` o `,5`.",
            "",
            "### 6.1. Filas semestrales con cosecha positiva (`eva_limpia`)",
            "",
            "| Cultivo | Sistema | Filas (`area_cosechada > 0`) | Enteros exactos (`,00`) "
            "| Terminados en `,00` o `,50` (múltiplos de 0,5) | Terminados en `,X0` (1 decimal) |",
            "| :--- | :--- | ---: | ---: | ---: | ---: |",
        ]
    )

    y_sem = df_sem_pos["rendimiento"].to_numpy(dtype=float)
    df_sem_pos["es_entero"] = np.abs(y_sem - np.round(y_sem)) <= 1e-6
    df_sem_pos["es_mult_05"] = np.abs(y_sem * 2.0 - np.round(y_sem * 2.0)) <= 1e-6
    df_sem_pos["es_1_dec"] = np.abs(y_sem * 10.0 - np.round(y_sem * 10.0)) <= 1e-6

    res_red = (
        df_sem_pos.groupby(["cultivo", "sistema"], as_index=False)
        .agg(
            n=("rendimiento", "count"),
            enteros=("es_entero", "sum"),
            mult_05=("es_mult_05", "sum"),
            un_dec=("es_1_dec", "sum"),
        )
        .sort_values(["cultivo", "sistema"])
    )
    for f in res_red.to_dict(orient="records"):
        n_f = int(f["n"])
        p_ent = float(f["enteros"]) / n_f * 100.0
        p_05 = float(f["mult_05"]) / n_f * 100.0
        p_1d = float(f["un_dec"]) / n_f * 100.0
        lineas.append(
            f"| {f['cultivo']} | `{f['sistema']}` | {_fmt_ent(n_f)} | "
            f"{_fmt_ent(f['enteros'])} ({_fmt_dec(p_ent)} %) | "
            f"{_fmt_ent(f['mult_05'])} ({_fmt_dec(p_05)} %) | "
            f"{_fmt_ent(f['un_dec'])} ({_fmt_dec(p_1d)} %) |"
        )

    lineas.extend(
        [
            "",
            "### 6.2. Series anuales agregadas (`anual_municipio_sistema`)",
            "",
            "| Cultivo | Sistema | Registros anuales (`area_cosechada > 0`) "
            "| Enteros exactos (`,00`) | Terminados en `,00` o `,50` | Terminados en `,X0` |",
            "| :--- | :--- | ---: | ---: | ---: | ---: |",
        ]
    )

    df_anual_pos = anual_mpio_sistema.loc[anual_mpio_sistema["area_cosechada"] > 0].copy()
    y_an = df_anual_pos["rendimiento"].to_numpy(dtype=float)
    df_anual_pos["es_entero"] = np.abs(y_an - np.round(y_an)) <= 1e-6
    df_anual_pos["es_mult_05"] = np.abs(y_an * 2.0 - np.round(y_an * 2.0)) <= 1e-6
    df_anual_pos["es_1_dec"] = np.abs(y_an * 10.0 - np.round(y_an * 10.0)) <= 1e-6

    res_red_an = (
        df_anual_pos.groupby(["cultivo", "sistema"], as_index=False)
        .agg(
            n=("rendimiento", "count"),
            enteros=("es_entero", "sum"),
            mult_05=("es_mult_05", "sum"),
            un_dec=("es_1_dec", "sum"),
        )
        .sort_values(["cultivo", "sistema"])
    )
    for f in res_red_an.to_dict(orient="records"):
        n_f = int(f["n"])
        p_ent = float(f["enteros"]) / n_f * 100.0
        p_05 = float(f["mult_05"]) / n_f * 100.0
        p_1d = float(f["un_dec"]) / n_f * 100.0
        lineas.append(
            f"| {f['cultivo']} | `{f['sistema']}` | {_fmt_ent(n_f)} | "
            f"{_fmt_ent(f['enteros'])} ({_fmt_dec(p_ent)} %) | "
            f"{_fmt_ent(f['mult_05'])} ({_fmt_dec(p_05)} %) | "
            f"{_fmt_ent(f['un_dec'])} ({_fmt_dec(p_1d)} %) |"
        )

    ruta_md.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return ruta_md


def ejecutar_diagnostico_calidad(
    ruta_config: str | Path,
    ruta_reporte: str | Path = "docs/calidad_series.md",
) -> Path:
    cfg = cargar_configuracion(ruta_config)
    dir_interim = Path(cfg.fuente.parquet_filtrado).parent

    df_filtrado = pd.read_parquet(cfg.fuente.parquet_filtrado)
    df_limpio = limpiar_eva(df_filtrado, cfg)
    anual_mpio_cultivo = pd.read_parquet(dir_interim / "anual_municipio_cultivo.parquet")
    anual_mpio_sistema = pd.read_parquet(dir_interim / "anual_municipio_sistema.parquet")
    periodo_mpio_cultivo = pd.read_parquet(dir_interim / "periodo_municipio_cultivo.parquet")

    return generar_reporte_calidad_series(
        df_limpio=df_limpio,
        anual_mpio_cultivo=anual_mpio_cultivo,
        anual_mpio_sistema=anual_mpio_sistema,
        periodo_mpio_cultivo=periodo_mpio_cultivo,
        cfg=cfg,
        ruta_salida=ruta_reporte,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera el diagnostico de valores repetidos y calidad de series de EVA."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Ruta al archivo YAML de configuracion de la edicion.",
    )
    parser.add_argument(
        "--reporte",
        default="docs/calidad_series.md",
        help="Ruta de salida para el reporte de calidad de series.",
    )
    args = parser.parse_args()
    ejecutar_diagnostico_calidad(args.config, ruta_reporte=args.reporte)


if __name__ == "__main__":
    main()
