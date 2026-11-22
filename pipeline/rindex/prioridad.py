"""Tipologia de decision municipal, indice de prioridad y sensibilidad de Dirichlet."""

import numpy as np
import pandas as pd
from scipy import stats

from rindex.config import ConfiguracionEdicion


def _rango_percentil_0_1(valores: np.ndarray) -> np.ndarray:
    arr = np.asarray(valores, dtype=float)
    n = len(arr)
    if n == 0:
        return np.array([], dtype=float)
    if n == 1:
        return np.array([1.0], dtype=float)
    if np.all(arr == arr[0]):
        return np.full(n, 0.5, dtype=float)
    rangos = stats.rankdata(arr, method="average")
    return (rangos - 1.0) / float(n - 1)


def construir_tipologia_decision(periodo_mpio_cultivo: pd.DataFrame) -> pd.DataFrame:
    eleg = periodo_mpio_cultivo.loc[periodo_mpio_cultivo["elegible_500"]].copy()
    if eleg.empty:
        return pd.DataFrame()

    mediana_depto = eleg.groupby(["codigo_dane_departamento", "cultivo"], as_index=False)[
        "rendimiento"
    ].transform("median")
    eleg["mediana_rendimiento_depto"] = mediana_depto

    # Mediana regional del CV calculada sobre las series informativas del cultivo
    cv_informativo = eleg["cv_interanual"].where(~eleg["serie_poco_informativa"], np.nan)
    eleg["_cv_inf"] = cv_informativo
    mediana_cv_reg = eleg.groupby("cultivo")["_cv_inf"].transform("median")
    eleg["mediana_cv_regional"] = mediana_cv_reg
    eleg = eleg.drop(columns=["_cv_inf"])

    es_alto = eleg["rendimiento"] >= eleg["mediana_rendimiento_depto"]
    es_estable = eleg["cv_interanual"] <= eleg["mediana_cv_regional"]
    no_medible = eleg["serie_poco_informativa"] | eleg["cv_interanual"].isna()

    cuadrantes = np.where(
        no_medible,
        "estabilidad_no_medible",
        np.where(
            es_alto & es_estable,
            "consolidar",
            np.where(
                es_alto & (~es_estable),
                "proteger",
                np.where((~es_alto) & es_estable, "tecnificar", "intervencion_integral"),
            ),
        ),
    )
    eleg["cuadrante"] = cuadrantes
    return eleg.sort_values(
        ["cultivo", "codigo_dane_departamento", "codigo_dane_municipio"]
    ).reset_index(drop=True)


def generar_pesos_dirichlet(
    parametros: tuple[float, float, float, float],
    juegos: int,
    semilla: int,
) -> np.ndarray:
    rng = np.random.default_rng(semilla)
    return rng.dirichlet(np.asarray(parametros, dtype=float), size=juegos)


