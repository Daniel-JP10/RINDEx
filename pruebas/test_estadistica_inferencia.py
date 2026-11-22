"""Pruebas unitarias con resultado conocido para estadistica, bootstrap y clasificacion ENSO."""

import math

import numpy as np
import pandas as pd
import pytest

from rindex.clima import clasificar_enso_anual, parsear_oni_ascii
from rindex.estadistica import (
    ajustar_p_benjamini_hochberg,
    ajustar_p_holm,
    bootstrap_hodges_lehmann_vectorizado,
    bootstrap_mediana_vectorizado,
    calcular_pendiente_theil_sen,
    estimador_hodges_lehmann_diferencia,
    estimador_hodges_lehmann_log_razon,
    prueba_spearman_permutacion_exacta,
    prueba_wilcoxon_pareada,
    remuestrear_municipios_completos,
)


def test_theil_sen_recupera_pendiente_exacta_serie_lineal() -> None:
    anios = np.array([2019, 2020, 2021, 2022, 2023, 2024, 2025], dtype=float)
    pendiente_esperada = 0.35
    intercepto = 2.1
    rendimientos = intercepto + pendiente_esperada * (anios - 2019.0)

    pendiente_calc = calcular_pendiente_theil_sen(anios, rendimientos)
    assert pytest.approx(pendiente_calc, abs=1e-12) == pendiente_esperada


def test_holm_y_benjamini_hochberg_coinciden_con_calculo_a_mano() -> None:
    # Vector desordenado de 4 valores p: [0.04, 0.01, 0.03, 0.20]
    # Ordenados: p_(1)=0.01 (idx 1), p_(2)=0.03 (idx 2), p_(3)=0.04 (idx 0), p_(4)=0.20 (idx 3)
    # Holm (m=4):
    # q_(1) = 4 * 0.01 = 0.04
    # q_(2) = max(0.04, 3 * 0.03) = 0.09
    # q_(3) = max(0.09, 2 * 0.04) = 0.09 (monotonicidad step-down)
    # q_(4) = max(0.09, 1 * 0.20) = 0.20
    # En orden original: [0.09, 0.04, 0.09, 0.20]
    valores_p = [0.04, 0.01, 0.03, 0.20]
    holm_esperado = np.array([0.09, 0.04, 0.09, 0.20])
    holm_calc = ajustar_p_holm(valores_p)
    np.testing.assert_allclose(holm_calc, holm_esperado, atol=1e-12)

    # Benjamini-Hochberg (m=4):
    # r=1: 0.01 * 4/1 = 0.04
    # r=2: 0.03 * 4/2 = 0.06
    # r=3: 0.04 * 4/3 = 0.05333333333333334 -> step-up min(0.053333..., 0.20) = 0.053333...
    #      y para r=2: min(0.06, 0.053333...) = 0.053333...
    # r=4: 0.20 * 4/4 = 0.20
    # En orden original: [4/75, 0.04, 4/75, 0.20]
    bh_esperado = np.array([0.04 * 4.0 / 3.0, 0.04, 0.04 * 4.0 / 3.0, 0.20])
    bh_calc = ajustar_p_benjamini_hochberg(valores_p)
    np.testing.assert_allclose(bh_calc, bh_esperado, atol=1e-12)


def test_hodges_lehmann_coincide_con_caso_pequeno_a_mano() -> None:
    # d = [1.0, 2.0, 6.0]
    # Promedios de Walsh (i <= j):
    # (1+1)/2 = 1.0, (1+2)/2 = 1.5, (1+6)/2 = 3.5,
    # (2+2)/2 = 2.0, (2+6)/2 = 4.0,
    # (6+6)/2 = 6.0
    # Ordenados (6 valores): [1.0, 1.5, 2.0, 3.5, 4.0, 6.0]
    # Mediana = (2.0 + 3.5) / 2 = 2.75
    d = np.array([1.0, 2.0, 6.0])
    hl_diff = estimador_hodges_lehmann_diferencia(d)
    assert pytest.approx(hl_diff, abs=1e-12) == 2.75

    hl_log, hl_razon = estimador_hodges_lehmann_log_razon(d)
    assert pytest.approx(hl_log, abs=1e-12) == 2.75
    assert pytest.approx(hl_razon, abs=1e-12) == math.exp(2.75)


def test_wilcoxon_sobre_diferencias_nulas_no_rechaza() -> None:
    diferencias_cero = np.zeros(10, dtype=float)
    res_cero = prueba_wilcoxon_pareada(diferencias_cero)
    assert res_cero.valor_p == 1.0
    assert res_cero.r_biserial_pareado == 0.0

    # Diferencias perfectamente simetricas alrededor de cero tampoco rechazan
    diferencias_sim = np.array([-3.0, -2.0, -1.0, 1.0, 2.0, 3.0])
    res_sim = prueba_wilcoxon_pareada(diferencias_sim)
    assert res_sim.valor_p == 1.0
    assert pytest.approx(res_sim.r_biserial_pareado, abs=1e-12) == 0.0


