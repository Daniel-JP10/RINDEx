"""Clasificacion de niveles de evidencia por cultivo y municipio (D9) y descriptivo arroz 2021."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from rindex.agregacion import construir_tablas_agregadas
from rindex.calidad import calcular_metricas_repeticion_series
from rindex.config import ConfiguracionEdicion, cargar_configuracion
from rindex.limpieza import limpiar_eva


def clasificar_nivel_evidencia_cultivo(
    pct_pares_identicos: float,
    pct_rendimientos_enteros: float,
    cfg: ConfiguracionEdicion,
) -> str:
    reglas = cfg.evidencia.cultivo
    if (
        pct_pares_identicos < reglas.alto_max_pares_identicos_pct
        and pct_rendimientos_enteros < reglas.alto_max_enteros_pct
    ):
        return "alto"
    if (
        pct_pares_identicos < reglas.medio_max_pares_identicos_pct
        or pct_rendimientos_enteros < reglas.medio_max_enteros_pct
    ):
        return "medio"
    return "bajo"


def calcular_evidencia_por_cultivo(
    df_limpio: pd.DataFrame,
    anual_mpio_cultivo: pd.DataFrame,
    cfg: ConfiguracionEdicion,
) -> pd.DataFrame:
    diag = calcular_metricas_repeticion_series(
        anual_mpio_cultivo,
        llaves_serie=["codigo_dane_municipio", "cultivo"],
    )
    conteos_anios = (
        anual_mpio_cultivo.loc[anual_mpio_cultivo["area_cosechada"] > 0]
        .groupby(["codigo_dane_municipio", "cultivo"], as_index=False)["anio"]
        .count()
        .rename(columns={"anio": "anios_con_dato"})
    )
    diag = diag.merge(conteos_anios, on=["codigo_dane_municipio", "cultivo"], how="left")
    diag["anios_con_dato"] = diag["anios_con_dato"].fillna(0).astype(int)
    diag_2 = diag.loc[diag["anios_con_dato"] >= 2]

    rep_cul = diag_2.groupby("cultivo", as_index=False).agg(
        series_evaluadas=("anios_con_dato", "count"),
        pares_consecutivos=("pares_consecutivos", "sum"),
        pares_identicos=("pares_identicos", "sum"),
        series_poco_informativas=("serie_poco_informativa", "sum"),
    )
    rep_cul["pct_pares_identicos"] = np.where(
        rep_cul["pares_consecutivos"] > 0,
        rep_cul["pares_identicos"] / rep_cul["pares_consecutivos"] * 100.0,
        0.0,
    )

    df_sem_pos = df_limpio.loc[df_limpio["area_cosechada"] > 0].copy()
    y_sem = df_sem_pos["rendimiento"].to_numpy(dtype=float)
    df_sem_pos["es_entero"] = np.abs(y_sem - np.round(y_sem)) <= 1e-6
    ent_sem = df_sem_pos.groupby("cultivo", as_index=False).agg(
        filas_semestrales=("rendimiento", "count"),
        filas_enteras_semestral=("es_entero", "sum"),
    )
    ent_sem["pct_rendimientos_enteros"] = np.where(
        ent_sem["filas_semestrales"] > 0,
        ent_sem["filas_enteras_semestral"] / ent_sem["filas_semestrales"] * 100.0,
        0.0,
    )

    df_an_pos = anual_mpio_cultivo.loc[anual_mpio_cultivo["area_cosechada"] > 0].copy()
    y_an = df_an_pos["rendimiento"].to_numpy(dtype=float)
    df_an_pos["es_entero_anual"] = np.abs(y_an - np.round(y_an)) <= 1e-6
    ent_an = df_an_pos.groupby("cultivo", as_index=False).agg(
        registros_anuales=("rendimiento", "count"),
        registros_enteros_anual=("es_entero_anual", "sum"),
    )
    ent_an["pct_enteros_anual"] = np.where(
        ent_an["registros_anuales"] > 0,
        ent_an["registros_enteros_anual"] / ent_an["registros_anuales"] * 100.0,
        0.0,
    )

    res = (
        rep_cul.merge(ent_sem, on="cultivo", how="outer")
        .merge(ent_an, on="cultivo", how="outer")
        .sort_values("cultivo")
        .reset_index(drop=True)
    )
    res["nivel_evidencia"] = [
        clasificar_nivel_evidencia_cultivo(
            pct_pares_identicos=float(f["pct_pares_identicos"]),
            pct_rendimientos_enteros=float(f["pct_rendimientos_enteros"]),
            cfg=cfg,
        )
        for f in res.to_dict(orient="records")
    ]
    return res


def calcular_evidencia_municipal(
    periodo_mpio_cultivo: pd.DataFrame,
    evidencia_cultivo: pd.DataFrame,
    cfg: ConfiguracionEdicion,
) -> pd.DataFrame:
    reglas_m = cfg.evidencia.municipal
    anios_min = cfg.parametros.anios_minimos_con_dato

    df = periodo_mpio_cultivo[
        [
            "codigo_dane_departamento",
            "departamento",
            "codigo_dane_municipio",
            "municipio",
            "cultivo",
            "anios_con_dato",
            "area_cosechada",
            "elegible_500",
            "proporcion_repetidos",
            "serie_poco_informativa",
            "filas_atipicas",
        ]
    ].copy()

    mapa_cul = dict(
        zip(
            evidencia_cultivo["cultivo"],
            evidencia_cultivo["nivel_evidencia"],
            strict=True,
        )
    )
    df["nivel_evidencia_cultivo"] = df["cultivo"].map(mapa_cul).fillna("bajo")

    cond_alto = (
        (df["anios_con_dato"] >= anios_min)
        & (df["proporcion_repetidos"] < reglas_m.alto_max_proporcion_repetidos)
        & (df["filas_atipicas"] <= reglas_m.alto_max_filas_atipicas)
    )
    cond_medio = (
        (df["anios_con_dato"] >= anios_min)
        & (df["proporcion_repetidos"] <= reglas_m.medio_max_proporcion_repetidos)
        & (df["filas_atipicas"] <= reglas_m.medio_max_filas_atipicas)
    )

    df["nivel_evidencia_municipal"] = np.where(
        cond_alto,
        "alto",
        np.where(cond_medio, "medio", "bajo"),
    )
    return df.sort_values(["cultivo", "codigo_dane_municipio"]).reset_index(drop=True)


def calcular_concentracion_arroz_2021(
    anual_mpio_cultivo: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, float]]:
    arroz_21 = anual_mpio_cultivo.loc[
        (anual_mpio_cultivo["cultivo"] == "Arroz") & (anual_mpio_cultivo["anio"] == 2021)
    ].copy()

    arroz_21["area_no_cosechada_ha"] = np.maximum(
        0.0,
        arroz_21["area_sembrada"] - arroz_21["area_cosechada"],
    )
    arroz_21["tasa_propia_pct"] = np.where(
        arroz_21["area_sembrada"] > 0,
        arroz_21["area_no_cosechada_ha"] / arroz_21["area_sembrada"] * 100.0,
        0.0,
    )
    total_no_cos = float(arroz_21["area_no_cosechada_ha"].sum())
    total_sem = float(arroz_21["area_sembrada"].sum())
    total_cos = float(arroz_21["area_cosechada"].sum())

    arroz_21 = arroz_21.sort_values(
        ["area_no_cosechada_ha", "codigo_dane_municipio"],
        ascending=[False, True],
    ).reset_index(drop=True)
    arroz_21["rango"] = np.arange(1, len(arroz_21) + 1, dtype=int)
    arroz_21["pct_total_regional"] = np.where(
        total_no_cos > 0,
        arroz_21["area_no_cosechada_ha"] / total_no_cos * 100.0,
        0.0,
    )
    arroz_21["pct_acumulado_regional"] = arroz_21["pct_total_regional"].cumsum()

    top5_ha = float(arroz_21.head(5)["area_no_cosechada_ha"].sum())
    top10_ha = float(arroz_21.head(10)["area_no_cosechada_ha"].sum())
    resumen = {
        "area_sembrada_regional_2021_ha": total_sem,
        "area_cosechada_regional_2021_ha": total_cos,
        "area_no_cosechada_regional_2021_ha": total_no_cos,
        "tasa_regional_2021_pct": (total_no_cos / total_sem * 100.0) if total_sem > 0 else 0.0,
        "top5_area_no_cosechada_ha": top5_ha,
        "top5_pct_regional": (top5_ha / total_no_cos * 100.0) if total_no_cos > 0 else 0.0,
        "top10_area_no_cosechada_ha": top10_ha,
        "top10_pct_regional": (top10_ha / total_no_cos * 100.0) if total_no_cos > 0 else 0.0,
    }
    cols = [
        "rango",
        "codigo_dane_departamento",
        "departamento",
        "codigo_dane_municipio",
        "municipio",
        "area_sembrada",
        "area_cosechada",
        "area_no_cosechada_ha",
        "tasa_propia_pct",
        "pct_total_regional",
        "pct_acumulado_regional",
    ]
    return arroz_21[cols], resumen


def ejecutar_evidencia(ruta_config: str | Path) -> dict[str, pd.DataFrame]:
    cfg = cargar_configuracion(ruta_config)
    ruta_filtrado = Path(cfg.fuente.parquet_filtrado)
    dir_interim = ruta_filtrado.parent
    dir_resultados = dir_interim / "resultados"
    dir_resultados.mkdir(parents=True, exist_ok=True)

    df_filtrado = pd.read_parquet(ruta_filtrado)
    df_limpio = limpiar_eva(df_filtrado, cfg)
    anual_path = dir_interim / "anual_municipio_cultivo.parquet"
    per_path = dir_interim / "periodo_municipio_cultivo.parquet"
    if anual_path.exists() and per_path.exists():
        anual_mpio_cultivo = pd.read_parquet(anual_path)
        periodo_mpio_cultivo = pd.read_parquet(per_path)
    else:
        tablas = construir_tablas_agregadas(df_limpio, cfg)
        anual_mpio_cultivo = tablas["anual_municipio_cultivo"]
        periodo_mpio_cultivo = tablas["periodo_municipio_cultivo"]

    ev_cultivo = calcular_evidencia_por_cultivo(df_limpio, anual_mpio_cultivo, cfg)
    ev_municipal = calcular_evidencia_municipal(periodo_mpio_cultivo, ev_cultivo, cfg)
    arroz_2021, _ = calcular_concentracion_arroz_2021(anual_mpio_cultivo)

    ev_cultivo.to_parquet(dir_resultados / "evidencia_cultivo.parquet", index=False)
    ev_municipal.to_parquet(dir_resultados / "evidencia_municipal.parquet", index=False)
    arroz_2021.to_parquet(dir_resultados / "arroz_2021_concentracion.parquet", index=False)

    return {
        "evidencia_cultivo": ev_cultivo,
        "evidencia_municipal": ev_municipal,
        "arroz_2021_concentracion": arroz_2021,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calcula niveles de evidencia por cultivo y municipio y descriptivo arroz 2021."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Ruta al archivo YAML de configuracion de la edicion.",
    )
    args = parser.parse_args()
    ejecutar_evidencia(args.config)


if __name__ == "__main__":
    main()
