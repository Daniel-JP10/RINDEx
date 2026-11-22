"""Pruebas unitarias para la carga y validacion de la configuracion YAML."""

from pathlib import Path
from typing import Any

import pytest
import yaml

from rindex.config import cargar_configuracion, validar_diccionario_config


def config_base_valida() -> dict[str, Any]:
    return {
        "id_edicion": "caribe_2019_2025",
        "nombre_visible": "Region Caribe 2019-2025",
        "region": "Caribe",
        "departamentos": {
            "08": "Atlantico",
            "13": "Bolivar",
            "20": "Cesar",
            "23": "Cordoba",
            "44": "La Guajira",
            "47": "Magdalena",
            "70": "Sucre",
        },
        "departamentos_excluidos": [
            {
                "codigo": "88",
                "nombre": "San Andres",
                "motivo": "volumenes marginales y sin comparabilidad con el continente",
            }
        ],
        "cultivos": ["Maíz", "Yuca", "Arroz"],
        "anios": {"inicio": 2019, "fin": 2025},
        "fuente": {
            "archivo_local": "data/raw/eva_2019_2025.xlsx",
            "nombre_original": "Evaluaciones_Agropecuarias_Municipales.xlsx",
            "url_respaldo": "https://www.datos.gov.co/api/views/uejq-wxrr/rows.csv?accessType=DOWNLOAD",
            "ficha": "https://www.datos.gov.co/Agricultura-y-Desarrollo-Rural/Evaluaciones-Agropecuarias-Municipales-EVA-2019-20/uejq-wxrr/about_data",
        },
        "parametros": {
            "semilla_aleatoria": 2026,
            "replicas_bootstrap": 5000,
            "area_cosechada_minima_ha": 500,
            "umbrales_elegibilidad_ha": [300, 500, 1000],
            "anios_minimos_con_dato": 4,
            "umbral_z_robusto": 3.5,
        },
        "mapeo_desagregacion": {
            "Arroz riego": {"cultivo": "Arroz", "sistema": "riego", "color": "no_aplica"},
            "Arroz secano manual": {
                "cultivo": "Arroz",
                "sistema": "secano_manual",
                "color": "no_aplica",
            },
            "Arroz secano mecanizado": {
                "cultivo": "Arroz",
                "sistema": "secano_mecanizado",
                "color": "no_aplica",
            },
            "Maíz amarillo tecnificado": {
                "cultivo": "Maíz",
                "sistema": "tecnificado",
                "color": "amarillo",
            },
            "Maíz amarillo tradicional": {
                "cultivo": "Maíz",
                "sistema": "tradicional",
                "color": "amarillo",
            },
            "Maíz blanco tecnificado": {
                "cultivo": "Maíz",
                "sistema": "tecnificado",
                "color": "blanco",
            },
            "Maíz blanco tradicional": {
                "cultivo": "Maíz",
                "sistema": "tradicional",
                "color": "blanco",
            },
            "Maíz tecnificado": {
                "cultivo": "Maíz",
                "sistema": "tecnificado",
                "color": "sin_dato",
            },
            "Maíz tradicional": {
                "cultivo": "Maíz",
                "sistema": "tradicional",
                "color": "sin_dato",
            },
            "Yuca consumo en fresco": {
                "cultivo": "Yuca",
                "sistema": "fresco",
                "color": "no_aplica",
            },
            "Yuca industrial": {
                "cultivo": "Yuca",
                "sistema": "industrial",
                "color": "no_aplica",
            },
        },
        "limites_plausibilidad_rendimiento": {
            "Maíz": {"minimo": 0.2, "maximo": 12.0},
            "Arroz": {"minimo": 0.5, "maximo": 12.0},
            "Yuca": {"minimo": 2.0, "maximo": 40.0},
        },
    }


def test_cargar_configuracion_real_valida() -> None:
    cfg = cargar_configuracion(Path("config/caribe_2019_2025.yaml"))
    assert cfg.id_edicion == "caribe_2019_2025"
    assert cfg.region == "Caribe"
    assert set(cfg.departamentos.keys()) == {"08", "13", "20", "23", "44", "47", "70"}
    assert "88" not in cfg.departamentos
    assert len(cfg.departamentos_excluidos) == 1
    assert cfg.departamentos_excluidos[0].codigo == "88"
    assert cfg.cultivos == ("Maíz", "Yuca", "Arroz")
    assert cfg.anios.inicio == 2019
    assert cfg.anios.fin == 2025
    assert cfg.parametros.semilla_aleatoria == 2026
    assert cfg.parametros.replicas_bootstrap == 5000
    assert cfg.parametros.area_cosechada_minima_ha == 500.0
    assert cfg.parametros.anios_minimos_con_dato == 4
    assert cfg.parametros.umbral_z_robusto == 3.5
    assert len(cfg.mapeo_desagregacion) == 11
    assert cfg.limites_plausibilidad_rendimiento["Maíz"].minimo == 0.2
    assert cfg.limites_plausibilidad_rendimiento["Yuca"].maximo == 40.0


@pytest.mark.parametrize(
    "campo_faltante",
    [
        "id_edicion",
        "nombre_visible",
        "region",
        "departamentos",
        "departamentos_excluidos",
        "cultivos",
        "anios",
        "fuente",
        "parametros",
        "mapeo_desagregacion",
        "limites_plausibilidad_rendimiento",
    ],
)
def test_error_con_campo_raiz_faltante(campo_faltante: str) -> None:
    datos = config_base_valida()
    del datos[campo_faltante]
    with pytest.raises(ValueError, match=campo_faltante):
        validar_diccionario_config(datos)


def test_error_con_subcampo_faltante_en_archivo(tmp_path: Path) -> None:
    datos = config_base_valida()
    del datos["parametros"]["semilla_aleatoria"]
    ruta_yaml = tmp_path / "invalido.yaml"
    ruta_yaml.write_text(yaml.safe_dump(datos), encoding="utf-8")

    with pytest.raises(ValueError, match="parametros.semilla_aleatoria"):
        cargar_configuracion(ruta_yaml)
