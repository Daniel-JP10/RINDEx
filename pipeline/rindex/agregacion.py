"""Agregacion multiescala con rendimiento ponderado y validaciones cruzadas."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from rindex.config import ConfiguracionEdicion, cargar_configuracion
from rindex.limpieza import limpiar_eva

ANIO_QUIEBRE_2022 = 2022
ANIO_POSIBLEMENTE_INCOMPLETO = 2025
TOLERANCIA_CONSERVACION = 1e-6


def _agregar_base_anual(
    df_limpio: pd.DataFrame,
    llaves_agrupacion: list[str],
    columnas_primer_valor: dict[str, str],
) -> pd.DataFrame:
    df_aux = df_limpio.assign(
        _atipica=(df_limpio["fuera_de_rango"] | df_limpio["atipico_robusto"]).astype(int),
        _fuera=df_limpio["fuera_de_rango"].astype(int),
        _robusto=df_limpio["atipico_robusto"].astype(int),
    )

    especificacion_agg: dict[str, tuple[str, str]] = {
        col_dest: (col_orig, "first") for col_dest, col_orig in columnas_primer_valor.items()
    }
    especificacion_agg.update(
        {
            "registros": ("periodo", "count"),
            "area_sembrada": ("area_sembrada", "sum"),
            "area_cosechada": ("area_cosechada", "sum"),
            "produccion": ("produccion", "sum"),
            "filas_fuera_de_rango": ("_fuera", "sum"),
            "filas_atipico_robusto": ("_robusto", "sum"),
            "filas_atipicas": ("_atipica", "sum"),
        }
    )

    agrupado = (
        df_aux.groupby(llaves_agrupacion, as_index=False)
        .agg(**especificacion_agg)
        .sort_values(llaves_agrupacion)
        .reset_index(drop=True)
    )

    agrupado["area_no_cosechada"] = agrupado["area_sembrada"] - agrupado["area_cosechada"]
    agrupado["tasa_area_no_cosechada"] = np.where(
        agrupado["area_sembrada"] > 0,
        agrupado["area_no_cosechada"] / agrupado["area_sembrada"],
        np.nan,
    )
    agrupado["rendimiento"] = np.where(
        agrupado["area_cosechada"] > 0,
        agrupado["produccion"] / agrupado["area_cosechada"],
        np.nan,
    )
    agrupado["quiebre_2022"] = agrupado["anio"] >= ANIO_QUIEBRE_2022
    agrupado["anio_posiblemente_incompleto"] = agrupado["anio"] == ANIO_POSIBLEMENTE_INCOMPLETO
    return agrupado


def construir_anual_municipio_sistema(df_limpio: pd.DataFrame) -> pd.DataFrame:
    return _agregar_base_anual(
        df_limpio,
        llaves_agrupacion=[
            "codigo_dane_departamento",
            "codigo_dane_municipio",
            "cultivo",
            "sistema",
            "anio",
        ],
        columnas_primer_valor={
            "departamento": "departamento",
            "municipio": "municipio",
        },
    )


def construir_anual_municipio_cultivo(df_limpio: pd.DataFrame) -> pd.DataFrame:
    return _agregar_base_anual(
        df_limpio,
        llaves_agrupacion=[
            "codigo_dane_departamento",
            "codigo_dane_municipio",
            "cultivo",
            "anio",
        ],
        columnas_primer_valor={
            "departamento": "departamento",
            "municipio": "municipio",
        },
    )


def construir_anual_departamento_cultivo(df_limpio: pd.DataFrame) -> pd.DataFrame:
    return _agregar_base_anual(
        df_limpio,
        llaves_agrupacion=["codigo_dane_departamento", "cultivo", "anio"],
        columnas_primer_valor={"departamento": "departamento"},
    )


def construir_anual_region_cultivo(
    df_limpio: pd.DataFrame,
    cfg: ConfiguracionEdicion,
) -> pd.DataFrame:
    tabla = _agregar_base_anual(
        df_limpio,
        llaves_agrupacion=["cultivo", "anio"],
        columnas_primer_valor={},
    )
    tabla.insert(0, "region", cfg.region)
    return tabla


def _construir_tabla_periodo(
    df_anual: pd.DataFrame,
    llaves_periodo: list[str],
    cfg: ConfiguracionEdicion,
) -> pd.DataFrame:
    df_aux = df_anual.assign(
        _anio_con_dato=(df_anual["area_cosechada"] > 0).astype(int),
        _rend_valido=np.where(df_anual["area_cosechada"] > 0, df_anual["rendimiento"], np.nan),
    )

    agrupado = (
        df_aux.groupby(llaves_periodo, as_index=False)
        .agg(
            departamento=("departamento", "first"),
            municipio=("municipio", "first"),
            registros=("registros", "sum"),
            area_sembrada=("area_sembrada", "sum"),
            area_cosechada=("area_cosechada", "sum"),
            produccion=("produccion", "sum"),
            anios_con_dato=("_anio_con_dato", "sum"),
            media_rend_anual=("_rend_valido", "mean"),
            std_rend_anual=("_rend_valido", lambda s: float(s.dropna().std(ddof=1))),
            filas_fuera_de_rango=("filas_fuera_de_rango", "sum"),
            filas_atipico_robusto=("filas_atipico_robusto", "sum"),
            filas_atipicas=("filas_atipicas", "sum"),
        )
        .sort_values(llaves_periodo)
        .reset_index(drop=True)
    )

    agrupado["area_no_cosechada"] = agrupado["area_sembrada"] - agrupado["area_cosechada"]
    agrupado["tasa_area_no_cosechada"] = np.where(
        agrupado["area_sembrada"] > 0,
        agrupado["area_no_cosechada"] / agrupado["area_sembrada"],
        np.nan,
    )
    agrupado["rendimiento"] = np.where(
        agrupado["area_cosechada"] > 0,
        agrupado["produccion"] / agrupado["area_cosechada"],
        np.nan,
    )
    agrupado["cv_interanual"] = np.where(
        (agrupado["anios_con_dato"] >= 2) & (agrupado["media_rend_anual"] > 0),
        agrupado["std_rend_anual"] / agrupado["media_rend_anual"],
        np.nan,
    )

    agrupado = agrupado.drop(columns=["media_rend_anual", "std_rend_anual"])

    anios_min = cfg.parametros.anios_minimos_con_dato
    agrupado["elegible_300"] = (agrupado["area_cosechada"] >= 300.0) & (
        agrupado["anios_con_dato"] >= anios_min
    )
    agrupado["elegible_500"] = (agrupado["area_cosechada"] >= 500.0) & (
        agrupado["anios_con_dato"] >= anios_min
    )
    agrupado["elegible_1000"] = (agrupado["area_cosechada"] >= 1000.0) & (
        agrupado["anios_con_dato"] >= anios_min
    )
    return agrupado


def construir_periodo_municipio_cultivo(
    df_anual_mpio_cultivo: pd.DataFrame,
    cfg: ConfiguracionEdicion,
) -> pd.DataFrame:
    return _construir_tabla_periodo(
        df_anual_mpio_cultivo,
        llaves_periodo=["codigo_dane_departamento", "codigo_dane_municipio", "cultivo"],
        cfg=cfg,
    )


def construir_periodo_municipio_sistema(
    df_anual_mpio_sistema: pd.DataFrame,
    cfg: ConfiguracionEdicion,
) -> pd.DataFrame:
    return _construir_tabla_periodo(
        df_anual_mpio_sistema,
        llaves_periodo=[
            "codigo_dane_departamento",
            "codigo_dane_municipio",
            "cultivo",
            "sistema",
        ],
        cfg=cfg,
    )


def construir_tablas_agregadas(
    df_limpio: pd.DataFrame,
    cfg: ConfiguracionEdicion,
) -> dict[str, pd.DataFrame]:
    anual_mpio_sistema = construir_anual_municipio_sistema(df_limpio)
    anual_mpio_cultivo = construir_anual_municipio_cultivo(df_limpio)
    anual_depto_cultivo = construir_anual_departamento_cultivo(df_limpio)
    anual_region_cultivo = construir_anual_region_cultivo(df_limpio, cfg)
    periodo_mpio_cultivo = construir_periodo_municipio_cultivo(anual_mpio_cultivo, cfg)
    periodo_mpio_sistema = construir_periodo_municipio_sistema(anual_mpio_sistema, cfg)

    return {
        "anual_municipio_sistema": anual_mpio_sistema,
        "anual_municipio_cultivo": anual_mpio_cultivo,
        "anual_departamento_cultivo": anual_depto_cultivo,
        "anual_region_cultivo": anual_region_cultivo,
        "periodo_municipio_cultivo": periodo_mpio_cultivo,
        "periodo_municipio_sistema": periodo_mpio_sistema,
    }


def verificar_conservacion_y_jerarquia(
    df_filtrado: pd.DataFrame,
    tablas: dict[str, pd.DataFrame],
    tolerancia: float = TOLERANCIA_CONSERVACION,
) -> None:
    columnas_suma = ("area_sembrada", "area_cosechada", "produccion")
    base_totales = {col: float(df_filtrado[col].sum()) for col in columnas_suma}

    for nombre_tabla, df_tabla in tablas.items():
        for col in columnas_suma:
            diferencia = abs(float(df_tabla[col].sum()) - base_totales[col])
            if diferencia > tolerancia:
                raise ValueError(
                    f"Fallo de conservacion en '{nombre_tabla}' para '{col}': "
                    f"diferencia={diferencia} > {tolerancia}."
                )

    mpio_a_depto = (
        tablas["anual_municipio_cultivo"]
        .groupby(["codigo_dane_departamento", "cultivo", "anio"], as_index=False)
        .agg(
            area_sembrada=("area_sembrada", "sum"),
            area_cosechada=("area_cosechada", "sum"),
            produccion=("produccion", "sum"),
        )
        .sort_values(["codigo_dane_departamento", "cultivo", "anio"])
        .reset_index(drop=True)
    )
    depto_tabla = (
        tablas["anual_departamento_cultivo"]
        .sort_values(["codigo_dane_departamento", "cultivo", "anio"])
        .reset_index(drop=True)
    )
    for col in columnas_suma:
        max_dif_depto = float((mpio_a_depto[col] - depto_tabla[col]).abs().max())
        if max_dif_depto > tolerancia:
            raise ValueError(
                f"Incoherencia jerarquica municipio->departamento en '{col}': {max_dif_depto}."
            )

    depto_a_region = (
        tablas["anual_departamento_cultivo"]
        .groupby(["cultivo", "anio"], as_index=False)
        .agg(
            area_sembrada=("area_sembrada", "sum"),
            area_cosechada=("area_cosechada", "sum"),
            produccion=("produccion", "sum"),
        )
        .sort_values(["cultivo", "anio"])
        .reset_index(drop=True)
    )
    region_tabla = (
        tablas["anual_region_cultivo"].sort_values(["cultivo", "anio"]).reset_index(drop=True)
    )
    for col in columnas_suma:
        max_dif_region = float((depto_a_region[col] - region_tabla[col]).abs().max())
        if max_dif_region > tolerancia:
            raise ValueError(
                f"Incoherencia jerarquica departamento->region en '{col}': {max_dif_region}."
            )


def _fmt_ent(valor: int | float) -> str:
    return f"{int(valor):,}".replace(",", ".")


def _fmt_dec(valor: float, decimales: int = 2) -> str:
    if pd.isna(valor):
        return "N/A"
    texto = f"{float(valor):,.{decimales}f}"
    partes = texto.split(".")
    entero = partes[0].replace(",", ".")
    return f"{entero},{partes[1]}" if len(partes) > 1 else entero


def _serie_ent(serie: pd.Series) -> pd.Series:
    return serie.astype(int).map(_fmt_ent)


def _serie_dec(serie: pd.Series, decimales: int = 2) -> pd.Series:
    return serie.astype(float).map(lambda v: _fmt_dec(v, decimales))


def generar_reporte_validacion_limpieza(
    df_filtrado: pd.DataFrame,
    df_limpio: pd.DataFrame,
    tablas: dict[str, pd.DataFrame],
    cfg: ConfiguracionEdicion,
    ruta_salida: str | Path = "docs/validacion_limpieza.md",
) -> Path:
    verificar_conservacion_y_jerarquia(df_filtrado, tablas)
    ruta_md = Path(ruta_salida)
    ruta_md.parent.mkdir(parents=True, exist_ok=True)

    lineas: list[str] = [
        f"# Validación de limpieza, sistemas y agregación — {cfg.nombre_visible}",
        "",
        f"- **Edicion**: `{cfg.id_edicion}`",
        f"- **Region**: {cfg.region}",
        f"- **Tolerancia numerica de conservacion**: `{TOLERANCIA_CONSERVACION}`",
        "",
        "## 1. Conservación de sumas entre niveles de agregación",
        "",
        "| Nivel / Tabla | Filas | Area sembrada (ha) | Area cosechada (ha) "
        "| Produccion (t) | Max. dif. absoluta vs. filtrada | Estado |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | :---: |",
    ]

    sem_base = float(df_filtrado["area_sembrada"].sum())
    cos_base = float(df_filtrado["area_cosechada"].sum())
    prod_base = float(df_filtrado["produccion"].sum())

    entradas_niveles = [("eva_filtrada (base)", df_filtrado), ("eva_limpia", df_limpio)] + list(
        tablas.items()
    )
    for nombre, df_t in entradas_niveles:
        sem_t = float(df_t["area_sembrada"].sum())
        cos_t = float(df_t["area_cosechada"].sum())
        prod_t = float(df_t["produccion"].sum())
        max_dif = max(abs(sem_t - sem_base), abs(cos_t - cos_base), abs(prod_t - prod_base))
        lineas.append(
            f"| `{nombre}` | {_fmt_ent(len(df_t))} | {_fmt_dec(sem_t)} | "
            f"{_fmt_dec(cos_t)} | {_fmt_dec(prod_t)} | {_fmt_dec(max_dif, 8)} | OK |"
        )

    lineas.extend(
        [
            "",
            "## 2. Coincidencia de totales regionales por cultivo con `perfil_datos.md`",
            "",
            "| Cultivo | Area sembrada (ha) | Area cosechada (ha) | Area no cosechada (ha) "
            "| Produccion regional (t) | Rendimiento agregado (t/ha) |",
            "| :--- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    reg_cultivo = (
        tablas["anual_region_cultivo"]
        .groupby("cultivo", as_index=False)
        .agg(
            area_sembrada=("area_sembrada", "sum"),
            area_cosechada=("area_cosechada", "sum"),
            area_no_cosechada=("area_no_cosechada", "sum"),
            produccion=("produccion", "sum"),
        )
        .sort_values("cultivo")
    )
    reg_cultivo["rendimiento"] = reg_cultivo["produccion"] / reg_cultivo["area_cosechada"]
    filas_md_reg = (
        "| **"
        + reg_cultivo["cultivo"]
        + "** | "
        + _serie_dec(reg_cultivo["area_sembrada"])
        + " | "
        + _serie_dec(reg_cultivo["area_cosechada"])
        + " | "
        + _serie_dec(reg_cultivo["area_no_cosechada"])
        + " | "
        + _serie_dec(reg_cultivo["produccion"])
        + " | "
        + _serie_dec(reg_cultivo["rendimiento"], 4)
        + " |"
    )
    lineas.extend(filas_md_reg.tolist())

    mpio_a_depto = (
        tablas["anual_municipio_cultivo"]
        .groupby(["codigo_dane_departamento", "cultivo", "anio"], as_index=False)
        .agg(
            area_sembrada=("area_sembrada", "sum"),
            area_cosechada=("area_cosechada", "sum"),
            produccion=("produccion", "sum"),
        )
        .sort_values(["codigo_dane_departamento", "cultivo", "anio"])
        .reset_index(drop=True)
    )
    depto_ord = (
        tablas["anual_departamento_cultivo"]
        .sort_values(["codigo_dane_departamento", "cultivo", "anio"])
        .reset_index(drop=True)
    )
    depto_a_reg = (
        tablas["anual_departamento_cultivo"]
        .groupby(["cultivo", "anio"], as_index=False)
        .agg(
            area_sembrada=("area_sembrada", "sum"),
            area_cosechada=("area_cosechada", "sum"),
            produccion=("produccion", "sum"),
        )
        .sort_values(["cultivo", "anio"])
        .reset_index(drop=True)
    )
    reg_ord = tablas["anual_region_cultivo"].sort_values(["cultivo", "anio"]).reset_index(drop=True)

    dif_mpio_depto = max(
        float((mpio_a_depto["area_sembrada"] - depto_ord["area_sembrada"]).abs().max()),
        float((mpio_a_depto["area_cosechada"] - depto_ord["area_cosechada"]).abs().max()),
        float((mpio_a_depto["produccion"] - depto_ord["produccion"]).abs().max()),
    )
    dif_depto_reg = max(
        float((depto_a_reg["area_sembrada"] - reg_ord["area_sembrada"]).abs().max()),
        float((depto_a_reg["area_cosechada"] - reg_ord["area_cosechada"]).abs().max()),
        float((depto_a_reg["produccion"] - reg_ord["produccion"]).abs().max()),
    )

    lineas.extend(
        [
            "",
            "## 3. Coherencia jerárquica (municipio -> departamento -> región)",
            "",
            f"- **Celdas evaluadas (departamento-cultivo-anio)**: {_fmt_ent(len(depto_ord))} "
            f"— diferencia maxima municipio vs. departamento: `{_fmt_dec(dif_mpio_depto, 8)}`",
            f"- **Celdas evaluadas (region-cultivo-anio)**: {_fmt_ent(len(reg_ord))} "
            f"— diferencia maxima departamento vs. region: `{_fmt_dec(dif_depto_reg, 8)}`",
            "",
            "## 4. Conteo de filas atípicas por cultivo, sistema y criterio",
            "",
            "| Cultivo | Sistema | Filas totales | Filas con cosecha > 0 "
            "| `fuera_de_rango` | `atipico_robusto` (`|z| > 3,5`) | Total atipicas (union) |",
            "| :--- | :--- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    df_atip = df_limpio.assign(
        _cosecha_pos=(df_limpio["area_cosechada"] > 0).astype(int),
        _fuera=df_limpio["fuera_de_rango"].astype(int),
        _rob=df_limpio["atipico_robusto"].astype(int),
        _union=(df_limpio["fuera_de_rango"] | df_limpio["atipico_robusto"]).astype(int),
    )
    res_atip = (
        df_atip.groupby(["cultivo", "sistema"], as_index=False)
        .agg(
            filas=("periodo", "count"),
            cosecha_pos=("_cosecha_pos", "sum"),
            fuera=("_fuera", "sum"),
            rob=("_rob", "sum"),
            union=("_union", "sum"),
        )
        .sort_values(["cultivo", "sistema"])
    )
    filas_md_atip = (
        "| "
        + res_atip["cultivo"]
        + " | `"
        + res_atip["sistema"]
        + "` | "
        + _serie_ent(res_atip["filas"])
        + " | "
        + _serie_ent(res_atip["cosecha_pos"])
        + " | "
        + _serie_ent(res_atip["fuera"])
        + " | "
        + _serie_ent(res_atip["rob"])
        + " | "
        + _serie_ent(res_atip["union"])
        + " |"
    )
    lineas.extend(filas_md_atip.tolist())

    enc_15 = (
        "| Codigo Mpio | Municipio | Depto | Cultivo | Sistema | Periodo "
        "| Area cosechada (ha) | Produccion (t) | Rendimiento (t/ha) | `z_robusto` "
        "| `fuera_de_rango` | `atipico_robusto` |"
    )
    lineas.extend(
        [
            "",
            "### Las 15 filas con puntuación `|z_robusto|` más extrema",
            "",
            enc_15,
            "| :---: | :--- | :--- | :--- | :--- | :---: | ---: | ---: | ---: | ---: |:---:|:---:|",
        ]
    )
    df_con_z = df_limpio.loc[df_limpio["z_robusto"].notna()].copy()
    df_con_z["abs_z"] = df_con_z["z_robusto"].abs()
    top_15 = df_con_z.sort_values("abs_z", ascending=False).head(15)
    if len(top_15) > 0:
        filas_md_15 = (
            "| `"
            + top_15["codigo_dane_municipio"]
            + "` | "
            + top_15["municipio"]
            + " | "
            + top_15["departamento"]
            + " | "
            + top_15["cultivo"]
            + " | `"
            + top_15["sistema"]
            + "` | `"
            + top_15["periodo"]
            + "` | "
            + _serie_dec(top_15["area_cosechada"])
            + " | "
            + _serie_dec(top_15["produccion"])
            + " | "
            + _serie_dec(top_15["rendimiento"], 4)
            + " | "
            + _serie_dec(top_15["z_robusto"], 2)
            + " | "
            + top_15["fuera_de_rango"].astype(str)
            + " | "
            + top_15["atipico_robusto"].astype(str)
            + " |"
        )
        lineas.extend(filas_md_15.tolist())

    cms_semestral = int((df_limpio["area_cosechada"] > df_limpio["area_sembrada"]).sum())
    t_anual_sis = tablas["anual_municipio_sistema"]
    t_anual_cul = tablas["anual_municipio_cultivo"]
    t_per_sis = tablas["periodo_municipio_sistema"]
    t_per_cul = tablas["periodo_municipio_cultivo"]

    cms_anual_sis = int((t_anual_sis["area_cosechada"] > t_anual_sis["area_sembrada"]).sum())
    cms_anual_cul = int((t_anual_cul["area_cosechada"] > t_anual_cul["area_sembrada"]).sum())
    cms_per_sis = int((t_per_sis["area_cosechada"] > t_per_sis["area_sembrada"]).sum())
    cms_per_cul = int((t_per_cul["area_cosechada"] > t_per_cul["area_sembrada"]).sum())

    lineas.extend(
        [
            "",
            "## 5. Persistencia de `area_cosechada > area_sembrada` al agregar por año y periodo",
            "",
            (
                "- **Registros semestrales (`eva_limpia`) con `area_cosechada > area_sembrada`**: "
                f"{_fmt_ent(cms_semestral)} de {_fmt_ent(len(df_limpio))}"
            ),
            (
                "- **Casos anuales en `anual_municipio_sistema` con "
                "`area_cosechada > area_sembrada`**: "
                f"{_fmt_ent(cms_anual_sis)} de {_fmt_ent(len(t_anual_sis))}"
            ),
            (
                "- **Casos anuales en `anual_municipio_cultivo` con "
                "`area_cosechada > area_sembrada`**: "
                f"{_fmt_ent(cms_anual_cul)} de {_fmt_ent(len(t_anual_cul))}"
            ),
            (
                "- **Casos acumulados (2019-2025) en `periodo_municipio_sistema` que persisten**: "
                f"{_fmt_ent(cms_per_sis)} de {_fmt_ent(len(t_per_sis))}"
            ),
            (
                "- **Casos acumulados (2019-2025) en `periodo_municipio_cultivo` que persisten**: "
                f"{_fmt_ent(cms_per_cul)} de {_fmt_ent(len(t_per_cul))}"
            ),
            "",
            "## 6. Municipios elegibles por cultivo según umbral de área cosechada acumulada",
            "",
            "| Cultivo | Municipios totales | `elegible_300` (>= 300 ha y >= 4 anios) "
            "| `elegible_500` (>= 500 ha y >= 4 anios) "
            "| `elegible_1000` (>= 1.000 ha y >= 4 anios) |",
            "| :--- | ---: | ---: | ---: | ---: |",
        ]
    )

    res_eleg = (
        t_per_cul.assign(
            e300=t_per_cul["elegible_300"].astype(int),
            e500=t_per_cul["elegible_500"].astype(int),
            e1000=t_per_cul["elegible_1000"].astype(int),
        )
        .groupby("cultivo", as_index=False)
        .agg(
            total=("codigo_dane_municipio", "count"),
            e300=("e300", "sum"),
            e500=("e500", "sum"),
            e1000=("e1000", "sum"),
        )
        .sort_values("cultivo")
    )
    filas_md_eleg = (
        "| "
        + res_eleg["cultivo"]
        + " | "
        + _serie_ent(res_eleg["total"])
        + " | "
        + _serie_ent(res_eleg["e300"])
        + " | "
        + _serie_ent(res_eleg["e500"])
        + " | "
        + _serie_ent(res_eleg["e1000"])
        + " |"
    )
    lineas.extend(filas_md_eleg.tolist())

    # H5: municipios con los 3 cultivos simultaneamente elegibles
    mpios_3_e300 = int(
        (
            t_per_cul.loc[t_per_cul["elegible_300"]]
            .groupby("codigo_dane_municipio")["cultivo"]
            .nunique()
            == 3
        ).sum()
    )
    mpios_3_e500 = int(
        (
            t_per_cul.loc[t_per_cul["elegible_500"]]
            .groupby("codigo_dane_municipio")["cultivo"]
            .nunique()
            == 3
        ).sum()
    )
    mpios_3_e1000 = int(
        (
            t_per_cul.loc[t_per_cul["elegible_1000"]]
            .groupby("codigo_dane_municipio")["cultivo"]
            .nunique()
            == 3
        ).sum()
    )
    lineas.append("")
    lineas.append(
        f"- **Municipios con los 3 cultivos simultaneamente elegibles (para H5)**: "
        f"`300 ha`: {_fmt_ent(mpios_3_e300)} | `500 ha`: {_fmt_ent(mpios_3_e500)} | "
        f"`1.000 ha`: {_fmt_ent(mpios_3_e1000)}"
    )

    # H2 y H3 sobre registros anuales con area_cosechada > 0
    sis_pos = t_anual_sis.loc[t_anual_sis["area_cosechada"] > 0]
    maiz_pos = sis_pos.loc[sis_pos["cultivo"] == "Maíz"]
    conteo_sis_maiz = maiz_pos.groupby(["codigo_dane_municipio", "anio"])["sistema"].nunique()
    pares_h2 = int((conteo_sis_maiz == 2).sum())
    mpios_h2 = int(
        conteo_sis_maiz.loc[conteo_sis_maiz == 2]
        .index.get_level_values("codigo_dane_municipio")
        .nunique()
    )

    arroz_pos = sis_pos.loc[sis_pos["cultivo"] == "Arroz"]
    piv_arroz = arroz_pos.assign(activo=1).pivot_table(
        index=["codigo_dane_municipio", "anio"],
        columns="sistema",
        values="activo",
        fill_value=0,
    )
    for col_s in ("riego", "secano_mecanizado", "secano_manual"):
        if col_s not in piv_arroz.columns:
            piv_arroz[col_s] = 0

    tripletas_h3 = int(
        (
            (piv_arroz["riego"] > 0)
            & (piv_arroz["secano_mecanizado"] > 0)
            & (piv_arroz["secano_manual"] > 0)
        ).sum()
    )
    pares_riego_mec = int(((piv_arroz["riego"] > 0) & (piv_arroz["secano_mecanizado"] > 0)).sum())
    pares_riego_man = int(((piv_arroz["riego"] > 0) & (piv_arroz["secano_manual"] > 0)).sum())
    pares_mec_man = int(
        ((piv_arroz["secano_mecanizado"] > 0) & (piv_arroz["secano_manual"] > 0)).sum()
    )

    lineas.extend(
        [
            "",
            "## 7. Disponibilidad de pares para H2 (maíz) y tripletas/pares para H3 (arroz)",
            "",
            (
                "- **H2 Maíz (`tecnificado` vs. `tradicional` con `area_cosechada > 0`)**: "
                f"**{_fmt_ent(pares_h2)}** pares municipio-anio en "
                f"**{_fmt_ent(mpios_h2)}** municipios."
            ),
            (
                "- **H3 Arroz — tripletas completas "
                "(`riego`, `secano_mecanizado`, `secano_manual`)**: "
                f"**{_fmt_ent(tripletas_h3)}** municipio-anios."
            ),
            f"- **H3 Arroz — pares `riego` vs. `secano_mecanizado`**: "
            f"**{_fmt_ent(pares_riego_mec)}** municipio-anios.",
            f"- **H3 Arroz — pares `riego` vs. `secano_manual`**: "
            f"**{_fmt_ent(pares_riego_man)}** municipio-anios.",
            f"- **H3 Arroz — pares `secano_mecanizado` vs. `secano_manual`**: "
            f"**{_fmt_ent(pares_mec_man)}** municipio-anios.",
            "",
            (
                "## 8. Tasa de área no cosechada por año y cultivo "
                "(2019-2021 vs. 2022-2025, descriptiva)"
            ),
            "",
            "| Cultivo | Anio | Subperiodo | Area sembrada (ha) | Area cosechada (ha) "
            "| Area no cosechada (ha) | Tasa de area no cosechada (%) |",
            "| :--- | :---: | :---: | ---: | ---: | ---: | ---: |",
        ]
    )

    reg_anual = tablas["anual_region_cultivo"].sort_values(["cultivo", "anio"]).copy()
    reg_anual["subperiodo"] = np.where(
        reg_anual["quiebre_2022"],
        "2022-2025 (post-quiebre)",
        "2019-2021 (pre-quiebre)",
    )
    reg_anual["tasa_pct"] = reg_anual["tasa_area_no_cosechada"] * 100.0

    filas_md_tasa_anual = (
        "| "
        + reg_anual["cultivo"]
        + " | "
        + reg_anual["anio"].astype(str)
        + " | "
        + reg_anual["subperiodo"]
        + " | "
        + _serie_dec(reg_anual["area_sembrada"])
        + " | "
        + _serie_dec(reg_anual["area_cosechada"])
        + " | "
        + _serie_dec(reg_anual["area_no_cosechada"])
        + " | "
        + _serie_dec(reg_anual["tasa_pct"], 2)
        + " % |"
    )
    lineas.extend(filas_md_tasa_anual.tolist())

    res_subp = (
        reg_anual.groupby(["cultivo", "subperiodo"], as_index=False)
        .agg(
            area_sembrada=("area_sembrada", "sum"),
            area_cosechada=("area_cosechada", "sum"),
            area_no_cosechada=("area_no_cosechada", "sum"),
        )
        .sort_values(["cultivo", "subperiodo"])
    )
    res_subp["tasa_pct"] = np.where(
        res_subp["area_sembrada"] > 0,
        (res_subp["area_no_cosechada"] / res_subp["area_sembrada"]) * 100.0,
        0.0,
    )

    lineas.extend(
        [
            "",
            "### Comparación descriptiva por subperiodo (2019-2021 vs. 2022-2025)",
            "",
            "| Cultivo | Subperiodo | Area sembrada (ha) | Area cosechada (ha) "
            "| Area no cosechada (ha) | Tasa acumulada de area no cosechada (%) |",
            "| :--- | :---: | ---: | ---: | ---: | ---: |",
        ]
    )
    filas_md_subp = (
        "| **"
        + res_subp["cultivo"]
        + "** | "
        + res_subp["subperiodo"]
        + " | "
        + _serie_dec(res_subp["area_sembrada"])
        + " | "
        + _serie_dec(res_subp["area_cosechada"])
        + " | "
        + _serie_dec(res_subp["area_no_cosechada"])
        + " | "
        + _serie_dec(res_subp["tasa_pct"], 2)
        + " % |"
    )
    lineas.extend(filas_md_subp.tolist())

    ruta_md.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return ruta_md


def ejecutar_agregacion(
    ruta_config: str | Path,
    ruta_reporte: str | Path | None = "docs/validacion_limpieza.md",
) -> dict[str, pd.DataFrame]:
    cfg = cargar_configuracion(ruta_config)
    ruta_filtrado = Path(cfg.fuente.parquet_filtrado)
    if not ruta_filtrado.exists():
        raise FileNotFoundError(
            f"No existe el parquet filtrado '{ruta_filtrado}'. Ejecute primero rindex.ingesta."
        )

    df_filtrado = pd.read_parquet(ruta_filtrado)
    df_limpio = limpiar_eva(df_filtrado, cfg)

    directorio_interim = ruta_filtrado.parent
    directorio_interim.mkdir(parents=True, exist_ok=True)

    tablas = construir_tablas_agregadas(df_limpio, cfg)
    verificar_conservacion_y_jerarquia(df_filtrado, tablas)

    for nombre_tabla, df_tabla in tablas.items():
        df_tabla.to_parquet(directorio_interim / f"{nombre_tabla}.parquet", index=False)

    if ruta_reporte is not None:
        generar_reporte_validacion_limpieza(
            df_filtrado=df_filtrado,
            df_limpio=df_limpio,
            tablas=tablas,
            cfg=cfg,
            ruta_salida=ruta_reporte,
        )

    return tablas


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ejecuta la limpieza, mapeo de sistemas y agregacion multiescala de EVA."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Ruta al archivo YAML de configuracion de la edicion.",
    )
    parser.add_argument(
        "--reporte",
        default="docs/validacion_limpieza.md",
        help="Ruta de salida para el reporte de validacion de limpieza y agregacion.",
    )
    args = parser.parse_args()
    ejecutar_agregacion(args.config, ruta_reporte=args.reporte)


if __name__ == "__main__":
    main()