def calcular_indice_prioridad(
    df_tipologia: pd.DataFrame,
    df_escenarios: pd.DataFrame,
    cfg: ConfiguracionEdicion,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    cols_esc = [
        "codigo_dane_municipio",
        "cultivo",
        "s1_p50",
        "s1_p10",
        "s1_p90",
        "s1_brecha_relativa_pct",
        "combinado_p50",
    ]
    base = df_tipologia.merge(
        df_escenarios[cols_esc],
        on=["codigo_dane_municipio", "cultivo"],
        how="inner",
    )

    pesos_cfg = cfg.priorizacion.pesos
    w_defecto = np.array(
        [
            pesos_cfg.ganancia,
            pesos_cfg.brecha_relativa,
            pesos_cfg.estabilidad,
            pesos_cfg.confiabilidad,
        ],
        dtype=float,
    )
    w_defecto = w_defecto / w_defecto.sum()

    matriz_w_dir = generar_pesos_dirichlet(
        parametros=cfg.priorizacion.parametros_dirichlet,
        juegos=cfg.priorizacion.juegos_dirichlet,
        semilla=cfg.parametros.semilla_aleatoria + 7000,
    )

    partes_out: list[pd.DataFrame] = []
    resumen_tau: list[dict[str, object]] = []
    top_k = cfg.priorizacion.top_k
    umbral_rob = cfg.priorizacion.umbral_robustez_top

    for cultivo, sub_raw in base.groupby("cultivo", sort=True):
        sub = sub_raw.sort_values("codigo_dane_municipio").copy().reset_index(drop=True)
        n_c = len(sub)

        comp_ganancia = _rango_percentil_0_1(sub["s1_p50"].to_numpy(dtype=float))
        comp_brecha = _rango_percentil_0_1(sub["s1_brecha_relativa_pct"].to_numpy(dtype=float))

        # Estabilidad: 1 menos el percentil del CV (series poco informativas reciben 0.5 neutro)
        cv_arr = sub["cv_interanual"].to_numpy(dtype=float)
        poco_inf = sub["serie_poco_informativa"].to_numpy(dtype=bool)
        mascara_cv_valido = (~poco_inf) & (~np.isnan(cv_arr))
        comp_estabilidad = np.full(n_c, 0.5, dtype=float)
        if mascara_cv_valido.sum() >= 2:
            comp_estabilidad[mascara_cv_valido] = 1.0 - _rango_percentil_0_1(
                cv_arr[mascara_cv_valido]
            )

        # Confiabilidad: 1 menos proporcion de repetidos y tasa de filas atipicas
        prop_rep = sub["proporcion_repetidos"].to_numpy(dtype=float)
        prop_atip = np.where(
            sub["registros"] > 0,
            sub["filas_atipicas"] / sub["registros"],
            0.0,
        )
        puntaje_conf_crudo = np.clip(1.0 - 0.5 * (prop_rep + prop_atip), 0.0, 1.0)
        comp_confiabilidad = _rango_percentil_0_1(puntaje_conf_crudo)

        mat_comp = np.column_stack(
            [comp_ganancia, comp_brecha, comp_estabilidad, comp_confiabilidad]
        )
        indice_def = 100.0 * (mat_comp @ w_defecto)
        indice_def = np.clip(indice_def, 0.0, 100.0)

        # Rango 1 = mayor indice (desempate determinista por orden de codigo_dane_municipio)
        orden_def = np.argsort(-indice_def, kind="mergesort")
        rango_def = np.empty(n_c, dtype=int)
        rango_def[orden_def] = np.arange(1, n_c + 1)

        # Simulacion vectorizada de 2000 juegos de Dirichlet
        puntajes_sim = 100.0 * (mat_comp @ matriz_w_dir.T)
        orden_sim = np.argsort(-puntajes_sim, axis=0, kind="mergesort")
        rangos_sim = np.empty_like(orden_sim)
        filas_idx = np.arange(1, n_c + 1)[:, None]
        np.put_along_axis(rangos_sim, orden_sim, filas_idx, axis=0)

        rango_med = np.median(rangos_sim, axis=1)
        rango_p10 = np.quantile(rangos_sim, 0.10, axis=1)
        rango_p90 = np.quantile(rangos_sim, 0.90, axis=1)
        prop_top = np.mean(rangos_sim <= min(top_k, n_c), axis=1)
        prio_rob = prop_top >= umbral_rob

        # Tau de Kendall mediana entre el ranking por defecto y los 2000 juegos aleatorios
        taus = np.empty(matriz_w_dir.shape[0], dtype=float)
        for j in range(matriz_w_dir.shape[0]):
            taus[j] = float(stats.kendalltau(rango_def, rangos_sim[:, j]).statistic)
        tau_mediana = float(np.nanmedian(taus))
        tau_p10, tau_p90 = (float(v) for v in np.nanquantile(taus, [0.10, 0.90]))

        resumen_tau.append(
            {
                "cultivo": str(cultivo),
                "municipios_elegibles": n_c,
                "juegos_dirichlet": int(matriz_w_dir.shape[0]),
                "tau_kendall_mediana": tau_mediana,
                "tau_kendall_p10": tau_p10,
                "tau_kendall_p90": tau_p90,
                "municipios_prioridad_robusta": int(prio_rob.sum()),
            }
        )

        sub["comp_ganancia"] = comp_ganancia
        sub["comp_brecha_relativa"] = comp_brecha
        sub["comp_estabilidad"] = comp_estabilidad
        sub["comp_confiabilidad"] = comp_confiabilidad
        sub["indice_prioridad"] = indice_def
        sub["rango_defecto"] = rango_def
        sub["rango_mediano"] = rango_med
        sub["rango_p10"] = rango_p10
        sub["rango_p90"] = rango_p90
        sub["proporcion_top20"] = prop_top
        sub["prioridad_robusta"] = prio_rob
        sub["tau_kendall_mediana_cultivo"] = tau_mediana

        partes_out.append(sub.sort_values("rango_defecto").reset_index(drop=True))

    return pd.concat(partes_out, ignore_index=True), pd.DataFrame(resumen_tau)
