import type { MunicipioCultivoItem } from "../datos/cargador.ts";
import { usarTiendaRindex } from "../estado/tiendaRindex.ts";
import {
  formatearDecimal,
  formatearEntero,
  formatearPorcentaje,
} from "../utilidades/formato.ts";

interface PropsFichaMunicipal {
  municipio: MunicipioCultivoItem | null;
  alCerrar?: () => void;
}

export function FichaMunicipal({
  municipio,
  alCerrar,
}: PropsFichaMunicipal): React.JSX.Element {
  const modo = usarTiendaRindex((s) => s.modo);
  const cultivoActivo = usarTiendaRindex((s) => s.cultivoActivo);
  const seleccionarMunicipio = usarTiendaRindex((s) => s.seleccionarMunicipio);

  if (!municipio) {
    return (
      <aside className="ficha-municipal" aria-label="Ficha municipal">
        <h3>Ficha municipal</h3>
        <p className="portada-nota">
          Haz clic sobre un municipio en el mapa o usa el buscador superior para
          inspeccionar su brecha de rendimiento en {cultivoActivo.toLowerCase()},
          serie histórica 2019–2025 y nivel de evidencia.
        </p>
      </aside>
    );
  }

  const cerrar = (): void => {
    seleccionarMunicipio(null);
    alCerrar?.();
  };

  const puntosSerie = municipio.serie_anual
    .filter((s) => s.rendimiento_tha !== null)
    .sort((a, b) => a.anio - b.anio);

  const anchoSvg = 240;
  const altoSvg = 72;
  const minRend =
    puntosSerie.length > 0
      ? Math.min(...puntosSerie.map((p) => p.rendimiento_tha ?? 0)) * 0.85
      : 0;
  const maxRendBase =
    puntosSerie.length > 0
      ? Math.max(
          ...puntosSerie.map(
            (p) => (p.rendimiento_tha ?? 0) + (municipio.brecha.brecha_p90_tha ?? 0),
          ),
        )
      : 10;
  const maxRend = Math.max(maxRendBase * 1.05, minRend + 0.5);

  const coordX = (idx: number): number => {
    if (puntosSerie.length <= 1) {
      return anchoSvg / 2;
    }
    return 12 + (idx / (puntosSerie.length - 1)) * (anchoSvg - 24);
  };
  const coordY = (val: number): number => {
    const frac = (val - minRend) / (maxRend - minRend);
    return altoSvg - 10 - frac * (altoSvg - 20);
  };

  const rutaLinea = puntosSerie
    .map((p, i) => `${i === 0 ? "M" : "L"}${coordX(i).toFixed(1)},${coordY(p.rendimiento_tha ?? 0).toFixed(1)}`)
    .join(" ");

  const brechaP10 = municipio.brecha.brecha_p10_tha ?? 0;
  const brechaP90 = municipio.brecha.brecha_p90_tha ?? 0;
  const rutaBanda =
    puntosSerie.length > 1
      ? [
          ...puntosSerie.map(
            (p, i) =>
              `${i === 0 ? "M" : "L"}${coordX(i).toFixed(1)},${coordY((p.rendimiento_tha ?? 0) + brechaP90).toFixed(1)}`,
          ),
          ...[...puntosSerie]
            .reverse()
            .map(
              (p, iRev) =>
                `L${coordX(puntosSerie.length - 1 - iRev).toFixed(1)},${coordY((p.rendimiento_tha ?? 0) + brechaP10).toFixed(1)}`,
            ),
          "Z",
        ].join(" ")
      : "";

  return (
    <aside
      className="ficha-municipal"
      aria-label={`Ficha municipal de ${municipio.nombre}`}
      data-testid="ficha-municipal"
    >
      <div className="ficha-cabecera">
        <div>
          <h3>{municipio.nombre}</h3>
          <span className="buscador-opcion-depto">
            {municipio.departamento} · DANE {municipio.codigo}
          </span>
        </div>
        <button
          type="button"
          className="ficha-cerrar"
          onClick={cerrar}
          aria-label="Cerrar ficha municipal"
        >
          Cerrar
        </button>
      </div>

      {!municipio.con_datos ? (
        <p className="portada-nota">
          Sin registros de {cultivoActivo.toLowerCase()} en EVA 2019–2025.
        </p>
      ) : (
        <>
          <div>
            <span className="buscador-opcion-depto">
              Brecha de rendimiento ({cultivoActivo})
            </span>
            <div className="ficha-dato-principal cifra-tabular">
              {municipio.elegible && municipio.brecha.brecha_relativa_pct !== null
                ? formatearPorcentaje(municipio.brecha.brecha_relativa_pct)
                : "No elegible (< 500 ha o < 4 años)"}
            </div>
            {municipio.elegible &&
            municipio.brecha.ganancia_p10_t !== null &&
            municipio.brecha.ganancia_p90_t !== null ? (
              <span className="buscador-opcion-depto cifra-tabular">
                Ganancia S1: {formatearEntero(municipio.brecha.ganancia_p10_t)} a{" "}
                {formatearEntero(municipio.brecha.ganancia_p90_t)} t/año (p50:{" "}
                {formatearEntero(municipio.brecha.ganancia_p50_t ?? 0)} t)
              </span>
            ) : null}
          </div>

          {puntosSerie.length > 0 ? (
            <svg
              viewBox={`0 0 ${anchoSvg} ${altoSvg}`}
              width="100%"
              height={altoSvg}
              role="img"
              aria-label={`Mini serie anual de rendimiento con banda punteada de brecha en ${municipio.nombre}`}
            >
              {rutaBanda ? <path d={rutaBanda} className="banda-incertidumbre" /> : null}
              <path
                d={rutaLinea}
                fill="none"
                stroke="var(--color-tinta)"
                strokeWidth="2"
              />
            </svg>
          ) : null}

          <div className="ficha-fila-meta">
            <span>Rendimiento medio</span>
            <strong className="cifra-tabular">
              {municipio.rendimiento_tha !== null
                ? `${formatearDecimal(municipio.rendimiento_tha)} t/ha`
                : "N/D"}
            </strong>
          </div>

          <div className="ficha-fila-meta">
            <span>Cuadrante</span>
            <strong>{municipio.priorizacion.cuadrante ?? "No elegible"}</strong>
          </div>

          <div className="ficha-fila-meta">
            <span>Evidencia municipal</span>
            <strong>{municipio.nivel_evidencia}</strong>
          </div>

          {modo === "tecnico" ? (
            <div className="ficha-fila-meta">
              <span>Rango prioridad / CV</span>
              <strong className="cifra-tabular">
                {municipio.priorizacion.rango !== null
                  ? `#${municipio.priorizacion.rango} [${municipio.priorizacion.rango_p10 ?? "-"}; ${municipio.priorizacion.rango_p90 ?? "-"}]`
                  : "N/A"}{" "}
                ·{" "}
                {municipio.cv_interanual_pct !== null
                  ? `CV ${formatearPorcentaje(municipio.cv_interanual_pct)}`
                  : "CV N/D"}
              </strong>
            </div>
          ) : null}
        </>
      )}
    </aside>
  );
}
