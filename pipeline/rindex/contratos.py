"""Contratos de datos con Pandera para la base EVA cruda y normalizada."""

import re
import unicodedata

import pandas as pd
import pandera.pandas as pa

COLUMNAS_CRUDAS_A_NORMALIZADAS: dict[str, str] = {
    "Código Dane departamento": "codigo_dane_departamento",
    "Departamento": "departamento",
    "Código Dane municipio": "codigo_dane_municipio",
    "Municipio": "municipio",
    "Grupo cultivo": "grupo_cultivo",
    "Subgrupo": "subgrupo",
    "Cultivo": "cultivo",
    "Desagregación cultivo": "desagregacion_cultivo",
    "Año": "anio",
    "Periodo": "periodo",
    "Área sembrada": "area_sembrada",
    "Área cosechada": "area_cosechada",
    "Producción": "produccion",
    "Rendimiento": "rendimiento",
    "Ciclo del cultivo": "ciclo_del_cultivo",
    "Estado físico del cultivo": "estado_fisico_del_cultivo",
    "Código del cultivo": "codigo_del_cultivo",
    "Nombre científico del cultivo": "nombre_cientifico_del_cultivo",
}

PATRON_PERIODO = r"^\d{4}[AB]?$"


def normalizar_nombre_columna(nombre: str) -> str:
    if nombre in COLUMNAS_CRUDAS_A_NORMALIZADAS:
        return COLUMNAS_CRUDAS_A_NORMALIZADAS[nombre]
    texto = nombre.strip().lower().replace("ñ", "ni")
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    return texto.strip("_")


def normalizar_columnas_df(df: pd.DataFrame) -> pd.DataFrame:
    mapeo = {col: normalizar_nombre_columna(str(col)) for col in df.columns}
    return df.rename(columns=mapeo)


def _definir_columnas_esquema(
    nombres: dict[str, str],
    anio_min: int,
    anio_max: int,
) -> dict[str, pa.Column]:
    return {
        nombres["Código Dane departamento"]: pa.Column(
            int,
            checks=pa.Check.gt(0),
            nullable=False,
            coerce=True,
        ),
        nombres["Departamento"]: pa.Column(
            str,
            checks=pa.Check.str_length(min_value=1),
            nullable=False,
            coerce=True,
        ),
        nombres["Código Dane municipio"]: pa.Column(
            int,
            checks=pa.Check.gt(0),
            nullable=False,
            coerce=True,
        ),
        nombres["Municipio"]: pa.Column(
            str,
            checks=pa.Check.str_length(min_value=1),
            nullable=False,
            coerce=True,
        ),
        nombres["Grupo cultivo"]: pa.Column(
            str,
            checks=pa.Check.str_length(min_value=1),
            nullable=False,
            coerce=True,
        ),
        nombres["Subgrupo"]: pa.Column(
            str,
            checks=pa.Check.str_length(min_value=1),
            nullable=False,
            coerce=True,
        ),
        nombres["Cultivo"]: pa.Column(
            str,
            checks=pa.Check.str_length(min_value=1),
            nullable=False,
            coerce=True,
        ),
        nombres["Desagregación cultivo"]: pa.Column(
            str,
            checks=pa.Check.str_length(min_value=1),
            nullable=False,
            coerce=True,
        ),
        nombres["Año"]: pa.Column(
            int,
            checks=pa.Check.in_range(anio_min, anio_max),
            nullable=False,
            coerce=True,
        ),
        nombres["Periodo"]: pa.Column(
            str,
            checks=pa.Check.str_matches(PATRON_PERIODO),
            nullable=False,
            coerce=True,
        ),
        nombres["Área sembrada"]: pa.Column(
            float,
            checks=pa.Check.ge(0.0),
            nullable=False,
            coerce=True,
        ),
        nombres["Área cosechada"]: pa.Column(
            float,
            checks=pa.Check.ge(0.0),
            nullable=False,
            coerce=True,
        ),
        nombres["Producción"]: pa.Column(
            float,
            checks=pa.Check.ge(0.0),
            nullable=False,
            coerce=True,
        ),
        nombres["Rendimiento"]: pa.Column(
            float,
            checks=pa.Check.ge(0.0),
            nullable=False,
            coerce=True,
        ),
        nombres["Ciclo del cultivo"]: pa.Column(
            str,
            checks=pa.Check.str_length(min_value=1),
            nullable=False,
            coerce=True,
        ),
        nombres["Estado físico del cultivo"]: pa.Column(
            str,
            checks=pa.Check.str_length(min_value=1),
            nullable=False,
            coerce=True,
        ),
        nombres["Código del cultivo"]: pa.Column(
            int,
            checks=pa.Check.gt(0),
            nullable=False,
            coerce=True,
        ),
        nombres["Nombre científico del cultivo"]: pa.Column(
            str,
            checks=pa.Check.str_length(min_value=1),
            nullable=False,
            coerce=True,
        ),
    }


def construir_esquema_eva_cruda(
    anio_min: int = 2019,
    anio_max: int = 2025,
) -> pa.DataFrameSchema:
    identidad = {k: k for k in COLUMNAS_CRUDAS_A_NORMALIZADAS}
    return pa.DataFrameSchema(
        columns=_definir_columnas_esquema(identidad, anio_min, anio_max),
        strict=True,
    )


def construir_esquema_eva_normalizada(
    anio_min: int = 2019,
    anio_max: int = 2025,
) -> pa.DataFrameSchema:
    return pa.DataFrameSchema(
        columns=_definir_columnas_esquema(COLUMNAS_CRUDAS_A_NORMALIZADAS, anio_min, anio_max),
        strict=True,
    )


def validar_contrato_eva(
    df: pd.DataFrame,
    anio_min: int = 2019,
    anio_max: int = 2025,
) -> pd.DataFrame:
    columnas_actuales = set(df.columns)
    columnas_normalizadas = set(COLUMNAS_CRUDAS_A_NORMALIZADAS.values())
    if columnas_actuales == columnas_normalizadas:
        esquema = construir_esquema_eva_normalizada(anio_min=anio_min, anio_max=anio_max)
    else:
        esquema = construir_esquema_eva_cruda(anio_min=anio_min, anio_max=anio_max)
    return esquema.validate(df, lazy=True)
