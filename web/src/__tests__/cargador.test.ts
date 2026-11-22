import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  cargarMunicipiosCultivo,
  limpiarCacheDatos,
  validarHallazgos,
  validarMeta,
  validarMunicipiosCultivo,
  validarSistemas,
  validarTopoJson,
} from "../datos/cargador.ts";

describe("Cargadores de datos y validacion ligera en tiempo de ejecucion", () => {
  beforeEach(() => {
    limpiarCacheDatos();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("falla con mensaje claro cuando falta un campo obligatorio en cualquier JSON", () => {
    expect(() => validarMeta({ version_esquema: "1.0.0" })).toThrowError(
      /Falta el campo obligatorio/,
    );
    expect(() => validarHallazgos({ version_esquema: "1.0.0", tarjetas: [] })).toThrowError(
      /debe contener al menos un hallazgo/,
    );
    expect(() =>
      validarMunicipiosCultivo({ version_esquema: "1.0.0", cultivo: "Maíz" }, "municipios_maiz.json"),
    ).toThrowError(/Falta el campo obligatorio 'nivel_evidencia_cultivo'/);
    expect(() => validarSistemas({ version_esquema: "1.0.0" })).toThrowError(
      /Falta el campo obligatorio/,
    );
    expect(() => validarTopoJson({ type: "Topology", objects: {} })).toThrowError(
      /Falta el campo obligatorio 'arcs'/,
    );
  });

  it("carga perezosamente solo el cultivo seleccionado y reutiliza la cache en memoria", async () => {
    const respuestaSimulada = {
      version_esquema: "1.0.0",
      cultivo: "Arroz",
      nivel_evidencia_cultivo: "alto",
      municipios: [
        {
          codigo: "70265",
          nombre: "Guaranda",
          codigo_departamento: "70",
          departamento: "Sucre",
          con_datos: true,
          elegible: true,
          anios_con_dato: 7,
          area_sembrada_ha: 10000,
          area_cosechada_ha: 9000,
          produccion_t: 40000,
          rendimiento_tha: 4.44,
          tasa_area_no_cosechada_pct: 10.0,
          cv_interanual_pct: 8.5,
          nivel_evidencia: "alto",
          calidad: {
            proporcion_repetidos_pct: 0,
            serie_poco_informativa: false,
            filas_atipicas: 0,
            excluido_d4: false,
          },
          rendimiento_por_sistema: { secano_mecanizado: 4.44 },
          serie_anual: [],
          brecha: {
            brecha_relativa_pct: 21.0,
            brecha_p10_tha: 0.6,
            brecha_p50_tha: 0.9,
            brecha_p90_tha: 1.2,
            ganancia_p10_t: 5000,
            ganancia_p50_t: 8933,
            ganancia_p90_t: 12000,
          },
          priorizacion: {
            cuadrante: "tecnificar",
            indice_prioridad: 85.7,
            rango: 1,
            rango_p10: 1.0,
            rango_p90: 9.0,
            proporcion_top20_pct: 98.5,
            prioridad_robusta: true,
          },
        },
      ],
    };

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => respuestaSimulada,
    });
    vi.stubGlobal("fetch", fetchMock);

    const primero = await cargarMunicipiosCultivo("Arroz");
    const segundo = await cargarMunicipiosCultivo("Arroz");

    expect(primero.cultivo).toBe("Arroz");
    expect(segundo).toBe(primero);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(String(fetchMock.mock.calls[0]?.[0])).toContain("municipios_arroz.json");
  });

  it("propaga errores HTTP visibles al fallar fetch", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: "Not Found",
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(cargarMunicipiosCultivo("Yuca")).rejects.toThrowError(/HTTP 404/);
  });
});
