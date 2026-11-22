"""Procesamiento y validacion topologica del Marco Geoestadistico Nacional (MGN) para el Caribe."""

import argparse
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests
import shapely
import topojson as tp
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon, mapping, shape
from shapely.validation import make_valid

from rindex.config import ConfiguracionEdicion, cargar_configuracion
from rindex.fuente import calcular_sha256

CONTEOS_ESPERADOS_CARIBE: dict[str, int] = {
    "08": 23,
    "13": 46,
    "20": 25,
    "23": 30,
    "44": 15,
    "47": 30,
    "70": 26,
}


def limpiar_geometria_poligonal(geom: Any) -> Polygon | MultiPolygon:
    if not geom.is_valid:
        geom = make_valid(geom)
    if isinstance(geom, (Polygon, MultiPolygon)):
        return geom
    if isinstance(geom, GeometryCollection):
        poligonos = [
            g for g in geom.geoms if isinstance(g, (Polygon, MultiPolygon)) and not g.is_empty
        ]
        if not poligonos:
            return Polygon()
        unido = shapely.unary_union(poligonos)
        return unido if isinstance(unido, (Polygon, MultiPolygon)) else Polygon()
    return Polygon()


def proyectar_area_equivalente(geom: Polygon | MultiPolygon) -> Polygon | MultiPolygon:
    # Proyeccion sinusoidal de area equivalente centrada en el meridiano del Caribe (-74,5°)
    radio_autalico_m = 6371007.181
    lon_central_rad = math.radians(-74.5)

    def _transformar(coords: np.ndarray) -> np.ndarray:
        pts = np.asarray(coords, dtype=float)
        lon_rad = np.radians(pts[:, 0]) - lon_central_rad
        lat_rad = np.radians(pts[:, 1])
        x = radio_autalico_m * lon_rad * np.cos(lat_rad)
        y = radio_autalico_m * lat_rad
        return np.column_stack([x, y])

    return shapely.transform(geom, _transformar)


def calcular_area_equivalente_km2(geom: Polygon | MultiPolygon) -> float:
    if geom.is_empty:
        return 0.0
    return float(proyectar_area_equivalente(geom).area / 1e6)


