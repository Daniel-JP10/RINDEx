import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import {
  extraerVariablesCss,
  hexALab,
  razonContrasteWcag,
} from "../utilidades/color.ts";

const RUTA_TOKENS = path.resolve(process.cwd(), "src", "estilos", "tokens.css");
const cssTokens = fs.readFileSync(RUTA_TOKENS, "utf-8");
const { claro, oscuro } = extraerVariablesCss(cssTokens);

describe("Tokens de diseno y accesibilidad WCAG 2.1", () => {
  it("cumple contraste minimo 4.5:1 para todo texto contra su fondo real en claro, oscuro, portada y pildoras", () => {
    const paresTexto: Array<[string, string, string]> = [
      /* Tema claro salvia */
      ["Claro: tinta / fondo", claro["--color-tinta"]!, claro["--color-fondo"]!],
      ["Claro: tinta / superficie", claro["--color-tinta"]!, claro["--color-superficie"]!],
      [
        "Claro: tinta / sup. elevada",
        claro["--color-tinta"]!,
        claro["--color-superficie-elevada"]!,
      ],
      [
        "Claro: tinta sec. / fondo",
        claro["--color-tinta-secundaria"]!,
        claro["--color-fondo"]!,
      ],
      [
        "Claro: tinta sec. / superficie",
        claro["--color-tinta-secundaria"]!,
        claro["--color-superficie"]!,
      ],
      ["Claro: acento / fondo", claro["--color-acento"]!, claro["--color-fondo"]!],
      ["Claro: acento / superficie", claro["--color-acento"]!, claro["--color-superficie"]!],
      ["Claro: texto maiz / fondo", claro["--color-texto-maiz"]!, claro["--color-fondo"]!],
      ["Claro: texto yuca / fondo", claro["--color-texto-yuca"]!, claro["--color-fondo"]!],
      ["Claro: texto arroz / fondo", claro["--color-texto-arroz"]!, claro["--color-fondo"]!],

      /* Pildoras vibrantes de cultivo */
      [
        "Pildora maiz: tinta oscura / maiz",
        claro["--color-tinta-sobre-maiz"]!,
        claro["--color-maiz"]!,
      ],
      [
        "Pildora yuca: tinta oscura / yuca",
        claro["--color-tinta-sobre-yuca"]!,
        claro["--color-yuca"]!,
      ],
      [
        "Pildora arroz: tinta oscura / arroz",
        claro["--color-tinta-sobre-arroz"]!,
        claro["--color-arroz"]!,
      ],

      /* Portada y superficies de marca oscuras */
      [
        "Portada: tinta clara / verde profundo",
        claro["--color-marca-tinta-clara"]!,
        claro["--color-marca-profundo"]!,
      ],
      [
        "Portada: tinta suave / verde profundo",
        claro["--color-marca-tinta-suave"]!,
        claro["--color-marca-profundo"]!,
      ],
      [
        "Portada: tinta suave / sup. oscura",
        claro["--color-marca-tinta-suave"]!,
        claro["--color-marca-superficie"]!,
      ],
      [
        "Portada: verde brote / verde profundo",
        claro["--color-marca-brote"]!,
        claro["--color-marca-profundo"]!,
      ],
      [
        "Portada: verde brote / sup. oscura",
        claro["--color-marca-brote"]!,
        claro["--color-marca-superficie"]!,
      ],

      /* Tema oscuro */
      ["Oscuro: tinta / fondo", oscuro["--color-tinta"]!, oscuro["--color-fondo"]!],
      ["Oscuro: tinta / superficie", oscuro["--color-tinta"]!, oscuro["--color-superficie"]!],
      [
        "Oscuro: tinta sec. / fondo",
        oscuro["--color-tinta-secundaria"]!,
        oscuro["--color-fondo"]!,
      ],
      [
        "Oscuro: tinta sec. / superficie",
        oscuro["--color-tinta-secundaria"]!,
        oscuro["--color-superficie"]!,
      ],
      ["Oscuro: acento / fondo", oscuro["--color-acento"]!, oscuro["--color-fondo"]!],
      ["Oscuro: acento / superficie", oscuro["--color-acento"]!, oscuro["--color-superficie"]!],
      ["Oscuro: texto maiz / fondo", oscuro["--color-texto-maiz"]!, oscuro["--color-fondo"]!],
      ["Oscuro: texto yuca / fondo", oscuro["--color-texto-yuca"]!, oscuro["--color-fondo"]!],
      ["Oscuro: texto arroz / fondo", oscuro["--color-texto-arroz"]!, oscuro["--color-fondo"]!],
    ];

    for (const [etiqueta, colorA, colorB] of paresTexto) {
      const razon = razonContrasteWcag(colorA, colorB);
      expect(razon, `${etiqueta} obtuvo ${razon.toFixed(2)}:1`).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("cumple contraste minimo 3:1 para lineas, puntos y bordes con significado", () => {
    const paresGraficos: Array<[string, string, string]> = [
      ["Claro: grafico maiz / fondo", claro["--color-grafico-maiz"]!, claro["--color-fondo"]!],
      ["Claro: grafico yuca / fondo", claro["--color-grafico-yuca"]!, claro["--color-fondo"]!],
      ["Claro: grafico arroz / fondo", claro["--color-grafico-arroz"]!, claro["--color-fondo"]!],
      [
        "Claro: grafico maiz / superficie",
        claro["--color-grafico-maiz"]!,
        claro["--color-superficie"]!,
      ],
      [
        "Claro: grafico yuca / superficie",
        claro["--color-grafico-yuca"]!,
        claro["--color-superficie"]!,
      ],
      [
        "Claro: grafico arroz / superficie",
        claro["--color-grafico-arroz"]!,
        claro["--color-superficie"]!,
      ],
      ["Oscuro: grafico maiz / fondo", oscuro["--color-grafico-maiz"]!, oscuro["--color-fondo"]!],
      ["Oscuro: grafico yuca / fondo", oscuro["--color-grafico-yuca"]!, oscuro["--color-fondo"]!],
      [
        "Oscuro: grafico arroz / fondo",
        oscuro["--color-grafico-arroz"]!,
        oscuro["--color-fondo"]!,
      ],
      [
        "Oscuro: grafico maiz / superficie",
        oscuro["--color-grafico-maiz"]!,
        oscuro["--color-superficie"]!,
      ],
      [
        "Oscuro: grafico yuca / superficie",
        oscuro["--color-grafico-yuca"]!,
        oscuro["--color-superficie"]!,
      ],
      [
        "Oscuro: grafico arroz / superficie",
        oscuro["--color-grafico-arroz"]!,
        oscuro["--color-superficie"]!,
      ],
    ];

    for (const [etiqueta, colorA, colorB] of paresGraficos) {
      const razon = razonContrasteWcag(colorA, colorB);
      expect(razon, `${etiqueta} obtuvo ${razon.toFixed(2)}:1`).toBeGreaterThanOrEqual(3.0);
    }
  });

  it("conserva cultivos vibrantes identicos en claro y oscuro y escalas de 5 pasos monotonas en L*", () => {
    expect(claro["--color-maiz"]).toBe("#F2B705");
    expect(oscuro["--color-maiz"]).toBe("#F2B705");
    expect(claro["--color-yuca"]).toBe("#E4572E");
    expect(oscuro["--color-yuca"]).toBe("#E4572E");
    expect(claro["--color-arroz"]).toBe("#17A398");
    expect(oscuro["--color-arroz"]).toBe("#17A398");

    for (const cultivo of ["maiz", "yuca", "arroz"] as const) {
      const lumClaro = [1, 2, 3, 4, 5].map((i) =>
        hexALab(claro[`--escala-${cultivo}-${i}`]!).L,
      );
      const lumOscuro = [1, 2, 3, 4, 5].map((i) =>
        hexALab(oscuro[`--escala-${cultivo}-${i}`]!).L,
      );

      for (let i = 1; i < 5; i += 1) {
        expect(lumClaro[i]!).toBeLessThan(lumClaro[i - 1]!);
        expect(lumOscuro[i]!).toBeLessThan(lumOscuro[i - 1]!);
      }
    }
  });
});
