"""Pruebas unitarias para brecha potencial, escenarios, tipologia y priorizacion."""

import numpy as np
import pandas as pd
import pytest

from rindex.brecha import calcular_brecha_potencial, simular_brecha_bootstrap_unidad
from rindex.config import ConfiguracionEdicion, validar_diccionario_config
from rindex.escenarios import combinar_escenarios_sin_doble_conteo, evaluar_s1_lineal
from rindex.evidencia import clasificar_nivel_evidencia_cultivo
from rindex.prioridad import generar_pesos_dirichlet
from test_config import config_base_valida


def _cfg_prueba() -> ConfiguracionEdicion:
    return validar_diccionario_config(config_base_valida())


def _construir_tablas_sistema_sinteticas(
    rendimientos_depto_08: list[float],
    rendimientos_depto_13: list[float] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    filas_per: list[dict[str, object]] = []
    filas_anual: list[dict[str, object]] = []

    grupos = [("08", "Atlántico", rendimientos_depto_08)]
    if rendimientos_depto_13 is not None:
        grupos.append(("13", "Bolívar", rendimientos_depto_13))

    for cod_dep, nom_dep, lista_r in grupos:
        for idx, r in enumerate(lista_r, start=1):
            cod_mpio = f"{cod_dep}{idx:03d}"
            filas_per.append(
                {
                    "codigo_dane_departamento": cod_dep,
                    "departamento": nom_dep,
                    "codigo_dane_municipio": cod_mpio,
                    "municipio": f"Mpio_{cod_mpio}",
                    "cultivo": "Maíz",
                    "sistema": "tradicional",
                    "registros": 5,
                    "area_sembrada": 1000.0,
                    "area_cosechada": 1000.0,
                    "area_no_cosechada": 0.0,
                    "tasa_area_no_cosechada": 0.0,
                    "produccion": 1000.0 * r,
                    "anios_con_dato": 5,
                    "rendimiento": r,
                    "cv_interanual": 0.05,
                    "filas_fuera_de_rango": 0,
                    "filas_atipico_robusto": 0,
                    "filas_atipicas": 0,
                    "proporcion_repetidos": 0.0,
                    "serie_poco_informativa": False,
                    "elegible_300": True,
                    "elegible_500": True,
                    "elegible_1000": True,
                }
            )
            for t_idx, anio in enumerate((2019, 2020, 2021, 2022, 2023)):
                variacion = (-0.05 + 0.025 * t_idx) * r
                r_t = max(0.1, r + variacion)
                filas_anual.append(
                    {
                        "codigo_dane_departamento": cod_dep,
                        "departamento": nom_dep,
                        "codigo_dane_municipio": cod_mpio,
                        "municipio": f"Mpio_{cod_mpio}",
                        "cultivo": "Maíz",
                        "sistema": "tradicional",
                        "anio": anio,
                        "registros": 1,
                        "area_sembrada": 200.0,
                        "area_cosechada": 200.0,
                        "area_no_cosechada": 0.0,
                        "tasa_area_no_cosechada": 0.0,
                        "produccion": 200.0 * r_t,
                        "rendimiento": r_t,
                        "filas_fuera_de_rango": 0,
                        "filas_atipico_robusto": 0,
                        "filas_atipicas": 0,
                        "quiebre_2022": anio >= 2022,
                        "anio_posiblemente_incompleto": False,
                    }
                )

    return pd.DataFrame(filas_per), pd.DataFrame(filas_anual)


def test_brecha_cero_sobre_referencia_y_positiva_bajo_ella() -> None:
    cfg = _cfg_prueba()
    # 5 municipios en depto 08 con rendimientos [1.0, 2.0, 3.0, 4.0, 5.0] -> P75 = 4.0
    df_per, df_anual = _construir_tablas_sistema_sinteticas([1.0, 2.0, 3.0, 4.0, 5.0])
    brecha = calcular_brecha_potencial(df_per, df_anual, cfg, replicas_boot=200).set_index(
        "codigo_dane_municipio"
    )

    # Municipios en o sobre P75 (4.0 y 5.0): brecha y ganancia exactamente cero
    for cod in ("08004", "08005"):
        assert float(brecha.loc[cod, "brecha_tha"]) == 0.0
        assert float(brecha.loc[cod, "ganancia_anual_t"]) == 0.0
        assert float(brecha.loc[cod, "ganancia_p50"]) == 0.0
        assert float(brecha.loc[cod, "ganancia_p90"]) == 0.0

    # Municipios bajo P75 (1.0, 2.0, 3.0): brecha y ganancia estrictamente positivas
    for cod, esperado_b in (("08001", 3.0), ("08002", 2.0), ("08003", 1.0)):
        assert pytest.approx(float(brecha.loc[cod, "brecha_tha"]), abs=1e-9) == esperado_b
        assert float(brecha.loc[cod, "ganancia_anual_t"]) > 0.0
        assert float(brecha.loc[cod, "ganancia_p50"]) > 0.0


def test_linealidad_s1() -> None:
    ganancias_100 = np.array([0.0, 120.0, 450.5, 1800.0])
    mitad = evaluar_s1_lineal(ganancias_100, 0.5)
    cuarto = evaluar_s1_lineal(ganancias_100, 0.25)
    cero = evaluar_s1_lineal(ganancias_100, 0.0)

    np.testing.assert_allclose(mitad, 0.5 * ganancias_100, atol=1e-12)
    np.testing.assert_allclose(cuarto, 0.25 * ganancias_100, atol=1e-12)
    np.testing.assert_allclose(cero, 0.0, atol=1e-12)


def test_regla_combinacion_sin_doble_conteo() -> None:
    s1 = np.array([100.0, 300.0, 0.0])
    s2 = np.array([250.0, 120.0, 50.0])
    s3 = np.array([40.0, 30.0, 10.0])

    comb = combinar_escenarios_sin_doble_conteo(s1, s2, s3)
    esperado = np.array([290.0, 330.0, 60.0])

    np.testing.assert_allclose(comb, esperado, atol=1e-12)
    assert np.all(comb >= np.maximum(s1, s2))
    assert np.all(comb <= (s1 + s2 + s3))


def test_caida_a_referencia_regional_con_menos_de_5_municipios() -> None:
    cfg = _cfg_prueba()
    # Depto 08 tiene solo 3 municipios (< 5) -> debe usar referencia regional
    # Depto 13 tiene 5 municipios (>= 5) -> usa referencia departamental
    df_per, df_anual = _construir_tablas_sistema_sinteticas(
        rendimientos_depto_08=[1.5, 2.0, 2.5],
        rendimientos_depto_13=[3.0, 3.5, 4.0, 4.5, 5.0],
    )
    brecha = calcular_brecha_potencial(df_per, df_anual, cfg, replicas_boot=200)

    sub_08 = brecha.loc[brecha["codigo_dane_departamento"] == "08"]
    sub_13 = brecha.loc[brecha["codigo_dane_departamento"] == "13"]

    assert sub_08["referencia_regional"].all()
    assert not sub_13["referencia_regional"].any()

    p75_regional = float(np.percentile(df_per["rendimiento"], 75.0))
    p75_depto_13 = float(np.percentile([3.0, 3.5, 4.0, 4.5, 5.0], 75.0))

    assert pytest.approx(float(sub_08["rendimiento_referencia"].iloc[0]), abs=1e-9) == p75_regional
    assert pytest.approx(float(sub_13["rendimiento_referencia"].iloc[0]), abs=1e-9) == p75_depto_13


def test_dirichlet_reproducible_con_semilla_y_pesos_suman_1() -> None:
    w1 = generar_pesos_dirichlet((1.0, 1.0, 1.0, 1.0), juegos=2000, semilla=2026)
    w2 = generar_pesos_dirichlet((1.0, 1.0, 1.0, 1.0), juegos=2000, semilla=2026)

    assert w1.shape == (2000, 4)
    np.testing.assert_allclose(w1, w2, atol=0.0)
    np.testing.assert_allclose(w1.sum(axis=1), np.ones(2000), atol=1e-12)
    assert np.all(w1 >= 0.0)


def test_bootstrap_dos_niveles_varianza_mayor_o_igual_que_un_nivel() -> None:
    areas = np.array([200.0, 210.0, 190.0, 205.0, 195.0, 200.0])
    rend_anuales = np.array([1.8, 2.0, 1.9, 2.1, 1.85, 1.95])
    prods = areas * rend_anuales
    grupo_ref = np.array([2.2, 2.5, 3.0, 3.8, 4.5, 5.2, 6.0, 6.8])

    brecha_1, gan_1 = simular_brecha_bootstrap_unidad(
        areas_anuales=areas,
        producciones_anuales=prods,
        rendimientos_grupo_ref=grupo_ref,
        semilla=2026,
        replicas=5000,
        dos_niveles=False,
    )
    brecha_2, gan_2 = simular_brecha_bootstrap_unidad(
        areas_anuales=areas,
        producciones_anuales=prods,
        rendimientos_grupo_ref=grupo_ref,
        semilla=2026,
        replicas=5000,
        dos_niveles=True,
    )

    assert float(np.var(brecha_2, ddof=1)) >= float(np.var(brecha_1, ddof=1))
    assert float(np.var(gan_2, ddof=1)) >= float(np.var(gan_1, ddof=1))


def test_clasificacion_nivel_evidencia_cultivo_reglas_d9() -> None:
    cfg = _cfg_prueba()
    assert clasificar_nivel_evidencia_cultivo(18.0, 28.3, cfg) == "alto"
    assert clasificar_nivel_evidencia_cultivo(19.0, 37.3, cfg) == "alto"
    assert clasificar_nivel_evidencia_cultivo(30.0, 60.0, cfg) == "medio"
    assert clasificar_nivel_evidencia_cultivo(45.8, 91.1, cfg) == "bajo"
