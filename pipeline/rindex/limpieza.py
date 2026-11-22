"""Limpieza, mapeo de sistemas productivos y marcacion de valores atipicos."""

import numpy as np
import pandas as pd

from rindex.config import ConfiguracionEdicion

FACTOR_CONSISTENCIA_MAD = 0.67448975


def aplicar_mapeo_desagregacion(
    df: pd.DataFrame,
    cfg: ConfiguracionEdicion,
) -> pd.DataFrame:
    valores_presentes = set(df["desagregacion_cultivo"].dropna().unique())
    valores_configurados = set(cfg.mapeo_desagregacion.keys())
    sin_mapear = sorted(valores_presentes - valores_configurados)
    if sin_mapear:
        lista_txt = ", ".join(f"'{v}'" for v in sin_mapear)
        raise ValueError(
            f"Existen valores de desagregacion_cultivo sin mapear en la configuracion: {lista_txt}."
        )

    mapa_cultivo = {k: v.cultivo for k, v in cfg.mapeo_desagregacion.items()}
    mapa_sistema = {k: v.sistema for k, v in cfg.mapeo_desagregacion.items()}
    mapa_color = {k: v.color for k, v in cfg.mapeo_desagregacion.items()}

    cultivo_esperado = df["desagregacion_cultivo"].map(mapa_cultivo)
    inconsistentes = df["cultivo"] != cultivo_esperado
    if inconsistentes.any():
        ejemplos = (
            df.loc[inconsistentes, ["cultivo", "desagregacion_cultivo"]]
            .drop_duplicates()
            .to_dict(orient="records")
        )
        raise ValueError(
            f"Inconsistencia entre cultivo y mapeo de desagregacion_cultivo: {ejemplos}."
        )

    resultado = df.copy()
    resultado["sistema"] = resultado["desagregacion_cultivo"].map(mapa_sistema)
    resultado["color"] = resultado["desagregacion_cultivo"].map(mapa_color)
    return resultado


def marcar_atipicos_rendimiento(
    df: pd.DataFrame,
    cfg: ConfiguracionEdicion,
) -> pd.DataFrame:
    resultado = df.copy()

    # Filas con area cosechada y produccion en cero se conservan pero no aportan al rendimiento
    mascara_aporta = resultado["area_cosechada"] > 0
    rendimiento_efectivo = np.where(
        mascara_aporta,
        resultado["produccion"] / resultado["area_cosechada"],
        np.nan,
    )
    resultado["rendimiento"] = rendimiento_efectivo

    mapa_min = {k: v.minimo for k, v in cfg.limites_plausibilidad_rendimiento.items()}
    mapa_max = {k: v.maximo for k, v in cfg.limites_plausibilidad_rendimiento.items()}
    lim_min = resultado["cultivo"].map(mapa_min)
    lim_max = resultado["cultivo"].map(mapa_max)

    fuera_rango = mascara_aporta & (
        (resultado["rendimiento"] < lim_min) | (resultado["rendimiento"] > lim_max)
    )
    resultado["fuera_de_rango"] = fuera_rango.fillna(False).astype(bool)

    mascara_positiva = mascara_aporta & (resultado["produccion"] > 0)
    log_rend = pd.Series(np.nan, index=resultado.index, dtype=float)
    log_rend.loc[mascara_positiva] = np.log(resultado.loc[mascara_positiva, "rendimiento"])

    resultado["_log_rend"] = log_rend
    mediana_log = resultado.groupby(["cultivo", "sistema"])["_log_rend"].transform("median")
    resultado["_desv_abs_log"] = (resultado["_log_rend"] - mediana_log).abs()
    mad_log = resultado.groupby(["cultivo", "sistema"])["_desv_abs_log"].transform("median")

    diferencia_log = resultado["_log_rend"] - mediana_log
    z_robusto = np.where(
        mascara_positiva & (mad_log > 0),
        FACTOR_CONSISTENCIA_MAD * diferencia_log / mad_log,
        np.where(
            mascara_positiva & (mad_log == 0) & (diferencia_log != 0),
            np.sign(diferencia_log) * np.inf,
            np.where(mascara_positiva, 0.0, np.nan),
        ),
    )
    resultado["z_robusto"] = z_robusto
    resultado["atipico_robusto"] = (
        pd.Series(z_robusto, index=resultado.index).abs() > cfg.parametros.umbral_z_robusto
    ).fillna(False)

    return resultado.drop(columns=["_log_rend", "_desv_abs_log"])


def limpiar_eva(
    df_filtrado: pd.DataFrame,
    cfg: ConfiguracionEdicion,
) -> pd.DataFrame:
    df_mapeado = aplicar_mapeo_desagregacion(df_filtrado, cfg)
    return marcar_atipicos_rendimiento(df_mapeado, cfg)