def test_permutacion_exacta_serie_monotona_7_valores_da_2_sobre_5040() -> None:
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])
    y_creciente = np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0])
    y_decreciente = y_creciente[::-1]

    res_pos = prueba_spearman_permutacion_exacta(x, y_creciente)
    assert res_pos.n == 7
    assert pytest.approx(res_pos.rho, abs=1e-12) == 1.0
    assert pytest.approx(res_pos.valor_p_exacto, abs=1e-12) == 2.0 / 5040.0

    res_neg = prueba_spearman_permutacion_exacta(x, y_decreciente)
    assert pytest.approx(res_neg.rho, abs=1e-12) == -1.0
    assert pytest.approx(res_neg.valor_p_exacto, abs=1e-12) == 2.0 / 5040.0


def test_bootstrap_misma_semilla_da_resultados_identicos() -> None:
    valores = np.array([0.5, 0.8, 1.1, 1.4, 0.9, 1.2, 0.7, 1.5, 1.0, 0.6])
    ic_med_1 = bootstrap_mediana_vectorizado(valores, semilla=2026, replicas=1000)
    ic_med_2 = bootstrap_mediana_vectorizado(valores, semilla=2026, replicas=1000)
    assert ic_med_1 == ic_med_2

    ic_hl_1 = bootstrap_hodges_lehmann_vectorizado(
        valores, semilla=2026, replicas=1000, exponenciar=True
    )
    ic_hl_2 = bootstrap_hodges_lehmann_vectorizado(
        valores, semilla=2026, replicas=1000, exponenciar=True
    )
    assert ic_hl_1 == ic_hl_2


def test_bootstrap_remuestrea_municipios_completos_y_no_filas_sueltas() -> None:
    # Municipio A tiene 3 anios [2019, 2020, 2021], Municipio B tiene 2 anios [2022, 2023],
    # Municipio C tiene 4 anios [2019, 2020, 2021, 2022]
    df = pd.DataFrame(
        [
            {"codigo_dane_municipio": "08001", "anio": 2019, "marca": "A_19"},
            {"codigo_dane_municipio": "08001", "anio": 2020, "marca": "A_20"},
            {"codigo_dane_municipio": "08001", "anio": 2021, "marca": "A_21"},
            {"codigo_dane_municipio": "13001", "anio": 2022, "marca": "B_22"},
            {"codigo_dane_municipio": "13001", "anio": 2023, "marca": "B_23"},
            {"codigo_dane_municipio": "20001", "anio": 2019, "marca": "C_19"},
            {"codigo_dane_municipio": "20001", "anio": 2020, "marca": "C_20"},
            {"codigo_dane_municipio": "20001", "anio": 2021, "marca": "C_21"},
            {"codigo_dane_municipio": "20001", "anio": 2022, "marca": "C_22"},
        ]
    )
    esperado_por_mpio = {
        "08001": ["A_19", "A_20", "A_21"],
        "13001": ["B_22", "B_23"],
        "20001": ["C_19", "C_20", "C_21", "C_22"],
    }

    for sem in (2026, 2027, 2028):
        remuestreado = remuestrear_municipios_completos(df, semilla=sem)
        # Se seleccionan exactamente 3 clones municipales (igual al numero de municipios unicos)
        assert remuestreado["_id_clon_bootstrap"].nunique() == 3
        for _, sub_clon in remuestreado.groupby("_id_clon_bootstrap"):
            mpio = str(sub_clon["codigo_dane_municipio"].iloc[0])
            assert list(sub_clon["marca"]) == esperado_por_mpio[mpio]


def test_clasificacion_enso_oni_sintetico_es_la_esperada() -> None:
    temporadas = [
        "DJF",
        "JFM",
        "FMA",
        "MAM",
        "AMJ",
        "MJJ",
        "JJA",
        "JAS",
        "ASO",
        "SON",
        "OND",
        "NDJ",
    ]
    lineas = ["SEAS YR TOTAL ANOM"]
    # 2020: 12 temporadas con -0.7 -> media -0.7 -> nina (12 temporadas nina, 0 nino)
    for t in temporadas:
        lineas.append(f"{t} 2020 26.0 -0.70")
    # 2021: 12 temporadas con +0.8 -> media +0.8 -> nino (0 temporadas nina, 12 nino)
    for t in temporadas:
        lineas.append(f"{t} 2021 27.8 0.80")
    # 2022: 6 temporadas con -0.6, 3 con 0.0, 3 con +0.6 -> media -0.15 -> neutro (6 nina, 3 nino)
    valores_2022 = [-0.6] * 6 + [0.0] * 3 + [0.6] * 3
    for t, val in zip(temporadas, valores_2022, strict=True):
        lineas.append(f"{t} 2022 26.8 {val:.2f}")

    df_temp = parsear_oni_ascii("\n".join(lineas))
    df_anual = clasificar_enso_anual(df_temp, umbral_oni=0.5).set_index("anio")

    assert df_anual.loc[2020, "clasificacion_enso"] == "nina"
    assert int(df_anual.loc[2020, "temporadas_nina"]) == 12
    assert int(df_anual.loc[2020, "temporadas_nino"]) == 0

    assert df_anual.loc[2021, "clasificacion_enso"] == "nino"
    assert int(df_anual.loc[2021, "temporadas_nina"]) == 0
    assert int(df_anual.loc[2021, "temporadas_nino"]) == 12

    assert df_anual.loc[2022, "clasificacion_enso"] == "neutro"
    assert pytest.approx(float(df_anual.loc[2022, "oni_anual"]), abs=1e-9) == -0.15
    assert int(df_anual.loc[2022, "temporadas_nina"]) == 6
    assert int(df_anual.loc[2022, "temporadas_nino"]) == 3
