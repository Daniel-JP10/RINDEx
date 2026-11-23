"""Calculo de brecha potencial de rendimiento y ganancia anual con bootstrap de dos niveles."""

import numpy as np
import pandas as pd

from rindex.config import ConfiguracionEdicion


def simular_brecha_bootstrap_unidad(
    areas_anuales: np.ndarray,
    producciones_anuales: np.ndarray,
    rendimientos_grupo_ref: np.ndarray,
    semilla: int,
    replicas: int = 5000,
    dos_niveles: bool = True,
    percentil_ref: float = 75.0,
) -> tuple[np.ndarray, np.ndarray]:
    areas = np.asarray(areas_anuales, dtype=float)
    prods = np.asarray(producciones_anuales, dtype=float)
    ref_pool = np.asarray(rendimientos_grupo_ref, dtype=float)

    k = len(areas)
    m = len(ref_pool)
    if k == 0 or m == 0:
        ceros = np.zeros(replicas, dtype=float)
        return ceros, ceros

    rng = np.random.default_rng(semilla)
    idx_anios = rng.integers(0, k, size=(replicas, k))
    areas_boot = areas[idx_anios]
    prods_boot = prods[idx_anios]

    suma_area = areas_boot.sum(axis=1)
    suma_prod = prods_boot.sum(axis=1)
    rend_mpio_boot = np.where(suma_area > 0, suma_prod / suma_area, 0.0)
    area_media_boot = suma_area / float(k)

    if dos_niveles and m >= 2:
        idx_ref = rng.integers(0, m, size=(replicas, m))
        muestra_ref = ref_pool[idx_ref]
        ref_boot = np.percentile(muestra_ref, percentil_ref, axis=1)
    else:
        ref_fija = float(np.percentile(ref_pool, percentil_ref))
        ref_boot = np.full(replicas, ref_fija, dtype=float)

    brechas_boot = np.maximum(0.0, ref_boot - rend_mpio_boot)
    ganancias_boot = brechas_boot * area_media_boot
    return brechas_boot, ganancias_boot


