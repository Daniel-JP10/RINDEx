"""Pruebas unitarias para limpieza, mapeo de sistemas, atipicos y agregacion."""

import pandas as pd
import pytest

from rindex.agregacion import (
    construir_tablas_agregadas,
    verificar_conservacion_y_jerarquia,
)
from rindex.config import ConfiguracionEdicion, validar_diccionario_config
from rindex.limpieza import limpiar_eva
from test_config import config_base_valida


def _cfg_sintetica() -> ConfiguracionEdicion:
    return validar_diccionario_config(config_base_valida())


def _fila_base(
    mpio: str = "08638",
    depto: str = "08",
    cultivo: str = "Maíz",
    desagregacion: str = "Maíz amarillo tecnificado",
    anio: int = 2021,
    periodo: str = "2021A",
    sembrada: float = 100.0,
    cosechada: float = 100.0,
    produccion: float = 400.0,
) -> dict[str, object]:
    rend = produccion / cosechada if cosechada > 0 else 0.0
    return {
        "codigo_dane_departamento": depto,
        "departamento": "Atlántico" if depto == "08" else "Bolívar",
        "codigo_dane_municipio": mpio,
        "municipio": f"Mpio_{mpio}",
        "grupo_cultivo": "Cereales",
        "subgrupo": "Cereales",
        "cultivo": cultivo,
        "desagregacion_cultivo": desagregacion,
        "anio": anio,
        "periodo": periodo,
        "area_sembrada": sembrada,
        "area_cosechada": cosechada,
        "produccion": produccion,
        "rendimiento": rend,
        "ciclo_del_cultivo": "Transitorio",
        "estado_fisico_del_cultivo": "Grano seco",
        "codigo_del_cultivo": 1050101,
        "nombre_cientifico_del_cultivo": "Zea mays",
    }


def test_valor_desagregacion_sin_mapear_genera_error() -> None:
    cfg = _cfg_sintetica()
    df = pd.DataFrame([_fila_base(desagregacion="Maíz transgenico experimental")])
    with pytest.raises(ValueError, match="Maíz transgenico experimental"):
        limpiar_eva(df, cfg)


def test_atipicos_rendimiento_extremo_marcado_y_normal_no() -> None:
    cfg = _cfg_sintetica()
    rendimientos_normales = [4.0, 4.2, 3.9, 4.1, 4.05, 3.95, 4.15, 3.85]
    filas = [
        _fila_base(
            anio=2019 + (i % 5),
            periodo=f"{2019 + (i % 5)}A",
            cosechada=100.0,
            produccion=100.0 * r,
        )
        for i, r in enumerate(rendimientos_normales)
    ]
    # Rendimiento extremo: 45 t/ha en maiz (limite maximo 12 t/ha y z_robusto >> 3.5)
    filas.append(
        _fila_base(
            anio=2024,
            periodo="2024B",
            cosechada=100.0,
            produccion=4500.0,
        )
    )
    # Fila con cosecha y produccion en cero: no debe marcarse como atipica ni aportar rendimiento
    filas.append(
        _fila_base(
            anio=2025,
            periodo="2025A",
            sembrada=50.0,
            cosechada=0.0,
            produccion=0.0,
        )
    )
    df = pd.DataFrame(filas)
    limpio = limpiar_eva(df, cfg)

    normales = limpio.iloc[: len(rendimientos_normales)]
    extrema = limpio.iloc[len(rendimientos_normales)]
    cero = limpio.iloc[-1]

    assert not normales["fuera_de_rango"].any()
    assert not normales["atipico_robusto"].any()

    assert bool(extrema["fuera_de_rango"]) is True
    assert bool(extrema["atipico_robusto"]) is True

    assert bool(cero["fuera_de_rango"]) is False
    assert bool(cero["atipico_robusto"]) is False
    assert pd.isna(cero["rendimiento"])


