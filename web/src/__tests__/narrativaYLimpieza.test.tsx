import fs from "node:fs";
import path from "node:path";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../App.tsx";
import { limpiarCacheDatos } from "../datos/cargador.ts";
import { usarTiendaRindex, type IdSeccion } from "../estado/tiendaRindex.ts";

const dirDatosPublic = path.resolve(process.cwd(), "public", "data");

function leerJsonPublico(rutaRelativa: string): unknown {
  const ruta = path.join(dirDatosPublic, ...rutaRelativa.split("/"));
  return JSON.parse(fs.readFileSync(ruta, "utf-8")) as unknown;
}

function afirmarTextoLimpio(texto: string, contexto: string): void {
  expect(texto, `${contexto}: contiene .json`).not.toMatch(/\.json/i);
  expect(texto, `${contexto}: contiene parquet`).not.toMatch(/parquet/i);
  expect(texto, `${contexto}: contiene hallazgos`).not.toMatch(/hallazgos/i);
  expect(texto, `${contexto}: contiene codigo D seguido de numero`).not.toMatch(/\bD\d+\b/);
  expect(texto, `${contexto}: contiene guion bajo`).not.toContain("_");
  expect(texto, `${contexto}: contiene construccion`).not.toMatch(/construcci[oó]n/i);
}

const VISTAS_ANALITICAS: ReadonlyArray<{ seccion: IdSeccion; testId: string }> = [
  { seccion: "por_que_rinde_menos", testId: "grafico-pesas" },
  { seccion: "lo_que_no_sabemos", testId: "panel-calidad" },
  { seccion: "matriz", testId: "grafico-matriz" },
  { seccion: "simula", testId: "simulador-escenarios" },
  { seccion: "prioriza", testId: "tabla-prioridad" },
  { seccion: "metodologia", testId: "panel-metodologia" },
];

describe("Regla absoluta de limpieza narrativa, vistas analiticas y sincronia", () => {
  beforeEach(() => {
    limpiarCacheDatos();
    usarTiendaRindex.getState().reiniciar();

    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const urlStr = typeof input === "string" ? input : input.toString();
        const coincidencia = /\/data\/(.+)$/.exec(urlStr);
        if (!coincidencia?.[1]) {
          return Promise.resolve(new Response("Not found", { status: 404 }));
        }
        const payload = leerJsonPublico(coincidencia[1]);
        return Promise.resolve(
          new Response(JSON.stringify(payload), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        );
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    limpiarCacheDatos();
  });

  it("no expone artefactos internos, codigos D1-D10, guiones bajos ni construccion en ninguna vista ni modo", async () => {
    const { container } = render(<App />);

    await waitFor(() => {
      expect(screen.getByTestId("frase-gancho-portada").textContent).toContain("681.536");
    });

    /* Verificar mapa con filtros, linea de tiempo y ficha abierta */
    act(() => {
      usarTiendaRindex.getState().seleccionarMunicipio("23189");
      usarTiendaRindex.getState().establecerDepartamentoFiltro("23");
      usarTiendaRindex.getState().establecerAnioActivo(2021);
    });
    await waitFor(() => {
      expect(screen.getByTestId("ficha-municipal").textContent).toContain("Ciénaga de Oro");
    });
    afirmarTextoLimpio(container.textContent ?? "", "Decisor mapa + filtros + ficha");

    act(() => {
      usarTiendaRindex.getState().limpiarFiltros();
    });

    /* Verificar las 6 vistas analiticas en Decisor y en Tecnico */
    for (const modoNombre of ["decisor", "tecnico"] as const) {
      if (modoNombre === "tecnico") {
        fireEvent.click(screen.getByRole("radio", { name: "Técnico" }));
        await waitFor(() => {
          expect(usarTiendaRindex.getState().modo).toBe("tecnico");
        });
      }

      for (const vista of VISTAS_ANALITICAS) {
        act(() => {
          usarTiendaRindex.getState().establecerSeccionActiva(vista.seccion);
        });
        await waitFor(() => {
          expect(screen.getByTestId(vista.testId)).toBeTruthy();
        });
        afirmarTextoLimpio(
          container.textContent ?? "",
          `Modo ${modoNombre} vista ${vista.seccion}`,
        );
      }
    }
  });

  it("sincroniza el_golpe con Arroz y muestra el rango precalculado exacto en SimuladorEscenarios", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByTestId("frase-gancho-portada").textContent).toContain("681.536");
    });

    /* Entrar a simula en Maiz y comprobar rango combinado exacto precalculado (D10) */
    act(() => {
      usarTiendaRindex.getState().establecerSeccionActiva("simula");
    });
    await waitFor(() => {
      expect(screen.getByTestId("simulador-rango-combinado").textContent).toContain(
        "305.976 a 322.441",
      );
    });

    /* Entrar a el_golpe sincroniza a Arroz */
    act(() => {
      usarTiendaRindex.getState().establecerSeccionActiva("el_golpe");
    });
    await waitFor(() => {
      expect(usarTiendaRindex.getState().cultivoActivo).toBe("Arroz");
    });
    expect(screen.getByTestId("panel-subtitulo").textContent).toContain("cinco municipios");

    /* Entrar a prioriza muestra su subtitulo propio y la tabla de prioridad */
    act(() => {
      usarTiendaRindex.getState().establecerSeccionActiva("prioriza");
    });
    await waitFor(() => {
      expect(screen.getByTestId("tabla-prioridad")).toBeTruthy();
    });
    expect(screen.getByTestId("panel-subtitulo").textContent).toContain("2.000 ponderaciones");
  });
});
