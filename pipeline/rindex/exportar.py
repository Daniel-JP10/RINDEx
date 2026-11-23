"""Exportacion determinista de JSON para la web y validacion contra JSON Schema y TopoJSON."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import jsonschema
import numpy as np
import pandas as pd

from rindex.config import ConfiguracionEdicion, cargar_configuracion
from rindex.evidencia import calcular_concentracion_arroz_2021

VERSION_ESQUEMA = "1.0.0"
MAX_BYTES_ARCHIVO_WEB = 2 * 1024 * 1024

ARCHIVOS_ESQUEMA: dict[str, str] = {
    "meta.json": "meta.schema.json",
    "regional.json": "regional.schema.json",
    "departamental.json": "departamental.schema.json",
    "municipios_maiz.json": "municipios_maiz.schema.json",
    "municipios_arroz.json": "municipios_arroz.schema.json",
    "municipios_yuca.json": "municipios_yuca.schema.json",
    "escenarios.json": "escenarios.schema.json",
    "sistemas.json": "sistemas.schema.json",
    "hallazgos.json": "hallazgos.schema.json",
    "calidad.json": "calidad.schema.json",
}


def _ent(valor: float | int) -> int:
    return int(round(float(valor)))


def _rend(valor: float | int | None) -> float | None:
    if valor is None or pd.isna(valor):
        return None
    return round(float(valor), 2)


def _pct(valor: float | int | None) -> float | None:
    if valor is None or pd.isna(valor):
        return None
    return round(float(valor), 1)


def _dec(valor: float | int | None, digitos: int = 4) -> float | None:
    if valor is None or pd.isna(valor):
        return None
    return round(float(valor), digitos)


def _obtener_info_git() -> tuple[str, str]:
    try:
        commit_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        fecha_commit = subprocess.check_output(
            ["git", "log", "-1", "--format=%cI"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        if commit_hash and fecha_commit:
            return commit_hash, fecha_commit
    except Exception:
        pass
    return "0000000", "2026-11-22T00:00:00+00:00"


def construir_meta_json(cfg: ConfiguracionEdicion) -> dict[str, Any]:
    ruta_man = Path(cfg.fuente.manifiesto)
    man = json.loads(ruta_man.read_text(encoding="utf-8")) if ruta_man.exists() else {}
    commit_hash, fecha_gen = _obtener_info_git()

    hash_eva = str(man.get("hash", "0" * 64))
    hash_oni = str(man.get("oni", {}).get("hash", "0" * 64))
    info_geo = man.get("geografia", {})
    hash_geo = str(info_geo.get("hash", "0" * 64))

    return {
        "version_esquema": VERSION_ESQUEMA,
        "id_edicion": cfg.id_edicion,
        "nombre_visible": cfg.nombre_visible,
        "region": cfg.region,
        "anios": {
            "inicio": cfg.anios.inicio,
            "fin": cfg.anios.fin,
        },
        "cultivos": list(cfg.cultivos),
        "departamentos": dict(sorted(cfg.departamentos.items())),
        "departamentos_excluidos": [
            {
                "codigo": d.codigo,
                "nombre": d.nombre,
                "motivo": d.motivo,
            }
            for d in cfg.departamentos_excluidos
        ],
        "commit_hash": commit_hash,
        "fecha_generacion": fecha_gen,
        "semilla_aleatoria": cfg.parametros.semilla_aleatoria,
        "umbrales": {
            "area_cosechada_minima_ha": _ent(cfg.parametros.area_cosechada_minima_ha),
            "anios_minimos_con_dato": int(cfg.parametros.anios_minimos_con_dato),
            "replicas_bootstrap": int(cfg.parametros.replicas_bootstrap),
            "juegos_dirichlet": int(cfg.priorizacion.juegos_dirichlet),
            "top_k": int(cfg.priorizacion.top_k),
            "umbral_robustez_top_pct": _pct(cfg.priorizacion.umbral_robustez_top * 100.0) or 80.0,
        },
        "fuentes": [
            {
                "id": "eva",
                "nombre": "Evaluaciones Agropecuarias Municipales (EVA 2019-2025)",
                "url": cfg.fuente.ficha,
                "licencia": "Datos Abiertos Colombia (datos.gov.co, recurso uejq-wxrr)",
                "hash_sha256": hash_eva,
            },
            {
                "id": "oni",
                "nombre": "Oceanic Nino Index (ONI ERSST.v5, NOAA CPC)",
                "url": cfg.clima.url_oni,
                "licencia": "Dominio Publico NOAA / U.S. Government Works",
                "hash_sha256": hash_oni,
            },
            {
                "id": "mgn",
                "nombre": "Marco Geoestadistico Nacional (MGN DANE)",
                "url": cfg.geografia.url_mgn,
                "licencia": cfg.geografia.licencia,
                "hash_sha256": hash_geo,
                "version": cfg.geografia.version_mgn,
            },
        ],
    }


def construir_regional_json(
    anual_region: pd.DataFrame,
    df_oni: pd.DataFrame,
) -> dict[str, Any]:
    df = anual_region.merge(
        df_oni[["anio", "oni_anual", "clasificacion_enso"]],
        on="anio",
        how="left",
    ).sort_values(["cultivo", "anio"])

    registros: list[dict[str, Any]] = []
    for f in df.to_dict(orient="records"):
        tasa_raw = f["tasa_area_no_cosechada"]
        tasa_pct = _pct(float(tasa_raw) * 100.0) if not pd.isna(tasa_raw) else None
        registros.append(
            {
                "cultivo": str(f["cultivo"]),
                "anio": int(f["anio"]),
                "area_sembrada_ha": _ent(f["area_sembrada"]),
                "area_cosechada_ha": _ent(f["area_cosechada"]),
                "area_no_cosechada_ha": _ent(f["area_no_cosechada"]),
                "produccion_t": _ent(f["produccion"]),
                "rendimiento_tha": _rend(f["rendimiento"]) or 0.0,
                "tasa_area_no_cosechada_pct": tasa_pct,
                "quiebre_2022": bool(f["quiebre_2022"]),
                "anio_posiblemente_incompleto": bool(f["anio_posiblemente_incompleto"]),
                "clase_enso": str(f["clasificacion_enso"]),
                "oni_anual": _rend(f["oni_anual"]) or 0.0,
            }
        )
    return {"version_esquema": VERSION_ESQUEMA, "registros": registros}


def construir_departamental_json(
    anual_depto: pd.DataFrame,
    df_oni: pd.DataFrame,
) -> dict[str, Any]:
    df = anual_depto.merge(
        df_oni[["anio", "oni_anual", "clasificacion_enso"]],
        on="anio",
        how="left",
    ).sort_values(["codigo_dane_departamento", "cultivo", "anio"])

    registros: list[dict[str, Any]] = []
    for f in df.to_dict(orient="records"):
        tasa_raw = f["tasa_area_no_cosechada"]
        tasa_pct = _pct(float(tasa_raw) * 100.0) if not pd.isna(tasa_raw) else None
        registros.append(
            {
                "codigo_departamento": str(f["codigo_dane_departamento"]).zfill(2),
                "departamento": str(f["departamento"]),
                "cultivo": str(f["cultivo"]),
                "anio": int(f["anio"]),
                "area_sembrada_ha": _ent(f["area_sembrada"]),
                "area_cosechada_ha": _ent(f["area_cosechada"]),
                "area_no_cosechada_ha": _ent(f["area_no_cosechada"]),
                "produccion_t": _ent(f["produccion"]),
                "rendimiento_tha": _rend(f["rendimiento"]) or 0.0,
                "tasa_area_no_cosechada_pct": tasa_pct,
                "quiebre_2022": bool(f["quiebre_2022"]),
                "anio_posiblemente_incompleto": bool(f["anio_posiblemente_incompleto"]),
                "clase_enso": str(f["clasificacion_enso"]),
                "oni_anual": _rend(f["oni_anual"]) or 0.0,
            }
        )
    return {"version_esquema": VERSION_ESQUEMA, "registros": registros}


def construir_municipios_cultivo_json(
    cultivo: str,
    catalogo_mpios: list[dict[str, str]],
    periodo_mpio_cultivo: pd.DataFrame,
    periodo_mpio_sistema: pd.DataFrame,
    anual_mpio_cultivo: pd.DataFrame,
    evidencia_cultivo: pd.DataFrame,
    evidencia_municipal: pd.DataFrame,
    df_escenarios: pd.DataFrame,
    df_prioridad: pd.DataFrame,
) -> dict[str, Any]:
    fila_ev_c = evidencia_cultivo.loc[evidencia_cultivo["cultivo"] == cultivo]
    nivel_ev_cultivo = str(fila_ev_c["nivel_evidencia"].iloc[0]) if not fila_ev_c.empty else "bajo"

    per_c = {
        str(f["codigo_dane_municipio"]): f
        for f in periodo_mpio_cultivo.loc[periodo_mpio_cultivo["cultivo"] == cultivo].to_dict(
            orient="records"
        )
    }
    ev_m_c = {
        str(f["codigo_dane_municipio"]): str(f["nivel_evidencia_municipal"])
        for f in evidencia_municipal.loc[evidencia_municipal["cultivo"] == cultivo].to_dict(
            orient="records"
        )
    }
    esc_c = {
        str(f["codigo_dane_municipio"]): f
        for f in df_escenarios.loc[df_escenarios["cultivo"] == cultivo].to_dict(orient="records")
    }
    prio_c = {
        str(f["codigo_dane_municipio"]): f
        for f in df_prioridad.loc[df_prioridad["cultivo"] == cultivo].to_dict(orient="records")
    }

    sis_por_mpio: dict[str, dict[str, float | None]] = {}
    sub_sis = periodo_mpio_sistema.loc[periodo_mpio_sistema["cultivo"] == cultivo].sort_values(
        ["codigo_dane_municipio", "sistema"]
    )
    for f in sub_sis.to_dict(orient="records"):
        cod_m = str(f["codigo_dane_municipio"])
        sis_por_mpio.setdefault(cod_m, {})[str(f["sistema"])] = _rend(f["rendimiento"])

    series_por_mpio: dict[str, list[dict[str, Any]]] = {}
    sub_anual = anual_mpio_cultivo.loc[anual_mpio_cultivo["cultivo"] == cultivo].sort_values(
        ["codigo_dane_municipio", "anio"]
    )
    for f in sub_anual.to_dict(orient="records"):
        cod_m = str(f["codigo_dane_municipio"])
        series_por_mpio.setdefault(cod_m, []).append(
            {
                "anio": int(f["anio"]),
                "area_sembrada_ha": _ent(f["area_sembrada"]),
                "area_cosechada_ha": _ent(f["area_cosechada"]),
                "produccion_t": _ent(f["produccion"]),
                "rendimiento_tha": _rend(f["rendimiento"]),
            }
        )

    municipios_out: list[dict[str, Any]] = []
    for m_base in catalogo_mpios:
        cod_m = m_base["codigo"]
        info_p = per_c.get(cod_m)
        info_e = esc_c.get(cod_m)
        info_pr = prio_c.get(cod_m)

        if info_p is None:
            municipios_out.append(
                {
                    "codigo": cod_m,
                    "nombre": m_base["nombre"],
                    "codigo_departamento": m_base["codigo_departamento"],
                    "departamento": m_base["departamento"],
                    "con_datos": False,
                    "elegible": False,
                    "anios_con_dato": 0,
                    "area_sembrada_ha": 0,
                    "area_cosechada_ha": 0,
                    "produccion_t": 0,
                    "rendimiento_tha": None,
                    "tasa_area_no_cosechada_pct": None,
                    "cv_interanual_pct": None,
                    "nivel_evidencia": "sin_datos",
                    "calidad": {
                        "proporcion_repetidos_pct": 0.0,
                        "serie_poco_informativa": True,
                        "filas_atipicas": 0,
                        "excluido_d4": False,
                    },
                    "rendimiento_por_sistema": {},
                    "serie_anual": [],
                    "brecha": {
                        "brecha_relativa_pct": None,
                        "brecha_p10_tha": None,
                        "brecha_p50_tha": None,
                        "brecha_p90_tha": None,
                        "ganancia_p10_t": None,
                        "ganancia_p50_t": None,
                        "ganancia_p90_t": None,
                    },
                    "priorizacion": {
                        "cuadrante": None,
                        "indice_prioridad": None,
                        "rango": None,
                        "rango_p10": None,
                        "rango_p90": None,
                        "proporcion_top20_pct": None,
                        "prioridad_robusta": False,
                    },
                }
            )
            continue

        tasa_raw = info_p["tasa_area_no_cosechada"]
        cv_raw = info_p["cv_interanual"]
        excluido_d4 = bool(float(info_p["area_cosechada"]) > float(info_p["area_sembrada"]))
        tasa_pct = (
            _pct(float(tasa_raw) * 100.0) if (not pd.isna(tasa_raw) and not excluido_d4) else None
        )
        cv_pct = _pct(float(cv_raw) * 100.0) if not pd.isna(cv_raw) else None

        if info_e is not None:
            brecha_obj = {
                "brecha_relativa_pct": _pct(info_e["s1_brecha_relativa_pct"]),
                "brecha_p10_tha": _rend(info_e["s1_brecha_p10"]),
                "brecha_p50_tha": _rend(info_e["s1_brecha_p50"]),
                "brecha_p90_tha": _rend(info_e["s1_brecha_p90"]),
                "ganancia_p10_t": _ent(info_e["s1_p10"]),
                "ganancia_p50_t": _ent(info_e["s1_p50"]),
                "ganancia_p90_t": _ent(info_e["s1_p90"]),
            }
        else:
            brecha_obj = {
                "brecha_relativa_pct": None,
                "brecha_p10_tha": None,
                "brecha_p50_tha": None,
                "brecha_p90_tha": None,
                "ganancia_p10_t": None,
                "ganancia_p50_t": None,
                "ganancia_p90_t": None,
            }

        if info_pr is not None:
            prio_obj = {
                "cuadrante": str(info_pr["cuadrante"]),
                "indice_prioridad": _rend(info_pr["indice_prioridad"]),
                "rango": int(info_pr["rango_defecto"]),
                "rango_p10": _pct(info_pr["rango_p10"]),
                "rango_p90": _pct(info_pr["rango_p90"]),
                "proporcion_top20_pct": _pct(float(info_pr["proporcion_top20"]) * 100.0),
                "prioridad_robusta": bool(info_pr["prioridad_robusta"]),
            }
        else:
            prio_obj = {
                "cuadrante": None,
                "indice_prioridad": None,
                "rango": None,
                "rango_p10": None,
                "rango_p90": None,
                "proporcion_top20_pct": None,
                "prioridad_robusta": False,
            }

        municipios_out.append(
            {
                "codigo": cod_m,
                "nombre": m_base["nombre"],
                "codigo_departamento": m_base["codigo_departamento"],
                "departamento": m_base["departamento"],
                "con_datos": True,
                "elegible": bool(info_p["elegible_500"]),
                "anios_con_dato": int(info_p["anios_con_dato"]),
                "area_sembrada_ha": _ent(info_p["area_sembrada"]),
                "area_cosechada_ha": _ent(info_p["area_cosechada"]),
                "produccion_t": _ent(info_p["produccion"]),
                "rendimiento_tha": _rend(info_p["rendimiento"]),
                "tasa_area_no_cosechada_pct": tasa_pct,
                "cv_interanual_pct": cv_pct,
                "nivel_evidencia": ev_m_c.get(cod_m, "bajo"),
                "calidad": {
                    "proporcion_repetidos_pct": _pct(float(info_p["proporcion_repetidos"]) * 100.0)
                    or 0.0,
                    "serie_poco_informativa": bool(info_p["serie_poco_informativa"]),
                    "filas_atipicas": int(info_p["filas_atipicas"]),
                    "excluido_d4": excluido_d4,
                },
                "rendimiento_por_sistema": sis_por_mpio.get(cod_m, {}),
                "serie_anual": series_por_mpio.get(cod_m, []),
                "brecha": brecha_obj,
                "priorizacion": prio_obj,
            }
        )

    return {
        "version_esquema": VERSION_ESQUEMA,
        "cultivo": cultivo,
        "nivel_evidencia_cultivo": nivel_ev_cultivo,
        "municipios": municipios_out,
    }


def construir_escenarios_json(
    df_escenarios: pd.DataFrame,
    df_totales_escenarios: pd.DataFrame,
) -> dict[str, Any]:
    totales: list[dict[str, Any]] = []
    for f in df_totales_escenarios.sort_values("cultivo").to_dict(orient="records"):
        totales.append(
            {
                "cultivo": str(f["cultivo"]),
                "municipios_elegibles": int(f["municipios_elegibles"]),
                "produccion_anual_media_t": _ent(f["produccion_anual_media_t"]),
                "s1_p10_t": _ent(f["s1_p10"]),
                "s1_p50_t": _ent(f["s1_p50"]),
                "s1_p90_t": _ent(f["s1_p90"]),
                "s1_p50_pct_prod": _pct(f["s1_p50_pct_prod"]) or 0.0,
                "s2_p10_t": _ent(f["s2_p10"]),
                "s2_p50_t": _ent(f["s2_p50"]),
                "s2_p90_t": _ent(f["s2_p90"]),
                "s2_p50_pct_prod": _pct(f["s2_p50_pct_prod"]) or 0.0,
                "s2_pct_extrapolado": _pct(f.get("s2_pct_extrapolado", 0.0)) or 0.0,
                "s3_p10_t": _ent(f["s3_p10"]),
                "s3_p50_t": _ent(f["s3_p50"]),
                "s3_p90_t": _ent(f["s3_p90"]),
                "s3_p50_pct_prod": _pct(f["s3_p50_pct_prod"]) or 0.0,
                "combinado_p10_t": _ent(f["combinado_p10"]),
                "combinado_p50_t": _ent(f["combinado_p50"]),
                "combinado_p90_t": _ent(f["combinado_p90"]),
                "combinado_p50_pct_prod": _pct(f["combinado_p50_pct_prod"]) or 0.0,
            }
        )

    mpios: list[dict[str, Any]] = []
    df_ord = df_escenarios.sort_values(["cultivo", "codigo_dane_municipio"])
    for f in df_ord.to_dict(orient="records"):
        mpios.append(
            {
                "codigo": str(f["codigo_dane_municipio"]),
                "nombre": str(f["municipio"]),
                "codigo_departamento": str(f["codigo_dane_departamento"]),
                "departamento": str(f["departamento"]),
                "cultivo": str(f["cultivo"]),
                "area_cosechada_media_anual_ha": _ent(f["area_cosechada_media_anual"]),
                "produccion_media_anual_t": _ent(f["produccion_media_anual"]),
                "rendimiento_tha": _rend(f["rendimiento_periodo"]) or 0.0,
                "s1_p10_t": _ent(f["s1_p10"]),
                "s1_p50_t": _ent(f["s1_p50"]),
                "s1_p90_t": _ent(f["s1_p90"]),
                "s2_area_convertible_ha": _ent(f["s2_area_convertible_ha"]),
                "s2_p10_t": _ent(f["s2_p10"]),
                "s2_p50_t": _ent(f["s2_p50"]),
                "s2_p90_t": _ent(f["s2_p90"]),
                "extrapolado": bool(f.get("extrapolado", f.get("efecto_regional", False))),
                "s3_p10_t": _ent(f["s3_p10"]),
                "s3_p50_t": _ent(f["s3_p50"]),
                "s3_p90_t": _ent(f["s3_p90"]),
                "indicativo": str(f["rotulo_s3"]) == "indicativo_quiebre_2022",
                "excluido_d4": bool(f["excluido_d4"]),
                "combinado_p10_t": _ent(f["combinado_p10"]),
                "combinado_p50_t": _ent(f["combinado_p50"]),
                "combinado_p90_t": _ent(f["combinado_p90"]),
            }
        )

    return {
        "version_esquema": VERSION_ESQUEMA,
        "totales_regionales": totales,
        "municipios": mpios,
    }


def construir_sistemas_json(
    periodo_mpio_cultivo: pd.DataFrame,
    periodo_mpio_sistema: pd.DataFrame,
) -> dict[str, Any]:
    depto_agrup = (
        periodo_mpio_sistema.groupby(
            ["codigo_dane_departamento", "departamento", "cultivo", "sistema"],
            as_index=False,
        )
        .agg(
            area_cosechada=("area_cosechada", "sum"),
            produccion=("produccion", "sum"),
            municipios_con_dato=("codigo_dane_municipio", "nunique"),
        )
        .sort_values(["codigo_dane_departamento", "cultivo", "sistema"])
    )
    depto_agrup["rendimiento"] = np.where(
        depto_agrup["area_cosechada"] > 0,
        depto_agrup["produccion"] / depto_agrup["area_cosechada"],
        np.nan,
    )

    deptos_map: dict[tuple[str, str, str], dict[str, Any]] = {}
    for f in depto_agrup.to_dict(orient="records"):
        llave = (
            str(f["codigo_dane_departamento"]),
            str(f["departamento"]),
            str(f["cultivo"]),
        )
        if llave not in deptos_map:
            deptos_map[llave] = {
                "codigo_departamento": llave[0],
                "departamento": llave[1],
                "cultivo": llave[2],
                "sistemas": {},
            }
        deptos_map[llave]["sistemas"][str(f["sistema"])] = {
            "area_cosechada_ha": _ent(f["area_cosechada"]),
            "produccion_t": _ent(f["produccion"]),
            "rendimiento_tha": _rend(f["rendimiento"]),
            "municipios_con_dato": int(f["municipios_con_dato"]),
        }

    eleg_map = {
        (str(f["codigo_dane_municipio"]), str(f["cultivo"])): bool(f["elegible_500"])
        for f in periodo_mpio_cultivo.to_dict(orient="records")
    }

    mpios_map: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    for f in periodo_mpio_sistema.sort_values(
        ["cultivo", "codigo_dane_municipio", "sistema"]
    ).to_dict(orient="records"):
        cod_m = str(f["codigo_dane_municipio"])
        nom_m = str(f["municipio"])
        cod_d = str(f["codigo_dane_departamento"])
        nom_d = str(f["departamento"])
        cult = str(f["cultivo"])
        llave_m = (cod_m, nom_m, cod_d, nom_d, cult)
        if llave_m not in mpios_map:
            mpios_map[llave_m] = {
                "codigo": cod_m,
                "nombre": nom_m,
                "codigo_departamento": cod_d,
                "departamento": nom_d,
                "cultivo": cult,
                "elegible": eleg_map.get((cod_m, cult), False),
                "sistemas": {},
            }
        mpios_map[llave_m]["sistemas"][str(f["sistema"])] = {
            "area_cosechada_ha": _ent(f["area_cosechada"]),
            "produccion_t": _ent(f["produccion"]),
            "rendimiento_tha": _rend(f["rendimiento"]),
            "anios_con_dato": int(f["anios_con_dato"]),
        }

    return {
        "version_esquema": VERSION_ESQUEMA,
        "departamentos": list(deptos_map.values()),
        "municipios": list(mpios_map.values()),
    }


def construir_calidad_json(
    evidencia_cultivo: pd.DataFrame,
    evidencia_municipal: pd.DataFrame,
    anual_mpio_cultivo: pd.DataFrame,
) -> dict[str, Any]:
    por_cultivo: list[dict[str, Any]] = []
    for f in evidencia_cultivo.sort_values("cultivo").to_dict(orient="records"):
        por_cultivo.append(
            {
                "cultivo": str(f["cultivo"]),
                "series_evaluadas": int(f["series_evaluadas"]),
                "pares_consecutivos": int(f["pares_consecutivos"]),
                "pares_identicos": int(f["pares_identicos"]),
                "pct_pares_identicos": _pct(f["pct_pares_identicos"]) or 0.0,
                "series_poco_informativas": int(f["series_poco_informativas"]),
                "filas_semestrales": int(f["filas_semestrales"]),
                "filas_enteras_semestral": int(f["filas_enteras_semestral"]),
                "pct_rendimientos_enteros": _pct(f["pct_rendimientos_enteros"]) or 0.0,
                "pct_enteros_anual": _pct(f["pct_enteros_anual"]) or 0.0,
                "nivel_evidencia": str(f["nivel_evidencia"]),
            }
        )

    piv = evidencia_municipal.pivot_table(
        index="cultivo",
        columns="nivel_evidencia_municipal",
        values="codigo_dane_municipio",
        aggfunc="count",
        fill_value=0,
    )
    for c_col in ("alto", "medio", "bajo"):
        if c_col not in piv.columns:
            piv[c_col] = 0

    resumen_mpio: list[dict[str, Any]] = []
    for cult in sorted(piv.index):
        a = int(piv.loc[cult, "alto"])
        m = int(piv.loc[cult, "medio"])
        b = int(piv.loc[cult, "bajo"])
        resumen_mpio.append(
            {
                "cultivo": str(cult),
                "alto": a,
                "medio": m,
                "bajo": b,
                "total_con_datos": a + m + b,
            }
        )

    df_a21, res_a21 = calcular_concentracion_arroz_2021(anual_mpio_cultivo)
    top10: list[dict[str, Any]] = []
    for f in df_a21.head(10).to_dict(orient="records"):
        top10.append(
            {
                "rango": int(f["rango"]),
                "codigo": str(f["codigo_dane_municipio"]),
                "nombre": str(f["municipio"]),
                "departamento": str(f["departamento"]),
                "area_sembrada_ha": _ent(f["area_sembrada"]),
                "area_cosechada_ha": _ent(f["area_cosechada"]),
                "area_no_cosechada_ha": _ent(f["area_no_cosechada_ha"]),
                "tasa_propia_pct": _pct(f["tasa_propia_pct"]) or 0.0,
                "pct_total_regional": _pct(f["pct_total_regional"]) or 0.0,
            }
        )

    return {
        "version_esquema": VERSION_ESQUEMA,
        "por_cultivo": por_cultivo,
        "resumen_evidencia_municipal": resumen_mpio,
        "arroz_2021_concentracion": {
            "area_sembrada_regional_ha": _ent(res_a21["area_sembrada_regional_2021_ha"]),
            "area_cosechada_regional_ha": _ent(res_a21["area_cosechada_regional_2021_ha"]),
            "area_no_cosechada_regional_ha": _ent(res_a21["area_no_cosechada_regional_2021_ha"]),
            "tasa_regional_pct": _pct(res_a21["tasa_regional_2021_pct"]) or 0.0,
            "top5_area_no_cosechada_ha": _ent(res_a21["top5_area_no_cosechada_ha"]),
            "top5_pct_regional": _pct(res_a21["top5_pct_regional"]) or 0.0,
            "top10_area_no_cosechada_ha": _ent(res_a21["top10_area_no_cosechada_ha"]),
            "top10_pct_regional": _pct(res_a21["top10_pct_regional"]) or 0.0,
            "top10_municipios": top10,
        },
    }


def construir_hallazgos_json(
    resumen_hipotesis: pd.DataFrame,
    sensibilidad_d7: pd.DataFrame,
    robustez: pd.DataFrame,
    evidencia_cultivo: pd.DataFrame,
    arroz_2021: pd.DataFrame,
    escenarios_regionales: pd.DataFrame,
    prioridad: pd.DataFrame,
    escenarios_totales_agregados: pd.DataFrame,
    resumen_sistemas_maiz: pd.DataFrame,
) -> dict[str, Any]:
    mapa_hip = {str(f["id_hipotesis"]): f for f in resumen_hipotesis.to_dict(orient="records")}
    mapa_d7 = {str(f["id_hipotesis"]): f for f in sensibilidad_d7.to_dict(orient="records")}
    mapa_rob = {
        str(f["id_hipotesis"]): str(f["clasificacion_robustez"])
        for f in robustez.to_dict(orient="records")
    }
    mapa_ev = {
        str(f["cultivo"]): str(f["nivel_evidencia"])
        for f in evidencia_cultivo.to_dict(orient="records")
    }
    mapa_ev_fila = {str(f["cultivo"]): f for f in evidencia_cultivo.to_dict(orient="records")}
    mapa_esc = {str(f["cultivo"]): f for f in escenarios_regionales.to_dict(orient="records")}

    tarjetas: list[dict[str, Any]] = []

    def _agregar_hip_razon(
        id_tarjeta: str,
        id_hip: str,
        funcion: str,
        texto_decisor: str,
        texto_tecnico: str,
    ) -> None:
        f = mapa_hip[id_hip]
        cult = str(f["cultivo"])
        cifra = _rend(f["efecto"]) or 0.0
        ic = [_rend(f["ic_95_inf"]) or 0.0, _rend(f["ic_95_sup"]) or 0.0]
        tarjetas.append(
            {
                "id": id_tarjeta,
                "cultivo": cult,
                "texto_decisor": texto_decisor,
                "texto_tecnico": texto_tecnico,
                "cifra": cifra,
                "unidad": "razon_hl",
                "intervalo": ic,
                "n": int(f["n"]),
                "prueba": "Wilcoxon pareado por municipio (Holm, D1)",
                "p_ajustado": _dec(f["valor_p_ajustado"], 4),
                "robustez": mapa_rob.get(id_hip, "firme"),
                "nivel_evidencia": mapa_ev.get(cult, "alto"),
                "origen": {
                    "parquet": "resultados/resumen_hipotesis.parquet",
                    "funcion": funcion,
                    "columna_cifra": "efecto",
                    "filtro": f"id_hipotesis={id_hip}",
                },
            }
        )

    f_h2 = mapa_hip["H2_Maiz_tec_vs_trad"]
    _agregar_hip_razon(
        id_tarjeta="h2_maiz_tecnificado",
        id_hip="H2_Maiz_tec_vs_trad",
        funcion="rindex.inferencia.evaluar_h2_maiz",
        texto_decisor=(
            f"El maiz tecnificado rinde {_rend(f_h2['efecto']):.2f} veces lo que el "
            f"tradicional en los mismos municipios y anios ({int(f_h2['n'])} municipios)."
        ),
        texto_tecnico=(
            "Estimador de Hodges-Lehmann sobre diferencias logaritmicas medias por municipio "
            "(D1) con bootstrap de 5.000 replicas remuestreando municipios completos."
        ),
    )

    f_h3_rm = mapa_hip["H3_Arroz_riego_vs_man"]
    _agregar_hip_razon(
        id_tarjeta="h3_arroz_riego_vs_manual",
        id_hip="H3_Arroz_riego_vs_man",
        funcion="rindex.inferencia.evaluar_h3_arroz",
        texto_decisor=(
            f"El arroz bajo riego duplica el rendimiento del secano manual "
            f"(razon {_rend(f_h3_rm['efecto']):.2f}x en {int(f_h3_rm['n'])} municipios con par)."
        ),
        texto_tecnico=(
            "Comparacion pareada de Wilcoxon a nivel municipal (D1, D2) corregida por "
            "multiplicidad con Holm dentro de la familia H3."
        ),
    )

    f_h3_mm = mapa_hip["H3_Arroz_mec_vs_man"]
    _agregar_hip_razon(
        id_tarjeta="h3_arroz_mecanizado_vs_manual",
        id_hip="H3_Arroz_mec_vs_man",
        funcion="rindex.inferencia.evaluar_h3_arroz",
        texto_decisor=(
            f"El arroz secano mecanizado supera en {_rend(f_h3_mm['efecto']):.2f} veces "
            f"el rendimiento del secano manual ({int(f_h3_mm['n'])} municipios con par)."
        ),
        texto_tecnico=(
            "Hallazgo firme utilizado para parametrizar el escenario S2 de tecnificacion "
            "en arroz desde secano manual hacia secano mecanizado."
        ),
    )

    f_h3_ins = mapa_hip["H3_Arroz_riego_vs_mec"]
    _agregar_hip_razon(
        id_tarjeta="h3_arroz_riego_vs_mecanizado",
        id_hip="H3_Arroz_riego_vs_mec",
        funcion="rindex.inferencia.evaluar_h3_arroz",
        texto_decisor=(
            f"La comparacion directa entre arroz riego y secano mecanizado tiene muestra "
            f"insuficiente ({int(f_h3_ins['n'])} municipios) y no se publica como hallazgo."
        ),
        texto_tecnico=(
            "Con n = 5 municipios (< 6, regla D6), el valor p bilateral exacto minimo de "
            "Wilcoxon es 0,0625 > 0,05; clasificado como insuficiente y excluido de S2."
        ),
    )

    for cult, suf in [("Arroz", "arroz"), ("Maíz", "maiz"), ("Yuca", "yuca")]:
        id_h4 = f"H4_{cult}"
        f4 = mapa_hip[id_h4]
        es_sig = float(f4["valor_p_ajustado"]) < 0.05
        txt_d = (
            f"El rendimiento municipal de {cult.lower()} difiere significativamente entre "
            f"departamentos (epsilon cuadrado = {_dec(f4['efecto'], 4):.4f})."
            if es_sig
            else (
                f"El rendimiento municipal de {cult.lower()} no muestra diferencias "
                f"estadisticamente significativas entre departamentos."
            )
        )
        tarjetas.append(
            {
                "id": f"h4_{suf}",
                "cultivo": cult,
                "texto_decisor": txt_d,
                "texto_tecnico": (
                    f"Prueba de Kruskal-Wallis (H = {_rend(f4['estadistico']):.2f}) entre "
                    f"{int(f4['n_secundario'])} departamentos con correccion de Holm."
                ),
                "cifra": _dec(f4["efecto"], 4) or 0.0,
                "unidad": "epsilon_cuadrado",
                "intervalo": [
                    _dec(f4["ic_95_inf"], 4) or 0.0,
                    _dec(f4["ic_95_sup"], 4) or 0.0,
                ],
                "n": int(f4["n"]),
                "prueba": "Kruskal-Wallis interdepartamental (Holm)",
                "p_ajustado": _dec(f4["valor_p_ajustado"], 4),
                "robustez": mapa_rob.get(id_h4, "firme"),
                "nivel_evidencia": mapa_ev.get(cult, "alto"),
                "origen": {
                    "parquet": "resultados/resumen_hipotesis.parquet",
                    "funcion": "rindex.inferencia.evaluar_h4_departamentos",
                    "columna_cifra": "efecto",
                    "filtro": f"id_hipotesis={id_h4}",
                },
            }
        )

    # H1 por cultivo
    f_h1_arroz = mapa_hip["H1_Arroz"]
    tarjetas.append(
        {
            "id": "h1_arroz",
            "cultivo": "Arroz",
            "texto_decisor": (
                "En arroz no hay evidencia de tendencia regional 2019-2025, con equivalencia "
                "practica dentro de +/- 1 % anual."
            ),
            "texto_tecnico": (
                "Pendientes municipales de Theil-Sen evaluadas con Wilcoxon (Holm); la "
                "sensibilidad D7 mantiene la conclusion sin evidencia de tendencia."
            ),
            "cifra": _pct(f_h1_arroz["efecto_secundario"]) or 0.0,
            "unidad": "pct_anual",
            "intervalo": [
                _pct(f_h1_arroz["ic_95_sec_inf"]) or 0.0,
                _pct(f_h1_arroz["ic_95_sec_sup"]) or 0.0,
            ],
            "n": int(f_h1_arroz["n"]),
            "prueba": "Theil-Sen + Wilcoxon con signo (Holm)",
            "p_ajustado": _dec(f_h1_arroz["valor_p_ajustado"], 4),
            "robustez": mapa_rob.get("H1_Arroz", "firme"),
            "nivel_evidencia": mapa_ev.get("Arroz", "alto"),
            "origen": {
                "parquet": "resultados/resumen_hipotesis.parquet",
                "funcion": "rindex.inferencia.evaluar_h1_tendencia",
                "columna_cifra": "efecto_secundario",
                "filtro": "id_hipotesis=H1_Arroz",
            },
        }
    )

    f_h1_maiz_d7 = mapa_d7["H1_Maíz"]
    tarjetas.append(
        {
            "id": "h1_maiz",
            "cultivo": "Maíz",
            "texto_decisor": (
                "En maiz se observa tendencia negativa estadisticamente significativa solo al "
                "excluir series poco informativas, de magnitud practicamente despreciable "
                f"({_rend(f_h1_maiz_d7['efecto_secundario']):.2f} % anual)."
            ),
            "texto_tecnico": (
                "En el escenario base (n = 180) p ajustado = 0,0549; en la sensibilidad "
                "post-hoc D7 (n = 167) p ajustado = 0,0422 con pendiente mediana de "
                "-0,0016 t/ha/anio (-0,17 % anual)."
            ),
            "cifra": _rend(f_h1_maiz_d7["efecto_secundario"]) or 0.0,
            "unidad": "pct_anual",
            "intervalo": [
                _rend(f_h1_maiz_d7["ic_95_sec_inf"]) or 0.0,
                _rend(f_h1_maiz_d7["ic_95_sec_sup"]) or 0.0,
            ],
            "n": int(f_h1_maiz_d7["n"]),
            "prueba": "Theil-Sen + Wilcoxon con signo (sensibilidad D7, Holm)",
            "p_ajustado": _dec(f_h1_maiz_d7["valor_p_ajustado"], 4),
            "robustez": mapa_rob.get("H1_Maíz", "fragil"),
            "nivel_evidencia": mapa_ev.get("Maíz", "alto"),
            "origen": {
                "parquet": "resultados/sensibilidad_d7.parquet",
                "funcion": "rindex.inferencia.evaluar_h1_tendencia",
                "columna_cifra": "efecto_secundario",
                "filtro": "id_hipotesis=H1_Maíz",
            },
        }
    )

    f_h1_yuca = mapa_hip["H1_Yuca"]
    tarjetas.append(
        {
            "id": "h1_yuca",
            "cultivo": "Yuca",
            "texto_decisor": (
                "En yuca la tendencia interanual no es medible por la repeticion de valores "
                "administrativos entre anios consecutivos."
            ),
            "texto_tecnico": (
                "El 29,65 % de las pendientes municipales de Theil-Sen son exactamente cero "
                "y el 45,75 % de los pares de anios consecutivos repiten el mismo rendimiento."
            ),
            "cifra": _pct(f_h1_yuca["efecto_secundario"]) or 0.0,
            "unidad": "pct_anual",
            "intervalo": [
                _pct(f_h1_yuca["ic_95_sec_inf"]) or 0.0,
                _pct(f_h1_yuca["ic_95_sec_sup"]) or 0.0,
            ],
            "n": int(f_h1_yuca["n"]),
            "prueba": "Theil-Sen + Wilcoxon con signo (D7)",
            "p_ajustado": _dec(f_h1_yuca["valor_p_ajustado"], 4),
            "robustez": mapa_rob.get("H1_Yuca", "firme"),
            "nivel_evidencia": mapa_ev.get("Yuca", "bajo"),
            "origen": {
                "parquet": "resultados/resumen_hipotesis.parquet",
                "funcion": "rindex.inferencia.evaluar_h1_tendencia",
                "columna_cifra": "efecto_secundario",
                "filtro": "id_hipotesis=H1_Yuca",
            },
        }
    )

    # Calidad de yuca
    ev_yuca = mapa_ev_fila["Yuca"]
    tarjetas.append(
        {
            "id": "calidad_yuca",
            "cultivo": "Yuca",
            "texto_decisor": (
                f"La yuca se clasifica con nivel de evidencia bajo porque el "
                f"{_pct(ev_yuca['pct_pares_identicos']):.1f} % de sus pares de anios "
                f"consecutivos repiten exactamente el mismo rendimiento."
            ),
            "texto_tecnico": (
                f"De {int(ev_yuca['pares_consecutivos'])} pares consecutivos, "
                f"{int(ev_yuca['pares_identicos'])} son identicos y el "
                f"{_pct(ev_yuca['pct_rendimientos_enteros']):.1f} % de las filas semestrales "
                "registran rendimientos enteros exactos (D9)."
            ),
            "cifra": _pct(ev_yuca["pct_pares_identicos"]) or 0.0,
            "unidad": "porcentaje",
            "intervalo": None,
            "n": int(ev_yuca["series_evaluadas"]),
            "prueba": "Diagnostico de repeticion y redondeo (D9)",
            "p_ajustado": None,
            "robustez": "firme",
            "nivel_evidencia": "bajo",
            "origen": {
                "parquet": "resultados/evidencia_cultivo.parquet",
                "funcion": "rindex.evidencia.calcular_evidencia_por_cultivo",
                "columna_cifra": "pct_pares_identicos",
                "filtro": "cultivo=Yuca",
            },
        }
    )

    # Arroz 2021 concentrado
    fila_top5 = arroz_2021.loc[arroz_2021["rango"] == 5].iloc[0]
    fila_top1 = arroz_2021.loc[arroz_2021["rango"] == 1].iloc[0]
    fila_top10 = arroz_2021.loc[arroz_2021["rango"] == 10].iloc[0]
    tarjetas.append(
        {
            "id": "arroz_2021_concentrado",
            "cultivo": "Arroz",
            "texto_decisor": (
                f"En 2021, solo 5 municipios de La Mojana y la depresion momposina concentraron "
                f"el {_pct(fila_top5['pct_acumulado_regional']):.1f} % del area de arroz no "
                "cosechada del Caribe."
            ),
            "texto_tecnico": (
                f"Majagual, Ayapel, Achi, Guaranda y San Marcos sumaron 27.725 ha de las "
                f"36.766 ha regionales no cosechadas (los 10 primeros concentraron el "
                f"{_pct(fila_top10['pct_acumulado_regional']):.1f} %, descriptivo segun D8)."
            ),
            "cifra": _pct(fila_top5["pct_acumulado_regional"]) or 0.0,
            "unidad": "porcentaje",
            "intervalo": [
                _pct(fila_top1["pct_acumulado_regional"]) or 0.0,
                _pct(fila_top10["pct_acumulado_regional"]) or 0.0,
            ],
            "n": 5,
            "prueba": "Analisis descriptivo de concentracion geografica (D8)",
            "p_ajustado": None,
            "robustez": "firme",
            "nivel_evidencia": mapa_ev.get("Arroz", "alto"),
            "origen": {
                "parquet": "resultados/arroz_2021_concentracion.parquet",
                "funcion": "rindex.evidencia.calcular_concentracion_arroz_2021",
                "columna_cifra": "pct_acumulado_regional",
                "filtro": "rango=5",
            },
        }
    )

    # Escenario combinado por cultivo y S1 maiz
    for cult, suf in [("Arroz", "arroz"), ("Maíz", "maiz"), ("Yuca", "yuca")]:
        f_e = mapa_esc[cult]
        tarjetas.append(
            {
                "id": f"combinado_{suf}",
                "cultivo": cult,
                "texto_decisor": (
                    f"El escenario combinado sin doble conteo en {cult.lower()} aporta una "
                    f"ganancia potencial mediana de {_ent(f_e['combinado_p50']):,} t/anio "
                    f"({_pct(f_e['combinado_p50_pct_prod']):.1f} % de la produccion actual)."
                ).replace(",", "."),
                "texto_tecnico": (
                    "Combinacion max(S1, S2) + S3 evaluada por bootstrap de dos niveles "
                    "(5.000 replicas) en municipios elegibles (>= 500 ha y >= 4 anios)."
                ),
                "cifra": float(_ent(f_e["combinado_p50"])),
                "unidad": "toneladas",
                "intervalo": [
                    float(_ent(f_e["combinado_p10"])),
                    float(_ent(f_e["combinado_p90"])),
                ],
                "n": int(f_e["municipios_elegibles"]),
                "prueba": "Simulacion bootstrap de escenarios S1, S2 y S3",
                "p_ajustado": None,
                "robustez": "firme",
                "nivel_evidencia": mapa_ev.get(cult, "alto"),
                "origen": {
                    "parquet": "resultados/escenarios_regionales.parquet",
                    "funcion": "rindex.escenarios.construir_escenarios_municipales",
                    "columna_cifra": "combinado_p50",
                    "filtro": f"cultivo={cult}",
                },
            }
        )

    f_e_maiz = mapa_esc["Maíz"]
    tarjetas.append(
        {
            "id": "s1_maiz",
            "cultivo": "Maíz",
            "texto_decisor": (
                f"Cerrar la brecha intradepartamental de rendimiento al percentil 75 (S1) en "
                f"maiz generaria {_ent(f_e_maiz['s1_p50']):,} t/anio adicionales "
                f"({_pct(f_e_maiz['s1_p50_pct_prod']):.1f} % de la produccion regional)."
            ).replace(",", "."),
            "texto_tecnico": (
                "Brecha potencial respecto al P75 departamental por sistema productivo con "
                "bootstrap de dos niveles (5.000 replicas)."
            ),
            "cifra": float(_ent(f_e_maiz["s1_p50"])),
            "unidad": "toneladas",
            "intervalo": [
                float(_ent(f_e_maiz["s1_p10"])),
                float(_ent(f_e_maiz["s1_p90"])),
            ],
            "n": int(f_e_maiz["municipios_elegibles"]),
            "prueba": "Simulacion bootstrap de dos niveles S1",
            "p_ajustado": None,
            "robustez": "firme",
            "nivel_evidencia": mapa_ev.get("Maíz", "alto"),
            "origen": {
                "parquet": "resultados/escenarios_regionales.parquet",
                "funcion": "rindex.escenarios.construir_escenarios_municipales",
                "columna_cifra": "s1_p50",
                "filtro": "cultivo=Maíz",
            },
        }
    )

    # Nucleo de prioridad robusta por cultivo
    for cult, suf in [("Arroz", "arroz"), ("Maíz", "maiz"), ("Yuca", "yuca")]:
        sub_p = prioridad.loc[prioridad["cultivo"] == cult]
        sub_rob = sub_p.loc[sub_p["prioridad_robusta"]].sort_values("rango_defecto")
        n_rob = int(len(sub_rob))
        nombres_rob = ", ".join(str(m) for m in sub_rob["municipio"].tolist())
        tarjetas.append(
            {
                "id": f"nucleo_robusto_{suf}",
                "cultivo": cult,
                "texto_decisor": (
                    f"En {cult.lower()}, {n_rob} municipios conforman el nucleo de prioridad "
                    f"robusta al mantenerse en el Top 20 bajo al menos el 80 % de las "
                    f"ponderaciones: {nombres_rob}."
                ),
                "texto_tecnico": (
                    "Analisis de sensibilidad del indice de prioridad (0-100) con 2.000 "
                    "vectores de pesos muestreados de una distribucion Dirichlet(1, 1, 1, 1)."
                ),
                "cifra": float(n_rob),
                "unidad": "municipios",
                "intervalo": None,
                "n": int(len(sub_p)),
                "prueba": "Sensibilidad Dirichlet (2.000 juegos de pesos)",
                "p_ajustado": None,
                "robustez": "firme",
                "nivel_evidencia": mapa_ev.get(cult, "alto"),
                "origen": {
                    "parquet": "resultados/prioridad.parquet",
                    "funcion": "rindex.prioridad.calcular_indice_prioridad",
                    "columna_cifra": "prioridad_robusta",
                    "filtro": f"cultivo={cult}",
                },
            }
        )

    # Totales regionales agregados por suma replica a replica (D10)
    mapa_agreg = {
        str(f["grupo"]): f for f in escenarios_totales_agregados.to_dict(orient="records")
    }
    f_tot = mapa_agreg["region_total"]
    tarjetas.append(
        {
            "id": "combinado_region_total",
            "cultivo": "Todos",
            "texto_decisor": (
                f"Sin sembrar una hectárea más, el Caribe podría cosechar entre "
                f"{_ent(f_tot['combinado_p10']):,} y {_ent(f_tot['combinado_p90']):,} "
                f"toneladas más al año sumando arroz, maíz y yuca."
            ).replace(",", "."),
            "texto_tecnico": (
                "Percentiles p10, p50 y p90 calculados sobre la suma réplica a réplica "
                "(5.000 réplicas bootstrap con índice común) de los tres cultivos."
            ),
            "cifra": float(_ent(f_tot["combinado_p50"])),
            "unidad": "toneladas",
            "intervalo": [
                float(_ent(f_tot["combinado_p10"])),
                float(_ent(f_tot["combinado_p90"])),
            ],
            "n": int(f_tot["municipios_elegibles"]),
            "prueba": "Suma réplica a réplica de bootstrap de dos niveles",
            "p_ajustado": None,
            "robustez": "firme",
            "nivel_evidencia": "medio",
            "origen": {
                "parquet": "resultados/escenarios_totales_agregados.parquet",
                "funcion": "rindex.escenarios.construir_escenarios_con_replicas",
                "columna_cifra": "combinado_p50",
                "filtro": "grupo=region_total",
            },
        }
    )

    f_ev_alta = mapa_agreg["evidencia_alta"]
    tarjetas.append(
        {
            "id": "combinado_region_evidencia_alta",
            "cultivo": "Arroz y Maíz",
            "texto_decisor": (
                f"Solo en los cultivos con evidencia alta (arroz y maíz), el potencial anual "
                f"se ubica entre {_ent(f_ev_alta['combinado_p10']):,} y "
                f"{_ent(f_ev_alta['combinado_p90']):,} toneladas."
            ).replace(",", "."),
            "texto_tecnico": (
                "Percentiles p10, p50 y p90 calculados sobre la suma réplica a réplica "
                "(5.000 réplicas bootstrap con índice común) excluyendo yuca."
            ),
            "cifra": float(_ent(f_ev_alta["combinado_p50"])),
            "unidad": "toneladas",
            "intervalo": [
                float(_ent(f_ev_alta["combinado_p10"])),
                float(_ent(f_ev_alta["combinado_p90"])),
            ],
            "n": int(f_ev_alta["municipios_elegibles"]),
            "prueba": "Suma réplica a réplica de bootstrap de dos niveles",
            "p_ajustado": None,
            "robustez": "firme",
            "nivel_evidencia": "alto",
            "origen": {
                "parquet": "resultados/escenarios_totales_agregados.parquet",
                "funcion": "rindex.escenarios.construir_escenarios_con_replicas",
                "columna_cifra": "combinado_p50",
                "filtro": "grupo=evidencia_alta",
            },
        }
    )

    f_maiz_trad = resumen_sistemas_maiz.loc[resumen_sistemas_maiz["sistema"] == "tradicional"].iloc[
        0
    ]
    pct_trad = _pct(f_maiz_trad["pct_area_cosechada"]) or 0.0
    tarjetas.append(
        {
            "id": "pct_area_maiz_tradicional",
            "cultivo": "Maíz",
            "texto_decisor": (
                f"El {pct_trad:.1f} % del área cosechada de maíz en el Caribe corresponde "
                "al sistema tradicional."
            ).replace(".", ","),
            "texto_tecnico": (
                "Proporción de área cosechada acumulada 2019-2025 en maíz tradicional "
                "sobre el total de área cosechada de maíz en los siete departamentos."
            ),
            "cifra": pct_trad,
            "unidad": "porcentaje",
            "intervalo": None,
            "n": int(f_maiz_trad["municipios_con_dato"]),
            "prueba": "Descriptivo ponderado por área cosechada acumulada",
            "p_ajustado": None,
            "robustez": "firme",
            "nivel_evidencia": mapa_ev.get("Maíz", "alto"),
            "origen": {
                "parquet": "resultados/resumen_sistemas_maiz.parquet",
                "funcion": "rindex.priorizacion.calcular_resumen_sistemas_maiz",
                "columna_cifra": "pct_area_cosechada",
                "filtro": "sistema=tradicional",
            },
        }
    )

    return {"version_esquema": VERSION_ESQUEMA, "tarjetas": tarjetas}


def _serializar_json_determinista(objeto: dict[str, Any]) -> bytes:
    texto = json.dumps(
        objeto,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return (texto + "\n").encode("utf-8")


def _redondear_segun_unidad(valor: float, unidad: str) -> float:
    if unidad in {"toneladas", "municipios"}:
        return float(int(round(valor)))
    if unidad == "epsilon_cuadrado":
        return round(float(valor), 4)
    if unidad == "razon_hl":
        return round(float(valor), 2)
    if unidad == "porcentaje":
        return round(float(valor), 1)
    return round(float(valor), 2)


def validar_archivos_exportados(
    archivos_generados: dict[str, dict[str, Any]],
    bytes_primera_corrida: dict[str, bytes],
    bytes_segunda_corrida: dict[str, bytes],
    dir_interim: Path,
    ruta_topojson: Path,
    dir_esquemas: Path = Path("contratos/web"),
) -> dict[str, Any]:
    # 1. Validacion contra JSON Schema y limite de 2 MB
    for nombre_arch, contenido in archivos_generados.items():
        tamano = len(bytes_primera_corrida[nombre_arch])
        if tamano >= MAX_BYTES_ARCHIVO_WEB:
            raise ValueError(
                f"El archivo '{nombre_arch}' pesa {tamano} bytes y supera el limite de 2 MB."
            )
        ruta_schema = dir_esquemas / ARCHIVOS_ESQUEMA[nombre_arch]
        if not ruta_schema.exists():
            raise FileNotFoundError(f"Falta el contrato JSON Schema: '{ruta_schema}'.")
        esquema = json.loads(ruta_schema.read_text(encoding="utf-8"))
        jsonschema.validate(instance=contenido, schema=esquema)

    # 2. Totales de regional.json coinciden con anual_region_cultivo.parquet
    df_reg = pd.read_parquet(dir_interim / "anual_region_cultivo.parquet")
    mapa_reg = {(str(f["cultivo"]), int(f["anio"])): f for f in df_reg.to_dict(orient="records")}
    for reg_json in archivos_generados["regional.json"]["registros"]:
        llave = (str(reg_json["cultivo"]), int(reg_json["anio"]))
        fila_pq = mapa_reg[llave]
        if abs(reg_json["area_sembrada_ha"] - float(fila_pq["area_sembrada"])) > 0.5 + 1e-6:
            raise ValueError(f"Desajuste de area_sembrada en regional.json para {llave}.")
        if abs(reg_json["area_cosechada_ha"] - float(fila_pq["area_cosechada"])) > 0.5 + 1e-6:
            raise ValueError(f"Desajuste de area_cosechada en regional.json para {llave}.")
        if abs(reg_json["produccion_t"] - float(fila_pq["produccion"])) > 0.5 + 1e-6:
            raise ValueError(f"Desajuste de produccion en regional.json para {llave}.")
        if abs(reg_json["rendimiento_tha"] - float(fila_pq["rendimiento"])) > 0.005 + 1e-6:
            raise ValueError(f"Desajuste de rendimiento en regional.json para {llave}.")

    # 3. Empate exacto de codigos municipales con caribe.topojson
    topo = json.loads(ruta_topojson.read_text(encoding="utf-8"))
    cods_topo = {
        str(g["properties"]["codigo"]) for g in topo["objects"]["municipios"]["geometries"]
    }
    for arch_m in (
        "municipios_maiz.json",
        "municipios_arroz.json",
        "municipios_yuca.json",
    ):
        cods_json = {str(m["codigo"]) for m in archivos_generados[arch_m]["municipios"]}
        if cods_json != cods_topo:
            raise ValueError(
                f"Desempate de codigos municipales entre '{arch_m}' y caribe.topojson."
            )

    for arch_sub in ("escenarios.json", "sistemas.json"):
        cods_sub = {str(m["codigo"]) for m in archivos_generados[arch_sub]["municipios"]}
        if not cods_sub.issubset(cods_topo):
            raise ValueError(f"Codigos municipales en '{arch_sub}' no existen en caribe.topojson.")

    # 4. Cada cifra de hallazgos.json coincide con su parquet de origen
    for tar in archivos_generados["hallazgos.json"]["tarjetas"]:
        orig = tar["origen"]
        df_orig = pd.read_parquet(dir_interim / orig["parquet"])
        col_f, val_f = str(orig["filtro"]).split("=", maxsplit=1)
        if df_orig[col_f].dtype.kind in {"i", "u"}:
            sub = df_orig.loc[df_orig[col_f] == int(val_f)]
        else:
            sub = df_orig.loc[df_orig[col_f].astype(str) == val_f]
        if sub.empty:
            raise ValueError(f"No se encontro origen para tarjeta '{tar['id']}'.")

        col_cifra = str(orig["columna_cifra"])
        if col_cifra == "prioridad_robusta":
            valor_pq = float(sub[col_cifra].astype(bool).sum())
        else:
            valor_pq = float(sub[col_cifra].iloc[0])

        if tar["id"] == "h1_maiz":
            esperado = round(valor_pq, 2)
        elif tar["unidad"] == "pct_anual":
            esperado = round(valor_pq, 1)
        else:
            esperado = _redondear_segun_unidad(valor_pq, str(tar["unidad"]))

        if abs(float(tar["cifra"]) - esperado) > 1e-9:
            raise ValueError(
                f"La cifra de la tarjeta '{tar['id']}' ({tar['cifra']}) no coincide "
                f"con su parquet de origen ({esperado})."
            )

    # 5. Dos corridas seguidas producen archivos identicos byte a byte
    for nombre_arch in archivos_generados:
        h1 = hashlib.sha256(bytes_primera_corrida[nombre_arch]).hexdigest()
        h2 = hashlib.sha256(bytes_segunda_corrida[nombre_arch]).hexdigest()
        if h1 != h2 or bytes_primera_corrida[nombre_arch] != bytes_segunda_corrida[nombre_arch]:
            raise ValueError(f"La exportacion de '{nombre_arch}' no es determinista byte a byte.")

    return {
        "archivos_validados": len(archivos_generados),
        "tamanos_bytes": {k: len(v) for k, v in bytes_primera_corrida.items()},
    }


def _generar_diccionario_archivos_web(
    cfg: ConfiguracionEdicion,
    dir_interim: Path,
    ruta_topojson: Path,
) -> dict[str, dict[str, Any]]:
    dir_res = dir_interim / "resultados"

    anual_region = pd.read_parquet(dir_interim / "anual_region_cultivo.parquet")
    anual_depto = pd.read_parquet(dir_interim / "anual_departamento_cultivo.parquet")
    anual_mpio_cultivo = pd.read_parquet(dir_interim / "anual_municipio_cultivo.parquet")
    periodo_mpio_cultivo = pd.read_parquet(dir_interim / "periodo_municipio_cultivo.parquet")
    periodo_mpio_sistema = pd.read_parquet(dir_interim / "periodo_municipio_sistema.parquet")
    df_oni = pd.read_parquet(cfg.clima.parquet_anual)

    resumen_hipotesis = pd.read_parquet(dir_res / "resumen_hipotesis.parquet")
    sensibilidad_d7 = pd.read_parquet(dir_res / "sensibilidad_d7.parquet")
    robustez = pd.read_parquet(dir_res / "robustez.parquet")
    evidencia_cultivo = pd.read_parquet(dir_res / "evidencia_cultivo.parquet")
    evidencia_municipal = pd.read_parquet(dir_res / "evidencia_municipal.parquet")
    arroz_2021 = pd.read_parquet(dir_res / "arroz_2021_concentracion.parquet")
    df_escenarios = pd.read_parquet(dir_res / "escenarios.parquet")
    df_totales_esc = pd.read_parquet(dir_res / "escenarios_regionales.parquet")
    df_totales_agreg = pd.read_parquet(dir_res / "escenarios_totales_agregados.parquet")
    df_resumen_maiz = pd.read_parquet(dir_res / "resumen_sistemas_maiz.parquet")
    df_prioridad = pd.read_parquet(dir_res / "prioridad.parquet")

    topo = json.loads(ruta_topojson.read_text(encoding="utf-8"))
    catalogo_mpios = sorted(
        [
            {
                "codigo": str(g["properties"]["codigo"]),
                "nombre": str(g["properties"]["nombre"]),
                "codigo_departamento": str(g["properties"]["departamento"]),
                "departamento": cfg.departamentos[str(g["properties"]["departamento"])],
            }
            for g in topo["objects"]["municipios"]["geometries"]
        ],
        key=lambda x: x["codigo"],
    )

    archivos: dict[str, dict[str, Any]] = {
        "meta.json": construir_meta_json(cfg),
        "regional.json": construir_regional_json(anual_region, df_oni),
        "departamental.json": construir_departamental_json(anual_depto, df_oni),
        "escenarios.json": construir_escenarios_json(df_escenarios, df_totales_esc),
        "sistemas.json": construir_sistemas_json(
            periodo_mpio_cultivo,
            periodo_mpio_sistema,
        ),
        "hallazgos.json": construir_hallazgos_json(
            resumen_hipotesis=resumen_hipotesis,
            sensibilidad_d7=sensibilidad_d7,
            robustez=robustez,
            evidencia_cultivo=evidencia_cultivo,
            arroz_2021=arroz_2021,
            escenarios_regionales=df_totales_esc,
            prioridad=df_prioridad,
            escenarios_totales_agregados=df_totales_agreg,
            resumen_sistemas_maiz=df_resumen_maiz,
        ),
        "calidad.json": construir_calidad_json(
            evidencia_cultivo=evidencia_cultivo,
            evidencia_municipal=evidencia_municipal,
            anual_mpio_cultivo=anual_mpio_cultivo,
        ),
    }

    for cult, nombre_arch in [
        ("Maíz", "municipios_maiz.json"),
        ("Arroz", "municipios_arroz.json"),
        ("Yuca", "municipios_yuca.json"),
    ]:
        archivos[nombre_arch] = construir_municipios_cultivo_json(
            cultivo=cult,
            catalogo_mpios=catalogo_mpios,
            periodo_mpio_cultivo=periodo_mpio_cultivo,
            periodo_mpio_sistema=periodo_mpio_sistema,
            anual_mpio_cultivo=anual_mpio_cultivo,
            evidencia_cultivo=evidencia_cultivo,
            evidencia_municipal=evidencia_municipal,
            df_escenarios=df_escenarios,
            df_prioridad=df_prioridad,
        )

    return archivos


def ejecutar_exportacion_web(
    ruta_config: str | Path,
    dir_salida: str | Path = "web/public/data",
    dir_esquemas: str | Path = "contratos/web",
) -> dict[str, Any]:
    cfg = cargar_configuracion(ruta_config)
    dir_interim = Path(cfg.fuente.parquet_filtrado).parent
    ruta_topojson = Path(cfg.geografia.topojson_salida)
    ruta_out = Path(dir_salida)
    ruta_out.mkdir(parents=True, exist_ok=True)

    archivos_1 = _generar_diccionario_archivos_web(cfg, dir_interim, ruta_topojson)
    bytes_1 = {k: _serializar_json_determinista(v) for k, v in archivos_1.items()}

    archivos_2 = _generar_diccionario_archivos_web(cfg, dir_interim, ruta_topojson)
    bytes_2 = {k: _serializar_json_determinista(v) for k, v in archivos_2.items()}

    resumen_val = validar_archivos_exportados(
        archivos_generados=archivos_1,
        bytes_primera_corrida=bytes_1,
        bytes_segunda_corrida=bytes_2,
        dir_interim=dir_interim,
        ruta_topojson=ruta_topojson,
        dir_esquemas=Path(dir_esquemas),
    )

    for nombre_arch, contenido_bytes in bytes_1.items():
        (ruta_out / nombre_arch).write_bytes(contenido_bytes)

    return resumen_val


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exporta y valida los archivos JSON estaticos de RINDEx para la web."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Ruta al archivo YAML de configuracion de la edicion.",
    )
    args = parser.parse_args()
    ejecutar_exportacion_web(args.config)


if __name__ == "__main__":
    main()
