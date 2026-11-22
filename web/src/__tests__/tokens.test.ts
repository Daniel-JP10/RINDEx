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
  it("cumple contraste minimo 4.5:1 para tinta sobre fondo y superficie en claro y oscuro", () => {
    const paresTexto: Array<[string, string, string]> = [
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
    ];

    for (const [etiqueta, colorA, colorB] of paresTexto) {
      const razon = razonContrasteWcag(colorA, colorB);
      expect(razon, `${etiqueta} obtuvo ${razon.toFixed(2)}:1`).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("cumple contraste minimo 3:1 para colores de cultivo contra el fondo en claro y oscuro", () => {
    const paresGraficos: Array<[string, string, string]> = [
      ["Claro: maiz / fondo", claro["--color-maiz"]!, claro["--color-fondo"]!],
      ["Claro: yuca / fondo", claro["--color-yuca"]!, claro["--color-fondo"]!],
      ["Claro: arroz / fondo", claro["--color-arroz"]!, claro["--color-fondo"]!],
      ["Oscuro: maiz / fondo", oscuro["--color-maiz"]!, oscuro["--color-fondo"]!],
      ["Oscuro: yuca / fondo", oscuro["--color-yuca"]!, oscuro["--color-fondo"]!],
      ["Oscuro: arroz / fondo", oscuro["--color-arroz"]!, oscuro["--color-fondo"]!],
    ];

    for (const [etiqueta, colorA, colorB] of paresGraficos) {
      const razon = razonContrasteWcag(colorA, colorB);
      expect(razon, `${etiqueta} obtuvo ${razon.toFixed(2)}:1`).toBeGreaterThanOrEqual(3.0);
    }
  });

  it("garantiza escalas secuenciales de 5 pasos monotonas en luminosidad CIE L*", () => {
    for (const cultivo of ["maiz", "yuca", "arroz"] as const) {
      const lumClaro = [1, 2, 3, 4, 5].map((i) =>
        hexALab(claro[`--escala-${cultivo}-${i}`]!).L,
      );
      const lumOscuro = [1, 2, 3, 4, 5].map((i) =>
        hexALab(oscuro[`--escala-${cultivo}-${i}`]!).L,
      );

      for (let i = 1; i < 5; i += 1) {
        expect(lumClaro[i]!).toBeLessThan(lumClaro[i - 1]!);
        expect(lumOscuro[i]!).toBeGreaterThan(lumOscuro[i - 1]!);
      }
    }
  });
});
