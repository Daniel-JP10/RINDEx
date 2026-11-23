import fs from "node:fs";
import path from "node:path";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../App.tsx";
import { limpiarCacheDatos } from "../datos/cargador.ts";
import { usarTiendaRindex } from "../estado/tiendaRindex.ts";

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

describe("Regla absoluta de limpieza narrativa y sincronia scroll-mapa", () => {
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

  it("no expone artefactos internos, codigos D1-D10, guiones bajos ni construccion en Decisor ni Tecnico", async () => {
    const { container } = render(<App />);

    await waitFor(() => {
      expect(screen.getByTestId("frase-gancho-portada").textContent).toContain("681.536");
    });

    /* Seleccionar un municipio para verificar tambien FichaMunicipal abierta */
    act(() => {
      usarTiendaRindex.getState().seleccionarMunicipio("23189");
    });
    await waitFor(() => {
      expect(screen.getByTestId("ficha-municipal").textContent).toContain("Ciénaga de Oro");
    });

    afirmarTextoLimpio(container.textContent ?? "", "Modo Decisor con mapa y ficha");

    /* Entrar al paso de sistemas productivos para verificar GraficoPesas en Decisor */
    act(() => {
      usarTiendaRindex.getState().establecerSeccionActiva("por_que_rinde_menos");
    });
    await waitFor(() => {
      expect(screen.getByTestId("grafico-pesas")).toBeTruthy();
    });
    afirmarTextoLimpio(container.textContent ?? "", "Modo Decisor con grafico de pesas");

    /* Cambiar a modo Tecnico y verificar todo de nuevo */
    const botonTecnico = screen.getByRole("radio", { name: "Técnico" });
    fireEvent.click(botonTecnico);
    await waitFor(() => {
      expect(usarTiendaRindex.getState().modo).toBe("tecnico");
    });
    afirmarTextoLimpio(container.textContent ?? "", "Modo Tecnico con grafico de pesas");

    act(() => {
      usarTiendaRindex.getState().establecerSeccionActiva("mapa_brecha");
    });
    await waitFor(() => {
      expect(screen.getByTestId("ficha-municipal")).toBeTruthy();
    });
    afirmarTextoLimpio(container.textContent ?? "", "Modo Tecnico con mapa y ficha");
  });

  it("sincroniza el_golpe con Arroz y muestra subtitulo coherente en prioriza", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByTestId("frase-gancho-portada").textContent).toContain("681.536");
    });

    expect(usarTiendaRindex.getState().cultivoActivo).toBe("Maíz");

    act(() => {
      usarTiendaRindex.getState().establecerSeccionActiva("el_golpe");
    });

    await waitFor(() => {
      expect(usarTiendaRindex.getState().cultivoActivo).toBe("Arroz");
    });
    expect(screen.getByTestId("panel-subtitulo").textContent).toContain("cinco municipios");

    act(() => {
      usarTiendaRindex.getState().establecerSeccionActiva("prioriza");
    });
    await waitFor(() => {
      expect(screen.getByTestId("panel-subtitulo").textContent).toContain("2.000 ponderaciones");
    });
  });
});
