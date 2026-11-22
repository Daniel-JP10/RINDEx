"""Evaluacion de robustez de las hipotesis bajo umbrales, exclusion anual, atipicos, D6 y D7."""

import numpy as np
import pandas as pd

from rindex.agregacion import construir_tablas_agregadas
from rindex.config import ConfiguracionEdicion
from rindex.inferencia import (
    ALFA_CONFIRMATORIO,
    MINIMO_UNIDADES_PRUEBA,
    ejecutar_bateria_hipotesis,
)


def clasificar_suficiencia_wilcoxon(n: int) -> str:
    return "insuficiente" if int(n) < MINIMO_UNIDADES_PRUEBA else "suficiente"


def _direccion_efecto(fila: dict[str, object]) -> int:
    ef = float(fila["efecto"])
    if np.isnan(ef):
        return 0
    nombre_ef = str(fila["nombre_efecto"])
    if "razon" in nombre_ef:
        if ef > 1.0:
            return 1
        return -1 if ef < 1.0 else 0
    if ef > 0.0:
        return 1
    return -1 if ef < 0.0 else 0


def _es_insuficiente_fila(fila: dict[str, object]) -> bool:
    n_u = int(fila["n"])
    p_adj = float(fila["valor_p_ajustado"])
    nom_est = str(fila["nombre_estadistico"])
    if np.isnan(p_adj):
        return True
    if nom_est in {"W", "chi2_F", "H"} and n_u < MINIMO_UNIDADES_PRUEBA:
        return True
    return False


def _misma_conclusion(
    fila_base: dict[str, object],
    fila_var: dict[str, object],
) -> bool:
    if _es_insuficiente_fila(fila_base) or _es_insuficiente_fila(fila_var):
        return False

    p_base = float(fila_base["valor_p_ajustado"])
    p_var = float(fila_var["valor_p_ajustado"])
    sig_base = p_base < ALFA_CONFIRMATORIO
    sig_var = p_var < ALFA_CONFIRMATORIO
    if sig_base != sig_var:
        return False

    nombre_ef = str(fila_base["nombre_efecto"])
    if nombre_ef in {"epsilon_cuadrado", "W de Kendall"}:
        return True

    dir_base = _direccion_efecto(fila_base)
    dir_var = _direccion_efecto(fila_var)
    if sig_base:
        return dir_base == dir_var
    return True


