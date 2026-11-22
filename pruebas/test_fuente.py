"""Pruebas unitarias para la gestion de la fuente cruda y el manifiesto."""

import json
import os
from pathlib import Path

import pandas as pd

from rindex.config import ConfiguracionEdicion, validar_diccionario_config
from rindex.fuente import preparar_fuente_cruda

RUTA_FIXTURE_CSV = Path("pruebas/fixtures/eva_sintetica.csv")

CAMPOS_MANIFIESTO = {
    "origen",
    "nombre_original",
    "fecha",
    "tamano",
    "filas",
    "columnas",
    "hash",
}


def _crear_config_prueba(tmp_path: Path, ruta_xlsx: Path) -> ConfiguracionEdicion:
    datos = {
        "id_edicion": "prueba_caribe",
        "nombre_visible": "Prueba Caribe",
        "region": "Caribe",
        "departamentos": {"08": "Atlantico", "13": "Bolivar"},
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
            "archivo_local": str(ruta_xlsx),
            "nombre_original": "EVA_Original_2019_2025.xlsx",
            "parquet_crudo": str(tmp_path / "interim" / "eva_crudo.parquet"),
            "parquet_filtrado": str(tmp_path / "interim" / "eva_filtrada.parquet"),
            "manifiesto": str(tmp_path / "raw" / "manifiesto.json"),
            "url_respaldo": "https://www.datos.gov.co/api/views/uejq-wxrr/rows.csv?accessType=DOWNLOAD",
            "ficha": "https://www.datos.gov.co/Agricultura-y-Desarrollo-Rural/Evaluaciones-Agropecuarias-Municipales-EVA-2019-20/uejq-wxrr/about_data",
        },
        "parametros": {
            "semilla_aleatoria": 2026,
            "replicas_bootstrap": 5000,
            "area_cosechada_minima_ha": 500,
            "anios_minimos_con_dato": 4,
        },
    }
    return validar_diccionario_config(datos)


def test_manifiesto_tiene_todos_los_campos_y_no_reconvierte_si_hash_igual(
    tmp_path: Path,
) -> None:
    df_fixture = pd.read_csv(RUTA_FIXTURE_CSV)
    ruta_xlsx = tmp_path / "raw" / "eva_2019_2025.xlsx"
    ruta_xlsx.parent.mkdir(parents=True, exist_ok=True)
    df_fixture.to_excel(ruta_xlsx, index=False)

    cfg = _crear_config_prueba(tmp_path, ruta_xlsx)
    manifiesto_1 = preparar_fuente_cruda(cfg)

    ruta_manifiesto = Path(cfg.fuente.manifiesto)
    ruta_parquet = Path(cfg.fuente.parquet_crudo)
    assert ruta_manifiesto.exists()
    assert ruta_parquet.exists()

    contenido_json = json.loads(ruta_manifiesto.read_text(encoding="utf-8"))
    assert set(contenido_json.keys()) == CAMPOS_MANIFIESTO
    assert contenido_json["origen"] == "local"
    assert contenido_json["nombre_original"] == "EVA_Original_2019_2025.xlsx"
    assert contenido_json["filas"] == len(df_fixture)
    assert contenido_json["columnas"] == 18
    assert contenido_json["tamano"] > 0
    assert len(contenido_json["hash"]) == 64

    tiempo_previo = 1700000000.0
    os.utime(ruta_parquet, (tiempo_previo, tiempo_previo))
    mtime_antes = ruta_parquet.stat().st_mtime

    manifiesto_2 = preparar_fuente_cruda(cfg)
    mtime_despues = ruta_parquet.stat().st_mtime

    assert mtime_despues == mtime_antes
    assert manifiesto_2["hash"] == manifiesto_1["hash"]
