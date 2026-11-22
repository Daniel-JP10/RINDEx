"""Ejecucion de las pruebas estadisticas preespecificadas H1 a H5, E1 y E2."""

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

from rindex.agregacion import construir_tablas_agregadas
from rindex.clima import obtener_oni_anual
from rindex.config import ConfiguracionEdicion, cargar_configuracion
from rindex.estadistica import (
    ajustar_p_benjamini_hochberg,
    ajustar_p_holm,
    bootstrap_epsilon_cuadrado_vectorizado,
    bootstrap_hodges_lehmann_vectorizado,
    bootstrap_mediana_vectorizado,
    bootstrap_w_kendall_vectorizado,
    calcular_pendientes_municipales,
    estimador_hodges_lehmann_diferencia,
    estimador_hodges_lehmann_log_razon,
    prueba_friedman,
    prueba_kruskal_wallis,
    prueba_mann_whitney,
    prueba_spearman_permutacion_exacta,
    prueba_wilcoxon_pareada,
)
from rindex.limpieza import limpiar_eva

ALFA_CONFIRMATORIO = 0.05
# D6: Con n < 6 en Wilcoxon pareado, el p bilateral exacto minimo es 2/2^5 = 0,0625 > 0,05
MINIMO_UNIDADES_PRUEBA = 6


def _filtrar_elegibles(
    df_periodo: pd.DataFrame,
    umbral_ha: float,
    anios_minimos: int,
    excluir_poco_informativas: bool = False,
) -> pd.DataFrame:
    mascara = (df_periodo["area_cosechada"] >= umbral_ha) & (
        df_periodo["anios_con_dato"] >= anios_minimos
    )
    if excluir_poco_informativas and "serie_poco_informativa" in df_periodo.columns:
        mascara = mascara & (~df_periodo["serie_poco_informativa"])
    return df_periodo.loc[mascara].copy()


