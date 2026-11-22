/* Funciones puras de formato numerico en espanol colombiano */

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

export function formatearRangoToneladas(minimo: number, maximo: number): string {
  return `${formatearEntero(minimo)} a ${formatearEntero(maximo)} t/año`;
}
