"""Gestion de la fuente de datos cruda, conversion a Parquet y manifiesto."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from rindex.config import ConfiguracionEdicion

TAMANO_BLOQUE_HASH = 65536


def calcular_sha256(ruta: str | Path) -> str:
    ruta_archivo = Path(ruta)
    resumen = hashlib.sha256()
    with ruta_archivo.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(TAMANO_BLOQUE_HASH), b""):
            resumen.update(bloque)
    return resumen.hexdigest()


def _descargar_respaldo_csv(url: str, destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    respuesta = requests.get(url, timeout=120)
    respuesta.raise_for_status()
    destino.write_bytes(respuesta.content)
    return destino


def _leer_archivo_crudo(ruta: Path) -> pd.DataFrame:
    sufijo = ruta.suffix.lower()
    if sufijo in {".xlsx", ".xls"}:
        df = pd.read_excel(ruta)
    elif sufijo == ".csv":
        df = pd.read_csv(ruta)
    else:
        raise ValueError(f"Formato de archivo crudo no soportado: '{sufijo}'.")

    for columna in df.columns:
        if pd.api.types.is_object_dtype(df[columna]) or pd.api.types.is_string_dtype(df[columna]):
            mascara_no_nula = df[columna].notna()
            df.loc[mascara_no_nula, columna] = (
                df.loc[mascara_no_nula, columna].astype(str).str.strip()
            )
    return df


def _leer_manifiesto_previo(ruta_manifiesto: Path) -> dict[str, Any] | None:
    if not ruta_manifiesto.exists():
        return None
    try:
        with ruta_manifiesto.open("r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
        return datos if isinstance(datos, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _escribir_manifiesto(ruta_manifiesto: Path, manifiesto: dict[str, Any]) -> None:
    ruta_manifiesto.parent.mkdir(parents=True, exist_ok=True)
    with ruta_manifiesto.open("w", encoding="utf-8") as archivo:
        json.dump(manifiesto, archivo, indent=2, ensure_ascii=False)


def preparar_fuente_cruda(cfg: ConfiguracionEdicion) -> dict[str, Any]:
    ruta_local = Path(cfg.fuente.archivo_local)
    ruta_parquet = Path(cfg.fuente.parquet_crudo)
    ruta_manifiesto = Path(cfg.fuente.manifiesto)

    if ruta_local.exists():
        ruta_fuente = ruta_local
        origen = "local"
        nombre_original = cfg.fuente.nombre_original
    else:
        ruta_csv = ruta_local.parent / "eva_respaldo.csv"
        ruta_fuente = _descargar_respaldo_csv(cfg.fuente.url_respaldo, ruta_csv)
        origen = "respaldo_csv"
        nombre_original = ruta_csv.name

    hash_actual = calcular_sha256(ruta_fuente)
    tamano_bytes = int(ruta_fuente.stat().st_size)
    manifiesto_previo = _leer_manifiesto_previo(ruta_manifiesto)

    if (
        ruta_parquet.exists()
        and manifiesto_previo is not None
        and manifiesto_previo.get("hash") == hash_actual
        and "filas" in manifiesto_previo
        and "columnas" in manifiesto_previo
    ):
        manifiesto = {
            "origen": origen,
            "nombre_original": nombre_original,
            "fecha": str(manifiesto_previo.get("fecha", datetime.now(UTC).isoformat())),
            "tamano": tamano_bytes,
            "filas": int(manifiesto_previo["filas"]),
            "columnas": int(manifiesto_previo["columnas"]),
            "hash": hash_actual,
        }
        _escribir_manifiesto(ruta_manifiesto, manifiesto)
        return manifiesto

    df = _leer_archivo_crudo(ruta_fuente)
    ruta_parquet.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(ruta_parquet, index=False)

    manifiesto = {
        "origen": origen,
        "nombre_original": nombre_original,
        "fecha": datetime.now(UTC).isoformat(),
        "tamano": tamano_bytes,
        "filas": int(df.shape[0]),
        "columnas": int(df.shape[1]),
        "hash": hash_actual,
    }
    _escribir_manifiesto(ruta_manifiesto, manifiesto)
    return manifiesto