def _actualizar_manifiesto_geo(
    ruta_manifiesto: Path,
    meta_geo: dict[str, Any],
) -> None:
    ruta_manifiesto.parent.mkdir(parents=True, exist_ok=True)
    datos: dict[str, Any] = {}
    if ruta_manifiesto.exists():
        datos = json.loads(ruta_manifiesto.read_text(encoding="utf-8"))
    datos["geografia"] = meta_geo
    ruta_manifiesto.write_text(
        json.dumps(datos, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def obtener_geojson_mgn(cfg: ConfiguracionEdicion) -> dict[str, Any]:
    ruta_local = Path(cfg.geografia.archivo_local)
    ruta_local.parent.mkdir(parents=True, exist_ok=True)
    origen = "respaldo_local"

    if not ruta_local.exists():
        codigos_consulta = sorted(
            set(cfg.departamentos.keys()) | {d.codigo for d in cfg.departamentos_excluidos}
        )
        lista_sql = ",".join(f"'{c}'" for c in codigos_consulta)
        params = {
            "where": f"DPTO_CCDGO IN ({lista_sql})",
            "outFields": (
                "DPTO_CCDGO,MPIO_CCDGO,MPIO_CDPMP,MPIO_TIPO,"
                "MPIO_NAREA,MPIO_NANO,DPTO_CNMBRE,MPIO_CNMBRE"
            ),
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "geojson",
        }
        respuesta = requests.get(cfg.geografia.url_mgn, params=params, timeout=60)
        respuesta.raise_for_status()
        ruta_local.write_bytes(respuesta.content)
        origen = "descarga_url"

    hash_sha256 = calcular_sha256(ruta_local)
    contenido = json.loads(ruta_local.read_text(encoding="utf-8"))
    meta_geo = {
        "origen": origen,
        "url": cfg.geografia.url_mgn,
        "version_mgn": cfg.geografia.version_mgn,
        "licencia": cfg.geografia.licencia,
        "nombre_archivo": ruta_local.name,
        "fecha": datetime.now(UTC).isoformat(),
        "tamano": ruta_local.stat().st_size,
        "features": len(contenido.get("features", [])),
        "hash": hash_sha256,
    }
    _actualizar_manifiesto_geo(Path(cfg.fuente.manifiesto), meta_geo)
    return contenido


def _reconstruir_coordenadas_arco(
    arco_delta: list[list[int]],
    escala: list[float],
    traslacion: list[float],
) -> list[tuple[float, float]]:
    x_acum = 0
    y_acum = 0
    puntos: list[tuple[float, float]] = []
    for dx, dy in arco_delta:
        x_acum += int(dx)
        y_acum += int(dy)
        lon = x_acum * float(escala[0]) + float(traslacion[0])
        lat = y_acum * float(escala[1]) + float(traslacion[1])
        puntos.append((lon, lat))
    return puntos


def _reconstruir_anillo(
    indices_arcos: list[int],
    arcos_decodificados: list[list[tuple[float, float]]],
) -> list[tuple[float, float]]:
    coords: list[tuple[float, float]] = []
    for idx in indices_arcos:
        if idx >= 0:
            seg = arcos_decodificados[idx]
        else:
            seg = list(reversed(arcos_decodificados[-idx - 1]))
        if coords and seg:
            coords.extend(seg[1:])
        else:
            coords.extend(seg)
    if coords and coords[0] != coords[-1]:
        coords.append(coords[0])
    return coords


def reconstruir_geometria_topojson(
    obj_geom: dict[str, Any],
    arcos_decodificados: list[list[tuple[float, float]]],
) -> Polygon | MultiPolygon:
    tipo = obj_geom.get("type")
    arcos_geom = obj_geom.get("arcs", [])
    if tipo == "Polygon":
        anillos = [_reconstruir_anillo(anillo, arcos_decodificados) for anillo in arcos_geom]
        if not anillos or len(anillos[0]) < 4:
            return Polygon()
        return limpiar_geometria_poligonal(Polygon(anillos[0], anillos[1:]))
    if tipo == "MultiPolygon":
        poligonos: list[Polygon] = []
        for poly_arcs in arcos_geom:
            anillos = [_reconstruir_anillo(anillo, arcos_decodificados) for anillo in poly_arcs]
            if anillos and len(anillos[0]) >= 4:
                p = limpiar_geometria_poligonal(Polygon(anillos[0], anillos[1:]))
                if isinstance(p, Polygon) and not p.is_empty:
                    poligonos.append(p)
                elif isinstance(p, MultiPolygon):
                    poligonos.extend(list(p.geoms))
        return limpiar_geometria_poligonal(MultiPolygon(poligonos))
    return Polygon()


def construir_topojson_caribe(
    geojson_crudo: dict[str, Any],
    codigos_datos: dict[str, str],
    cfg: ConfiguracionEdicion,
) -> tuple[dict[str, Any], pd.DataFrame, dict[str, Any]]:
    deptos_cfg = set(cfg.departamentos.keys())
    excluidos_cfg = {d.codigo for d in cfg.departamentos_excluidos}

    features_mpio: list[dict[str, Any]] = []
    geoms_orig_por_mpio: dict[str, Polygon | MultiPolygon] = {}
    areas_orig_km2: dict[str, float] = {}
    geoms_orig_por_depto: dict[str, list[Polygon | MultiPolygon]] = {
        d: [] for d in sorted(deptos_cfg)
    }
    conteo_por_depto: dict[str, int] = {d: 0 for d in sorted(deptos_cfg)}

    for feat in geojson_crudo.get("features", []):
        props = feat.get("properties", {})
        cod_mpio = str(props.get("MPIO_CDPMP", "")).strip().zfill(5)
        cod_dep = str(props.get("DPTO_CCDGO", cod_mpio[:2])).strip().zfill(2)
        if cod_dep in excluidos_cfg or cod_dep not in deptos_cfg:
            continue

        geom = limpiar_geometria_poligonal(shape(feat["geometry"]))
        if geom.is_empty or not geom.is_valid:
            raise ValueError(f"Geometria original invalida o vacia para el municipio '{cod_mpio}'.")

        lon_min, lat_min, lon_max, lat_max = geom.bounds
        if lon_min < -90.0 or lon_max > -60.0 or lat_min < -5.0 or lat_max > 15.0:
            raise ValueError(
                f"Coordenadas fuera de EPSG:4326 en Colombia para '{cod_mpio}': {geom.bounds}."
            )

        nombre_limpio = codigos_datos.get(cod_mpio, str(props.get("MPIO_CNMBRE", cod_mpio)).title())
        geoms_orig_por_mpio[cod_mpio] = geom
        areas_orig_km2[cod_mpio] = calcular_area_equivalente_km2(geom)
        geoms_orig_por_depto[cod_dep].append(geom)
        conteo_por_depto[cod_dep] = conteo_por_depto.get(cod_dep, 0) + 1

        features_mpio.append(
            {
                "type": "Feature",
                "properties": {
                    "codigo": cod_mpio,
                    "nombre": nombre_limpio,
                    "departamento": cod_dep,
                    "_capa": "municipios",
                },
                "geometry": mapping(geom),
            }
        )

    features_mpio.sort(key=lambda f: str(f["properties"]["codigo"]))

    cods_geo = set(geoms_orig_por_mpio.keys())
    cods_eva = set(codigos_datos.keys())
    faltantes_en_geo = sorted(cods_eva - cods_geo)
    faltantes_en_eva = sorted(cods_geo - cods_eva)
    if faltantes_en_geo or faltantes_en_eva:
        raise ValueError(
            f"Desempate de codigos DANE entre EVA y MGN: "
            f"faltan_en_geo={faltantes_en_geo}, faltan_en_eva={faltantes_en_eva}."
        )

    features_depto: list[dict[str, Any]] = []
    areas_depto_orig_km2: dict[str, float] = {}
    for cod_dep in sorted(deptos_cfg):
        union_dep = limpiar_geometria_poligonal(shapely.unary_union(geoms_orig_por_depto[cod_dep]))
        areas_depto_orig_km2[cod_dep] = calcular_area_equivalente_km2(union_dep)
        features_depto.append(
            {
                "type": "Feature",
                "properties": {
                    "codigo": cod_dep,
                    "nombre": cfg.departamentos[cod_dep],
                    "departamento": cod_dep,
                    "_capa": "departamentos",
                },
                "geometry": mapping(union_dep),
            }
        )

    vertices_originales = int(
        sum(shapely.get_num_coordinates(g) for g in geoms_orig_por_mpio.values())
    )

    fc_conjunta = {
        "type": "FeatureCollection",
        "features": features_mpio + features_depto,
    }
    topo = (
        tp.Topology(fc_conjunta, object_name="conjunta", prequantize=False)
        .toposimplify(epsilon=cfg.geografia.epsilon_simplificacion)
        .topoquantize(cfg.geografia.cuantizacion)
    )
    dict_q = topo.to_dict()

    geoms_mpio_out: list[dict[str, Any]] = []
    geoms_depto_out: list[dict[str, Any]] = []
    for g_obj in dict_q["objects"]["conjunta"]["geometries"]:
        props_in = dict(g_obj.get("properties", {}))
        capa = str(props_in.pop("_capa"))
        props_minimas = {
            "codigo": str(props_in["codigo"]),
            "nombre": str(props_in["nombre"]),
            "departamento": str(props_in["departamento"]),
        }
        item_limpio = {
            "type": g_obj["type"],
            "arcs": g_obj["arcs"],
            "properties": props_minimas,
        }
        if capa == "municipios":
            geoms_mpio_out.append(item_limpio)
        else:
            geoms_depto_out.append(item_limpio)

    geoms_mpio_out.sort(key=lambda g: str(g["properties"]["codigo"]))
    geoms_depto_out.sort(key=lambda g: str(g["properties"]["codigo"]))

    topo_final: dict[str, Any] = {
        "type": "Topology",
        "objects": {
            "municipios": {
                "type": "GeometryCollection",
                "geometries": geoms_mpio_out,
            },
            "departamentos": {
                "type": "GeometryCollection",
                "geometries": geoms_depto_out,
            },
        },
        "arcs": dict_q["arcs"],
        "transform": dict_q["transform"],
        "bbox": [round(float(x), 6) for x in dict_q["bbox"]],
    }

    escala = topo_final["transform"]["scale"]
    traslacion = topo_final["transform"]["translate"]
    arcos_decod = [
        _reconstruir_coordenadas_arco(arco, escala, traslacion) for arco in topo_final["arcs"]
    ]

    filas_val: list[dict[str, Any]] = []
    geoms_simpl_por_depto: dict[str, list[Polygon | MultiPolygon]] = {
        d: [] for d in sorted(deptos_cfg)
    }
    for g_obj in geoms_mpio_out:
        cod_m = str(g_obj["properties"]["codigo"])
        cod_d = str(g_obj["properties"]["departamento"])
        nom_m = str(g_obj["properties"]["nombre"])
        geom_s = reconstruir_geometria_topojson(g_obj, arcos_decod)
        es_valida = bool(geom_s.is_valid and not geom_s.is_empty)
        area_o = areas_orig_km2[cod_m]
        area_s = calcular_area_equivalente_km2(geom_s)
        dif_pct = abs(area_s - area_o) / area_o * 100.0 if area_o > 0 else 0.0
        geoms_simpl_por_depto[cod_d].append(geom_s)
        filas_val.append(
            {
                "codigo": cod_m,
                "nombre": nom_m,
                "departamento": cod_d,
                "geometria_valida": es_valida,
                "area_original_km2": area_o,
                "area_simplificada_km2": area_s,
                "diferencia_area_pct": dif_pct,
                "excede_3_pct": bool(dif_pct > cfg.geografia.max_diferencia_area_pct),
            }
        )

    df_val = pd.DataFrame(filas_val)

    # Verificar ausencia de huecos y solapamientos: la suma de areas municipales
    # simplificadas por departamento coincide con el area del poligono departamental disuelto
    max_desajuste_topologico_pct = 0.0
    for g_dep in geoms_depto_out:
        cod_d = str(g_dep["properties"]["codigo"])
        geom_dep_s = reconstruir_geometria_topojson(g_dep, arcos_decod)
        if not geom_dep_s.is_valid or geom_dep_s.is_empty:
            raise ValueError(f"Geometria departamental simplificada invalida para '{cod_d}'.")
        area_dep_s = calcular_area_equivalente_km2(geom_dep_s)
        suma_mpios_s = float(
            df_val.loc[df_val["departamento"] == cod_d, "area_simplificada_km2"].sum()
        )
        desajuste_pct = (
            abs(area_dep_s - suma_mpios_s) / area_dep_s * 100.0 if area_dep_s > 0 else 0.0
        )
        if desajuste_pct > max_desajuste_topologico_pct:
            max_desajuste_topologico_pct = desajuste_pct

    vertices_simplificados = int(sum(len(a) for a in topo_final["arcs"]))
    retencion_pct = (
        vertices_simplificados / vertices_originales * 100.0 if vertices_originales > 0 else 100.0
    )
    reduccion_pct = 100.0 - retencion_pct

    resumen_geo = {
        "total_municipios": len(geoms_mpio_out),
        "total_departamentos": len(geoms_depto_out),
        "conteo_por_departamento": conteo_por_depto,
        "vertices_originales": vertices_originales,
        "vertices_arcos_simplificados": vertices_simplificados,
        "retencion_vertices_pct": retencion_pct,
        "reduccion_simplificacion_pct": reduccion_pct,
        "epsilon_simplificacion": cfg.geografia.epsilon_simplificacion,
        "geometrias_invalidas": int((~df_val["geometria_valida"]).sum()),
        "max_diferencia_area_pct": float(df_val["diferencia_area_pct"].max()),
        "municipio_max_diferencia": str(
            df_val.sort_values("diferencia_area_pct", ascending=False).iloc[0]["codigo"]
        ),
        "excepciones_area_3pct": int(df_val["excede_3_pct"].sum()),
        "max_desajuste_huecos_solapamientos_pct": max_desajuste_topologico_pct,
    }
    return topo_final, df_val, resumen_geo


def validar_topojson_caribe(
    topo_dict: dict[str, Any],
    df_val: pd.DataFrame,
    resumen_geo: dict[str, Any],
    tamano_bytes: int,
    cfg: ConfiguracionEdicion,
    verificar_conteos_oficiales: bool = True,
) -> None:
    if verificar_conteos_oficiales:
        if int(resumen_geo["total_municipios"]) != 195:
            raise ValueError(
                f"Se esperaban 195 municipios y se obtuvieron {resumen_geo['total_municipios']}."
            )
        conteos = resumen_geo["conteo_por_departamento"]
        for dep, esp in CONTEOS_ESPERADOS_CARIBE.items():
            obs = int(conteos.get(dep, 0))
            if obs != esp:
                raise ValueError(
                    f"Conteo municipal incorrecto en departamento '{dep}': "
                    f"esperado={esp}, observado={obs}."
                )

    if int(resumen_geo["geometrias_invalidas"]) > 0:
        raise ValueError(
            f"Se encontraron {resumen_geo['geometrias_invalidas']} geometrias invalidas."
        )

    if int(resumen_geo["excepciones_area_3pct"]) > 0:
        excep = df_val.loc[df_val["excede_3_pct"], ["codigo", "nombre", "diferencia_area_pct"]]
        raise ValueError(
            f"Municipios con diferencia de area > {cfg.geografia.max_diferencia_area_pct}%: "
            f"{excep.to_dict(orient='records')}."
        )

    if float(resumen_geo["max_desajuste_huecos_solapamientos_pct"]) > 1e-3:
        raise ValueError(
            "Huecos o solapamientos detectados entre municipios vecinos: "
            f"desajuste={resumen_geo['max_desajuste_huecos_solapamientos_pct']}%."
        )

    tamano_kb = tamano_bytes / 1024.0
    if tamano_kb > cfg.geografia.max_tamano_kb:
        raise ValueError(
            f"El archivo caribe.topojson pesa {tamano_kb:.2f} KB, "
            f"superando el maximo de {cfg.geografia.max_tamano_kb} KB."
        )

    for capa in ("municipios", "departamentos"):
        if capa not in topo_dict.get("objects", {}):
            raise ValueError(f"Falta la capa '{capa}' en caribe.topojson.")
        for g in topo_dict["objects"][capa]["geometries"]:
            llaves_props = set(g.get("properties", {}).keys())
            if llaves_props != {"codigo", "nombre", "departamento"}:
                raise ValueError(f"Propiedades invalidas en capa '{capa}': {llaves_props}.")


def ejecutar_geografia(ruta_config: str | Path) -> dict[str, Any]:
    cfg = cargar_configuracion(ruta_config)
    geojson_crudo = obtener_geojson_mgn(cfg)

    ruta_filtrado = Path(cfg.fuente.parquet_filtrado)
    dir_interim = ruta_filtrado.parent
    per_path = dir_interim / "periodo_municipio_cultivo.parquet"
    if per_path.exists():
        df_ref = pd.read_parquet(per_path)
    else:
        df_ref = pd.read_parquet(ruta_filtrado)

    pares_mpio = (
        df_ref[["codigo_dane_municipio", "municipio"]]
        .drop_duplicates("codigo_dane_municipio")
        .to_dict(orient="records")
    )
    codigos_datos = {
        str(f["codigo_dane_municipio"]).zfill(5): str(f["municipio"]) for f in pares_mpio
    }

    topo_dict, df_val, resumen_geo = construir_topojson_caribe(
        geojson_crudo=geojson_crudo,
        codigos_datos=codigos_datos,
        cfg=cfg,
    )

    ruta_salida = Path(cfg.geografia.topojson_salida)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    contenido_json = json.dumps(
        topo_dict,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    bytes_json = (contenido_json + "\n").encode("utf-8")
    validar_topojson_caribe(
        topo_dict=topo_dict,
        df_val=df_val,
        resumen_geo=resumen_geo,
        tamano_bytes=len(bytes_json),
        cfg=cfg,
        verificar_conteos_oficiales=True,
    )
    ruta_salida.write_bytes(bytes_json)

    dir_resultados = dir_interim / "resultados"
    dir_resultados.mkdir(parents=True, exist_ok=True)
    df_val.to_parquet(dir_resultados / "validacion_geografia.parquet", index=False)

    resumen_geo["tamano_bytes"] = len(bytes_json)
    resumen_geo["tamano_kb"] = len(bytes_json) / 1024.0
    return resumen_geo


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera y valida web/public/data/geo/caribe.topojson desde MGN DANE."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Ruta al archivo YAML de configuracion de la edicion.",
    )
    args = parser.parse_args()
    ejecutar_geografia(args.config)


if __name__ == "__main__":
    main()