def test_conservacion_sumas_en_cada_nivel() -> None:
    cfg = _cfg_sintetica()
    filas = [
        _fila_base(
            mpio="08638", depto="08", anio=2019, sembrada=120.0, cosechada=100.0, produccion=400.0
        ),
        _fila_base(
            mpio="08638",
            depto="08",
            anio=2020,
            desagregacion="Maíz amarillo tradicional",
            sembrada=200.0,
            cosechada=180.0,
            produccion=360.0,
        ),
        _fila_base(
            mpio="13244",
            depto="13",
            cultivo="Arroz",
            desagregacion="Arroz riego",
            anio=2021,
            sembrada=350.0,
            cosechada=340.0,
            produccion=2040.0,
        ),
        _fila_base(
            mpio="13244",
            depto="13",
            cultivo="Yuca",
            desagregacion="Yuca consumo en fresco",
            anio=2022,
            sembrada=150.0,
            cosechada=140.0,
            produccion=1400.0,
        ),
    ]
    df_filtrado = pd.DataFrame(filas)
    df_limpio = limpiar_eva(df_filtrado, cfg)
    tablas = construir_tablas_agregadas(df_limpio, cfg)

    verificar_conservacion_y_jerarquia(df_filtrado, tablas)

    for df_tabla in tablas.values():
        assert pytest.approx(df_tabla["area_sembrada"].sum(), abs=1e-6) == 820.0
        assert pytest.approx(df_tabla["area_cosechada"].sum(), abs=1e-6) == 760.0
        assert pytest.approx(df_tabla["produccion"].sum(), abs=1e-6) == 4200.0


def test_rendimiento_agregado_es_ponderado_no_promedio_simple() -> None:
    cfg = _cfg_sintetica()
    # Fila 1: 10 ha con rendimiento 10 t/ha -> 100 t
    # Fila 2: 90 ha con rendimiento 2 t/ha -> 180 t
    # Promedio simple = 6.0 t/ha (incorrecto). Ponderado = 280 / 100 = 2.8 t/ha.
    filas = [
        _fila_base(periodo="2022A", sembrada=10.0, cosechada=10.0, produccion=100.0),
        _fila_base(periodo="2022B", sembrada=90.0, cosechada=90.0, produccion=180.0),
    ]
    df_limpio = limpiar_eva(pd.DataFrame(filas), cfg)
    tablas = construir_tablas_agregadas(df_limpio, cfg)

    rend_anual = float(tablas["anual_municipio_cultivo"]["rendimiento"].iloc[0])
    rend_periodo = float(tablas["periodo_municipio_cultivo"]["rendimiento"].iloc[0])

    assert pytest.approx(rend_anual, abs=1e-9) == 2.8
    assert pytest.approx(rend_periodo, abs=1e-9) == 2.8
    assert rend_anual != 6.0


def test_columnas_elegibilidad_responden_a_umbrales() -> None:
    cfg = _cfg_sintetica()
    filas: list[dict[str, object]] = []
    # Mpio 08001: 4 anios, 90 ha/anio = 360 ha -> elegible_300=True, 500=False, 1000=False
    for anio in (2019, 2020, 2021, 2022):
        filas.append(
            _fila_base(mpio="08001", anio=anio, sembrada=90.0, cosechada=90.0, produccion=360.0)
        )
    # Mpio 08002: 4 anios, 150 ha/anio = 600 ha -> elegible_300=True, 500=True, 1000=False
    for anio in (2019, 2020, 2021, 2022):
        filas.append(
            _fila_base(mpio="08002", anio=anio, sembrada=150.0, cosechada=150.0, produccion=600.0)
        )
    # Mpio 08003: 5 anios, 250 ha/anio = 1250 ha -> elegible_300=True, 500=True, 1000=True
    for anio in (2019, 2020, 2021, 2022, 2023):
        filas.append(
            _fila_base(mpio="08003", anio=anio, sembrada=250.0, cosechada=250.0, produccion=1000.0)
        )
    # Mpio 08004: 3 anios (< 4 min), 500 ha/anio = 1500 ha -> todos False por falta de anios
    for anio in (2019, 2020, 2021):
        filas.append(
            _fila_base(mpio="08004", anio=anio, sembrada=500.0, cosechada=500.0, produccion=2000.0)
        )

    df_limpio = limpiar_eva(pd.DataFrame(filas), cfg)
    tablas = construir_tablas_agregadas(df_limpio, cfg)
    per = tablas["periodo_municipio_cultivo"].set_index("codigo_dane_municipio")

    assert (
        bool(per.loc["08001", "elegible_300"]),
        bool(per.loc["08001", "elegible_500"]),
        bool(per.loc["08001", "elegible_1000"]),
    ) == (True, False, False)
    assert (
        bool(per.loc["08002", "elegible_300"]),
        bool(per.loc["08002", "elegible_500"]),
        bool(per.loc["08002", "elegible_1000"]),
    ) == (True, True, False)
    assert (
        bool(per.loc["08003", "elegible_300"]),
        bool(per.loc["08003", "elegible_500"]),
        bool(per.loc["08003", "elegible_1000"]),
    ) == (True, True, True)
    assert (
        bool(per.loc["08004", "elegible_300"]),
        bool(per.loc["08004", "elegible_500"]),
        bool(per.loc["08004", "elegible_1000"]),
    ) == (False, False, False)
