import type { ContratoCalidad } from "../tipos/generados/calidad.ts";
import type { ContratoDepartamental } from "../tipos/generados/departamental.ts";
import type { ContratoEscenarios } from "../tipos/generados/escenarios.ts";
import type { ContratoHallazgos } from "../tipos/generados/hallazgos.ts";
import type { ContratoMeta } from "../tipos/generados/meta.ts";
import type { ContratoMunicipiosArroz } from "../tipos/generados/municipios_arroz.ts";
import type { ContratoMunicipiosMaiz } from "../tipos/generados/municipios_maiz.ts";
import type { ContratoMunicipiosYuca } from "../tipos/generados/municipios_yuca.ts";
import type { ContratoRegional } from "../tipos/generados/regional.ts";
import type { ContratoSistemas } from "../tipos/generados/sistemas.ts";
import type { CultivoClave } from "../estado/tiendaRindex.ts";

export type ContratoMunicipiosCultivo =
  | ContratoMunicipiosMaiz
  | ContratoMunicipiosArroz
  | ContratoMunicipiosYuca;

export type MunicipioCultivoItem = ContratoMunicipiosCultivo["municipios"][number];

export interface GeometriaTopoJson {
  type: "Polygon" | "MultiPolygon";
  arcs: unknown[];
  properties: {
    codigo: string;
    nombre: string;
    departamento: string;
  };
}

export interface ContratoTopoJsonCaribe {
  type: "Topology";
  objects: {
    municipios: {
      type: "GeometryCollection";
      geometries: GeometriaTopoJson[];
    };
    departamentos: {
      type: "GeometryCollection";
      geometries: GeometriaTopoJson[];
    };
  };
  arcs: number[][][];
  transform?: {
    scale: [number, number];
    translate: [number, number];
  };
  bbox?: number[];
}

const ARCHIVOS_POR_CULTIVO: Record<CultivoClave, string> = {
  "Maíz": "municipios_maiz.json",
  "Arroz": "municipios_arroz.json",
  "Yuca": "municipios_yuca.json",
};

const cachePromesas = new Map<string, Promise<unknown>>();

export function limpiarCacheDatos(): void {
  cachePromesas.clear();
}

export function obtenerUrlDato(rutaRelativa: string): string {
  const base = import.meta.env.BASE_URL ?? "/";
  const baseNorm = base.endsWith("/") ? base : `${base}/`;
  const rutaLimpia = rutaRelativa.replace(/^\/+/, "");
  return `${baseNorm}data/${rutaLimpia}`;
}

function afirmarObjeto(valor: unknown, nombreArchivo: string): Record<string, unknown> {
  if (typeof valor !== "object" || valor === null || Array.isArray(valor)) {
    throw new Error(`El archivo '${nombreArchivo}' no contiene un objeto JSON valido.`);
  }
  return valor as Record<string, unknown>;
}

function afirmarCampos(
  obj: Record<string, unknown>,
  campos: readonly string[],
  contexto: string,
): void {
  for (const campo of campos) {
    if (!(campo in obj) || obj[campo] === undefined) {
      throw new Error(`Falta el campo obligatorio '${campo}' en ${contexto}.`);
    }
  }
}

export function validarMeta(datos: unknown): ContratoMeta {
  const obj = afirmarObjeto(datos, "meta.json");
  afirmarCampos(
    obj,
    [
      "version_esquema",
      "id_edicion",
      "nombre_visible",
      "region",
      "anios",
      "cultivos",
      "departamentos",
      "umbrales",
      "fuentes",
    ],
    "meta.json",
  );
  if (!Array.isArray(obj["fuentes"]) || obj["fuentes"].length === 0) {
    throw new Error("El campo 'fuentes' de meta.json debe ser un arreglo no vacio.");
  }
  return obj as unknown as ContratoMeta;
}

export function validarHallazgos(datos: unknown): ContratoHallazgos {
  const obj = afirmarObjeto(datos, "hallazgos.json");
  afirmarCampos(obj, ["version_esquema", "tarjetas"], "hallazgos.json");
  if (!Array.isArray(obj["tarjetas"]) || obj["tarjetas"].length === 0) {
    throw new Error("El campo 'tarjetas' de hallazgos.json debe contener al menos un hallazgo.");
  }
  const primera = afirmarObjeto(obj["tarjetas"][0], "hallazgos.json -> tarjetas[0]");
  afirmarCampos(
    primera,
    ["id", "cultivo", "texto_decisor", "texto_tecnico", "cifra", "origen"],
    "hallazgos.json -> tarjetas[0]",
  );
  return obj as unknown as ContratoHallazgos;
}

export function validarRegional(datos: unknown): ContratoRegional {
  const obj = afirmarObjeto(datos, "regional.json");
  afirmarCampos(obj, ["version_esquema", "registros"], "regional.json");
  if (!Array.isArray(obj["registros"]) || obj["registros"].length === 0) {
    throw new Error("El campo 'registros' de regional.json debe ser un arreglo no vacio.");
  }
  const primero = afirmarObjeto(obj["registros"][0], "regional.json -> registros[0]");
  afirmarCampos(
    primero,
    ["cultivo", "anio", "area_sembrada_ha", "area_cosechada_ha", "produccion_t", "rendimiento_tha"],
    "regional.json -> registros[0]",
  );
  return obj as unknown as ContratoRegional;
}

