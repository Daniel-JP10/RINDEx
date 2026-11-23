import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import type { ContratoMunicipiosCultivo } from "../datos/cargador.ts";
import type { ContratoDepartamental } from "../tipos/generados/departamental.ts";
import type { ContratoRegional } from "../tipos/generados/regional.ts";
import {
  ANIOS_TABLERO,
  DEPARTAMENTOS_CARIBE,
  calcularKpisTablero,
} from "../utilidades/tablero.ts";

const dirDatos = path.resolve(process.cwd(), "public", "data");

function leerJson<T>(archivo: string): T {
  return JSON.parse(fs.readFileSync(path.join(dirDatos, archivo), "utf-8")) as T;
}

const regional = leerJson<ContratoRegional>("regional.json");
const departamental = leerJson<ContratoDepartamental>("departamental.json");
const cultivosDatos: ReadonlyArray<{
  cultivo: "Maíz" | "Arroz" | "Yuca";
  datos: ContratoMunicipiosCultivo;
}> = [
  { cultivo: "Maíz", datos: leerJson<ContratoMunicipiosCultivo>("municipios_maiz.json") },
  { cultivo: "Arroz", datos: leerJson<ContratoMunicipiosCultivo>("municipios_arroz.json") },
  { cultivo: "Yuca", datos: leerJson<ContratoMunicipiosCultivo>("municipios_yuca.json") },
];

describe("Validaciones cruzadas del tablero (filtros y linea de tiempo vs. series oficiales)", () => {
  it("reproduce exactamente los totales regionales y rendimiento ponderado para los 21 pares cultivo-anio", () => {
    for (const { cultivo, datos } of cultivosDatos) {
      for (const anio of ANIOS_TABLERO) {
        const kpi = calcularKpisTablero(datos.municipios, null, null, anio);
        const ref = regional.registros.find(
          (r) => r.cultivo === cultivo && r.anio === anio,
        );
        expect(ref, `Falta registro regional para ${cultivo} ${anio}`).toBeDefined();
        if (!ref) {
          continue;
        }

        /* Tolerancia por redondeo a entero de hasta 195 municipios (max 0.5 por municipio) */
        expect(Math.abs(kpi.produccionTotalT - ref.produccion_t)).toBeLessThanOrEqual(100);
        expect(Math.abs(kpi.areaCosechadaTotalHa - ref.area_cosechada_ha)).toBeLessThanOrEqual(
          100,
        );
        expect(kpi.rendimientoPonderadoTha).not.toBeNull();
        expect(
          Math.abs((kpi.rendimientoPonderadoTha ?? 0) - ref.rendimiento_tha),
        ).toBeLessThanOrEqual(0.02);
      }
    }
  });

  it("reproduce los totales departamentales y rendimiento ponderado para las 147 combinaciones departamento-cultivo-anio", () => {
    for (const { cultivo, datos } of cultivosDatos) {
      for (const depto of DEPARTAMENTOS_CARIBE) {
        for (const anio of ANIOS_TABLERO) {
          const kpi = calcularKpisTablero(datos.municipios, depto.codigo, null, anio);
          const ref = departamental.registros.find(
            (r) =>
              r.codigo_departamento === depto.codigo &&
              r.cultivo === cultivo &&
              r.anio === anio,
          );
          if (!ref) {
            expect(kpi.produccionTotalT).toBe(0);
            continue;
          }

          expect(Math.abs(kpi.produccionTotalT - ref.produccion_t)).toBeLessThanOrEqual(30);
          expect(
            Math.abs(kpi.areaCosechadaTotalHa - ref.area_cosechada_ha),
          ).toBeLessThanOrEqual(30);
          if (ref.area_cosechada_ha > 0) {
            expect(kpi.rendimientoPonderadoTha).not.toBeNull();
            expect(
              Math.abs((kpi.rendimientoPonderadoTha ?? 0) - ref.rendimiento_tha),
            ).toBeLessThanOrEqual(0.03);
          }
        }
      }
    }
  });

  it("garantiza consistencia entre el periodo acumulado 2019-2025 y la suma de los 7 anios individuales", () => {
    for (const { datos } of cultivosDatos) {
      const kpiPeriodo = calcularKpisTablero(datos.municipios, null, null, null);
      let sumaProdAnios = 0;
      let sumaAreaAnios = 0;
      for (const anio of ANIOS_TABLERO) {
        const kpiAnio = calcularKpisTablero(datos.municipios, null, null, anio);
        sumaProdAnios += kpiAnio.produccionTotalT;
        sumaAreaAnios += kpiAnio.areaCosechadaTotalHa;
      }

      expect(Math.abs(kpiPeriodo.produccionTotalT - sumaProdAnios)).toBeLessThanOrEqual(400);
      expect(Math.abs(kpiPeriodo.areaCosechadaTotalHa - sumaAreaAnios)).toBeLessThanOrEqual(400);
    }
  });

  it("conserva la suma exacta de municipios elegibles al particionar por cuadrante de decision", () => {
    const cuadrantesTodos = [
      "consolidar",
      "proteger",
      "tecnificar",
      "intervencion_integral",
      "estabilidad_no_medible",
    ];
    for (const { datos } of cultivosDatos) {
      const totalElegibles = calcularKpisTablero(datos.municipios, null, null, null)
        .municipiosElegibles;
      const sumaCuadrantes = cuadrantesTodos.reduce(
        (acc, c) => acc + calcularKpisTablero(datos.municipios, null, c, null).municipiosElegibles,
        0,
      );
      expect(sumaCuadrantes).toBe(totalElegibles);
    }
  });
});