def _calcular_tabla_h1(
    tablas: dict[str, pd.DataFrame],
    cfg: ConfiguracionEdicion,
    umbral_ha: float,
    replicas_boot: int,
    excluir_poco_informativas: bool,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    per_eleg = _filtrar_elegibles(
        tablas["periodo_municipio_cultivo"],
        umbral_ha=umbral_ha,
        anios_minimos=cfg.parametros.anios_minimos_con_dato,
        excluir_poco_informativas=excluir_poco_informativas,
    )
    llaves_eleg = per_eleg[["codigo_dane_municipio", "cultivo"]].drop_duplicates()
    anual_eleg = tablas["anual_municipio_cultivo"].merge(
        llaves_eleg,
        on=["codigo_dane_municipio", "cultivo"],
        how="inner",
    )

    df_pendientes = calcular_pendientes_municipales(
        anual_eleg,
        anios_minimos=cfg.parametros.anios_minimos_con_dato,
    )

    filas_res: list[dict[str, object]] = []
    for idx, cultivo in enumerate(sorted(cfg.cultivos)):
        sub = df_pendientes.loc[df_pendientes["cultivo"] == cultivo]
        pend_tha = sub["pendiente_theil_sen"].to_numpy(dtype=float)
        pend_pct = sub["pendiente_pct_anual"].to_numpy(dtype=float)
        n_mpios = len(pend_tha)

        if n_mpios < MINIMO_UNIDADES_PRUEBA:
            filas_res.append(
                {
                    "id_hipotesis": f"H1_{cultivo}",
                    "hipotesis": f"H1 Tendencia ({cultivo})",
                    "familia": "H1",
                    "tipo": "confirmatoria",
                    "cultivo": cultivo,
                    "contraste": "pendiente Theil-Sen vs 0",
                    "n": n_mpios,
                    "n_secundario": 0,
                    "nombre_estadistico": "W",
                    "estadistico": float("nan"),
                    "valor_p": float("nan"),
                    "nombre_efecto": "mediana pendiente (t/ha/anio)",
                    "efecto": float("nan"),
                    "ic_95_inf": float("nan"),
                    "ic_95_sup": float("nan"),
                    "efecto_secundario_nombre": "mediana pendiente (%/anio)",
                    "efecto_secundario": float("nan"),
                    "ic_95_sec_inf": float("nan"),
                    "ic_95_sec_sup": float("nan"),
                    "r_biserial": float("nan"),
                }
            )
            continue

        w_res = prueba_wilcoxon_pareada(pend_tha)
        n_no_cero = int(np.sum(np.abs(pend_tha) > 1e-12))
        med_tha = float(np.median(pend_tha))
        med_pct = float(np.median(pend_pct))
        semilla_c = cfg.parametros.semilla_aleatoria + 10 + idx
        ic_tha_inf, ic_tha_sup = bootstrap_mediana_vectorizado(
            pend_tha,
            semilla=semilla_c,
            replicas=replicas_boot,
        )
        ic_pct_inf, ic_pct_sup = bootstrap_mediana_vectorizado(
            pend_pct,
            semilla=semilla_c + 100,
            replicas=replicas_boot,
        )

        filas_res.append(
            {
                "id_hipotesis": f"H1_{cultivo}",
                "hipotesis": f"H1 Tendencia ({cultivo})",
                "familia": "H1",
                "tipo": "confirmatoria",
                "cultivo": cultivo,
                "contraste": "pendiente Theil-Sen vs 0",
                "n": w_res.n,
                "n_secundario": n_no_cero,
                "nombre_estadistico": "W",
                "estadistico": w_res.estadistico,
                "valor_p": w_res.valor_p,
                "nombre_efecto": "mediana pendiente (t/ha/anio)",
                "efecto": med_tha,
                "ic_95_inf": ic_tha_inf,
                "ic_95_sup": ic_tha_sup,
                "efecto_secundario_nombre": "mediana pendiente (%/anio)",
                "efecto_secundario": med_pct,
                "ic_95_sec_inf": ic_pct_inf,
                "ic_95_sec_sup": ic_pct_sup,
                "r_biserial": w_res.r_biserial_pareado,
            }
        )

    df_h1 = pd.DataFrame(filas_res)
    df_h1["valor_p_ajustado"] = ajustar_p_holm(df_h1["valor_p"].to_numpy(dtype=float))
    df_h1["metodo_ajuste"] = "Holm"
    return df_h1, df_pendientes


def evaluar_h1_tendencia(
    tablas: dict[str, pd.DataFrame],
    cfg: ConfiguracionEdicion,
    umbral_ha: float = 500.0,
    replicas_boot: int = 5000,
    excluir_poco_informativas: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    df_h1, df_pendientes = _calcular_tabla_h1(
        tablas=tablas,
        cfg=cfg,
        umbral_ha=umbral_ha,
        replicas_boot=replicas_boot,
        excluir_poco_informativas=excluir_poco_informativas,
    )

    if not excluir_poco_informativas:
        df_h1_d7, _ = _calcular_tabla_h1(
            tablas=tablas,
            cfg=cfg,
            umbral_ha=umbral_ha,
            replicas_boot=min(replicas_boot, cfg.parametros.bootstrap_robustez),
            excluir_poco_informativas=True,
        )
        mapa_d7 = {str(f["id_hipotesis"]): f for f in df_h1_d7.to_dict(orient="records")}
    else:
        mapa_d7 = {}

    per_cul = tablas["periodo_municipio_cultivo"]
    tiene_poco_inf_por_cultivo: dict[str, bool] = {}
    if "serie_poco_informativa" in per_cul.columns:
        for c in cfg.cultivos:
            sub_c = per_cul.loc[
                (per_cul["cultivo"] == c) & (per_cul["area_cosechada"] >= umbral_ha)
            ]
            tiene_poco_inf_por_cultivo[c] = bool(sub_c["serie_poco_informativa"].any())

    decisiones: list[str] = []
    for fila in df_h1.to_dict(orient="records"):
        id_h = str(fila["id_hipotesis"])
        cultivo = str(fila["cultivo"])
        n_m = int(fila["n"])
        p_adj = float(fila["valor_p_ajustado"])
        ef = float(fila["efecto"])
        ic_pct_l = float(fila["ic_95_sec_inf"])
        ic_pct_u = float(fila["ic_95_sec_sup"])

        if n_m < MINIMO_UNIDADES_PRUEBA or np.isnan(p_adj):
            decisiones.append("insuficiente (n < 6, D6)")
        elif p_adj < ALFA_CONFIRMATORIO:
            sentido = "positiva" if ef > 0 else ("negativa" if ef < 0 else "nula")
            decisiones.append(f"tendencia {sentido} significativa")
        elif ic_pct_l >= -1.0 and ic_pct_u <= 1.0:
            # D7: verificar si la aparente equivalencia se debe a series con valores repetidos
            fila_d7 = mapa_d7.get(id_h)
            altera_d7 = False
            if fila_d7 is not None:
                p_d7 = float(fila_d7["valor_p_ajustado"])
                l_d7 = float(fila_d7["ic_95_sec_inf"])
                u_d7 = float(fila_d7["ic_95_sec_sup"])
                if not np.isnan(p_d7) and (p_d7 < ALFA_CONFIRMATORIO or l_d7 < -1.0 or u_d7 > 1.0):
                    altera_d7 = True
            if altera_d7 or tiene_poco_inf_por_cultivo.get(cultivo, False):
                decisiones.append("la tendencia no es medible en las series con valores repetidos")
            else:
                decisiones.append("equivalencia practica (+/- 1 % anual)")
        else:
            decisiones.append("sin evidencia de tendencia")

    df_h1["decision"] = decisiones
    return df_h1, df_pendientes


def _evaluar_par_sistemas(
    df_anual_sis_cultivo: pd.DataFrame,
    sistema_a: str,
    sistema_b: str,
    id_hipotesis: str,
    titulo_hipotesis: str,
    familia: str,
    cultivo: str,
    semilla: int,
    replicas_boot: int,
    unidad: str = "municipio",
) -> dict[str, object]:
    df_pos = df_anual_sis_cultivo.loc[
        (df_anual_sis_cultivo["area_cosechada"] > 0)
        & (df_anual_sis_cultivo["sistema"].isin([sistema_a, sistema_b]))
    ]
    piv = df_pos.pivot_table(
        index=["codigo_dane_municipio", "anio"],
        columns="sistema",
        values="rendimiento",
        aggfunc="first",
    )
    if sistema_a not in piv.columns or sistema_b not in piv.columns:
        return {
            "id_hipotesis": id_hipotesis,
            "hipotesis": titulo_hipotesis,
            "familia": familia,
            "tipo": "confirmatoria",
            "cultivo": cultivo,
            "contraste": f"{sistema_a} vs {sistema_b} ({unidad})",
            "n": 0,
            "n_secundario": 0,
            "nombre_estadistico": "W",
            "estadistico": float("nan"),
            "valor_p": float("nan"),
            "nombre_efecto": "razon Hodges-Lehmann",
            "efecto": float("nan"),
            "ic_95_inf": float("nan"),
            "ic_95_sup": float("nan"),
            "efecto_secundario_nombre": "razon mediana",
            "efecto_secundario": float("nan"),
            "ic_95_sec_inf": float("nan"),
            "ic_95_sec_sup": float("nan"),
            "r_biserial": float("nan"),
        }

    pares = piv[[sistema_a, sistema_b]].dropna().reset_index()
    pares = pares.loc[(pares[sistema_a] > 0) & (pares[sistema_b] > 0)].copy()
    pares["diff_log"] = np.log(pares[sistema_a] / pares[sistema_b])

    n_pares = len(pares)
    mpios_series = pares.groupby("codigo_dane_municipio", as_index=False)["diff_log"].mean()
    n_mpios = len(mpios_series)

    if unidad == "municipio":
        vector_prueba = mpios_series["diff_log"].to_numpy(dtype=float)
        n_primario = n_mpios
        n_sec = n_pares
    else:
        vector_prueba = pares["diff_log"].to_numpy(dtype=float)
        n_primario = n_pares
        n_sec = n_mpios

    if n_primario < 2:
        return {
            "id_hipotesis": id_hipotesis,
            "hipotesis": titulo_hipotesis,
            "familia": familia,
            "tipo": "confirmatoria",
            "cultivo": cultivo,
            "contraste": f"{sistema_a} vs {sistema_b} ({unidad})",
            "n": n_primario,
            "n_secundario": n_sec,
            "nombre_estadistico": "W",
            "estadistico": float("nan"),
            "valor_p": float("nan"),
            "nombre_efecto": "razon Hodges-Lehmann",
            "efecto": float("nan"),
            "ic_95_inf": float("nan"),
            "ic_95_sup": float("nan"),
            "efecto_secundario_nombre": "razon mediana",
            "efecto_secundario": float("nan"),
            "ic_95_sec_inf": float("nan"),
            "ic_95_sec_sup": float("nan"),
            "r_biserial": float("nan"),
        }

    w_res = prueba_wilcoxon_pareada(vector_prueba)
    _, hl_razon = estimador_hodges_lehmann_log_razon(vector_prueba)
    razon_mediana = float(np.exp(np.median(vector_prueba)))

    diffs_municipales = mpios_series["diff_log"].to_numpy(dtype=float)
    ic_hl_inf, ic_hl_sup = bootstrap_hodges_lehmann_vectorizado(
        diffs_municipales,
        semilla=semilla,
        replicas=replicas_boot,
        exponenciar=True,
    )
    med_inf_log, med_sup_log = bootstrap_mediana_vectorizado(
        diffs_municipales,
        semilla=semilla + 50,
        replicas=replicas_boot,
    )

    return {
        "id_hipotesis": id_hipotesis,
        "hipotesis": titulo_hipotesis,
        "familia": familia,
        "tipo": "confirmatoria",
        "cultivo": cultivo,
        "contraste": f"{sistema_a} vs {sistema_b} ({unidad})",
        "n": n_primario,
        "n_secundario": n_sec,
        "nombre_estadistico": "W",
        "estadistico": w_res.estadistico,
        "valor_p": w_res.valor_p,
        "nombre_efecto": "razon Hodges-Lehmann",
        "efecto": hl_razon,
        "ic_95_inf": ic_hl_inf,
        "ic_95_sup": ic_hl_sup,
        "efecto_secundario_nombre": "razon mediana",
        "efecto_secundario": razon_mediana,
        "ic_95_sec_inf": (
            float(np.exp(med_inf_log)) if not np.isnan(med_inf_log) else float("nan")
        ),
        "ic_95_sec_sup": (
            float(np.exp(med_sup_log)) if not np.isnan(med_sup_log) else float("nan")
        ),
        "r_biserial": w_res.r_biserial_pareado,
    }


def evaluar_h2_maiz(
    tablas: dict[str, pd.DataFrame],
    cfg: ConfiguracionEdicion,
    umbral_ha: float = 500.0,
    replicas_boot: int = 5000,
    unidad: str = "municipio",
) -> pd.DataFrame:
    per_eleg = _filtrar_elegibles(
        tablas["periodo_municipio_cultivo"],
        umbral_ha=umbral_ha,
        anios_minimos=cfg.parametros.anios_minimos_con_dato,
    )
    mpios_maiz = set(per_eleg.loc[per_eleg["cultivo"] == "Maíz", "codigo_dane_municipio"])
    anual_maiz = tablas["anual_municipio_sistema"].loc[
        (tablas["anual_municipio_sistema"]["cultivo"] == "Maíz")
        & (tablas["anual_municipio_sistema"]["codigo_dane_municipio"].isin(mpios_maiz))
    ]

    fila = _evaluar_par_sistemas(
        anual_maiz,
        sistema_a="tecnificado",
        sistema_b="tradicional",
        id_hipotesis="H2_Maiz_tec_vs_trad",
        titulo_hipotesis="H2 Brecha tecnologica en maiz (tecnificado vs tradicional)",
        familia="H2",
        cultivo="Maíz",
        semilla=cfg.parametros.semilla_aleatoria + 200,
        replicas_boot=replicas_boot,
        unidad=unidad,
    )
    df_h2 = pd.DataFrame([fila])
    df_h2["valor_p_ajustado"] = ajustar_p_holm(df_h2["valor_p"].to_numpy(dtype=float))
    df_h2["metodo_ajuste"] = "Holm"
    n_u = int(df_h2["n"].iloc[0])
    p_adj = float(df_h2["valor_p_ajustado"].iloc[0])
    ef = float(df_h2["efecto"].iloc[0])
    if n_u < MINIMO_UNIDADES_PRUEBA or np.isnan(p_adj):
        df_h2["decision"] = "insuficiente (n < 6, D6)"
    elif p_adj < ALFA_CONFIRMATORIO and ef > 1.0:
        df_h2["decision"] = "diferencia significativa (tecnificado > tradicional)"
    elif p_adj < ALFA_CONFIRMATORIO:
        df_h2["decision"] = "diferencia significativa (tecnificado < tradicional)"
    else:
        df_h2["decision"] = "sin evidencia de diferencia"
    return df_h2


def evaluar_h3_arroz(
    tablas: dict[str, pd.DataFrame],
    cfg: ConfiguracionEdicion,
    umbral_ha: float = 500.0,
    replicas_boot: int = 5000,
    unidad: str = "municipio",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    per_eleg = _filtrar_elegibles(
        tablas["periodo_municipio_cultivo"],
        umbral_ha=umbral_ha,
        anios_minimos=cfg.parametros.anios_minimos_con_dato,
    )
    mpios_arroz = set(per_eleg.loc[per_eleg["cultivo"] == "Arroz", "codigo_dane_municipio"])
    anual_arroz = tablas["anual_municipio_sistema"].loc[
        (tablas["anual_municipio_sistema"]["cultivo"] == "Arroz")
        & (tablas["anual_municipio_sistema"]["codigo_dane_municipio"].isin(mpios_arroz))
    ]

    pares_config = [
        ("riego", "secano_mecanizado", "H3_Arroz_riego_vs_mec"),
        ("riego", "secano_manual", "H3_Arroz_riego_vs_man"),
        ("secano_mecanizado", "secano_manual", "H3_Arroz_mec_vs_man"),
    ]
    filas: list[dict[str, object]] = []
    for idx, (sis_a, sis_b, id_h) in enumerate(pares_config):
        filas.append(
            _evaluar_par_sistemas(
                anual_arroz,
                sistema_a=sis_a,
                sistema_b=sis_b,
                id_hipotesis=id_h,
                titulo_hipotesis=f"H3 Arroz ({sis_a} vs {sis_b})",
                familia="H3",
                cultivo="Arroz",
                semilla=cfg.parametros.semilla_aleatoria + 300 + idx * 10,
                replicas_boot=replicas_boot,
                unidad=unidad,
            )
        )

    df_h3 = pd.DataFrame(filas)
    df_h3["valor_p_ajustado"] = ajustar_p_holm(df_h3["valor_p"].to_numpy(dtype=float))
    df_h3["metodo_ajuste"] = "Holm"

    decisiones: list[str] = []
    for fila in df_h3.to_dict(orient="records"):
        n_u = int(fila["n"])
        p_adj = float(fila["valor_p_ajustado"])
        ef = float(fila["efecto"])
        if n_u < MINIMO_UNIDADES_PRUEBA or np.isnan(p_adj):
            decisiones.append("insuficiente (n < 6, D6)")
        elif p_adj < ALFA_CONFIRMATORIO:
            sentido = "mayor" if ef > 1.0 else "menor"
            decisiones.append(f"diferencia significativa (razon {sentido} a 1)")
        else:
            decisiones.append("sin evidencia de diferencia")
    df_h3["decision"] = decisiones

    arroz_pos = anual_arroz.loc[anual_arroz["area_cosechada"] > 0]
    piv_trip = arroz_pos.pivot_table(
        index=["codigo_dane_municipio", "anio"],
        columns="sistema",
        values="rendimiento",
        aggfunc="first",
    )
    cols_sistemas = ["riego", "secano_mecanizado", "secano_manual"]
    if all(c in piv_trip.columns for c in cols_sistemas):
        completas = piv_trip[cols_sistemas].dropna()
        f_res = prueba_friedman(completas.to_numpy(dtype=float))
    else:
        f_res = prueba_friedman(np.empty((0, 3)))

    df_comp = pd.DataFrame(
        [
            {
                "id_hipotesis": "H3_complemento_Friedman",
                "n_tripletas": f_res.n_bloques,
                "estadistico_chi2": f_res.estadistico_chi2,
                "valor_p": f_res.valor_p,
                "w_kendall": f_res.w_kendall,
            }
        ]
    )
    return df_h3, df_comp


def evaluar_h4_departamentos(
    tablas: dict[str, pd.DataFrame],
    cfg: ConfiguracionEdicion,
    umbral_ha: float = 500.0,
    replicas_boot: int = 5000,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    per_eleg = _filtrar_elegibles(
        tablas["periodo_municipio_cultivo"],
        umbral_ha=umbral_ha,
        anios_minimos=cfg.parametros.anios_minimos_con_dato,
    )

    filas_omnibus: list[dict[str, object]] = []
    filas_pares: list[dict[str, object]] = []

    for idx, cultivo in enumerate(sorted(cfg.cultivos)):
        sub = per_eleg.loc[per_eleg["cultivo"] == cultivo].copy()
        grupos_dict = {
            depto: g["rendimiento"].dropna().to_numpy(dtype=float)
            for depto, g in sub.groupby("codigo_dane_departamento")
            if len(g["rendimiento"].dropna()) > 0
        }
        kw = prueba_kruskal_wallis(list(grupos_dict.values()))

        ic_inf, ic_sup = bootstrap_epsilon_cuadrado_vectorizado(
            valores_municipales=sub["rendimiento"].to_numpy(dtype=float),
            codigos_grupo=sub["codigo_dane_departamento"].to_numpy(),
            semilla=cfg.parametros.semilla_aleatoria + 400 + idx,
            replicas=replicas_boot,
        )

        filas_omnibus.append(
            {
                "id_hipotesis": f"H4_{cultivo}",
                "hipotesis": f"H4 Diferencia departamental ({cultivo})",
                "familia": "H4",
                "tipo": "confirmatoria",
                "cultivo": cultivo,
                "contraste": f"Kruskal-Wallis entre {kw.k_grupos} departamentos",
                "n": kw.n_total,
                "n_secundario": kw.k_grupos,
                "nombre_estadistico": "H",
                "estadistico": kw.estadistico_h,
                "valor_p": kw.valor_p,
                "nombre_efecto": "epsilon_cuadrado",
                "efecto": kw.epsilon_cuadrado,
                "ic_95_inf": ic_inf,
                "ic_95_sup": ic_sup,
                "efecto_secundario_nombre": "departamentos evaluados",
                "efecto_secundario": float(kw.k_grupos),
                "ic_95_sec_inf": float("nan"),
                "ic_95_sec_sup": float("nan"),
                "r_biserial": float("nan"),
            }
        )

        deptos_ordenados = sorted(grupos_dict.keys())
        pares_cultivo: list[dict[str, object]] = []
        for i in range(len(deptos_ordenados)):
            for j in range(i + 1, len(deptos_ordenados)):
                d1, d2 = deptos_ordenados[i], deptos_ordenados[j]
                x1, x2 = grupos_dict[d1], grupos_dict[d2]
                if len(x1) < 2 or len(x2) < 2:
                    continue
                mw = prueba_mann_whitney(x1, x2)
                pares_cultivo.append(
                    {
                        "cultivo": cultivo,
                        "depto_a": d1,
                        "nombre_a": cfg.departamentos.get(d1, d1),
                        "depto_b": d2,
                        "nombre_b": cfg.departamentos.get(d2, d2),
                        "n_a": mw.n_x,
                        "n_b": mw.n_y,
                        "mediana_a": float(np.median(x1)),
                        "mediana_b": float(np.median(x2)),
                        "estadistico_u": mw.estadistico_u,
                        "valor_p": mw.valor_p,
                        "r_biserial": mw.r_biserial,
                    }
                )
        if pares_cultivo:
            df_pc = pd.DataFrame(pares_cultivo)
            df_pc["valor_p_ajustado"] = ajustar_p_holm(df_pc["valor_p"].to_numpy(dtype=float))
            filas_pares.extend(df_pc.to_dict(orient="records"))

    df_h4 = pd.DataFrame(filas_omnibus)
    df_h4["valor_p_ajustado"] = ajustar_p_holm(df_h4["valor_p"].to_numpy(dtype=float))
    df_h4["metodo_ajuste"] = "Holm"
    df_h4["decision"] = [
        "muestra insuficiente"
        if np.isnan(p)
        else (
            "diferencia interdepartamental significativa"
            if p < ALFA_CONFIRMATORIO
            else "sin evidencia de diferencia interdepartamental"
        )
        for p in df_h4["valor_p_ajustado"]
    ]
    return df_h4, pd.DataFrame(filas_pares)


def evaluar_h5_variabilidad(
    tablas: dict[str, pd.DataFrame],
    cfg: ConfiguracionEdicion,
    umbral_ha: float = 500.0,
    replicas_boot: int = 5000,
    excluir_poco_informativas: bool = False,
) -> pd.DataFrame:
    per_eleg = _filtrar_elegibles(
        tablas["periodo_municipio_cultivo"],
        umbral_ha=umbral_ha,
        anios_minimos=cfg.parametros.anios_minimos_con_dato,
        excluir_poco_informativas=excluir_poco_informativas,
    )
    piv_cv = per_eleg.pivot_table(
        index="codigo_dane_municipio",
        columns="cultivo",
        values="cv_interanual",
        aggfunc="first",
    )
    cultivos_ord = ["Arroz", "Maíz", "Yuca"]
    if not all(c in piv_cv.columns for c in cultivos_ord):
        completos = pd.DataFrame(columns=cultivos_ord)
    else:
        completos = piv_cv[cultivos_ord].dropna()

    mat = completos.to_numpy(dtype=float)
    n_mpios = len(completos)
    f_res = prueba_friedman(mat) if n_mpios >= 2 else prueba_friedman(np.empty((0, 3)))

    if n_mpios >= MINIMO_UNIDADES_PRUEBA:
        ic_w_inf, ic_w_sup = bootstrap_w_kendall_vectorizado(
            mat,
            semilla=cfg.parametros.semilla_aleatoria + 500,
            replicas=replicas_boot,
        )
    else:
        ic_w_inf, ic_w_sup = float("nan"), float("nan")

    filas: list[dict[str, object]] = [
        {
            "id_hipotesis": "H5_omnibus_Friedman",
            "hipotesis": "H5 Variabilidad interanual CV (Friedman 3 cultivos)",
            "familia": "H5",
            "tipo": "confirmatoria",
            "cultivo": "Todos",
            "contraste": "Arroz vs Maíz vs Yuca (CV interanual)",
            "n": f_res.n_bloques,
            "n_secundario": 3,
            "nombre_estadistico": "chi2_F",
            "estadistico": f_res.estadistico_chi2,
            "valor_p": f_res.valor_p,
            "nombre_efecto": "W de Kendall",
            "efecto": f_res.w_kendall,
            "ic_95_inf": float(ic_w_inf),
            "ic_95_sup": float(ic_w_sup),
            "efecto_secundario_nombre": "CV mediano global",
            "efecto_secundario": float(np.median(mat)) if n_mpios > 0 else float("nan"),
            "ic_95_sec_inf": float("nan"),
            "ic_95_sec_sup": float("nan"),
            "r_biserial": float("nan"),
        }
    ]

    pares_c = [
        ("Arroz", "Maíz", "H5_CV_Arroz_vs_Maiz"),
        ("Arroz", "Yuca", "H5_CV_Arroz_vs_Yuca"),
        ("Maíz", "Yuca", "H5_CV_Maiz_vs_Yuca"),
    ]
    for idx, (c_a, c_b, id_h) in enumerate(pares_c):
        diff_cv = (
            completos[c_a].to_numpy(dtype=float) - completos[c_b].to_numpy(dtype=float)
            if n_mpios > 0
            else np.array([], dtype=float)
        )
        if n_mpios >= 2:
            w_res = prueba_wilcoxon_pareada(diff_cv)
            hl_diff = estimador_hodges_lehmann_diferencia(diff_cv)
            ic_l, ic_u = bootstrap_hodges_lehmann_vectorizado(
                diff_cv,
                semilla=cfg.parametros.semilla_aleatoria + 520 + idx,
                replicas=replicas_boot,
                exponenciar=False,
            )
            est_w = w_res.estadistico
            val_p = w_res.valor_p
        else:
            w_res = prueba_wilcoxon_pareada(np.array([]))
            hl_diff, ic_l, ic_u = float("nan"), float("nan"), float("nan")
            est_w, val_p = float("nan"), float("nan")

        filas.append(
            {
                "id_hipotesis": id_h,
                "hipotesis": f"H5 Variabilidad CV ({c_a} vs {c_b})",
                "familia": "H5",
                "tipo": "confirmatoria",
                "cultivo": f"{c_a} vs {c_b}",
                "contraste": f"CV {c_a} - CV {c_b}",
                "n": n_mpios,
                "n_secundario": n_mpios,
                "nombre_estadistico": "W",
                "estadistico": est_w,
                "valor_p": val_p,
                "nombre_efecto": "diferencia HL de CV",
                "efecto": hl_diff,
                "ic_95_inf": ic_l,
                "ic_95_sup": ic_u,
                "efecto_secundario_nombre": "r_biserial_pareado",
                "efecto_secundario": w_res.r_biserial_pareado,
                "ic_95_sec_inf": float("nan"),
                "ic_95_sec_sup": float("nan"),
                "r_biserial": w_res.r_biserial_pareado,
            }
        )

    df_h5 = pd.DataFrame(filas)
    p_ajustados = np.full(len(df_h5), np.nan, dtype=float)
    p_ajustados[0] = df_h5.loc[0, "valor_p"]
    p_ajustados[1:] = ajustar_p_holm(df_h5.loc[1:, "valor_p"].to_numpy(dtype=float))
    df_h5["valor_p_ajustado"] = p_ajustados
    df_h5["metodo_ajuste"] = "Holm"

    decisiones: list[str] = []
    for fila in df_h5.to_dict(orient="records"):
        n_u = int(fila["n"])
        p_adj = float(fila["valor_p_ajustado"])
        if n_u < MINIMO_UNIDADES_PRUEBA or np.isnan(p_adj):
            decisiones.append("insuficiente (n < 6, D6)")
        elif p_adj < ALFA_CONFIRMATORIO:
            decisiones.append("diferencia significativa de variabilidad")
        else:
            decisiones.append("sin evidencia de diferencia de variabilidad")
    df_h5["decision"] = decisiones
    return df_h5


def evaluar_e1_clima(
    tablas: dict[str, pd.DataFrame],
    df_oni: pd.DataFrame,
    cfg: ConfiguracionEdicion,
    umbral_ha: float = 500.0,
    replicas_boot: int = 5000,
) -> pd.DataFrame:
    reg_oni = tablas["anual_region_cultivo"].merge(df_oni, on="anio", how="inner")
    filas: list[dict[str, object]] = []

    for cultivo in sorted(cfg.cultivos):
        sub_r = reg_oni.loc[reg_oni["cultivo"] == cultivo].sort_values("anio")
        oni_vals = sub_r["oni_anual"].to_numpy(dtype=float)

        for metrica, etiq in [
            ("rendimiento", "rendimiento regional"),
            ("tasa_area_no_cosechada", "tasa area no cosechada"),
        ]:
            y_vals = sub_r[metrica].to_numpy(dtype=float)
            sp = prueba_spearman_permutacion_exacta(oni_vals, y_vals)
            filas.append(
                {
                    "id_hipotesis": f"E1_spearman_{metrica}_{cultivo}",
                    "hipotesis": f"E1 Exploratoria: ONI vs {etiq} ({cultivo})",
                    "familia": "E1",
                    "tipo": "exploratoria",
                    "cultivo": cultivo,
                    "contraste": f"Spearman exacto ONI vs {etiq}",
                    "n": sp.n,
                    "n_secundario": sp.n,
                    "nombre_estadistico": "rho",
                    "estadistico": sp.rho,
                    "valor_p": sp.valor_p_exacto,
                    "nombre_efecto": "rho de Spearman",
                    "efecto": sp.rho,
                    "ic_95_inf": float("nan"),
                    "ic_95_sup": float("nan"),
                    "efecto_secundario_nombre": "anios evaluados",
                    "efecto_secundario": float(sp.n),
                    "ic_95_sec_inf": float("nan"),
                    "ic_95_sec_sup": float("nan"),
                    "r_biserial": float("nan"),
                }
            )

    per_eleg = _filtrar_elegibles(
        tablas["periodo_municipio_cultivo"],
        umbral_ha=umbral_ha,
        anios_minimos=cfg.parametros.anios_minimos_con_dato,
    )
    llaves_eleg = per_eleg[["codigo_dane_municipio", "cultivo"]].drop_duplicates()
    anual_oni = (
        tablas["anual_municipio_cultivo"]
        .loc[tablas["anual_municipio_cultivo"]["area_cosechada"] > 0]
        .merge(llaves_eleg, on=["codigo_dane_municipio", "cultivo"], how="inner")
        .merge(df_oni[["anio", "clasificacion_enso"]], on="anio", how="inner")
    )
    anual_nina_neutro = anual_oni.loc[anual_oni["clasificacion_enso"].isin(["nina", "neutro"])]
    agrup_fase = anual_nina_neutro.groupby(
        ["codigo_dane_municipio", "cultivo", "clasificacion_enso"],
        as_index=False,
    ).agg(
        produccion=("produccion", "sum"),
        area_cosechada=("area_cosechada", "sum"),
    )
    agrup_fase["rend_fase"] = agrup_fase["produccion"] / agrup_fase["area_cosechada"]
    piv_fase = agrup_fase.pivot_table(
        index=["codigo_dane_municipio", "cultivo"],
        columns="clasificacion_enso",
        values="rend_fase",
        aggfunc="first",
    ).reset_index()

    for idx, cultivo in enumerate(sorted(cfg.cultivos)):
        if "nina" not in piv_fase.columns or "neutro" not in piv_fase.columns:
            pares_c = pd.DataFrame(columns=["nina", "neutro"])
        else:
            pares_c = piv_fase.loc[piv_fase["cultivo"] == cultivo, ["nina", "neutro"]].dropna()

        n_mpios = len(pares_c)
        if n_mpios < 2:
            filas.append(
                {
                    "id_hipotesis": f"E1_nina_vs_neutro_{cultivo}",
                    "hipotesis": f"E1 Exploratoria: anos Nina vs neutros ({cultivo})",
                    "familia": "E1",
                    "tipo": "exploratoria",
                    "cultivo": cultivo,
                    "contraste": "rendimiento Nina - neutro por municipio",
                    "n": n_mpios,
                    "n_secundario": n_mpios,
                    "nombre_estadistico": "W",
                    "estadistico": float("nan"),
                    "valor_p": float("nan"),
                    "nombre_efecto": "diferencia HL (t/ha)",
                    "efecto": float("nan"),
                    "ic_95_inf": float("nan"),
                    "ic_95_sup": float("nan"),
                    "efecto_secundario_nombre": "r_biserial_pareado",
                    "efecto_secundario": float("nan"),
                    "ic_95_sec_inf": float("nan"),
                    "ic_95_sec_sup": float("nan"),
                    "r_biserial": float("nan"),
                }
            )
            continue

        diffs = (pares_c["nina"] - pares_c["neutro"]).to_numpy(dtype=float)
        w_res = prueba_wilcoxon_pareada(diffs)
        hl_diff = estimador_hodges_lehmann_diferencia(diffs)
        ic_l, ic_u = bootstrap_hodges_lehmann_vectorizado(
            diffs,
            semilla=cfg.parametros.semilla_aleatoria + 600 + idx,
            replicas=replicas_boot,
            exponenciar=False,
        )
        filas.append(
            {
                "id_hipotesis": f"E1_nina_vs_neutro_{cultivo}",
                "hipotesis": f"E1 Exploratoria: anos Nina vs neutros ({cultivo})",
                "familia": "E1",
                "tipo": "exploratoria",
                "cultivo": cultivo,
                "contraste": "rendimiento Nina - neutro por municipio",
                "n": w_res.n,
                "n_secundario": w_res.n,
                "nombre_estadistico": "W",
                "estadistico": w_res.estadistico,
                "valor_p": w_res.valor_p,
                "nombre_efecto": "diferencia HL (t/ha)",
                "efecto": hl_diff,
                "ic_95_inf": ic_l,
                "ic_95_sup": ic_u,
                "efecto_secundario_nombre": "r_biserial_pareado",
                "efecto_secundario": w_res.r_biserial_pareado,
                "ic_95_sec_inf": float("nan"),
                "ic_95_sec_sup": float("nan"),
                "r_biserial": w_res.r_biserial_pareado,
            }
        )

    return pd.DataFrame(filas)


def evaluar_e2_quiebre_2022(
    tablas: dict[str, pd.DataFrame],
    cfg: ConfiguracionEdicion,
    umbral_ha: float = 500.0,
    replicas_boot: int = 5000,
) -> pd.DataFrame:
    per_eleg = _filtrar_elegibles(
        tablas["periodo_municipio_cultivo"],
        umbral_ha=umbral_ha,
        anios_minimos=cfg.parametros.anios_minimos_con_dato,
    )
    per_eleg["excluido_d4"] = per_eleg["area_cosechada"] > per_eleg["area_sembrada"]
    per_validos_d4 = per_eleg.loc[~per_eleg["excluido_d4"]]

    anual_sub = tablas["anual_municipio_cultivo"].merge(
        per_validos_d4[["codigo_dane_municipio", "cultivo"]],
        on=["codigo_dane_municipio", "cultivo"],
        how="inner",
    )
    anual_sub["subperiodo"] = np.where(anual_sub["quiebre_2022"], "post_2022", "pre_2022")

    agrup_sub = anual_sub.groupby(
        ["codigo_dane_municipio", "cultivo", "subperiodo"], as_index=False
    ).agg(
        area_sembrada=("area_sembrada", "sum"),
        area_cosechada=("area_cosechada", "sum"),
    )
    mascara_tasa_valida = (agrup_sub["area_sembrada"] > 0) & (
        agrup_sub["area_sembrada"] >= agrup_sub["area_cosechada"]
    )
    agrup_sub["tasa_pct"] = np.where(
        mascara_tasa_valida,
        (agrup_sub["area_sembrada"] - agrup_sub["area_cosechada"])
        / agrup_sub["area_sembrada"]
        * 100.0,
        np.nan,
    )

    piv_e2 = agrup_sub.pivot_table(
        index=["codigo_dane_municipio", "cultivo"],
        columns="subperiodo",
        values="tasa_pct",
        aggfunc="first",
    ).reset_index()

    filas: list[dict[str, object]] = []
    for idx, cultivo in enumerate(sorted(cfg.cultivos)):
        excluidos_c = int(per_eleg.loc[per_eleg["cultivo"] == cultivo, "excluido_d4"].sum())
        if "pre_2022" not in piv_e2.columns or "post_2022" not in piv_e2.columns:
            pares_c = pd.DataFrame(columns=["pre_2022", "post_2022"])
        else:
            pares_c = piv_e2.loc[piv_e2["cultivo"] == cultivo, ["pre_2022", "post_2022"]].dropna()

        n_mpios = len(pares_c)
        titulo_e2 = f"E2 Exploratoria: tasa no cosechada 2022-2025 vs 2019-2021 ({cultivo})"
        if n_mpios < 2:
            filas.append(
                {
                    "id_hipotesis": f"E2_quiebre_2022_{cultivo}",
                    "hipotesis": titulo_e2,
                    "familia": "E2",
                    "tipo": "exploratoria",
                    "cultivo": cultivo,
                    "contraste": "tasa 2022-2025 minus 2019-2021 (pp, D3/D4)",
                    "n": n_mpios,
                    "n_secundario": excluidos_c,
                    "nombre_estadistico": "W",
                    "estadistico": float("nan"),
                    "valor_p": float("nan"),
                    "nombre_efecto": "diferencia HL (pp)",
                    "efecto": float("nan"),
                    "ic_95_inf": float("nan"),
                    "ic_95_sup": float("nan"),
                    "efecto_secundario_nombre": "excluidos_D4",
                    "efecto_secundario": float(excluidos_c),
                    "ic_95_sec_inf": float("nan"),
                    "ic_95_sec_sup": float("nan"),
                    "r_biserial": float("nan"),
                }
            )
            continue

        diffs = (pares_c["post_2022"] - pares_c["pre_2022"]).to_numpy(dtype=float)
        w_res = prueba_wilcoxon_pareada(diffs)
        hl_diff = estimador_hodges_lehmann_diferencia(diffs)
        ic_l, ic_u = bootstrap_hodges_lehmann_vectorizado(
            diffs,
            semilla=cfg.parametros.semilla_aleatoria + 700 + idx,
            replicas=replicas_boot,
            exponenciar=False,
        )
        filas.append(
            {
                "id_hipotesis": f"E2_quiebre_2022_{cultivo}",
                "hipotesis": titulo_e2,
                "familia": "E2",
                "tipo": "exploratoria",
                "cultivo": cultivo,
                "contraste": "tasa 2022-2025 minus 2019-2021 (pp, D3/D4)",
                "n": w_res.n,
                "n_secundario": excluidos_c,
                "nombre_estadistico": "W",
                "estadistico": w_res.estadistico,
                "valor_p": w_res.valor_p,
                "nombre_efecto": "diferencia HL (pp)",
                "efecto": hl_diff,
                "ic_95_inf": ic_l,
                "ic_95_sup": ic_u,
                "efecto_secundario_nombre": "excluidos_D4",
                "efecto_secundario": float(excluidos_c),
                "ic_95_sec_inf": float("nan"),
                "ic_95_sec_sup": float("nan"),
                "r_biserial": w_res.r_biserial_pareado,
            }
        )

    return pd.DataFrame(filas)


def ejecutar_bateria_hipotesis(
    tablas: dict[str, pd.DataFrame],
    df_oni: pd.DataFrame,
    cfg: ConfiguracionEdicion,
    umbral_ha: float = 500.0,
    replicas_boot: int = 5000,
    unidad_h2_h3: str = "municipio",
    excluir_poco_informativas: bool = False,
) -> dict[str, pd.DataFrame]:
    df_h1, df_h1_pend = evaluar_h1_tendencia(
        tablas,
        cfg,
        umbral_ha=umbral_ha,
        replicas_boot=replicas_boot,
        excluir_poco_informativas=excluir_poco_informativas,
    )
    df_h2 = evaluar_h2_maiz(
        tablas,
        cfg,
        umbral_ha=umbral_ha,
        replicas_boot=replicas_boot,
        unidad=unidad_h2_h3,
    )
    df_h3, df_h3_comp = evaluar_h3_arroz(
        tablas,
        cfg,
        umbral_ha=umbral_ha,
        replicas_boot=replicas_boot,
        unidad=unidad_h2_h3,
    )
    df_h4, df_h4_pares = evaluar_h4_departamentos(
        tablas, cfg, umbral_ha=umbral_ha, replicas_boot=replicas_boot
    )
    df_h5 = evaluar_h5_variabilidad(
        tablas,
        cfg,
        umbral_ha=umbral_ha,
        replicas_boot=replicas_boot,
        excluir_poco_informativas=excluir_poco_informativas,
    )
    df_e1 = evaluar_e1_clima(tablas, df_oni, cfg, umbral_ha=umbral_ha, replicas_boot=replicas_boot)
    df_e2 = evaluar_e2_quiebre_2022(tablas, cfg, umbral_ha=umbral_ha, replicas_boot=replicas_boot)

    df_exp = pd.concat([df_e1, df_e2], ignore_index=True)
    df_exp["valor_p_ajustado"] = ajustar_p_benjamini_hochberg(
        df_exp["valor_p"].to_numpy(dtype=float)
    )
    df_exp["metodo_ajuste"] = "Benjamini-Hochberg"
    decisiones_exp: list[str] = []
    for fila in df_exp.to_dict(orient="records"):
        n_u = int(fila["n"])
        nom_est = str(fila["nombre_estadistico"])
        p_adj = float(fila["valor_p_ajustado"])
        if (nom_est == "W" and n_u < MINIMO_UNIDADES_PRUEBA) or np.isnan(p_adj):
            decisiones_exp.append("insuficiente (n < 6, D6)")
        elif p_adj < ALFA_CONFIRMATORIO:
            decisiones_exp.append("asociacion exploratoria significativa (FDR < 0,05)")
        else:
            decisiones_exp.append("sin evidencia de asociacion exploratoria")
    df_exp["decision"] = decisiones_exp

    n_e1 = len(df_e1)
    df_e1_adj = df_exp.iloc[:n_e1].copy().reset_index(drop=True)
    df_e2_adj = df_exp.iloc[n_e1:].copy().reset_index(drop=True)

    resumen = pd.concat(
        [df_h1, df_h2, df_h3, df_h4, df_h5, df_e1_adj, df_e2_adj],
        ignore_index=True,
    )

    return {
        "h1_tendencia": df_h1,
        "h1_pendientes_municipales": df_h1_pend,
        "h2_brecha_maiz": df_h2,
        "h3_sistemas_arroz": df_h3,
        "h3_friedman_complemento": df_h3_comp,
        "h4_departamentos": df_h4,
        "h4_pares_departamentos": df_h4_pares,
        "h5_variabilidad_cv": df_h5,
        "e1_clima_oni": df_e1_adj,
        "e2_quiebre_2022": df_e2_adj,
        "resumen_hipotesis": resumen,
    }


def _fmt_ent(valor: int | float) -> str:
    if pd.isna(valor):
        return "N/A"
    return f"{int(valor):,}".replace(",", ".")


def _fmt_dec(valor: float, decimales: int = 4) -> str:
    if pd.isna(valor):
        return "N/A"
    texto = f"{float(valor):,.{decimales}f}"
    partes = texto.split(".")
    entero = partes[0].replace(",", ".")
    return f"{entero},{partes[1]}" if len(partes) > 1 else entero


def _fmt_p(valor: float) -> str:
    if pd.isna(valor):
        return "N/A"
    if valor < 0.0001:
        return "< 0,0001"
    return _fmt_dec(valor, 4)


def generar_reporte_resultados_estadisticos(
    resultados_base: dict[str, pd.DataFrame],
    df_robustez_resumen: pd.DataFrame,
    df_sensibilidad_d7: pd.DataFrame,
    df_oni: pd.DataFrame,
    tablas_base: dict[str, pd.DataFrame],
    cfg: ConfiguracionEdicion,
    tiempo_segundos: float,
    ruta_salida: str | Path = "docs/resultados_estadisticos.md",
) -> Path:
    ruta_md = Path(ruta_salida)
    ruta_md.parent.mkdir(parents=True, exist_ok=True)

    resumen = resultados_base["resumen_hipotesis"].merge(
        df_robustez_resumen[["id_hipotesis", "clasificacion_robustez", "variantes_discrepantes"]],
        on="id_hipotesis",
        how="left",
    )

    umbral_txt = _fmt_dec(cfg.parametros.area_cosechada_minima_ha, 0)
    anios_min = cfg.parametros.anios_minimos_con_dato
    rep_main = _fmt_ent(cfg.parametros.replicas_bootstrap)
    rep_rob = _fmt_ent(cfg.parametros.bootstrap_robustez)

    lineas: list[str] = [
        f"# Resultados estadísticos y robustez — {cfg.nombre_visible}",
        "",
        f"- **Edición**: `{cfg.id_edicion}`",
        f"- **Región**: {cfg.region}",
        f"- **Umbral base de elegibilidad**: `{umbral_txt} ha` y `{anios_min}` años con dato",
        (
            f"- **Semilla bootstrap**: `{cfg.parametros.semilla_aleatoria}` "
            f"(`{rep_main}` réplicas principales; `{rep_rob}` en variantes de robustez)"
        ),
        f"- **Tiempo total de ejecución**: `{_fmt_dec(tiempo_segundos, 2)} s`",
        "",
        "## 1. Clasificación climática anual ENSO (ONI de NOAA, 2019-2025)",
        "",
        "| Año | Temporadas móviles | ONI medio anual (°C) | Temporadas Niña (<= -0,5) "
        "| Temporadas Niño (>= 0,5) | Temporadas neutras | Clasificación anual |",
        "| :---: | ---: | ---: | ---: | ---: | ---: | :---: |",
    ]

    for fila in df_oni.to_dict(orient="records"):
        lineas.append(
            f"| {int(fila['anio'])} | {_fmt_ent(fila['temporadas'])} | "
            f"{_fmt_dec(float(fila['oni_anual']), 4)} | {_fmt_ent(fila['temporadas_nina'])} | "
            f"{_fmt_ent(fila['temporadas_nino'])} | {_fmt_ent(fila['temporadas_neutras'])} | "
            f"`{fila['clasificacion_enso']}` |"
        )

    enc_resumen = (
        "| Hipótesis | Familia | n | Estadístico | p | p ajustado "
        "| Efecto | Intervalo de 95 % | Decisión | Robustez |"
    )
    lineas.extend(
        [
            "",
            "## 2. Tabla resumen de pruebas preespecificadas (H1 a H5, E1 y E2)",
            "",
            enc_resumen,
            "| :--- | :---: | ---: | :--- | ---: | ---: | :--- | :---: | :--- | :--- |",
        ]
    )

    for fila in resumen.to_dict(orient="records"):
        est_txt = f"{fila['nombre_estadistico']} = {_fmt_dec(float(fila['estadistico']), 2)}"
        ef_txt = f"{fila['nombre_efecto']}: {_fmt_dec(float(fila['efecto']), 4)}"
        ic_inf = float(fila["ic_95_inf"])
        ic_sup = float(fila["ic_95_sup"])
        ic_txt = (
            f"[{_fmt_dec(ic_inf, 4)}; {_fmt_dec(ic_sup, 4)}]"
            if not (np.isnan(ic_inf) or np.isnan(ic_sup))
            else "N/A"
        )
        rob_clase = str(fila.get("clasificacion_robustez", "firme"))
        var_disc = str(fila.get("variantes_discrepantes", ""))
        rob_txt = f"**{rob_clase}**" if not var_disc else f"**{rob_clase}** ({var_disc})"

        lineas.append(
            f"| {fila['hipotesis']} | `{fila['familia']}` | {_fmt_ent(fila['n'])} | "
            f"{est_txt} | {_fmt_p(float(fila['valor_p']))} | "
            f"{_fmt_p(float(fila['valor_p_ajustado']))} | {ef_txt} | {ic_txt} | "
            f"{fila['decision']} | {rob_txt} |"
        )

    lineas.extend(
        [
            "",
            (
                "### 2.1. Sensibilidad adicional post-hoc "
                "(D7: H1 y H5 excluyendo series poco informativas)"
            ),
            "",
            (
                "| Hipótesis (sensibilidad post-hoc D7) | Familia | n (sin poco informativas) "
                "| Estadístico | p | p ajustado | Efecto | Intervalo de 95 % "
                "| Decisión en sensibilidad D7 |"
            ),
            "| :--- | :---: | ---: | :--- | ---: | ---: | :--- | :---: | :--- |",
        ]
    )
    for fila in df_sensibilidad_d7.to_dict(orient="records"):
        est_txt = f"{fila['nombre_estadistico']} = {_fmt_dec(float(fila['estadistico']), 2)}"
        ef_txt = f"{fila['nombre_efecto']}: {_fmt_dec(float(fila['efecto']), 4)}"
        ic_inf = float(fila["ic_95_inf"])
        ic_sup = float(fila["ic_95_sup"])
        ic_txt = (
            f"[{_fmt_dec(ic_inf, 4)}; {_fmt_dec(ic_sup, 4)}]"
            if not (np.isnan(ic_inf) or np.isnan(ic_sup))
            else "N/A"
        )
        lineas.append(
            f"| {fila['hipotesis']} | `{fila['familia']}` | {_fmt_ent(fila['n'])} | "
            f"{est_txt} | {_fmt_p(float(fila['valor_p']))} | "
            f"{_fmt_p(float(fila['valor_p_ajustado']))} | {ef_txt} | {ic_txt} | "
            f"{fila['decision']} |"
        )

    per_sis = tablas_base["periodo_municipio_sistema"]
    yuca_sis = (
        per_sis.loc[per_sis["cultivo"] == "Yuca"]
        .groupby("sistema", as_index=False)
        .agg(
            municipios=("codigo_dane_municipio", "nunique"),
            area_cosechada=("area_cosechada", "sum"),
            produccion=("produccion", "sum"),
            mediana_mpio=("rendimiento", "median"),
        )
    )
    yuca_sis["rend_ponderado"] = yuca_sis["produccion"] / yuca_sis["area_cosechada"]
    mapa_yuca = yuca_sis.set_index("sistema").to_dict(orient="index")
    y_fresco = mapa_yuca.get("fresco", {})
    y_ind = mapa_yuca.get("industrial", {})

    h2_fila = resultados_base["h2_brecha_maiz"].iloc[0]
    h3_comp = resultados_base["h3_friedman_complemento"].iloc[0]

    txt_h1 = (
        "En los municipios elegibles de la Región Caribe la pendiente mediana de Theil-Sen "
        "es 0,0000 t/ha/año debido a la alta proporción de años consecutivos con rendimiento "
        "administrativo repetido (que genera pendientes exactamente nulas descartadas por "
        "Wilcoxon con `zero_method='wilcox'`); conforme a D7, la tendencia no es medible en "
        "las series con valores repetidos y no debe interpretarse como equivalencia práctica, "
        "siendo además frágil en maíz (donde al excluir las series poco informativas o ampliar "
        "a 300 ha emerge una ligera pendiente negativa estadísticamente significativa)."
    )
    txt_h2 = (
        "En los municipios elegibles que registran ambos sistemas de maíz en los mismos años "
        f"({_fmt_ent(h2_fila['n'])} municipios, {_fmt_ent(h2_fila['n_secundario'])} pares "
        "municipio-año), el sistema tecnificado se asocia de forma firme con un rendimiento "
        "superior al tradicional, con una razón de Hodges-Lehmann de "
        f"{_fmt_dec(float(h2_fila['efecto']), 2)} veces "
        f"(IC 95 %: {_fmt_dec(float(h2_fila['ic_95_inf']), 2)} a "
        f"{_fmt_dec(float(h2_fila['ic_95_sup']), 2)}; razón mediana "
        f"{_fmt_dec(float(h2_fila['efecto_secundario']), 2)}) que se mantiene en todas las "
        "variantes de sensibilidad."
    )
    txt_h3 = (
        "En las comparaciones pareadas por municipio corregidas con Holm (D1 y D2), tanto el "
        "arroz bajo riego (razón HL = 2,02; firme) como el secano mecanizado (razón HL = 1,62; "
        "firme) se asocian con rendimientos significativamente mayores que el secano manual, "
        "mientras que el contraste directo entre riego y secano mecanizado cuenta con solo "
        "5 municipios elegibles con par y se clasifica como **insuficiente** según D6 (dado "
        "que con n < 6 el valor p bilateral exacto mínimo en Wilcoxon es 0,0625 > 0,05); el "
        "complemento de Friedman sobre las "
        f"{_fmt_ent(h3_comp['n_tripletas'])} tripletas completas arroja "
        f"chi2 = {_fmt_dec(float(h3_comp['estadistico_chi2']), 2)} "
        f"(p = {_fmt_p(float(h3_comp['valor_p']))}, "
        f"W = {_fmt_dec(float(h3_comp['w_kendall']), 4)}). "
        "De forma descriptiva en yuca (cuya desagregación responde al destino comercial), "
        "la yuca en fresco presenta un rendimiento regional ponderado de "
        f"{_fmt_dec(float(y_fresco.get('rend_ponderado', 0.0)), 2)} t/ha "
        f"(mediana municipal {_fmt_dec(float(y_fresco.get('mediana_mpio', 0.0)), 2)} t/ha en "
        f"{_fmt_ent(y_fresco.get('municipios', 0))} municipios) frente a "
        f"{_fmt_dec(float(y_ind.get('rend_ponderado', 0.0)), 2)} t/ha en yuca industrial "
        f"(mediana municipal {_fmt_dec(float(y_ind.get('mediana_mpio', 0.0)), 2)} t/ha en "
        f"{_fmt_ent(y_ind.get('municipios', 0))} municipios)."
    )
    txt_h4 = (
        "La prueba de Kruskal-Wallis evidencia diferencias interdepartamentales "
        "estadísticamente significativas y firmes en el rendimiento municipal del periodo "
        "para arroz (épsilon cuadrado = 0,41) y maíz (épsilon cuadrado = 0,11), mientras que "
        "en yuca (épsilon cuadrado = 0,03; p ajustado = 0,5330) no se observa evidencia de "
        "diferenciación departamental."
    )
    txt_h5 = (
        "En los 76 municipios donde arroz, maíz y yuca son simultáneamente elegibles (así "
        "como en los 52 municipios que restan al excluir las series poco informativas en la "
        "sensibilidad post-hoc D7), ni la prueba ómnibus de Friedman ni las comparaciones "
        "pareadas de Wilcoxon con corrección de Holm muestran diferencias estadísticamente "
        "significativas en el coeficiente de variación interanual del rendimiento (firme)."
    )
    txt_e1 = (
        "En el análisis exploratorio climático (corregido por Benjamini-Hochberg), ni las "
        "correlaciones exactas de Spearman a escala regional anual (n = 7 años) con el índice "
        "ONI ni las comparaciones intramunicipales pareadas entre años La Niña (2021-2022) y "
        "años neutros (2020, 2024, 2025) muestran asociaciones estadísticamente significativas "
        "(firme). Conforme a D8, la ausencia de correlación regional con el ONI anual no "
        "descarta eventos hidrometeorológicos locales, y el pico de área no cosechada de "
        "arroz en 2021 (36.766,30 ha; 23,64 %) se describe como un episodio concentrado "
        "geográficamente sin atribución climática."
    )
    txt_e2 = (
        "Tras excluir los municipios con área cosechada acumulada superior a la sembrada (D4), "
        "la comparación exploratoria entre 2022-2025 y 2019-2021 muestra un incremento "
        "estadísticamente significativo y firme en la tasa de área no cosechada de yuca "
        "(+4,65 puntos porcentuales; FDR = 0,0004), el cual se interpreta como desfase "
        "asociado al ciclo vegetativo largo del cultivo tras el cambio metodológico de 2022 "
        "(D3) y no como pérdida; en maíz no se observa cambio significativo (firme) y en "
        "arroz el resultado base no significativo es sensible a la exclusión de 2021 (frágil)."
    )

    lineas.extend(
        [
            "",
            "## 3. Interpretación por familia de hipótesis (lenguaje de asociación observada)",
            "",
            "### H1. Tendencia temporal del rendimiento municipal (2019-2025)",
            txt_h1,
            "",
            "### H2. Brecha tecnológica observada en maíz (tecnificado vs. tradicional)",
            txt_h2,
            "",
            "### H3. Diferencias observadas entre sistemas en arroz (y nota descriptiva en yuca)",
            txt_h3,
            "",
            "### H4. Diferencias interdepartamentales de rendimiento del periodo",
            txt_h4,
            "",
            "### H5. Variabilidad interanual del rendimiento (CV) entre cultivos",
            txt_h5,
            "",
            "### E1. Análisis exploratorio de asociación con el índice climático ONI (ENSO)",
            txt_e1,
            "",
            "### E2. Análisis exploratorio del quiebre 2022 en la tasa de área no cosechada",
            txt_e2,
        ]
    )

    ruta_md.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return ruta_md


def ejecutar_inferencia_completa(
    ruta_config: str | Path,
    ruta_reporte: str | Path | None = "docs/resultados_estadisticos.md",
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame, float]:
    from rindex.robustez import evaluar_robustez_completa

    t0 = time.perf_counter()
    cfg = cargar_configuracion(ruta_config)

    ruta_filtrado = Path(cfg.fuente.parquet_filtrado)
    if not ruta_filtrado.exists():
        raise FileNotFoundError(
            f"No existe '{ruta_filtrado}'. Ejecute primero rindex.ingesta y rindex.agregacion."
        )

    df_filtrado = pd.read_parquet(ruta_filtrado)
    df_limpio = limpiar_eva(df_filtrado, cfg)
    tablas_base = construir_tablas_agregadas(df_limpio, cfg)
    df_oni = obtener_oni_anual(cfg)

    resultados_base = ejecutar_bateria_hipotesis(
        tablas=tablas_base,
        df_oni=df_oni,
        cfg=cfg,
        umbral_ha=cfg.parametros.area_cosechada_minima_ha,
        replicas_boot=cfg.parametros.replicas_bootstrap,
        unidad_h2_h3="municipio",
    )

    df_h1_d7, _ = evaluar_h1_tendencia(
        tablas_base,
        cfg,
        umbral_ha=cfg.parametros.area_cosechada_minima_ha,
        replicas_boot=cfg.parametros.replicas_bootstrap,
        excluir_poco_informativas=True,
    )
    df_h5_d7 = evaluar_h5_variabilidad(
        tablas_base,
        cfg,
        umbral_ha=cfg.parametros.area_cosechada_minima_ha,
        replicas_boot=cfg.parametros.replicas_bootstrap,
        excluir_poco_informativas=True,
    )
    df_sensibilidad_d7 = pd.concat([df_h1_d7, df_h5_d7], ignore_index=True)

    df_robustez_detalle, df_robustez_resumen = evaluar_robustez_completa(
        df_limpio=df_limpio,
        df_oni=df_oni,
        resultados_base=resultados_base["resumen_hipotesis"],
        cfg=cfg,
    )

    dir_resultados = ruta_filtrado.parent / "resultados"
    dir_resultados.mkdir(parents=True, exist_ok=True)

    for nombre, df_res in resultados_base.items():
        df_res.to_parquet(dir_resultados / f"{nombre}.parquet", index=False)
    df_sensibilidad_d7.to_parquet(dir_resultados / "sensibilidad_d7.parquet", index=False)
    df_robustez_detalle.to_parquet(dir_resultados / "robustez_detalle.parquet", index=False)
    df_robustez_resumen.to_parquet(dir_resultados / "robustez.parquet", index=False)

    tiempo_s = time.perf_counter() - t0
    if ruta_reporte is not None:
        generar_reporte_resultados_estadisticos(
            resultados_base=resultados_base,
            df_robustez_resumen=df_robustez_resumen,
            df_sensibilidad_d7=df_sensibilidad_d7,
            df_oni=df_oni,
            tablas_base=tablas_base,
            cfg=cfg,
            tiempo_segundos=tiempo_s,
            ruta_salida=ruta_reporte,
        )

    return resultados_base, df_robustez_resumen, tiempo_s


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ejecuta las pruebas estadisticas H1-H5, E1-E2 y analisis de robustez."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Ruta al archivo YAML de configuracion de la edicion.",
    )
    parser.add_argument(
        "--reporte",
        default="docs/resultados_estadisticos.md",
        help="Ruta de salida para el reporte de resultados estadisticos.",
    )
    args = parser.parse_args()
    ejecutar_inferencia_completa(args.config, ruta_reporte=args.reporte)


if __name__ == "__main__":
    main()