export function validarDepartamental(datos: unknown): ContratoDepartamental {
  const obj = afirmarObjeto(datos, "departamental.json");
  afirmarCampos(obj, ["version_esquema", "registros"], "departamental.json");
  if (!Array.isArray(obj["registros"]) || obj["registros"].length === 0) {
    throw new Error("El campo 'registros' de departamental.json debe ser un arreglo no vacio.");
  }
  return obj as unknown as ContratoDepartamental;
}

export function validarMunicipiosCultivo(
  datos: unknown,
  archivo = "municipios_cultivo.json",
): ContratoMunicipiosCultivo {
  const obj = afirmarObjeto(datos, archivo);
  afirmarCampos(
    obj,
    ["version_esquema", "cultivo", "nivel_evidencia_cultivo", "municipios"],
    archivo,
  );
  if (!Array.isArray(obj["municipios"]) || obj["municipios"].length === 0) {
    throw new Error(`El campo 'municipios' de '${archivo}' debe contener registros.`);
  }
  const primero = afirmarObjeto(obj["municipios"][0], `${archivo} -> municipios[0]`);
  afirmarCampos(
    primero,
    [
      "codigo",
      "nombre",
      "codigo_departamento",
      "departamento",
      "elegible",
      "nivel_evidencia",
      "brecha",
      "priorizacion",
    ],
    `${archivo} -> municipios[0]`,
  );
  return obj as unknown as ContratoMunicipiosCultivo;
}

export function validarEscenarios(datos: unknown): ContratoEscenarios {
  const obj = afirmarObjeto(datos, "escenarios.json");
  afirmarCampos(obj, ["version_esquema", "totales_regionales", "municipios"], "escenarios.json");
  if (!Array.isArray(obj["totales_regionales"]) || obj["totales_regionales"].length === 0) {
    throw new Error("El campo 'totales_regionales' de escenarios.json no puede estar vacio.");
  }
  return obj as unknown as ContratoEscenarios;
}

export function validarSistemas(datos: unknown): ContratoSistemas {
  const obj = afirmarObjeto(datos, "sistemas.json");
  afirmarCampos(obj, ["version_esquema", "departamentos", "municipios"], "sistemas.json");
  if (!Array.isArray(obj["municipios"]) || obj["municipios"].length === 0) {
    throw new Error("El campo 'municipios' de sistemas.json no puede estar vacio.");
  }
  return obj as unknown as ContratoSistemas;
}

export function validarCalidad(datos: unknown): ContratoCalidad {
  const obj = afirmarObjeto(datos, "calidad.json");
  afirmarCampos(
    obj,
    ["version_esquema", "por_cultivo", "resumen_evidencia_municipal", "arroz_2021_concentracion"],
    "calidad.json",
  );
  return obj as unknown as ContratoCalidad;
}

export function validarTopoJson(datos: unknown): ContratoTopoJsonCaribe {
  const obj = afirmarObjeto(datos, "geo/caribe.topojson");
  afirmarCampos(obj, ["type", "objects", "arcs"], "geo/caribe.topojson");
  const objects = afirmarObjeto(obj["objects"], "geo/caribe.topojson -> objects");
  afirmarCampos(objects, ["municipios", "departamentos"], "geo/caribe.topojson -> objects");
  return obj as unknown as ContratoTopoJsonCaribe;
}

async function obtenerJsonConCache<T>(
  rutaRelativa: string,
  validador: (datos: unknown) => T,
): Promise<T> {
  const promesaExistente = cachePromesas.get(rutaRelativa);
  if (promesaExistente) {
    return promesaExistente as Promise<T>;
  }

  const url = obtenerUrlDato(rutaRelativa);
  const promesa = fetch(url)
    .then(async (respuesta) => {
      if (!respuesta.ok) {
        throw new Error(
          `No se pudo cargar '${rutaRelativa}' (HTTP ${respuesta.status} ${respuesta.statusText}).`,
        );
      }
      const jsonBruto: unknown = await respuesta.json();
      return validador(jsonBruto);
    })
    .catch((error: unknown) => {
      cachePromesas.delete(rutaRelativa);
      if (error instanceof Error) {
        throw error;
      }
      throw new Error(`Error inesperado al cargar '${rutaRelativa}'.`);
    });

  cachePromesas.set(rutaRelativa, promesa);
  return promesa;
}

export function cargarMeta(): Promise<ContratoMeta> {
  return obtenerJsonConCache("meta.json", validarMeta);
}

export function cargarHallazgos(): Promise<ContratoHallazgos> {
  return obtenerJsonConCache("hallazgos.json", validarHallazgos);
}

export function cargarRegional(): Promise<ContratoRegional> {
  return obtenerJsonConCache("regional.json", validarRegional);
}

export function cargarDepartamental(): Promise<ContratoDepartamental> {
  return obtenerJsonConCache("departamental.json", validarDepartamental);
}

export function cargarEscenarios(): Promise<ContratoEscenarios> {
  return obtenerJsonConCache("escenarios.json", validarEscenarios);
}

export function cargarSistemas(): Promise<ContratoSistemas> {
  return obtenerJsonConCache("sistemas.json", validarSistemas);
}

export function cargarCalidad(): Promise<ContratoCalidad> {
  return obtenerJsonConCache("calidad.json", validarCalidad);
}

export function cargarTopoJsonCaribe(): Promise<ContratoTopoJsonCaribe> {
  return obtenerJsonConCache("geo/caribe.topojson", validarTopoJson);
}

export function cargarMunicipiosCultivo(
  cultivo: CultivoClave,
): Promise<ContratoMunicipiosCultivo> {
  const archivo = ARCHIVOS_POR_CULTIVO[cultivo];
  return obtenerJsonConCache(archivo, (datos) => validarMunicipiosCultivo(datos, archivo));
}
