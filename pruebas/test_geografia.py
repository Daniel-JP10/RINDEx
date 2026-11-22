"""Pruebas unitarias para procesamiento topologico y validaciones de geografia."""

import json

import pytest

from rindex.config import validar_diccionario_config
from rindex.geografia import (
    construir_topojson_caribe,
    validar_topojson_caribe,
)
from test_config import config_base_valida


def _geojson_sintetico_dos_municipios() -> dict[str, object]:
    # Dos municipios adyacentes que comparten el borde en lon = -74.5
    # mas un registro de San Andres (88001) que debe excluirse
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "DPTO_CCDGO": "08",
                    "MPIO_CDPMP": "08001",
                    "MPIO_CNMBRE": "BARRANQUILLA",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-74.6, 10.9],
                            [-74.5, 10.9],
                            [-74.5, 11.0],
                            [-74.6, 11.0],
                            [-74.6, 10.9],
                        ]
                    ],
                },
            },
            {
                "type": "Feature",
                "properties": {
                    "DPTO_CCDGO": "08",
                    "MPIO_CDPMP": "08758",
                    "MPIO_CNMBRE": "SOLEDAD",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-74.5, 10.9],
                            [-74.4, 10.9],
                            [-74.4, 11.0],
                            [-74.5, 11.0],
                            [-74.5, 10.9],
                        ]
                    ],
                },
            },
            {
                "type": "Feature",
                "properties": {
                    "DPTO_CCDGO": "88",
                    "MPIO_CDPMP": "88001",
                    "MPIO_CNMBRE": "SAN ANDRES",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-81.72, 12.50],
                            [-81.70, 12.50],
                            [-81.70, 12.55],
                            [-81.72, 12.55],
                            [-81.72, 12.50],
                        ]
                    ],
                },
            },
        ],
    }


def test_construir_topojson_excluye_san_andres_y_disuelve_departamento() -> None:
    datos_cfg = config_base_valida()
    datos_cfg["departamentos"] = {"08": "Atlántico"}
    cfg = validar_diccionario_config(datos_cfg)

    geojson_crudo = _geojson_sintetico_dos_municipios()
    codigos_datos = {"08001": "Barranquilla", "08758": "Soledad"}

    topo_dict, df_val, resumen = construir_topojson_caribe(
        geojson_crudo=geojson_crudo,
        codigos_datos=codigos_datos,
        cfg=cfg,
    )
    bytes_out = json.dumps(topo_dict).encode("utf-8")
    validar_topojson_caribe(
        topo_dict=topo_dict,
        df_val=df_val,
        resumen_geo=resumen,
        tamano_bytes=len(bytes_out),
        cfg=cfg,
        verificar_conteos_oficiales=False,
    )

    mpios = topo_dict["objects"]["municipios"]["geometries"]
    deptos = topo_dict["objects"]["departamentos"]["geometries"]
    assert len(mpios) == 2
    assert len(deptos) == 1
    assert [m["properties"]["codigo"] for m in mpios] == ["08001", "08758"]
    assert deptos[0]["properties"] == {
        "codigo": "08",
        "nombre": "Atlántico",
        "departamento": "08",
    }
    assert pytest.approx(float(resumen["max_desajuste_huecos_solapamientos_pct"]), abs=1e-6) == 0.0


def test_desempate_de_codigos_entre_eva_y_geografia_falla() -> None:
    datos_cfg = config_base_valida()
    datos_cfg["departamentos"] = {"08": "Atlántico"}
    cfg = validar_diccionario_config(datos_cfg)

    geojson_crudo = _geojson_sintetico_dos_municipios()
    with pytest.raises(ValueError, match="Desempate de codigos DANE"):
        construir_topojson_caribe(
            geojson_crudo=geojson_crudo,
            codigos_datos={"08001": "Barranquilla", "08999": "Inexistente"},
            cfg=cfg,
        )
