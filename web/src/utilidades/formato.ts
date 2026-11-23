/* Funciones puras de formato numerico y etiquetas legibles en espanol colombiano */

const formateadorEntero = new Intl.NumberFormat("es-CO", {
  maximumFractionDigits: 0,
});

export function formatearEntero(valor: number): string {
  return formateadorEntero.format(Math.round(valor));
}

export function formatearDecimal(valor: number, decimales = 2): string {
  return new Intl.NumberFormat("es-CO", {
    minimumFractionDigits: decimales,
    maximumFractionDigits: decimales,
  }).format(valor);
}

export function formatearPorcentaje(valor: number, decimales = 1): string {
  return `${formatearDecimal(valor, decimales)} %`;
}

export function formatearMultiplicador(valor: number, decimales = 2): string {
  return `${formatearDecimal(valor, decimales)}×`;
}

export function formatearRangoToneladas(minimo: number, maximo: number): string {
  return `${formatearEntero(minimo)} a ${formatearEntero(maximo)} t/año`;
}

const ETIQUETAS_CUADRANTE: Record<string, string> = {
  consolidar: "Consolidar",
  proteger: "Proteger",
  tecnificar: "Tecnificar",
  intervencion_integral: "Intervención integral",
  estabilidad_no_medible: "Estabilidad no medible",
};

export function etiquetarCuadrante(clave: string | null | undefined): string {
  if (!clave) {
    return "No elegible";
  }
  return ETIQUETAS_CUADRANTE[clave] ?? "No elegible";
}

const ETIQUETAS_EVIDENCIA: Record<string, string> = {
  alto: "Alta",
  medio: "Media",
  bajo: "Baja",
  sin_datos: "Sin datos",
};

export function etiquetarEvidencia(clave: string | null | undefined): string {
  if (!clave) {
    return "Sin datos";
  }
  return ETIQUETAS_EVIDENCIA[clave] ?? "Sin datos";
}

const ETIQUETAS_SISTEMA: Record<string, string> = {
  tradicional: "Tradicional",
  tecnificado: "Tecnificado",
  secano_manual: "Secano manual",
  secano_mecanizado: "Secano mecanizado",
  riego: "Riego",
  fresco: "Consumo en fresco",
  industrial: "Industrial",
};

export function etiquetarSistema(clave: string): string {
  return ETIQUETAS_SISTEMA[clave] ?? clave;
}
