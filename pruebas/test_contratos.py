"""Pruebas unitarias para el contrato Pandera de la base EVA."""

from pathlib import Path

import pandas as pd
import pandera.errors as pa_errors
import pytest

from rindex.contratos import normalizar_columnas_df, validar_contrato_eva

RUTA_FIXTURE_CSV = Path("pruebas/fixtures/eva_sintetica.csv")


def _cargar_df_valido() -> pd.DataFrame:
    return pd.read_csv(RUTA_FIXTURE_CSV)


def test_contrato_acepta_ejemplo_valido_crudo_y_normalizado() -> None:
    df_crudo = _cargar_df_valido()
    validado_crudo = validar_contrato_eva(df_crudo, anio_min=2019, anio_max=2025)
    assert len(validado_crudo) == len(df_crudo)

    df_norm = normalizar_columnas_df(df_crudo)
    validado_norm = validar_contrato_eva(df_norm, anio_min=2019, anio_max=2025)
    assert len(validado_norm) == len(df_crudo)


@pytest.mark.parametrize(
    "columna_numerica",
    ["Área sembrada", "Área cosechada", "Producción", "Rendimiento"],
)
def test_contrato_rechaza_valores_negativos(columna_numerica: str) -> None:
    df = _cargar_df_valido()
    df.loc[0, columna_numerica] = -1.5
    with pytest.raises(pa_errors.SchemaErrors):
        validar_contrato_eva(df, anio_min=2019, anio_max=2025)


@pytest.mark.parametrize("anio_invalido", [2018, 2026, 1995])
def test_contrato_rechaza_anios_fuera_de_rango(anio_invalido: int) -> None:
    df = _cargar_df_valido()
    df.loc[0, "Año"] = anio_invalido
    with pytest.raises(pa_errors.SchemaErrors):
        validar_contrato_eva(df, anio_min=2019, anio_max=2025)


@pytest.mark.parametrize("periodo_invalido", ["2021C", "2021-A", "21A", "2021AB", "texto"])
def test_contrato_rechaza_periodos_mal_formados(periodo_invalido: str) -> None:
    df = _cargar_df_valido()
    df.loc[0, "Periodo"] = periodo_invalido
    with pytest.raises(pa_errors.SchemaErrors):
        validar_contrato_eva(df, anio_min=2019, anio_max=2025)
