"""Descarga, respaldo local y clasificacion anual ENSO a partir del indice ONI de NOAA."""

import json
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

from rindex.config import ConfiguracionEdicion
from rindex.fuente import calcular_sha256


def parsear_oni_ascii(contenido_texto: str) -> pd.DataFrame:
    df = pd.read_csv(StringIO(contenido_texto.strip()), sep=r"\s+")
    mapeo_cols = {
        "SEAS": "temporada",
        "YR": "anio",
        "TOTAL": "total_sst",
        "ANOM": "anomalia_oni",
    }
    columnas_faltantes = set(mapeo_cols.keys()) - set(df.columns)
    if columnas_faltantes:
        raise ValueError(f"Formato ONI invalido, faltan columnas: {sorted(columnas_faltantes)}.")
    df = df.rename(columns=mapeo_cols)
    df["temporada"] = df["temporada"].astype(str).str.strip()
    df["anio"] = df["anio"].astype(int)
    df["total_sst"] = df["total_sst"].astype(float)
    df["anomalia_oni"] = df["anomalia_oni"].astype(float)
    return df[["temporada", "anio", "total_sst", "anomalia_oni"]].reset_index(drop=True)


def clasificar_enso_anual(
    df_oni_temporadas: pd.DataFrame,
    umbral_oni: float = 0.5,
    anio_inicio: int | None = None,
    anio_fin: int | None = None,
) -> pd.DataFrame:
    df = df_oni_temporadas.copy()
    if anio_inicio is not None:
        df = df.loc[df["anio"] >= anio_inicio]
    if anio_fin is not None:
        df = df.loc[df["anio"] <= anio_fin]

    df["_es_nina"] = (df["anomalia_oni"] <= -umbral_oni).astype(int)
    df["_es_nino"] = (df["anomalia_oni"] >= umbral_oni).astype(int)
    df["_es_neutro"] = (
        (df["anomalia_oni"] > -umbral_oni) & (df["anomalia_oni"] < umbral_oni)
    ).astype(int)

    anual = (
        df.groupby("anio", as_index=False)
        .agg(
            temporadas=("temporada", "count"),
            oni_anual=("anomalia_oni", "mean"),
            temporadas_nina=("_es_nina", "sum"),
            temporadas_nino=("_es_nino", "sum"),
            temporadas_neutras=("_es_neutro", "sum"),
        )
        .sort_values("anio")
        .reset_index(drop=True)
    )

    anual["clasificacion_enso"] = np.where(
        anual["oni_anual"] <= -umbral_oni,
        "nina",
        np.where(anual["oni_anual"] >= umbral_oni, "nino", "neutro"),
    )
    return anual


def _actualizar_manifiesto_oni(
    ruta_manifiesto: Path,
    info_oni: dict[str, Any],
) -> None:
    ruta_manifiesto.parent.mkdir(parents=True, exist_ok=True)
    datos_manifiesto: dict[str, Any] = {}
    if ruta_manifiesto.exists():
        try:
            contenido = json.loads(ruta_manifiesto.read_text(encoding="utf-8"))
            if isinstance(contenido, dict):
                datos_manifiesto = contenido
        except (OSError, json.JSONDecodeError):
            datos_manifiesto = {}

    datos_manifiesto["oni"] = info_oni
    with ruta_manifiesto.open("w", encoding="utf-8") as archivo:
        json.dump(datos_manifiesto, archivo, indent=2, ensure_ascii=False)


def obtener_oni_anual(
    cfg: ConfiguracionEdicion,
    ruta_respaldo_local: str | Path | None = None,
) -> pd.DataFrame:
    ruta_destino = Path(
        ruta_respaldo_local if ruta_respaldo_local is not None else cfg.clima.archivo_local
    )
    ruta_destino.parent.mkdir(parents=True, exist_ok=True)

    origen = "respaldo_local"
    if not ruta_destino.exists():
        respuesta = requests.get(cfg.clima.url_oni, timeout=60)
        respuesta.raise_for_status()
        ruta_destino.write_bytes(respuesta.content)
        origen = "descarga_noaa"

    texto = ruta_destino.read_text(encoding="utf-8")
    df_temporadas = parsear_oni_ascii(texto)
    hash_oni = calcular_sha256(ruta_destino)

    info_oni = {
        "origen": origen,
        "url": cfg.clima.url_oni,
        "nombre_archivo": ruta_destino.name,
        "fecha": datetime.now(UTC).isoformat(),
        "tamano": int(ruta_destino.stat().st_size),
        "filas": int(len(df_temporadas)),
        "columnas": int(df_temporadas.shape[1]),
        "hash": hash_oni,
    }
    _actualizar_manifiesto_oni(Path(cfg.fuente.manifiesto), info_oni)

    df_anual = clasificar_enso_anual(
        df_temporadas,
        umbral_oni=cfg.clima.umbral_oni,
        anio_inicio=cfg.anios.inicio,
        anio_fin=cfg.anios.fin,
    )

    ruta_parquet = Path(cfg.clima.parquet_anual)
    ruta_parquet.parent.mkdir(parents=True, exist_ok=True)
    df_anual.to_parquet(ruta_parquet, index=False)
    return df_anual
