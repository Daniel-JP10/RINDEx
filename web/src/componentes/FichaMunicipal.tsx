import type { MunicipioCultivoItem } from "../datos/cargador.ts";
import { usarTiendaRindex } from "../estado/tiendaRindex.ts";
import {
  etiquetarCuadrante,
  etiquetarEvidencia,
  formatearDecimal,
  formatearEntero,
  formatearPorcentaje,
} from "../utilidades/formato.ts";

interface PropsFichaMunicipal {
  municipio: MunicipioCultivoItem | null;
  totalElegibles?: number;
  anioActivo?: number | null;
  alCerrar?: () => void;
}

export function FichaMunicipal({
  municipio,
  totalElegibles,
  anioActivo = null,
  alCerrar,
}: PropsFichaMunicipal): React.JSX.Element {
  const cultivoActivo = usarTiendaRindex((s) => s.cultivoActivo);
  const seleccionarMunicipio = usarTiendaRindex((s) => s.seleccionarMunicipio);

  if (!municipio) {
    return (
      <aside className="ficha-municipal" aria-label="Ficha municipal">
        <h3>Ficha municipal</h3>
        <p className="texto-secundario">
          Haz clic sobre un municipio en el mapa o usa el buscador superior para revisar su
          brecha de rendimiento en {cultivoActivo.toLowerCase()}, serie histórica 2019–2025 y
          precisión del registro.
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

  const registroAnioActivo =
    anioActivo !== null ? puntosSerie.find((p) => p.anio === anioActivo) ?? null : null;

  const anchoSvg = 240;
  const altoSvg = 68;
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
    .map(
      (p, i) =>
        `${i === 0 ? "M" : "L"}${coordX(i).toFixed(1)},${coordY(p.rendimiento_tha ?? 0).toFixed(1)}`,
    )
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

  const idxAnioActivo =
    anioActivo !== null ? puntosSerie.findIndex((p) => p.anio === anioActivo) : -1;

  const textoPrioridad =
    municipio.priorizacion.rango !== null
      ? totalElegibles && totalElegibles > 0
        ? `puesto ${municipio.priorizacion.rango} de ${totalElegibles}, entre ${Math.round(
            municipio.priorizacion.rango_p10 ?? municipio.priorizacion.rango,
          )} y ${Math.round(
            municipio.priorizacion.rango_p90 ?? municipio.priorizacion.rango,
          )} según los pesos`
        : `puesto ${municipio.priorizacion.rango}, entre ${Math.round(
            municipio.priorizacion.rango_p10 ?? municipio.priorizacion.rango,
          )} y ${Math.round(
            municipio.priorizacion.rango_p90 ?? municipio.priorizacion.rango,
          )} según los pesos`
      : "No elegible";

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
            {municipio.departamento} · código {municipio.codigo}
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
        <p className="texto-secundario">
          Sin registros de {cultivoActivo.toLowerCase()} entre 2019 y 2025.
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
                : "No elegible (menos de 500 ha o 4 años)"}
            </div>
            {municipio.elegible &&
            municipio.brecha.ganancia_p10_t !== null &&
            municipio.brecha.ganancia_p90_t !== null ? (
              <span className="buscador-opcion-depto cifra-tabular">
                Ganancia anual: {formatearEntero(municipio.brecha.ganancia_p10_t)} a{" "}
                {formatearEntero(municipio.brecha.ganancia_p90_t)} t/año (mediana{" "}
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
              {idxAnioActivo >= 0 && puntosSerie[idxAnioActivo] ? (
                <circle
                  cx={coordX(idxAnioActivo)}
                  cy={coordY(puntosSerie[idxAnioActivo]!.rendimiento_tha ?? 0)}
                  r={4.5}
                  fill="var(--color-acento)"
                  stroke="var(--color-superficie-elevada)"
                  strokeWidth="1.5"
                />
              ) : null}
            </svg>
          ) : null}

          {anioActivo !== null ? (
            <div className="ficha-fila-meta">
              <span>Rendimiento en {anioActivo}</span>
              <strong className="cifra-tabular">
                {registroAnioActivo && registroAnioActivo.rendimiento_tha !== null
                  ? `${formatearDecimal(registroAnioActivo.rendimiento_tha)} t/ha`
                  : "Sin dato"}
              </strong>
            </div>
          ) : null}

          <div className="ficha-fila-meta">
            <span>Rendimiento medio</span>
            <strong className="cifra-tabular">
              {municipio.rendimiento_tha !== null
                ? `${formatearDecimal(municipio.rendimiento_tha)} t/ha`
                : "No disponible"}
            </strong>
          </div>

          <div className="ficha-fila-meta">
            <span>Cuadrante</span>
            <strong>{etiquetarCuadrante(municipio.priorizacion.cuadrante)}</strong>
          </div>

          <div className="ficha-fila-meta">
            <span>Evidencia municipal</span>
            <strong>{etiquetarEvidencia(municipio.nivel_evidencia)}</strong>
          </div>

          <div className="ficha-fila-meta ficha-fila-columna">
            <span>Prioridad en el cultivo</span>
            <strong className="cifra-tabular">{textoPrioridad}</strong>
          </div>

          <div className="ficha-fila-meta">
            <span>Variabilidad interanual</span>
            <strong className="cifra-tabular">
              {municipio.cv_interanual_pct !== null
                ? formatearPorcentaje(municipio.cv_interanual_pct)
                : "No disponible"}
            </strong>
          </div>
        </>
      )}
    </aside>
  );
}
