import fs from "node:fs";
import path from "node:path";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { BuscadorMunicipio } from "../componentes/BuscadorMunicipio.tsx";
import { MapaCaribe } from "../componentes/MapaCaribe.tsx";
import { Portada } from "../componentes/Portada.tsx";
import type { ContratoTopoJsonCaribe } from "../datos/cargador.ts";
import { usarTiendaRindex } from "../estado/tiendaRindex.ts";
import type { ContratoHallazgos } from "../tipos/generados/hallazgos.ts";
import type { ContratoMunicipiosMaiz } from "../tipos/generados/municipios_maiz.ts";
import type { ContratoSistemas } from "../tipos/generados/sistemas.ts";

const dirDatosPublic = path.resolve(process.cwd(), "public", "data");
const topoReal = JSON.parse(
  fs.readFileSync(path.join(dirDatosPublic, "geo", "caribe.topojson"), "utf-8"),
) as ContratoTopoJsonCaribe;
const maizReal = JSON.parse(
  fs.readFileSync(path.join(dirDatosPublic, "municipios_maiz.json"), "utf-8"),
) as ContratoMunicipiosMaiz;
const hallazgosReales = JSON.parse(
  fs.readFileSync(path.join(dirDatosPublic, "hallazgos.json"), "utf-8"),
) as ContratoHallazgos;
const sistemasReales = JSON.parse(
  fs.readFileSync(path.join(dirDatosPublic, "sistemas.json"), "utf-8"),
) as ContratoSistemas;

describe("MapaCaribe y Portada con datos reales de RINDEx", () => {
  beforeEach(() => {
    usarTiendaRindex.getState().reiniciar();
  });

  it("genera exactamente 195 trayectorias de municipio y 7 de departamento en menos de 100 ms", () => {
    let tiempoRenderMs = 0;
    const { container } = render(
      <MapaCaribe
        topoJson={topoReal}
        datosCultivo={maizReal}
        alMedirRender={(ms) => {
          tiempoRenderMs = ms;
        }}
      />,
    );

    const rutasMunicipios = container.querySelectorAll("path.municipio-ruta");
    const rutasDepartamentos = container.querySelectorAll("path.departamento-ruta");
    expect(rutasMunicipios.length).toBe(195);
    expect(rutasDepartamentos.length).toBe(7);
    expect(tiempoRenderMs).toBeLessThan(100);
    console.info(`[medicion-mapa] 195 municipios y 7 deptos renderizados en ${tiempoRenderMs.toFixed(2)} ms`);

    const tituloSvg = container.querySelector("svg > title");
    const descSvg = container.querySelector("svg > desc");
    expect(tituloSvg?.textContent).toContain("Región Caribe");
    expect(descSvg?.textContent).toContain("195 municipios");

    const filasTablaAccesible = container.querySelectorAll("table.sr-only tbody tr");
    expect(filasTablaAccesible.length).toBe(195);
  });

  it("permite seleccionar un municipio con teclado desde BuscadorMunicipio", () => {
    const opciones = maizReal.municipios.map((m) => ({
      codigo: m.codigo,
      nombre: m.nombre,
      departamento: m.departamento,
    }));

    render(<BuscadorMunicipio municipios={opciones} />);
    const entrada = screen.getByRole("combobox", { name: /Buscar municipio/i });
    fireEvent.focus(entrada);
    fireEvent.change(entrada, { target: { value: "Ciénaga de Oro" } });
    fireEvent.keyDown(entrada, { key: "Enter" });

    expect(usarTiendaRindex.getState().municipioSeleccionado).toBe("23189");
  });

  it("lee la cifra combinada de portada directamente de hallazgos.json sin numero fijo", () => {
    const hallazgosModificados: ContratoHallazgos = {
      ...hallazgosReales,
      tarjetas: hallazgosReales.tarjetas.map((t) => {
        if (t.id === "combinado_arroz") {
          return { ...t, cifra: 1000, intervalo: [500, 1500] as [number, number] };
        }
        if (t.id === "combinado_maiz") {
          return { ...t, cifra: 2000, intervalo: [1000, 3000] as [number, number] };
        }
        if (t.id === "combinado_yuca") {
          return { ...t, cifra: 3000, intervalo: [1500, 4500] as [number, number] };
        }
        return t;
      }),
    };

    const { rerender } = render(
      <Portada
        hallazgosIniciales={hallazgosReales}
        sistemasIniciales={sistemasReales}
        topoJsonInicial={topoReal}
      />,
    );

    const textoReal = screen.getByTestId("frase-gancho-portada").textContent ?? "";
    expect(textoReal).toContain("401.696 a 1.052.023 t/año");

    rerender(
      <Portada
        hallazgosIniciales={hallazgosModificados}
        sistemasIniciales={sistemasReales}
        topoJsonInicial={topoReal}
      />,
    );

    const textoModificado = screen.getByTestId("frase-gancho-portada").textContent ?? "";
    expect(textoModificado).toContain("3.000 a 9.000 t/año");
    expect(textoModificado).not.toContain("401.696");
  });

  it("imprime tabla de contrastes WCAG calculada desde tokens.css", async () => {
    const { extraerVariablesCss, razonContrasteWcag } = await import("../utilidades/color.ts");
    const css = fs.readFileSync(
      path.resolve(process.cwd(), "src", "estilos", "tokens.css"),
      "utf-8",
    );
    const { claro, oscuro } = extraerVariablesCss(css);
    const tabla: Array<[string, number]> = [
      ["claro tinta / fondo", razonContrasteWcag(claro["--color-tinta"]!, claro["--color-fondo"]!)],
      ["claro tinta / superficie", razonContrasteWcag(claro["--color-tinta"]!, claro["--color-superficie"]!)],
      ["claro tinta sec. / fondo", razonContrasteWcag(claro["--color-tinta-secundaria"]!, claro["--color-fondo"]!)],
      ["claro tinta sec. / superficie", razonContrasteWcag(claro["--color-tinta-secundaria"]!, claro["--color-superficie"]!)],
      ["oscuro tinta / fondo", razonContrasteWcag(oscuro["--color-tinta"]!, oscuro["--color-fondo"]!)],
      ["oscuro tinta / superficie", razonContrasteWcag(oscuro["--color-tinta"]!, oscuro["--color-superficie"]!)],
      ["oscuro tinta sec. / fondo", razonContrasteWcag(oscuro["--color-tinta-secundaria"]!, oscuro["--color-fondo"]!)],
      ["oscuro tinta sec. / superficie", razonContrasteWcag(oscuro["--color-tinta-secundaria"]!, oscuro["--color-superficie"]!)],
      ["claro maiz / fondo", razonContrasteWcag(claro["--color-maiz"]!, claro["--color-fondo"]!)],
      ["claro yuca / fondo", razonContrasteWcag(claro["--color-yuca"]!, claro["--color-fondo"]!)],
      ["claro arroz / fondo", razonContrasteWcag(claro["--color-arroz"]!, claro["--color-fondo"]!)],
      ["oscuro maiz / fondo", razonContrasteWcag(oscuro["--color-maiz"]!, oscuro["--color-fondo"]!)],
      ["oscuro yuca / fondo", razonContrasteWcag(oscuro["--color-yuca"]!, oscuro["--color-fondo"]!)],
      ["oscuro arroz / fondo", razonContrasteWcag(oscuro["--color-arroz"]!, oscuro["--color-fondo"]!)],
    ];
    for (const [par, razon] of tabla) {
      console.info(`[wcag] ${par}: ${razon.toFixed(2)}:1`);
    }
    expect(tabla.length).toBe(14);
  });
});