def calcular_brecha_potencial_con_replicas(
    periodo_mpio_sistema: pd.DataFrame,
    anual_mpio_sistema: pd.DataFrame,
    cfg: ConfiguracionEdicion,
    replicas_boot: int | None = None,
) -> tuple[pd.DataFrame, dict[tuple[str, str, str], np.ndarray]]:
    replicas = replicas_boot if replicas_boot is not None else cfg.parametros.replicas_bootstrap
    min_mpios_depto = cfg.priorizacion.minimo_municipios_referencia_depto
    pct_ref = cfg.priorizacion.percentil_referencia

    elegibles = periodo_mpio_sistema.loc[periodo_mpio_sistema["elegible_500"]].copy()
    if elegibles.empty:
        return pd.DataFrame(), {}

    elegibles = elegibles.sort_values(
        ["cultivo", "sistema", "codigo_dane_departamento", "codigo_dane_municipio"]
    ).reset_index(drop=True)

    elegibles["area_cosechada_media_anual"] = (
        elegibles["area_cosechada"] / elegibles["anios_con_dato"]
    )
    elegibles["produccion_media_anual"] = elegibles["produccion"] / elegibles["anios_con_dato"]

    # Construir piscinas de referencia por (depto, cultivo, sistema) y regional (cultivo, sistema)
    pool_regional: dict[tuple[str, str], np.ndarray] = {}
    for (cult, sis), sub_reg in elegibles.groupby(["cultivo", "sistema"]):
        pool_regional[(str(cult), str(sis))] = sub_reg["rendimiento"].dropna().to_numpy(dtype=float)

    pool_depto: dict[tuple[str, str, str], np.ndarray] = {}
    for (depto, cult, sis), sub_dep in elegibles.groupby(
        ["codigo_dane_departamento", "cultivo", "sistema"]
    ):
        pool_depto[(str(depto), str(cult), str(sis))] = (
            sub_dep["rendimiento"].dropna().to_numpy(dtype=float)
        )

    # Historial anual por (codigo_dane_municipio, cultivo, sistema) con cosecha positiva
    anual_pos = anual_mpio_sistema.loc[anual_mpio_sistema["area_cosechada"] > 0].sort_values(
        ["codigo_dane_municipio", "cultivo", "sistema", "anio"]
    )
    historial_anual: dict[tuple[str, str, str], tuple[np.ndarray, np.ndarray]] = {}
    for (mpio, cult, sis), sub_a in anual_pos.groupby(
        ["codigo_dane_municipio", "cultivo", "sistema"], sort=False
    ):
        historial_anual[(str(mpio), str(cult), str(sis))] = (
            sub_a["area_cosechada"].to_numpy(dtype=float),
            sub_a["produccion"].to_numpy(dtype=float),
        )

    filas_out: list[dict[str, object]] = []
    replicas_s1: dict[tuple[str, str, str], np.ndarray] = {}
    semilla_base = cfg.parametros.semilla_aleatoria + 1000

    for idx, fila in enumerate(elegibles.to_dict(orient="records")):
        depto = str(fila["codigo_dane_departamento"])
        mpio = str(fila["codigo_dane_municipio"])
        cult = str(fila["cultivo"])
        sis = str(fila["sistema"])
        rend_mpio = float(fila["rendimiento"])
        area_media = float(fila["area_cosechada_media_anual"])
        poco_inf = bool(fila.get("serie_poco_informativa", False))

        arr_depto = pool_depto.get((depto, cult, sis), np.array([], dtype=float))
        if len(arr_depto) >= min_mpios_depto:
            pool_ref = arr_depto
            es_ref_regional = False
            n_ref = len(arr_depto)
        else:
            pool_ref = pool_regional.get((cult, sis), np.array([rend_mpio], dtype=float))
            es_ref_regional = True
            n_ref = len(pool_ref)

        rend_ref = float(np.percentile(pool_ref, pct_ref))
        brecha_puntual = max(0.0, rend_ref - rend_mpio)
        brecha_rel_pct = (brecha_puntual / rend_ref * 100.0) if rend_ref > 0 else 0.0
        ganancia_puntual = brecha_puntual * area_media

        if brecha_puntual <= 0.0:
            b_p10, b_p50, b_p90 = 0.0, 0.0, 0.0
            g_p10, g_p50, g_p90 = 0.0, 0.0, 0.0
            ganancias_b = np.zeros(replicas, dtype=float)
        else:
            areas_h, prods_h = historial_anual.get(
                (mpio, cult, sis),
                (np.array([area_media]), np.array([area_media * rend_mpio])),
            )
            brechas_b, ganancias_b = simular_brecha_bootstrap_unidad(
                areas_anuales=areas_h,
                producciones_anuales=prods_h,
                rendimientos_grupo_ref=pool_ref,
                semilla=semilla_base + idx,
                replicas=replicas,
                dos_niveles=True,
                percentil_ref=pct_ref,
            )
            b_p10, b_p50, b_p90 = (float(v) for v in np.quantile(brechas_b, [0.10, 0.50, 0.90]))
            g_p10, g_p50, g_p90 = (float(v) for v in np.quantile(ganancias_b, [0.10, 0.50, 0.90]))

        replicas_s1[(mpio, cult, sis)] = ganancias_b

        registro = dict(fila)
        registro.update(
            {
                "n_grupo_referencia": int(n_ref),
                "referencia_regional": bool(es_ref_regional),
                "rendimiento_referencia": rend_ref,
                "brecha_tha": brecha_puntual,
                "brecha_relativa_pct": brecha_rel_pct,
                "ganancia_anual_t": ganancia_puntual,
                "brecha_p10": b_p10,
                "brecha_p50": b_p50,
                "brecha_p90": b_p90,
                "ganancia_p10": g_p10,
                "ganancia_p50": g_p50,
                "ganancia_p90": g_p90,
                "rango_no_informativo": poco_inf,
            }
        )
        filas_out.append(registro)

    return pd.DataFrame(filas_out), replicas_s1


def calcular_brecha_potencial(
    periodo_mpio_sistema: pd.DataFrame,
    anual_mpio_sistema: pd.DataFrame,
    cfg: ConfiguracionEdicion,
    replicas_boot: int | None = None,
) -> pd.DataFrame:
    df_brecha, _ = calcular_brecha_potencial_con_replicas(
        periodo_mpio_sistema=periodo_mpio_sistema,
        anual_mpio_sistema=anual_mpio_sistema,
        cfg=cfg,
        replicas_boot=replicas_boot,
    )
    return df_brecha
