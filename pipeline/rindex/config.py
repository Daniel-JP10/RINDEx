"""Carga y validacion de la configuracion YAML de cada edicion."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

CAMPOS_RAIZ_OBLIGATORIOS: tuple[str, ...] = (
    "id_edicion",
    "nombre_visible",
    "region",
    "departamentos",
    "departamentos_excluidos",
    "cultivos",
    "anios",
    "fuente",
    "parametros",
    "clima",
    "mapeo_desagregacion",
    "limites_plausibilidad_rendimiento",
)

CAMPOS_ANIOS_OBLIGATORIOS: tuple[str, ...] = ("inicio", "fin")

CAMPOS_FUENTE_OBLIGATORIOS: tuple[str, ...] = (
    "archivo_local",
    "url_respaldo",
    "ficha",
)

CAMPOS_PARAMETROS_OBLIGATORIOS: tuple[str, ...] = (
    "semilla_aleatoria",
    "replicas_bootstrap",
    "bootstrap_robustez",
    "area_cosechada_minima_ha",
    "anios_minimos_con_dato",
    "umbral_z_robusto",
)

CAMPOS_CLIMA_OBLIGATORIOS: tuple[str, ...] = (
    "url_oni",
    "umbral_oni",
    "regla_anual",
)


@dataclass(frozen=True)
class DepartamentoExcluido:
    codigo: str
    nombre: str
    motivo: str


@dataclass(frozen=True)
class RangoAnios:
    inicio: int
    fin: int


@dataclass(frozen=True)
class ConfigFuente:
    archivo_local: str
    nombre_original: str
    parquet_crudo: str
    parquet_filtrado: str
    manifiesto: str
    url_respaldo: str
    ficha: str


@dataclass(frozen=True)
class ConfigParametros:
    semilla_aleatoria: int
    replicas_bootstrap: int
    bootstrap_robustez: int
    area_cosechada_minima_ha: float
    umbrales_elegibilidad_ha: tuple[float, ...]
    anios_minimos_con_dato: int
    umbral_z_robusto: float


@dataclass(frozen=True)
class ConfigClima:
    url_oni: str
    archivo_local: str
    parquet_anual: str
    umbral_oni: float
    regla_anual: str


@dataclass(frozen=True)
class PesosPriorizacion:
    ganancia: float
    brecha_relativa: float
    estabilidad: float
    confiabilidad: float


@dataclass(frozen=True)
class ConfigPriorizacion:
    pesos: PesosPriorizacion
    juegos_dirichlet: int
    parametros_dirichlet: tuple[float, float, float, float]
    top_k: int
    umbral_robustez_top: float
    minimo_municipios_referencia_depto: int
    percentil_referencia: float


@dataclass(frozen=True)
class ConfigEvidenciaCultivo:
    alto_max_pares_identicos_pct: float
    alto_max_enteros_pct: float
    medio_max_pares_identicos_pct: float
    medio_max_enteros_pct: float


@dataclass(frozen=True)
class ConfigEvidenciaMunicipal:
    alto_max_proporcion_repetidos: float
    alto_max_filas_atipicas: int
    medio_max_proporcion_repetidos: float
    medio_max_filas_atipicas: int


@dataclass(frozen=True)
class ConfigEvidencia:
    cultivo: ConfigEvidenciaCultivo
    municipal: ConfigEvidenciaMunicipal


@dataclass(frozen=True)
class ConfigGeografia:
    url_mgn: str
    version_mgn: str
    licencia: str
    archivo_local: str
    topojson_salida: str
    epsilon_simplificacion: float
    cuantizacion: int
    max_tamano_kb: float
    max_diferencia_area_pct: float


@dataclass(frozen=True)
class MapeoDesagregacionItem:
    cultivo: str
    sistema: str
    color: str


@dataclass(frozen=True)
class LimitePlausibilidad:
    minimo: float
    maximo: float


@dataclass(frozen=True)
class ConfiguracionEdicion:
    id_edicion: str
    nombre_visible: str
    region: str
    departamentos: dict[str, str]
    departamentos_excluidos: tuple[DepartamentoExcluido, ...]
    cultivos: tuple[str, ...]
    anios: RangoAnios
    fuente: ConfigFuente
    parametros: ConfigParametros
    clima: ConfigClima
    priorizacion: ConfigPriorizacion
    evidencia: ConfigEvidencia
    geografia: ConfigGeografia
    mapeo_desagregacion: dict[str, MapeoDesagregacionItem]
    limites_plausibilidad_rendimiento: dict[str, LimitePlausibilidad]


def _verificar_campos(
    diccionario: dict[str, Any],
    campos: tuple[str, ...],
    prefijo: str = "",
) -> None:
    if not isinstance(diccionario, dict):
        nombre_seccion = prefijo.rstrip(".") or "raiz"
        raise ValueError(f"La seccion '{nombre_seccion}' debe ser un mapeo clave-valor.")
    for campo in campos:
        ruta_campo = f"{prefijo}{campo}"
        if campo not in diccionario or diccionario[campo] is None:
            raise ValueError(f"Falta el campo obligatorio en la configuracion: '{ruta_campo}'.")


def _validar_mapeo_desagregacion(
    raw_mapeo: Any,
) -> dict[str, MapeoDesagregacionItem]:
    if not isinstance(raw_mapeo, dict) or not raw_mapeo:
        raise ValueError("El campo 'mapeo_desagregacion' debe ser un diccionario no vacio.")
    resultado: dict[str, MapeoDesagregacionItem] = {}
    for clave, item in raw_mapeo.items():
        _verificar_campos(
            item,
            ("cultivo", "sistema", "color"),
            prefijo=f"mapeo_desagregacion.{clave}.",
        )
        resultado[str(clave)] = MapeoDesagregacionItem(
            cultivo=str(item["cultivo"]),
            sistema=str(item["sistema"]),
            color=str(item["color"]),
        )
    return resultado


def _validar_limites_plausibilidad(
    raw_limites: Any,
    cultivos: tuple[str, ...],
) -> dict[str, LimitePlausibilidad]:
    if not isinstance(raw_limites, dict) or not raw_limites:
        raise ValueError(
            "El campo 'limites_plausibilidad_rendimiento' debe ser un diccionario no vacio."
        )
    resultado: dict[str, LimitePlausibilidad] = {}
    for cultivo, item in raw_limites.items():
        _verificar_campos(
            item,
            ("minimo", "maximo"),
            prefijo=f"limites_plausibilidad_rendimiento.{cultivo}.",
        )
        minimo = float(item["minimo"])
        maximo = float(item["maximo"])
        if minimo < 0 or minimo >= maximo:
            raise ValueError(
                f"Limites de plausibilidad invalidos para '{cultivo}': [{minimo}, {maximo}]."
            )
        resultado[str(cultivo)] = LimitePlausibilidad(minimo=minimo, maximo=maximo)
    for cultivo in cultivos:
        if cultivo not in resultado:
            raise ValueError(f"Faltan limites de plausibilidad para el cultivo '{cultivo}'.")
    return resultado


def _validar_priorizacion(raw_prio: Any) -> ConfigPriorizacion:
    if not isinstance(raw_prio, dict):
        raw_prio = {}
    pesos_raw = raw_prio.get("pesos", {})
    pesos = PesosPriorizacion(
        ganancia=float(pesos_raw.get("ganancia", 0.40)),
        brecha_relativa=float(pesos_raw.get("brecha_relativa", 0.30)),
        estabilidad=float(pesos_raw.get("estabilidad", 0.15)),
        confiabilidad=float(pesos_raw.get("confiabilidad", 0.15)),
    )
    param_dir = raw_prio.get("parametros_dirichlet", [1.0, 1.0, 1.0, 1.0])
    return ConfigPriorizacion(
        pesos=pesos,
        juegos_dirichlet=int(raw_prio.get("juegos_dirichlet", 2000)),
        parametros_dirichlet=(
            float(param_dir[0]),
            float(param_dir[1]),
            float(param_dir[2]),
            float(param_dir[3]),
        ),
        top_k=int(raw_prio.get("top_k", 20)),
        umbral_robustez_top=float(raw_prio.get("umbral_robustez_top", 0.80)),
        minimo_municipios_referencia_depto=int(
            raw_prio.get("minimo_municipios_referencia_depto", 5)
        ),
        percentil_referencia=float(raw_prio.get("percentil_referencia", 75.0)),
    )


def _validar_evidencia(raw_ev: Any) -> ConfigEvidencia:
    if not isinstance(raw_ev, dict):
        raw_ev = {}
    cul_raw = raw_ev.get("cultivo", {})
    mpio_raw = raw_ev.get("municipal", {})
    return ConfigEvidencia(
        cultivo=ConfigEvidenciaCultivo(
            alto_max_pares_identicos_pct=float(cul_raw.get("alto_max_pares_identicos_pct", 25.0)),
            alto_max_enteros_pct=float(cul_raw.get("alto_max_enteros_pct", 50.0)),
            medio_max_pares_identicos_pct=float(cul_raw.get("medio_max_pares_identicos_pct", 40.0)),
            medio_max_enteros_pct=float(cul_raw.get("medio_max_enteros_pct", 70.0)),
        ),
        municipal=ConfigEvidenciaMunicipal(
            alto_max_proporcion_repetidos=float(
                mpio_raw.get("alto_max_proporcion_repetidos", 0.25)
            ),
            alto_max_filas_atipicas=int(mpio_raw.get("alto_max_filas_atipicas", 0)),
            medio_max_proporcion_repetidos=float(
                mpio_raw.get("medio_max_proporcion_repetidos", 0.50)
            ),
            medio_max_filas_atipicas=int(mpio_raw.get("medio_max_filas_atipicas", 1)),
        ),
    )


def _validar_geografia(raw_geo: Any) -> ConfigGeografia:
    if not isinstance(raw_geo, dict):
        raw_geo = {}
    url_def = (
        "https://geoportal.dane.gov.co/mparcgis/rest/services/"
        "Divipola/Serv_DIVIPOLA_MGN_2025/FeatureServer/317/query"
    )
    return ConfigGeografia(
        url_mgn=str(raw_geo.get("url_mgn", url_def)),
        version_mgn=str(raw_geo.get("version_mgn", "MGN 2025 (Geoportal DANE DIVIPOLA)")),
        licencia=str(
            raw_geo.get(
                "licencia",
                "Datos Abiertos DANE - Creative Commons Attribution 4.0 International (CC BY 4.0)",
            )
        ),
        archivo_local=str(
            raw_geo.get("archivo_local", "data/raw/geo/mgn_2025_municipios_caribe.geojson")
        ),
        topojson_salida=str(raw_geo.get("topojson_salida", "web/public/data/geo/caribe.topojson")),
        epsilon_simplificacion=float(raw_geo.get("epsilon_simplificacion", 0.001)),
        cuantizacion=int(raw_geo.get("cuantizacion", 100000)),
        max_tamano_kb=float(raw_geo.get("max_tamano_kb", 600.0)),
        max_diferencia_area_pct=float(raw_geo.get("max_diferencia_area_pct", 3.0)),
    )


def validar_diccionario_config(datos: dict[str, Any]) -> ConfiguracionEdicion:
    _verificar_campos(datos, CAMPOS_RAIZ_OBLIGATORIOS)
    _verificar_campos(datos["anios"], CAMPOS_ANIOS_OBLIGATORIOS, prefijo="anios.")
    _verificar_campos(datos["fuente"], CAMPOS_FUENTE_OBLIGATORIOS, prefijo="fuente.")
    _verificar_campos(datos["parametros"], CAMPOS_PARAMETROS_OBLIGATORIOS, prefijo="parametros.")
    _verificar_campos(datos["clima"], CAMPOS_CLIMA_OBLIGATORIOS, prefijo="clima.")

    if not isinstance(datos["departamentos"], dict) or not datos["departamentos"]:
        raise ValueError("El campo 'departamentos' debe ser un diccionario no vacio.")
    if not isinstance(datos["cultivos"], list) or not datos["cultivos"]:
        raise ValueError("El campo 'cultivos' debe ser una lista no vacia.")
    if not isinstance(datos["departamentos_excluidos"], list):
        raise ValueError("El campo 'departamentos_excluidos' debe ser una lista.")

    departamentos = {str(k).zfill(2): str(v) for k, v in datos["departamentos"].items()}
    cultivos = tuple(str(c) for c in datos["cultivos"])

    excluidos: list[DepartamentoExcluido] = []
    for idx, item in enumerate(datos["departamentos_excluidos"]):
        _verificar_campos(
            item,
            ("codigo", "nombre", "motivo"),
            prefijo=f"departamentos_excluidos[{idx}].",
        )
        excluidos.append(
            DepartamentoExcluido(
                codigo=str(item["codigo"]).zfill(2),
                nombre=str(item["nombre"]),
                motivo=str(item["motivo"]),
            )
        )

    anios = RangoAnios(
        inicio=int(datos["anios"]["inicio"]),
        fin=int(datos["anios"]["fin"]),
    )
    if anios.inicio > anios.fin:
        raise ValueError("El anio de inicio no puede ser mayor que el anio de fin.")

    fuente_raw = datos["fuente"]
    archivo_local = str(fuente_raw["archivo_local"])
    fuente = ConfigFuente(
        archivo_local=archivo_local,
        nombre_original=str(fuente_raw.get("nombre_original", Path(archivo_local).name)),
        parquet_crudo=str(fuente_raw.get("parquet_crudo", "data/interim/eva_crudo.parquet")),
        parquet_filtrado=str(
            fuente_raw.get("parquet_filtrado", "data/interim/eva_filtrada.parquet")
        ),
        manifiesto=str(fuente_raw.get("manifiesto", "data/raw/manifiesto.json")),
        url_respaldo=str(fuente_raw["url_respaldo"]),
        ficha=str(fuente_raw["ficha"]),
    )

    param_raw = datos["parametros"]
    umbrales_raw = param_raw.get("umbrales_elegibilidad_ha", [300, 500, 1000])
    parametros = ConfigParametros(
        semilla_aleatoria=int(param_raw["semilla_aleatoria"]),
        replicas_bootstrap=int(param_raw["replicas_bootstrap"]),
        bootstrap_robustez=int(param_raw["bootstrap_robustez"]),
        area_cosechada_minima_ha=float(param_raw["area_cosechada_minima_ha"]),
        umbrales_elegibilidad_ha=tuple(float(u) for u in umbrales_raw),
        anios_minimos_con_dato=int(param_raw["anios_minimos_con_dato"]),
        umbral_z_robusto=float(param_raw["umbral_z_robusto"]),
    )

    clima_raw = datos["clima"]
    clima = ConfigClima(
        url_oni=str(clima_raw["url_oni"]),
        archivo_local=str(clima_raw.get("archivo_local", "data/raw/oni.ascii.txt")),
        parquet_anual=str(clima_raw.get("parquet_anual", "data/interim/oni_anual.parquet")),
        umbral_oni=float(clima_raw["umbral_oni"]),
        regla_anual=str(clima_raw["regla_anual"]),
    )

    priorizacion = _validar_priorizacion(datos.get("priorizacion"))
    evidencia = _validar_evidencia(datos.get("evidencia"))
    geografia = _validar_geografia(datos.get("geografia"))
    mapeo = _validar_mapeo_desagregacion(datos["mapeo_desagregacion"])
    limites = _validar_limites_plausibilidad(
        datos["limites_plausibilidad_rendimiento"],
        cultivos,
    )

    return ConfiguracionEdicion(
        id_edicion=str(datos["id_edicion"]),
        nombre_visible=str(datos["nombre_visible"]),
        region=str(datos["region"]),
        departamentos=departamentos,
        departamentos_excluidos=tuple(excluidos),
        cultivos=cultivos,
        anios=anios,
        fuente=fuente,
        parametros=parametros,
        clima=clima,
        priorizacion=priorizacion,
        evidencia=evidencia,
        geografia=geografia,
        mapeo_desagregacion=mapeo,
        limites_plausibilidad_rendimiento=limites,
    )


def cargar_configuracion(ruta: str | Path) -> ConfiguracionEdicion:
    ruta_archivo = Path(ruta)
    if not ruta_archivo.exists():
        raise FileNotFoundError(f"No existe el archivo de configuracion: '{ruta_archivo}'.")
    with ruta_archivo.open("r", encoding="utf-8") as archivo:
        contenido = yaml.safe_load(archivo)
    if not isinstance(contenido, dict):
        raise ValueError(f"El archivo YAML '{ruta_archivo}' no contiene un objeto valido.")
    return validar_diccionario_config(contenido)
