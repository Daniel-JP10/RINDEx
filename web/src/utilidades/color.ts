/* Funciones puras para contraste WCAG 2.1 y luminancia perceptual CIE Lab */

export interface LabColor {
  L: number;
  a: number;
  b: number;
}

export function hexARgb(hex: string): [number, number, number] {
  const limpio = hex.trim().replace(/^#/, "");
  if (!/^[0-9a-fA-F]{6}$/.test(limpio)) {
    throw new Error(`Color hexadecimal invalido: '${hex}'.`);
  }
  const r = Number.parseInt(limpio.slice(0, 2), 16) / 255;
  const g = Number.parseInt(limpio.slice(2, 4), 16) / 255;
  const b = Number.parseInt(limpio.slice(4, 6), 16) / 255;
  return [r, g, b];
}

function canalLinealWcag(canal: number): number {
  return canal <= 0.03928 ? canal / 12.92 : Math.pow((canal + 0.055) / 1.055, 2.4);
}

export function luminanciaRelativaWcag(hex: string): number {
  const [r, g, b] = hexARgb(hex);
  return (
    0.2126 * canalLinealWcag(r) +
    0.7152 * canalLinealWcag(g) +
    0.0722 * canalLinealWcag(b)
  );
}

export function razonContrasteWcag(hexA: string, hexB: string): number {
  const lumA = luminanciaRelativaWcag(hexA);
  const lumB = luminanciaRelativaWcag(hexB);
  const mayor = Math.max(lumA, lumB);
  const menor = Math.min(lumA, lumB);
  return (mayor + 0.05) / (menor + 0.05);
}

function canalLinealLab(canal: number): number {
  return canal <= 0.04045 ? canal / 12.92 : Math.pow((canal + 0.055) / 1.055, 2.4);
}

export function hexALab(hex: string): LabColor {
  const [rRaw, gRaw, bRaw] = hexARgb(hex);
  const r = canalLinealLab(rRaw);
  const g = canalLinealLab(gRaw);
  const b = canalLinealLab(bRaw);

  const x = (0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / 0.95047;
  const y = (0.2126729 * r + 0.7151522 * g + 0.072175 * b) / 1.0;
  const z = (0.0193339 * r + 0.119192 * g + 0.9503041 * b) / 1.08883;

  const f = (t: number): number => (t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116);
  const fx = f(x);
  const fy = f(y);
  const fz = f(z);

  return {
    L: 116 * fy - 16,
    a: 500 * (fx - fy),
    b: 200 * (fy - fz),
  };
}

export function extraerVariablesCss(cssTexto: string): {
  claro: Record<string, string>;
  oscuro: Record<string, string>;
} {
  const extraerBloque = (bloque: string): Record<string, string> => {
    const mapa: Record<string, string> = {};
    const regex = /(--[a-z0-9-]+)\s*:\s*([^;]+);/gi;
    let match = regex.exec(bloque);
    while (match !== null) {
      const clave = match[1];
      const valor = match[2];
      if (clave && valor) {
        mapa[clave.trim()] = valor.trim();
      }
      match = regex.exec(bloque);
    }
    return mapa;
  };

  const finClaro = cssTexto.indexOf("@media (prefers-color-scheme: dark)");
  const inicioOscuro = cssTexto.indexOf(':root[data-tema="oscuro"]');
  const bloqueClaro =
    finClaro > 0 ? cssTexto.slice(0, finClaro) : cssTexto;
  const bloqueOscuro = inicioOscuro > 0 ? cssTexto.slice(inicioOscuro) : "";

  return {
    claro: extraerBloque(bloqueClaro),
    oscuro: extraerBloque(bloqueOscuro),
  };
}
