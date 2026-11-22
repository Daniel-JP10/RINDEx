"""Pruebas de validacion de JSON exportados y de la auditoria independiente."""

import importlib.util
from pathlib import Path

import pytest

from rindex.exportar import ARCHIVOS_ESQUEMA, ejecutar_exportacion_web

RUTA_XLSX_REAL = Path("data/raw/eva_2019_2025.xlsx")
RUTA_SCRIPT_AUDITORIA = Path("herramientas/auditoria_independiente.py")


def _cargar_modulo_auditoria():
    spec = importlib.util.spec_from_file_location(
        "auditoria_independiente",
        RUTA_SCRIPT_AUDITORIA,
    )
    assert spec is not None and spec.loader is not None
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.mark.skipif(
    not RUTA_XLSX_REAL.exists(),
    reason="No existe data/raw/eva_2019_2025.xlsx en este entorno; se omite auditoria real.",
)
def test_exportacion_web_y_auditoria_independiente_dentro_de_tolerancia(
    tmp_path: Path,
) -> None:
    res_exp = ejecutar_exportacion_web("config/caribe_2019_2025.yaml")
    assert res_exp["archivos_validados"] == len(ARCHIVOS_ESQUEMA)

    modulo_aud = _cargar_modulo_auditoria()
    reporte_tmp = tmp_path / "auditoria_independiente.md"
    df_aud, todo_ok = modulo_aud.ejecutar_auditoria_independiente(
        ruta_xlsx=RUTA_XLSX_REAL,
        dir_web_data=Path("web/public/data"),
        ruta_reporte=reporte_tmp,
    )
    assert todo_ok is True
    assert bool(df_aud["cumple"].all()) is True
    assert reporte_tmp.exists()
