"""Pruebas unitarias de ingesta, filtrado e integridad contra la base cruda."""

from pathlib import Path

import pandas as pd
import yaml

from rindex.config import cargar_configuracion
from rindex.ingesta import ejecutar_ingesta

RUTA_FIXTURE_CSV = Path("pruebas/fixtures/eva_sintetica.csv")


def _preparar_entorno_ingesta(
    tmp_path: Path,
    anio_inicio: int = 2020,
    anio_fin: int = 2024,
) -> tuple[Path, pd.DataFrame]:
    df_crudo = pd.read_csv(RUTA_FIXTURE_CSV)
    ruta_xlsx = tmp_path / "raw" / "eva_2019_2025.xlsx"
    ruta_xlsx.parent.mkdir(parents=True, exist_ok=True)
    df_crudo.to_excel(ruta_xlsx, index=False)

    datos_cfg = {
        "id_edicion": "caribe_sintetico",
        "nombre_visible": "Caribe Sintetico",
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
        "anios": {"inicio": anio_inicio, "fin": anio_fin},
        "fuente": {
            "archivo_local": str(ruta_xlsx),
            "nombre_original": "eva_sintetica.xlsx",
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
    ruta_yaml = tmp_path / "config.yaml"
    ruta_yaml.write_text(yaml.safe_dump(datos_cfg), encoding="utf-8")
    return ruta_yaml, df_crudo


def test_ingesta_filtra_departamentos_cultivos_anios_y_excluye_88(
    tmp_path: Path,
) -> None:
    ruta_yaml, _ = _preparar_entorno_ingesta(tmp_path, anio_inicio=2020, anio_fin=2024)
    cfg = cargar_configuracion(ruta_yaml)
    ruta_perfil = tmp_path / "docs" / "perfil_datos.md"

    df_filtrado = ejecutar_ingesta(ruta_yaml, ruta_perfil=ruta_perfil)

    assert Path(cfg.fuente.parquet_filtrado).exists()
    assert ruta_perfil.exists()

    deptos_presentes = set(df_filtrado["codigo_dane_departamento"].unique())
    assert deptos_presentes.issubset(set(cfg.departamentos.keys()))
    assert "88" not in deptos_presentes
    assert "05" not in deptos_presentes

    cultivos_presentes = set(df_filtrado["cultivo"].unique())
    assert cultivos_presentes == {"Maíz", "Yuca", "Arroz"}
    assert "Mango" not in cultivos_presentes

    anios_presentes = set(df_filtrado["anio"].unique())
    assert min(anios_presentes) >= 2020
    assert max(anios_presentes) <= 2024
    assert 2019 not in anios_presentes
    assert 2025 not in anios_presentes

    assert (df_filtrado["codigo_dane_municipio"].str.len() == 5).all()


def test_integridad_suma_produccion_filtrada_igual_a_cruda_restringida(
    tmp_path: Path,
) -> None:
    ruta_yaml, df_crudo = _preparar_entorno_ingesta(tmp_path, anio_inicio=2019, anio_fin=2025)
    cfg = cargar_configuracion(ruta_yaml)
    df_filtrado = ejecutar_ingesta(ruta_yaml, ruta_perfil=None)

    codigos_esperados = {int(c) for c in cfg.departamentos}
    mascara_cruda = (
        df_crudo["Código Dane departamento"].isin(codigos_esperados)
        & df_crudo["Cultivo"].isin(cfg.cultivos)
        & df_crudo["Año"].between(cfg.anios.inicio, cfg.anios.fin)
    )
    suma_cruda_restringida = float(df_crudo.loc[mascara_cruda, "Producción"].sum())
    suma_filtrada = float(df_filtrado["produccion"].sum())

    assert suma_filtrada == suma_cruda_restringida
    assert len(df_filtrado) == int(mascara_cruda.sum())
