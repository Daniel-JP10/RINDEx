import fs from "node:fs";
import path from "node:path";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { BuscadorMunicipio } from "../componentes/BuscadorMunicipio.tsx";
import { FichaMunicipal } from "../componentes/FichaMunicipal.tsx";
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

describe("MapaCaribe, FichaMunicipal y Portada con datos reales de RINDEx", () => {
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
    console.info(
      `[medicion-mapa] 195 municipios y 7 deptos renderizados en ${tiempoRenderMs.toFixed(2)} ms`,
    );

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

  it("muestra Prioridad en el cultivo y Variabilidad interanual en FichaMunicipal sin guiones bajos", () => {
    const mpio = maizReal.municipios.find((m) => m.codigo === "23189")!;
    const totalEleg = maizReal.municipios.filter((m) => m.elegible).length;

    const { container } = render(
      <FichaMunicipal municipio={mpio} totalElegibles={totalEleg} />,
    );
    const texto = container.textContent ?? "";
    expect(texto).toContain("Prioridad en el cultivo");
    expect(texto).toContain(`de ${totalEleg}`);
    expect(texto).toContain("según los pesos");
    expect(texto).toContain("Variabilidad interanual");
    expect(texto).not.toContain("Rango prioridad / CV");
    expect(texto).not.toContain("_");
  });

  it("lee combinado_region_total y combinado_region_evidencia_alta desde hallazgos sin numeros fijos", () => {
    const tarTotalReal = hallazgosReales.tarjetas.find(
      (t) => t.id === "combinado_region_total",
    )!;
    const hallazgosModificados: ContratoHallazgos = {
      ...hallazgosReales,
      tarjetas: hallazgosReales.tarjetas.map((t) => {
        if (t.id === "combinado_region_total") {
          return { ...t, cifra: 12000, intervalo: [10000, 15000] as [number, number] };
        }
        if (t.id === "combinado_region_evidencia_alta") {
          return { ...t, cifra: 8000, intervalo: [6000, 9500] as [number, number] };
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
    const p10RealFmt = new Intl.NumberFormat("es-CO").format(tarTotalReal.intervalo![0]!);
    const p90RealFmt = new Intl.NumberFormat("es-CO").format(tarTotalReal.intervalo![1]!);
    expect(textoReal).toContain(p10RealFmt);
    expect(textoReal).toContain(p90RealFmt);

    const textoAlta = screen.getByTestId("frase-evidencia-alta").textContent ?? "";
    expect(textoAlta).toContain("evidencia alta");

    rerender(
      <Portada
        hallazgosIniciales={hallazgosModificados}
        sistemasIniciales={sistemasReales}
        topoJsonInicial={topoReal}
      />,
    );

    const textoModificado = screen.getByTestId("frase-gancho-portada").textContent ?? "";
    expect(textoModificado).toContain("10.000");
    expect(textoModificado).toContain("15.000");
    expect(textoModificado).not.toContain(p10RealFmt);
  });

  it("imprime la nueva tabla de contrastes WCAG calculada desde tokens.css", async () => {
    const { extraerVariablesCss, razonContrasteWcag } = await import("../utilidades/color.ts");
    const css = fs.readFileSync(
      path.resolve(process.cwd(), "src", "estilos", "tokens.css"),
      "utf-8",
    );
    const { claro, oscuro } = extraerVariablesCss(css);
    const tabla: Array<[string, string, string]> = [
      ["Claro: tinta / fondo", claro["--color-tinta"]!, claro["--color-fondo"]!],
      ["Claro: tinta / superficie", claro["--color-tinta"]!, claro["--color-superficie"]!],
      ["Claro: tinta sec. / fondo", claro["--color-tinta-secundaria"]!, claro["--color-fondo"]!],
      ["Claro: acento / fondo", claro["--color-acento"]!, claro["--color-fondo"]!],
      ["Claro: texto maiz / fondo", claro["--color-texto-maiz"]!, claro["--color-fondo"]!],
      ["Claro: texto yuca / fondo", claro["--color-texto-yuca"]!, claro["--color-fondo"]!],
      ["Claro: texto arroz / fondo", claro["--color-texto-arroz"]!, claro["--color-fondo"]!],
      ["Pildora maiz: tinta / fondo", claro["--color-tinta-sobre-maiz"]!, claro["--color-maiz"]!],
      ["Pildora yuca: tinta / fondo", claro["--color-tinta-sobre-yuca"]!, claro["--color-yuca"]!],
      ["Pildora arroz: tinta / fondo", claro["--color-tinta-sobre-arroz"]!, claro["--color-arroz"]!],
      [
        "Portada: tinta clara / profundo",
        claro["--color-marca-tinta-clara"]!,
        claro["--color-marca-profundo"]!,
      ],
      [
        "Portada: tinta suave / sup. oscura",
        claro["--color-marca-tinta-suave"]!,
        claro["--color-marca-superficie"]!,
      ],
      [
        "Portada: verde brote / profundo",
        claro["--color-marca-brote"]!,
        claro["--color-marca-profundo"]!,
      ],
      [
        "Portada: verde brote / sup. oscura",
        claro["--color-marca-brote"]!,
        claro["--color-marca-superficie"]!,
      ],
      ["Oscuro: tinta / fondo", oscuro["--color-tinta"]!, oscuro["--color-fondo"]!],
      ["Oscuro: tinta sec. / superficie", oscuro["--color-tinta-secundaria"]!, oscuro["--color-superficie"]!],
      ["Oscuro: acento / superficie", oscuro["--color-acento"]!, oscuro["--color-superficie"]!],
      ["Grafico claro: maiz / fondo", claro["--color-grafico-maiz"]!, claro["--color-fondo"]!],
      ["Grafico claro: yuca / fondo", claro["--color-grafico-yuca"]!, claro["--color-fondo"]!],
      ["Grafico claro: arroz / fondo", claro["--color-grafico-arroz"]!, claro["--color-fondo"]!],
    ];
    for (const [par, a, b] of tabla) {
      const razon = razonContrasteWcag(a, b);
      console.info(`[wcag] ${par} (${a} sobre ${b}): ${razon.toFixed(2)}:1`);
    }
    expect(tabla.length).toBe(20);
  });
});
