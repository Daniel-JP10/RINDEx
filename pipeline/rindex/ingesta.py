"""Ingesta, validacion, filtrado y perfilado de la base EVA."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from rindex.config import ConfiguracionEdicion, cargar_configuracion
from rindex.contratos import normalizar_columnas_df, validar_contrato_eva
from rindex.fuente import preparar_fuente_cruda


def filtrar_eva(df_normalizado: pd.DataFrame, cfg: ConfiguracionEdicion) -> pd.DataFrame:
    df = df_normalizado.copy()
    codigos_deptos_validos = set(cfg.departamentos.keys())
    codigos_excluidos = {d.codigo for d in cfg.departamentos_excluidos}
    codigos_efectivos = codigos_deptos_validos - codigos_excluidos

    serie_depto = df["codigo_dane_departamento"].astype(str).str.zfill(2)
    serie_mpio = df["codigo_dane_municipio"].astype(str).str.zfill(5)

    mascara = (
        serie_depto.isin(codigos_efectivos)
        & df["cultivo"].isin(cfg.cultivos)
        & df["anio"].between(cfg.anios.inicio, cfg.anios.fin)
    )

    filtrado = df.loc[mascara].copy()
    filtrado["codigo_dane_departamento"] = serie_depto.loc[mascara]
    filtrado["codigo_dane_municipio"] = serie_mpio.loc[mascara]
    return filtrado.reset_index(drop=True)


def _formatear_entero(valor: int | float) -> str:
    return f"{int(valor):,}".replace(",", ".")


def _formatear_decimal(valor: float, decimales: int = 2) -> str:
    texto = f"{float(valor):,.{decimales}f}"
    partes = texto.split(".")
    entero = partes[0].replace(",", ".")
    return f"{entero},{partes[1]}" if len(partes) > 1 else entero


def _serie_entero_fmt(serie: pd.Series) -> pd.Series:
    return serie.astype(int).map(_formatear_entero)


def _serie_decimal_fmt(serie: pd.Series, decimales: int = 2) -> pd.Series:
    return serie.astype(float).map(lambda v: _formatear_decimal(v, decimales))


def generar_perfil_datos(
    df_crudo_norm: pd.DataFrame,
    df_filtrado: pd.DataFrame,
    cfg: ConfiguracionEdicion,
    ruta_salida: str | Path = "docs/perfil_datos.md",
) -> Path:
    ruta_md = Path(ruta_salida)
    ruta_md.parent.mkdir(parents=True, exist_ok=True)

    filas_totales = len(df_crudo_norm)
    filas_filtradas = len(df_filtrado)
    mpios_unicos_filt = int(df_filtrado["codigo_dane_municipio"].nunique())

    depto_crudo_str = df_crudo_norm["codigo_dane_departamento"].astype(str).str.zfill(2)
    filas_san_andres_total = int((depto_crudo_str == "88").sum())
    filas_san_andres_cultivos = int(
        ((depto_crudo_str == "88") & df_crudo_norm["cultivo"].isin(cfg.cultivos)).sum()
    )

    rango_txt = f"{cfg.anios.inicio}-{cfg.anios.fin}"
    enc_depto = (
        "| Codigo DANE | Departamento (config) | Filas filtradas "
        "| Municipios unicos (filtrada) | Municipios unicos (cruda depto) |"
    )
    lineas: list[str] = [
        f"# Perfil de datos EVA — {cfg.nombre_visible}",
        "",
        f"- **Edicion**: `{cfg.id_edicion}`",
        f"- **Region**: {cfg.region}",
        f"- **Cultivos**: {', '.join(cfg.cultivos)}",
        f"- **Rango de anios**: {cfg.anios.inicio} a {cfg.anios.fin}",
        "",
        "## 1. Volumen de registros y cobertura municipal por departamento",
        "",
        f"- **Filas totales en la base cruda nacional**: {_formatear_entero(filas_totales)}",
        (
            f"- **Filas filtradas ({cfg.region}, cultivos objetivo, {rango_txt})**: "
            f"{_formatear_entero(filas_filtradas)}"
        ),
        f"- **Municipios unicos en la base filtrada**: {_formatear_entero(mpios_unicos_filt)}",
        (
            f"- **Registros de San Andres (codigo 88) en base cruda**: "
            f"{_formatear_entero(filas_san_andres_total)} totales "
            f"({_formatear_entero(filas_san_andres_cultivos)} en cultivos objetivo; "
            "0 en base filtrada por exclusion documentada)."
        ),
        "",
        enc_depto,
        "| :---: | :--- | ---: | ---: | ---: |",
    ]

    mpios_crudo_por_depto = (
        df_crudo_norm.assign(
            depto_str=depto_crudo_str,
            mpio_str=df_crudo_norm["codigo_dane_municipio"].astype(str).str.zfill(5),
        )
        .groupby("depto_str")["mpio_str"]
        .nunique()
        .to_dict()
    )

    resumen_depto = (
        df_filtrado.groupby("codigo_dane_departamento", as_index=False)
        .agg(
            filas=("codigo_dane_municipio", "count"),
            municipios_unicos=("codigo_dane_municipio", "nunique"),
        )
        .sort_values("codigo_dane_departamento")
    )
    mapa_filas_depto = dict(
        zip(resumen_depto["codigo_dane_departamento"], resumen_depto["filas"], strict=True)
    )
    mapa_mpios_depto = dict(
        zip(
            resumen_depto["codigo_dane_departamento"],
            resumen_depto["municipios_unicos"],
            strict=True,
        )
    )

    for cod_depto, nombre_depto in sorted(cfg.departamentos.items()):
        filas_d = mapa_filas_depto.get(cod_depto, 0)
        mpios_d = mapa_mpios_depto.get(cod_depto, 0)
        mpios_crudo_d = mpios_crudo_por_depto.get(cod_depto, 0)
        lineas.append(
            f"| `{cod_depto}` | {nombre_depto} | {_formatear_entero(filas_d)} | "
            f"{_formatear_entero(mpios_d)} | {_formatear_entero(mpios_crudo_d)} |"
        )

    nulos_crudo = int(df_crudo_norm.isna().sum().sum())
    nulos_filtrado = int(df_filtrado.isna().sum().sum())
    dup_exactos_crudo = int(df_crudo_norm.duplicated().sum())
    dup_exactos_filtrado = int(df_filtrado.duplicated().sum())

    llave_unicidad = ["codigo_dane_municipio", "desagregacion_cultivo", "periodo"]
    mascara_dup_llave_filtrado = df_filtrado.duplicated(subset=llave_unicidad, keep=False)
    filas_en_conflicto_filtrado = int(mascara_dup_llave_filtrado.sum())
    pares_extra_llave_filtrado = int(
        df_filtrado.duplicated(subset=llave_unicidad, keep="first").sum()
    )

    mascara_dup_llave_crudo = df_crudo_norm.duplicated(subset=llave_unicidad, keep="first")
    pares_extra_llave_crudo = int(mascara_dup_llave_crudo.sum())

    llave_txt = "`(codigo_dane_municipio, desagregacion_cultivo, periodo)`"
    lineas.extend(
        [
            "",
            "## 2. Nulos y duplicados",
            "",
            (
                "- **Valores nulos en base cruda (todas las 18 columnas)**: "
                f"{_formatear_entero(nulos_crudo)}"
            ),
            (
                "- **Valores nulos en base filtrada (todas las 18 columnas)**: "
                f"{_formatear_entero(nulos_filtrado)}"
            ),
            f"- **Filas duplicadas exactas (base cruda)**: {_formatear_entero(dup_exactos_crudo)}",
            (
                "- **Filas duplicadas exactas (base filtrada)**: "
                f"{_formatear_entero(dup_exactos_filtrado)}"
            ),
            (
                f"- **Duplicados adicionales por llave {llave_txt} en base cruda**: "
                f"{_formatear_entero(pares_extra_llave_crudo)}"
            ),
            (
                f"- **Duplicados adicionales por llave {llave_txt} en base filtrada**: "
                f"{_formatear_entero(pares_extra_llave_filtrado)} "
                f"({_formatear_entero(filas_en_conflicto_filtrado)} filas involucradas)"
            ),
        ]
    )

    lineas.extend(
        [
            "",
            "## 3. Valores de `Desagregacion cultivo` por cultivo y anios de aparicion",
            "",
            "| Cultivo | Desagregacion cultivo | Filas | Anios en que aparece |",
            "| :--- | :--- | ---: | :--- |",
        ]
    )

    agrup_desag = (
        df_filtrado.groupby(["cultivo", "desagregacion_cultivo"], as_index=False)
        .agg(
            filas=("anio", "count"),
            anios=(
                "anio",
                lambda s: ", ".join(str(a) for a in sorted(s.unique())),
            ),
        )
        .sort_values(["cultivo", "desagregacion_cultivo"])
    )
    filas_md_desag = (
        "| "
        + agrup_desag["cultivo"]
        + " | "
        + agrup_desag["desagregacion_cultivo"]
        + " | "
        + _serie_entero_fmt(agrup_desag["filas"])
        + " | "
        + agrup_desag["anios"]
        + " |"
    )
    lineas.extend(filas_md_desag.tolist())

    enc_periodo = (
        "| Cultivo | Anio | Anual (`AAAA`) | Semestre A (`AAAAA`) "
        "| Semestre B (`AAAAB`) | Total semestral | Total registros |"
    )
    lineas.extend(
        [
            "",
            "## 4. Distribucion de `Periodo` (anual vs. semestral) por cultivo y anio",
            "",
            enc_periodo,
            "| :--- | :---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    es_sem_a = df_filtrado["periodo"].str.endswith("A")
    es_sem_b = df_filtrado["periodo"].str.endswith("B")
    es_anual = ~(es_sem_a | es_sem_b)

    df_periodos = df_filtrado.assign(
        anual=es_anual.astype(int),
        sem_a=es_sem_a.astype(int),
        sem_b=es_sem_b.astype(int),
    )
    tabla_periodos = (
        df_periodos.groupby(["cultivo", "anio"], as_index=False)
        .agg(
            anual=("anual", "sum"),
            sem_a=("sem_a", "sum"),
            sem_b=("sem_b", "sum"),
            total=("periodo", "count"),
        )
        .sort_values(["cultivo", "anio"])
    )
    tabla_periodos["total_sem"] = tabla_periodos["sem_a"] + tabla_periodos["sem_b"]
    filas_md_periodos = (
        "| "
        + tabla_periodos["cultivo"]
        + " | "
        + tabla_periodos["anio"].astype(str)
        + " | "
        + _serie_entero_fmt(tabla_periodos["anual"])
        + " | "
        + _serie_entero_fmt(tabla_periodos["sem_a"])
        + " | "
        + _serie_entero_fmt(tabla_periodos["sem_b"])
        + " | "
        + _serie_entero_fmt(tabla_periodos["total_sem"])
        + " | "
        + _serie_entero_fmt(tabla_periodos["total"])
        + " |"
    )
    lineas.extend(filas_md_periodos.tolist())

    mascara_cosecha_pos = df_filtrado["area_cosechada"] > 0
    df_rend = df_filtrado.loc[mascara_cosecha_pos].copy()
    df_rend["rendimiento_calc"] = df_rend["produccion"] / df_rend["area_cosechada"]
    df_rend["dif_abs"] = (df_rend["rendimiento"] - df_rend["rendimiento_calc"]).abs()
    denom = np.where(df_rend["rendimiento_calc"] > 0, df_rend["rendimiento_calc"], np.nan)
    df_rend["dif_rel_pct"] = (df_rend["dif_abs"] / denom) * 100.0
    df_rend["dif_rel_pct"] = df_rend["dif_rel_pct"].fillna(0.0)

    mediana_dif_abs = float(df_rend["dif_abs"].median()) if len(df_rend) > 0 else 0.0
    p95_dif_abs = float(df_rend["dif_abs"].quantile(0.95)) if len(df_rend) > 0 else 0.0
    max_dif_abs = float(df_rend["dif_abs"].max()) if len(df_rend) > 0 else 0.0
    filas_mayor_1pct = int((df_rend["dif_rel_pct"] > 1.0).sum())
    pct_mayor_1pct = (filas_mayor_1pct / len(df_rend) * 100.0) if len(df_rend) > 0 else 0.0

    enc_peores = (
        "| Codigo Mpio | Municipio | Depto | Cultivo | Desagregacion | Periodo "
        "| Area cosechada (ha) | Produccion (t) | Rend. reportado | Rend. calculado "
        "| Dif. absoluta | Dif. relativa (%) |"
    )
    lineas.extend(
        [
            "",
            "## 5. Validacion cruzada de rendimiento reportado vs. `produccion / area_cosechada`",
            "",
            (
                "- **Filas evaluadas con `area_cosechada > 0`**: "
                f"{_formatear_entero(len(df_rend))} de {_formatear_entero(filas_filtradas)}"
            ),
            (
                "- **Diferencia absoluta mediana (`|rendimiento - produccion/area_cosechada|`)**: "
                f"{_formatear_decimal(mediana_dif_abs, 6)} t/ha"
            ),
            f"- **Percentil 95 de diferencia absoluta**: {_formatear_decimal(p95_dif_abs, 6)} t/ha",
            f"- **Diferencia absoluta maxima**: {_formatear_decimal(max_dif_abs, 6)} t/ha",
            (
                "- **Filas con diferencia relativa > 1 %**: "
                f"{_formatear_entero(filas_mayor_1pct)} ({_formatear_decimal(pct_mayor_1pct, 2)} %)"
            ),
            "",
            "### Las 10 filas con mayor diferencia relativa en la base filtrada",
            "",
            enc_peores,
            "| :---: | :--- | :--- | :--- | :--- | :---: | ---: | ---: | ---: | ---: | ---: |---:|",
        ]
    )

    peores_10 = df_rend.sort_values(["dif_rel_pct", "dif_abs"], ascending=[False, False]).head(10)
    if len(peores_10) > 0:
        filas_md_peores = (
            "| `"
            + peores_10["codigo_dane_municipio"]
            + "` | "
            + peores_10["municipio"]
            + " | "
            + peores_10["departamento"]
            + " | "
            + peores_10["cultivo"]
            + " | "
            + peores_10["desagregacion_cultivo"]
            + " | `"
            + peores_10["periodo"]
            + "` | "
            + _serie_decimal_fmt(peores_10["area_cosechada"])
            + " | "
            + _serie_decimal_fmt(peores_10["produccion"])
            + " | "
            + _serie_decimal_fmt(peores_10["rendimiento"], 4)
            + " | "
            + _serie_decimal_fmt(peores_10["rendimiento_calc"], 4)
            + " | "
            + _serie_decimal_fmt(peores_10["dif_abs"], 4)
            + " | "
            + _serie_decimal_fmt(peores_10["dif_rel_pct"], 2)
            + " % |"
        )
        lineas.extend(filas_md_peores.tolist())

    mascara_cms_filt = df_filtrado["area_cosechada"] > df_filtrado["area_sembrada"]
    mascara_cms_crudo = df_crudo_norm["area_cosechada"] > df_crudo_norm["area_sembrada"]
    mascara_ppc_filt = (df_filtrado["produccion"] > 0) & (df_filtrado["area_cosechada"] == 0)
    mascara_ppc_crudo = (df_crudo_norm["produccion"] > 0) & (df_crudo_norm["area_cosechada"] == 0)
    mascara_cosecha_cero_filt = (df_filtrado["area_cosechada"] == 0) & (
        df_filtrado["produccion"] == 0
    )

    total_cms_filt = int(mascara_cms_filt.sum())
    total_cms_crudo = int(mascara_cms_crudo.sum())
    total_ppc_filt = int(mascara_ppc_filt.sum())
    total_ppc_crudo = int(mascara_ppc_crudo.sum())
    total_cosecha_cero_filt = int(mascara_cosecha_cero_filt.sum())

    lineas.extend(
        [
            "",
            "## 6. Anomalias de area y produccion",
            "",
            (
                "- **Filas con `area_cosechada > area_sembrada` (base filtrada)**: "
                f"{_formatear_entero(total_cms_filt)} "
                f"(en base cruda nacional: {_formatear_entero(total_cms_crudo)})"
            ),
            (
                "- **Filas con `produccion > 0` y `area_cosechada == 0` (base filtrada)**: "
                f"{_formatear_entero(total_ppc_filt)} "
                f"(en base cruda nacional: {_formatear_entero(total_ppc_crudo)})"
            ),
            (
                "- **Filas con `area_cosechada == 0` y `produccion == 0` (base filtrada)**: "
                f"{_formatear_entero(total_cosecha_cero_filt)}"
            ),
        ]
    )

    if total_cms_filt > 0:
        resumen_cms = (
            df_filtrado.loc[mascara_cms_filt]
            .groupby(["cultivo", "anio"], as_index=False)
            .agg(
                filas=("periodo", "count"),
                exceso_ha=(
                    "area_cosechada",
                    lambda s: float((s - df_filtrado.loc[s.index, "area_sembrada"]).sum()),
                ),
            )
            .sort_values(["cultivo", "anio"])
        )
        enc_dist_cms = (
            "| Cultivo | Anio | Filas con `area_cosechada > area_sembrada` "
            "| Exceso acumulado (ha) |"
        )
        lineas.extend(
            [
                "",
                "### Distribucion por cultivo y anio de filas con `area_cosechada > area_sembrada`",
                "",
                enc_dist_cms,
                "| :--- | :---: | ---: | ---: |",
            ]
        )
        filas_md_res_cms = (
            "| "
            + resumen_cms["cultivo"]
            + " | "
            + resumen_cms["anio"].astype(str)
            + " | "
            + _serie_entero_fmt(resumen_cms["filas"])
            + " | "
            + _serie_decimal_fmt(resumen_cms["exceso_ha"])
            + " |"
        )
        lineas.extend(filas_md_res_cms.tolist())

        df_cms = df_filtrado.loc[mascara_cms_filt].copy()
        df_cms["exceso_ha"] = df_cms["area_cosechada"] - df_cms["area_sembrada"]
        top_cms = df_cms.sort_values("exceso_ha", ascending=False).head(10)
        enc_cms = (
            "| Codigo Mpio | Municipio | Depto | Cultivo | Desagregacion | Periodo "
            "| Area sembrada (ha) | Area cosechada (ha) | Exceso (ha) | Produccion (t) |"
        )
        titulo_top_cms = (
            "### Top 10 filas con mayor exceso `area_cosechada - area_sembrada` (base filtrada)"
        )
        lineas.extend(
            [
                "",
                titulo_top_cms,
                "",
                enc_cms,
                "| :---: | :--- | :--- | :--- | :--- | :---: | ---: | ---: | ---: | ---: |",
            ]
        )
        filas_md_cms = (
            "| `"
            + top_cms["codigo_dane_municipio"]
            + "` | "
            + top_cms["municipio"]
            + " | "
            + top_cms["departamento"]
            + " | "
            + top_cms["cultivo"]
            + " | "
            + top_cms["desagregacion_cultivo"]
            + " | `"
            + top_cms["periodo"]
            + "` | "
            + _serie_decimal_fmt(top_cms["area_sembrada"])
            + " | "
            + _serie_decimal_fmt(top_cms["area_cosechada"])
            + " | "
            + _serie_decimal_fmt(top_cms["exceso_ha"])
            + " | "
            + _serie_decimal_fmt(top_cms["produccion"])
            + " |"
        )
        lineas.extend(filas_md_cms.tolist())

    enc_totales = (
        "| Cultivo | Anio | Registros | Area sembrada (ha) | Area cosechada (ha) "
        "| Area no cosechada (ha) | Produccion (t) | Rendimiento agregado (t/ha) |"
    )
    lineas.extend(
        [
            "",
            "## 7. Totales por anio y cultivo (area sembrada, area cosechada y produccion)",
            "",
            enc_totales,
            "| :--- | :---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    totales = (
        df_filtrado.groupby(["cultivo", "anio"], as_index=False)
        .agg(
            registros=("periodo", "count"),
            area_sembrada=("area_sembrada", "sum"),
            area_cosechada=("area_cosechada", "sum"),
            produccion=("produccion", "sum"),
        )
        .sort_values(["cultivo", "anio"])
    )
    totales["area_no_cosechada"] = totales["area_sembrada"] - totales["area_cosechada"]
    totales["rendimiento_agregado"] = np.where(
        totales["area_cosechada"] > 0,
        totales["produccion"] / totales["area_cosechada"],
        0.0,
    )

    filas_md_totales = (
        "| "
        + totales["cultivo"]
        + " | "
        + totales["anio"].astype(str)
        + " | "
        + _serie_entero_fmt(totales["registros"])
        + " | "
        + _serie_decimal_fmt(totales["area_sembrada"])
        + " | "
        + _serie_decimal_fmt(totales["area_cosechada"])
        + " | "
        + _serie_decimal_fmt(totales["area_no_cosechada"])
        + " | "
        + _serie_decimal_fmt(totales["produccion"])
        + " | "
        + _serie_decimal_fmt(totales["rendimiento_agregado"], 4)
        + " |"
    )
    lineas.extend(filas_md_totales.tolist())

    enc_subtotales = (
        "| Cultivo | Registros | Area sembrada (ha) | Area cosechada (ha) "
        "| Area no cosechada (ha) | Produccion (t) | Rendimiento agregado (t/ha) |"
    )
    lineas.extend(
        [
            "",
            "### Subtotales por cultivo (2019-2025)",
            "",
            enc_subtotales,
            "| :--- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    subtotales = (
        df_filtrado.groupby("cultivo", as_index=False)
        .agg(
            registros=("periodo", "count"),
            area_sembrada=("area_sembrada", "sum"),
            area_cosechada=("area_cosechada", "sum"),
            produccion=("produccion", "sum"),
        )
        .sort_values("cultivo")
    )
    subtotales["area_no_cosechada"] = subtotales["area_sembrada"] - subtotales["area_cosechada"]
    subtotales["rendimiento_agregado"] = np.where(
        subtotales["area_cosechada"] > 0,
        subtotales["produccion"] / subtotales["area_cosechada"],
        0.0,
    )
    filas_md_subtotales = (
        "| **"
        + subtotales["cultivo"]
        + "** | "
        + _serie_entero_fmt(subtotales["registros"])
        + " | "
        + _serie_decimal_fmt(subtotales["area_sembrada"])
        + " | "
        + _serie_decimal_fmt(subtotales["area_cosechada"])
        + " | "
        + _serie_decimal_fmt(subtotales["area_no_cosechada"])
        + " | "
        + _serie_decimal_fmt(subtotales["produccion"])
        + " | "
        + _serie_decimal_fmt(subtotales["rendimiento_agregado"], 4)
        + " |"
    )
    lineas.extend(filas_md_subtotales.tolist())

    ruta_md.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return ruta_md


def ejecutar_ingesta(
    ruta_config: str | Path,
    ruta_perfil: str | Path | None = "docs/perfil_datos.md",
) -> pd.DataFrame:
    cfg = cargar_configuracion(ruta_config)
    preparar_fuente_cruda(cfg)

    ruta_parquet_crudo = Path(cfg.fuente.parquet_crudo)
    df_crudo = pd.read_parquet(ruta_parquet_crudo)
    df_normalizado = normalizar_columnas_df(df_crudo)

    anio_min_global = min(2019, cfg.anios.inicio)
    anio_max_global = max(2025, cfg.anios.fin)
    df_validado = validar_contrato_eva(
        df_normalizado,
        anio_min=anio_min_global,
        anio_max=anio_max_global,
    )

    df_filtrado = filtrar_eva(df_validado, cfg)
    ruta_parquet_filtrado = Path(cfg.fuente.parquet_filtrado)
    ruta_parquet_filtrado.parent.mkdir(parents=True, exist_ok=True)
    df_filtrado.to_parquet(ruta_parquet_filtrado, index=False)

    if ruta_perfil is not None:
        generar_perfil_datos(df_validado, df_filtrado, cfg, ruta_salida=ruta_perfil)

    return df_filtrado


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ejecuta la ingesta validada de EVA y genera el perfil de datos."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Ruta al archivo YAML de configuracion de la edicion.",
    )
    parser.add_argument(
        "--perfil",
        default="docs/perfil_datos.md",
        help="Ruta de salida para el reporte de perfilado en Markdown.",
    )
    args = parser.parse_args()
    ejecutar_ingesta(args.config, ruta_perfil=args.perfil)


if __name__ == "__main__":
    main()