def evaluar_robustez_completa(
    df_limpio: pd.DataFrame,
    df_oni: pd.DataFrame,
    resultados_base: pd.DataFrame,
    cfg: ConfiguracionEdicion,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    tablas_completas = construir_tablas_agregadas(df_limpio, cfg)
    replicas_rob = cfg.parametros.bootstrap_robustez
    umbral_base = cfg.parametros.area_cosechada_minima_ha

    variantes: list[tuple[str, pd.DataFrame]] = []

    # 1. Umbrales alternativos de elegibilidad: 300 y 1000 ha
    for u_ha in (300.0, 1000.0):
        res_u = ejecutar_bateria_hipotesis(
            tablas=tablas_completas,
            df_oni=df_oni,
            cfg=cfg,
            umbral_ha=u_ha,
            replicas_boot=replicas_rob,
            unidad_h2_h3="municipio",
        )["resumen_hipotesis"]
        variantes.append((f"umbral_{int(u_ha)}ha", res_u))

    # 2. Dejar un anio fuera a la vez (2019 a 2025)
    for anio_fuera in range(cfg.anios.inicio, cfg.anios.fin + 1):
        df_sin_anio = df_limpio.loc[df_limpio["anio"] != anio_fuera]
        tablas_sin_anio = construir_tablas_agregadas(df_sin_anio, cfg)
        oni_sin_anio = df_oni.loc[df_oni["anio"] != anio_fuera]
        res_a = ejecutar_bateria_hipotesis(
            tablas=tablas_sin_anio,
            df_oni=oni_sin_anio,
            cfg=cfg,
            umbral_ha=umbral_base,
            replicas_boot=replicas_rob,
            unidad_h2_h3="municipio",
        )["resumen_hipotesis"]
        variantes.append((f"sin_{anio_fuera}", res_a))

    # 3. Excluir filas marcadas como atipicas
    mascara_atip = df_limpio["fuera_de_rango"] | df_limpio["atipico_robusto"]
    df_sin_atip = df_limpio.loc[~mascara_atip]
    tablas_sin_atip = construir_tablas_agregadas(df_sin_atip, cfg)
    res_atip = ejecutar_bateria_hipotesis(
        tablas=tablas_sin_atip,
        df_oni=df_oni,
        cfg=cfg,
        umbral_ha=umbral_base,
        replicas_boot=replicas_rob,
        unidad_h2_h3="municipio",
    )["resumen_hipotesis"]
    variantes.append(("sin_atipicos", res_atip))

    # 4. Unidad municipio-anio para H2 y H3 (D1)
    res_mpio_anio = ejecutar_bateria_hipotesis(
        tablas=tablas_completas,
        df_oni=df_oni,
        cfg=cfg,
        umbral_ha=umbral_base,
        replicas_boot=replicas_rob,
        unidad_h2_h3="municipio_anio",
    )["resumen_hipotesis"]
    res_mpio_anio_h2_h3 = res_mpio_anio.loc[res_mpio_anio["familia"].isin(["H2", "H3"])].copy()
    variantes.append(("municipio_anio", res_mpio_anio_h2_h3))

    # 5. Sensibilidad adicional post-hoc D7: H1 y H5 sin series poco informativas
    res_d7 = ejecutar_bateria_hipotesis(
        tablas=tablas_completas,
        df_oni=df_oni,
        cfg=cfg,
        umbral_ha=umbral_base,
        replicas_boot=replicas_rob,
        unidad_h2_h3="municipio",
        excluir_poco_informativas=True,
    )["resumen_hipotesis"]
    res_d7_h1_h5 = res_d7.loc[res_d7["familia"].isin(["H1", "H5"])].copy()
    variantes.append(("sin_poco_informativas_D7", res_d7_h1_h5))

    mapa_base = {
        str(fila["id_hipotesis"]): fila for fila in resultados_base.to_dict(orient="records")
    }

    filas_detalle: list[dict[str, object]] = []
    discrepancias_por_id: dict[str, list[str]] = {k: [] for k in mapa_base}

    for nombre_var, df_var in variantes:
        for fila_v in df_var.to_dict(orient="records"):
            id_h = str(fila_v["id_hipotesis"])
            if id_h not in mapa_base:
                continue
            fila_b = mapa_base[id_h]

            mantiene = _misma_conclusion(fila_b, fila_v)
            if not mantiene and not _es_insuficiente_fila(fila_b):
                discrepancias_por_id[id_h].append(nombre_var)

            filas_detalle.append(
                {
                    "id_hipotesis": id_h,
                    "familia": fila_v["familia"],
                    "variante": nombre_var,
                    "n": fila_v["n"],
                    "estadistico": fila_v["estadistico"],
                    "valor_p": fila_v["valor_p"],
                    "valor_p_ajustado": fila_v["valor_p_ajustado"],
                    "efecto": fila_v["efecto"],
                    "ic_95_inf": fila_v["ic_95_inf"],
                    "ic_95_sup": fila_v["ic_95_sup"],
                    "decision": fila_v["decision"],
                    "mantiene_conclusion": mantiene,
                }
            )

    filas_resumen: list[dict[str, object]] = []
    for id_h, fila_b in mapa_base.items():
        n_base = int(fila_b["n"])
        p_base = float(fila_b["valor_p_ajustado"])
        lista_disc = discrepancias_por_id[id_h]
        if _es_insuficiente_fila(fila_b):
            clasificacion = "insuficiente"
        elif len(lista_disc) == 0:
            clasificacion = "firme"
        else:
            clasificacion = "fragil"

        filas_resumen.append(
            {
                "id_hipotesis": id_h,
                "hipotesis": fila_b["hipotesis"],
                "familia": fila_b["familia"],
                "n_base": n_base,
                "efecto_base": fila_b["efecto"],
                "valor_p_ajustado_base": p_base,
                "decision_base": fila_b["decision"],
                "clasificacion_robustez": clasificacion,
                "num_discrepancias": len(lista_disc),
                "variantes_discrepantes": ", ".join(lista_disc),
            }
        )

    return pd.DataFrame(filas_detalle), pd.DataFrame(filas_resumen)
