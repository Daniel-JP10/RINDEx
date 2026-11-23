/* Calculos puros del tablero: filtros por departamento, cuadrante y linea de tiempo 2019-2025 */

import type { MunicipioCultivoItem } from "../datos/cargador.ts";

export const ANIOS_TABLERO: readonly number[] = [2019, 2020, 2021, 2022, 2023, 2024, 2025];

export const DEPARTAMENTOS_CARIBE: ReadonlyArray<{ codigo: string; nombre: string }> = [
  { codigo: "08", nombre: "Atlántico" },
  { codigo: "13", nombre: "Bolívar" },
  { codigo: "20", nombre: "Cesar" },
  { codigo: "23", nombre: "Córdoba" },
  { codigo: "44", nombre: "La Guajira" },
  { codigo: "47", nombre: "Magdalena" },
  { codigo: "70", nombre: "Sucre" },
];

export const CUADRANTES_FILTRO: ReadonlyArray<{ clave: string; etiqueta: string }> = [
  { clave: "consolidar", etiqueta: "Consolidar" },
  { clave: "proteger", etiqueta: "Proteger" },
  { clave: "tecnificar", etiqueta: "Tecnificar" },
  { clave: "intervencion_integral", etiqueta: "Intervención integral" },
];

export interface ResumenKpisTablero {
  produccionTotalT: number;
  areaSembradaTotalHa: number;
  areaCosechadaTotalHa: number;
  rendimientoPonderadoTha: number | null;
  municipiosConDato: number;
  municipiosElegibles: number;
  tasaNoCosechadaPct: number | null;
}

export function coincideFiltrosMunicipio(
  municipio: MunicipioCultivoItem,
  departamentoFiltro: string | null,
  cuadranteFiltro: string | null,
): boolean {
  if (departamentoFiltro !== null && municipio.codigo_departamento !== departamentoFiltro) {
    return false;
  }
  if (cuadranteFiltro !== null && municipio.priorizacion.cuadrante !== cuadranteFiltro) {
    return false;
  }
  return true;
}

export function calcularKpisTablero(
  municipios: readonly MunicipioCultivoItem[],
  departamentoFiltro: string | null,
  cuadranteFiltro: string | null,
  anioActivo: number | null,
): ResumenKpisTablero {
  let produccionTotalT = 0;
  let areaSembradaTotalHa = 0;
  let areaCosechadaTotalHa = 0;
  let municipiosConDato = 0;
  let municipiosElegibles = 0;

  for (const m of municipios) {
    if (!coincideFiltrosMunicipio(m, departamentoFiltro, cuadranteFiltro)) {
      continue;
    }

    if (anioActivo === null) {
      if (m.con_datos) {
        municipiosConDato += 1;
        produccionTotalT += m.produccion_t;
        areaSembradaTotalHa += m.area_sembrada_ha;
        areaCosechadaTotalHa += m.area_cosechada_ha;
      }
      if (m.elegible) {
        municipiosElegibles += 1;
      }
    } else {
      const registroAnio = m.serie_anual.find((s) => s.anio === anioActivo);
      if (registroAnio && (registroAnio.area_cosechada_ha > 0 || registroAnio.area_sembrada_ha > 0)) {
        municipiosConDato += 1;
        produccionTotalT += registroAnio.produccion_t;
        areaSembradaTotalHa += registroAnio.area_sembrada_ha;
        areaCosechadaTotalHa += registroAnio.area_cosechada_ha;
      }
      if (m.elegible) {
        municipiosElegibles += 1;
      }
    }
  }

  /* Regla de datos: rendimiento agregado siempre es produccion total sobre area cosechada total */
  const rendimientoPonderadoTha =
    areaCosechadaTotalHa > 0 ? produccionTotalT / areaCosechadaTotalHa : null;

  const tasaNoCosechadaPct =
    areaSembradaTotalHa > 0 && areaSembradaTotalHa >= areaCosechadaTotalHa
      ? ((areaSembradaTotalHa - areaCosechadaTotalHa) / areaSembradaTotalHa) * 100
      : null;

  return {
    produccionTotalT,
    areaSembradaTotalHa,
    areaCosechadaTotalHa,
    rendimientoPonderadoTha,
    municipiosConDato,
    municipiosElegibles,
    tasaNoCosechadaPct,
  };
}
