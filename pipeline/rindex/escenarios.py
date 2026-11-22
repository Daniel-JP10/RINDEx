"""Parametrizacion de escenarios S1, S2, S3 y combinacion sin doble conteo."""

import numpy as np
import pandas as pd

from rindex.config import ConfiguracionEdicion

# Hallazgos firmes de H2 y H3 (D6 excluye el paso a riego por n < 6)
RAZON_HL_MAIZ_H2_DEFECTO = (1.5483, 1.6729, 1.8017)
RAZON_HL_ARROZ_MEC_H3_DEFECTO = (1.4805, 1.6174, 1.8183)


def evaluar_s1_lineal(
    ganancia_100: float | np.ndarray,
    fraccion_x: float,
) -> float | np.ndarray:
    if fraccion_x < 0.0 or fraccion_x > 1.0:
        raise ValueError("La fraccion x de cierre de brecha debe estar en [0, 1].")
    return fraccion_x * ganancia_100


def combinar_escenarios_sin_doble_conteo(
    s1: float | np.ndarray,
    s2: float | np.ndarray,
    s3: float | np.ndarray,
) -> float | np.ndarray:
    return np.maximum(s1, s2) + s3


def _extraer_razones_firmes(
    resumen_hipotesis: pd.DataFrame | None,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    razon_maiz = RAZON_HL_MAIZ_H2_DEFECTO
    razon_arroz = RAZON_HL_ARROZ_MEC_H3_DEFECTO
    if resumen_hipotesis is None or resumen_hipotesis.empty:
        return razon_maiz, razon_arroz

    mapa = {str(f["id_hipotesis"]): f for f in resumen_hipotesis.to_dict(orient="records")}
    if "H2_Maiz_tec_vs_trad" in mapa:
        f_m = mapa["H2_Maiz_tec_vs_trad"]
        ef = float(f_m["efecto"])
        l_ci = float(f_m["ic_95_inf"])
        u_ci = float(f_m["ic_95_sup"])
        if not (np.isnan(ef) or np.isnan(l_ci) or np.isnan(u_ci)):
            razon_maiz = (l_ci, ef, u_ci)

    if "H3_Arroz_mec_vs_man" in mapa:
        f_a = mapa["H3_Arroz_mec_vs_man"]
        ef = float(f_a["efecto"])
        l_ci = float(f_a["ic_95_inf"])
        u_ci = float(f_a["ic_95_sup"])
        if not (np.isnan(ef) or np.isnan(l_ci) or np.isnan(u_ci)):
            razon_arroz = (l_ci, ef, u_ci)

    return razon_maiz, razon_arroz


def construir_escenarios_municipales(
    periodo_mpio_cultivo: pd.DataFrame,
    periodo_mpio_sistema: pd.DataFrame,
    anual_mpio_cultivo: pd.DataFrame,
    anual_mpio_sistema: pd.DataFrame,
    df_brecha: pd.DataFrame,
    cfg: ConfiguracionEdicion,
    resumen_hipotesis: pd.DataFrame | None = None,
    replicas_boot: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    replicas = replicas_boot if replicas_boot is not None else cfg.parametros.replicas_bootstrap
    razon_h2_maiz, razon_h3_arroz = _extraer_razones_firmes(resumen_hipotesis)

    elegibles_cul = periodo_mpio_cultivo.loc[periodo_mpio_cultivo["elegible_500"]].copy()
    elegibles_cul = elegibles_cul.sort_values(
        ["cultivo", "codigo_dane_departamento", "codigo_dane_municipio"]
    ).reset_index(drop=True)

    # S1 agregado por municipio y cultivo desde df_brecha
    if not df_brecha.empty:
        s1_agrup = df_brecha.groupby(["codigo_dane_municipio", "cultivo"], as_index=False).agg(
            s1_area_media_anual=("area_cosechada_media_anual", "sum"),
            s1_ganancia_puntual=("ganancia_anual_t", "sum"),
            s1_p10=("ganancia_p10", "sum"),
            s1_p50=("ganancia_p50", "sum"),
            s1_p90=("ganancia_p90", "sum"),
            s1_brecha_relativa_max=("brecha_relativa_pct", "max"),
        )
        s1_agrup["s1_brecha_p10"] = np.where(
            s1_agrup["s1_area_media_anual"] > 0,
            s1_agrup["s1_p10"] / s1_agrup["s1_area_media_anual"],
            0.0,
        )
        s1_agrup["s1_brecha_p50"] = np.where(
            s1_agrup["s1_area_media_anual"] > 0,
            s1_agrup["s1_p50"] / s1_agrup["s1_area_media_anual"],
            0.0,
        )
        s1_agrup["s1_brecha_p90"] = np.where(
            s1_agrup["s1_area_media_anual"] > 0,
            s1_agrup["s1_p90"] / s1_agrup["s1_area_media_anual"],
            0.0,
        )
    else:
        s1_agrup = pd.DataFrame(
            columns=[
                "codigo_dane_municipio",
                "cultivo",
                "s1_area_media_anual",
                "s1_ganancia_puntual",
                "s1_p10",
                "s1_p50",
                "s1_p90",
                "s1_brecha_relativa_max",
                "s1_brecha_p10",
                "s1_brecha_p50",
                "s1_brecha_p90",
            ]
        )

    mapa_s1 = {
        (str(f["codigo_dane_municipio"]), str(f["cultivo"])): f
        for f in s1_agrup.to_dict(orient="records")
    }

    # Indexar sistemas por (mpio, cultivo, sistema)
    mapa_per_sis = {
        (str(f["codigo_dane_municipio"]), str(f["cultivo"]), str(f["sistema"])): f
        for f in periodo_mpio_sistema.to_dict(orient="records")
    }
    anual_sis_pos = anual_mpio_sistema.loc[anual_mpio_sistema["area_cosechada"] > 0]
    hist_sis: dict[tuple[str, str, str], tuple[np.ndarray, np.ndarray]] = {}
    for (m, c, s), sub in anual_sis_pos.groupby(
        ["codigo_dane_municipio", "cultivo", "sistema"], sort=False
    ):
        hist_sis[(str(m), str(c), str(s))] = (
            sub["area_cosechada"].to_numpy(dtype=float),
            sub["produccion"].to_numpy(dtype=float),
        )

    anual_cul_pos = anual_mpio_cultivo.loc[anual_mpio_cultivo["area_cosechada"] > 0]
    hist_cul: dict[tuple[str, str], tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    for (m, c), sub in anual_cul_pos.groupby(["codigo_dane_municipio", "cultivo"], sort=False):
        hist_cul[(str(m), str(c))] = (
            sub["area_sembrada"].to_numpy(dtype=float),
            sub["area_cosechada"].to_numpy(dtype=float),
            sub["produccion"].to_numpy(dtype=float),
        )

    filas_esc: list[dict[str, object]] = []
    semilla_base = cfg.parametros.semilla_aleatoria + 3000

    for idx, fila in enumerate(elegibles_cul.to_dict(orient="records")):
        mpio = str(fila["codigo_dane_municipio"])
        depto = str(fila["codigo_dane_departamento"])
        cult = str(fila["cultivo"])
        anios_d = int(fila["anios_con_dato"])
        area_cos_media = float(fila["area_cosechada"]) / float(anios_d)
        prod_media = float(fila["produccion"]) / float(anios_d)

        info_s1 = mapa_s1.get((mpio, cult), {})
        s1_p10 = float(info_s1.get("s1_p10", 0.0))
        s1_p50 = float(info_s1.get("s1_p50", 0.0))
        s1_p90 = float(info_s1.get("s1_p90", 0.0))
        s1_b_p10 = float(info_s1.get("s1_brecha_p10", 0.0))
        s1_b_p50 = float(info_s1.get("s1_brecha_p50", 0.0))
        s1_b_p90 = float(info_s1.get("s1_brecha_p90", 0.0))
        s1_area = float(info_s1.get("s1_area_media_anual", area_cos_media))
        s1_brecha_rel = float(info_s1.get("s1_brecha_relativa_max", 0.0))

        # S2: Tecnificacion (Maiz tradicional->tecnificado; Arroz secano_manual->secano_mecanizado)
        s2_p10, s2_p50, s2_p90 = 0.0, 0.0, 0.0
        s2_area_base = 0.0
        efecto_regional_s2 = False

        if cult in {"Maíz", "Arroz"}:
            sis_origen = "tradicional" if cult == "Maíz" else "secano_manual"
            sis_destino = "tecnificado" if cult == "Maíz" else "secano_mecanizado"
            razon_ci = razon_h2_maiz if cult == "Maíz" else razon_h3_arroz

            info_orig = mapa_per_sis.get((mpio, cult, sis_origen))
            if info_orig is not None and float(info_orig["area_cosechada"]) > 0:
                anios_orig = max(1, int(info_orig["anios_con_dato"]))
                s2_area_base = float(info_orig["area_cosechada"]) / float(anios_orig)
                areas_o, prods_o = hist_sis.get(
                    (mpio, cult, sis_origen),
                    (
                        np.array([s2_area_base]),
                        np.array([float(info_orig["produccion"]) / float(anios_orig)]),
                    ),
                )
                rng = np.random.default_rng(semilla_base + idx)
                k_o = len(areas_o)
                idx_o = rng.integers(0, k_o, size=(replicas, k_o))
                suma_a_o = areas_o[idx_o].sum(axis=1)
                suma_p_o = prods_o[idx_o].sum(axis=1)
                rend_o_boot = np.where(suma_a_o > 0, suma_p_o / suma_a_o, 0.0)
                area_o_boot = suma_a_o / float(k_o)

                info_dest = mapa_per_sis.get((mpio, cult, sis_destino))
                if (
                    info_dest is not None
                    and float(info_dest["area_cosechada"]) > 0
                    and int(info_dest["anios_con_dato"]) >= 2
                ):
                    efecto_regional_s2 = False
                    areas_d, prods_d = hist_sis[(mpio, cult, sis_destino)]
                    k_d = len(areas_d)
                    idx_d = rng.integers(0, k_d, size=(replicas, k_d))
                    suma_a_d = areas_d[idx_d].sum(axis=1)
                    suma_p_d = prods_d[idx_d].sum(axis=1)
                    rend_d_boot = np.where(suma_a_d > 0, suma_p_d / suma_a_d, 0.0)
                    delta_rend_boot = np.maximum(0.0, rend_d_boot - rend_o_boot)
                else:
                    efecto_regional_s2 = True
                    sigma_razon = (razon_ci[2] - razon_ci[0]) / (2.0 * 1.95996)
                    razones_boot = np.clip(
                        rng.normal(loc=razon_ci[1], scale=max(sigma_razon, 1e-4), size=replicas),
                        1.0,
                        None,
                    )
                    delta_rend_boot = rend_o_boot * (razones_boot - 1.0)

                gan_s2_boot = area_o_boot * delta_rend_boot
                s2_p10, s2_p50, s2_p90 = (
                    float(v) for v in np.quantile(gan_s2_boot, [0.10, 0.50, 0.90])
                )

        # S3: Area no cosechada (indicativo, solo Arroz y Maiz, excluyendo D4)
        excluido_d4 = bool(float(fila["area_cosechada"]) > float(fila["area_sembrada"]))
        s3_p10, s3_p50, s3_p90 = 0.0, 0.0, 0.0
        tasa_no_cos = float(fila["tasa_area_no_cosechada"]) if not excluido_d4 else 0.0

        if cult in {"Arroz", "Maíz"} and not excluido_d4 and tasa_no_cos > 0.0:
            sem_arr, cos_arr, prod_arr = hist_cul[(mpio, cult)]
            rng_s3 = np.random.default_rng(semilla_base + 5000 + idx)
            k_c = len(sem_arr)
            idx_c = rng_s3.integers(0, k_c, size=(replicas, k_c))
            sem_b = sem_arr[idx_c].sum(axis=1)
            cos_b = cos_arr[idx_c].sum(axis=1)
            prod_b = prod_arr[idx_c].sum(axis=1)

            no_cos_media_b = np.maximum(0.0, sem_b - cos_b) / float(k_c)
            rend_b = np.where(cos_b > 0, prod_b / cos_b, 0.0)
            gan_s3_boot = no_cos_media_b * rend_b
            s3_p10, s3_p50, s3_p90 = (
                float(v) for v in np.quantile(gan_s3_boot, [0.10, 0.50, 0.90])
            )

        comb_p10 = float(combinar_escenarios_sin_doble_conteo(s1_p10, s2_p10, s3_p10))
        comb_p50 = float(combinar_escenarios_sin_doble_conteo(s1_p50, s2_p50, s3_p50))
        comb_p90 = float(combinar_escenarios_sin_doble_conteo(s1_p90, s2_p90, s3_p90))

        filas_esc.append(
            {
                "codigo_dane_departamento": depto,
                "departamento": fila["departamento"],
                "codigo_dane_municipio": mpio,
                "municipio": fila["municipio"],
                "cultivo": cult,
                "anios_con_dato": anios_d,
                "area_cosechada_media_anual": area_cos_media,
                "produccion_media_anual": prod_media,
                "rendimiento_periodo": float(fila["rendimiento"]),
                "s1_area_media_anual": s1_area,
                "s1_brecha_relativa_pct": s1_brecha_rel,
                "s1_brecha_p10": s1_b_p10,
                "s1_brecha_p50": s1_b_p50,
                "s1_brecha_p90": s1_b_p90,
                "s1_p10": s1_p10,
                "s1_p50": s1_p50,
                "s1_p90": s1_p90,
                "s2_area_convertible_ha": s2_area_base,
                "efecto_regional": bool(efecto_regional_s2),
                "extrapolado": bool(efecto_regional_s2),
                "s2_p10": s2_p10,
                "s2_p50": s2_p50,
                "s2_p90": s2_p90,
                "excluido_d4": excluido_d4,
                "rotulo_s3": "indicativo_quiebre_2022"
                if cult in {"Arroz", "Maíz"}
                else "excluido_D3",
                "s3_p10": s3_p10,
                "s3_p50": s3_p50,
                "s3_p90": s3_p90,
                "combinado_p10": comb_p10,
                "combinado_p50": comb_p50,
                "combinado_p90": comb_p90,
                "serie_poco_informativa": bool(fila.get("serie_poco_informativa", False)),
            }
        )

    df_esc = pd.DataFrame(filas_esc)

    # Totales regionales por cultivo al 100 % y como porcentaje de la produccion anual media
    df_esc["s2_p50_ext"] = np.where(df_esc["extrapolado"], df_esc["s2_p50"], 0.0)
    df_esc["mpio_s2_ext"] = (df_esc["extrapolado"] & (df_esc["s2_p50"] > 0)).astype(int)
    df_esc["mpio_s2_con_ganancia"] = (df_esc["s2_p50"] > 0).astype(int)

    totales_reg = (
        df_esc.groupby("cultivo", as_index=False)
        .agg(
            municipios_elegibles=("codigo_dane_municipio", "count"),
            municipios_con_s2=("mpio_s2_con_ganancia", "sum"),
            municipios_s2_extrapolados=("mpio_s2_ext", "sum"),
            produccion_anual_media_t=("produccion_media_anual", "sum"),
            s1_p10=("s1_p10", "sum"),
            s1_p50=("s1_p50", "sum"),
            s1_p90=("s1_p90", "sum"),
            s2_p10=("s2_p10", "sum"),
            s2_p50=("s2_p50", "sum"),
            s2_p90=("s2_p90", "sum"),
            s2_p50_extrapolado=("s2_p50_ext", "sum"),
            s3_p10=("s3_p10", "sum"),
            s3_p50=("s3_p50", "sum"),
            s3_p90=("s3_p90", "sum"),
            combinado_p10=("combinado_p10", "sum"),
            combinado_p50=("combinado_p50", "sum"),
            combinado_p90=("combinado_p90", "sum"),
        )
        .sort_values("cultivo")
    )
    df_esc = df_esc.drop(columns=["s2_p50_ext", "mpio_s2_ext", "mpio_s2_con_ganancia"])
    for pref in ("s1", "s2", "s3", "combinado"):
        totales_reg[f"{pref}_p50_pct_prod"] = np.where(
            totales_reg["produccion_anual_media_t"] > 0,
            totales_reg[f"{pref}_p50"] / totales_reg["produccion_anual_media_t"] * 100.0,
            0.0,
        )
    totales_reg["s2_pct_extrapolado"] = np.where(
        totales_reg["s2_p50"] > 0,
        totales_reg["s2_p50_extrapolado"] / totales_reg["s2_p50"] * 100.0,
        0.0,
    )

    return df_esc, totales_reg
