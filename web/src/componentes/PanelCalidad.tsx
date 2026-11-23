/* Panel de diagnostico de calidad de registro y niveles de evidencia por cultivo */

import type { ContratoCalidad } from "../tipos/generados/calidad.ts";
import {
  etiquetarEvidencia,
  formatearEntero,
  formatearPorcentaje,
} from "../utilidades/formato.ts";

interface PropsPanelCalidad {
  calidad: ContratoCalidad | null;
}

export function PanelCalidad({ calidad }: PropsPanelCalidad): React.JSX.Element {
  if (!calidad) {
    return (
      <div className="panel-analitico">
        <p className="texto-secundario">Cargando diagnóstico de calidad de las series...</p>
      </div>
    );
  }

  const mapaMpio = new Map(
    calidad.resumen_evidencia_municipal.map((r) => [r.cultivo, r]),
  );

  return (
    <div className="panel-analitico" data-testid="panel-calidad">
      <div className="calidad-tarjetas">
        {calidad.por_cultivo.map((item) => {
          const mpio = mapaMpio.get(item.cultivo);
          const totalM = mpio?.total_con_datos ?? 0;
          const pctAlto = totalM > 0 ? ((mpio?.alto ?? 0) / totalM) * 100 : 0;
          const pctMedio = totalM > 0 ? ((mpio?.medio ?? 0) / totalM) * 100 : 0;
          const pctBajo = totalM > 0 ? ((mpio?.bajo ?? 0) / totalM) * 100 : 0;

          return (
            <section
              key={item.cultivo}
              className="calidad-tarjeta"
              data-evidencia={item.nivel_evidencia}
            >
              <div className="calidad-cabecera">
                <h3 className="calidad-cultivo">{item.cultivo}</h3>
                <span className={`insignia-evidencia insignia-${item.nivel_evidencia}`}>
                  Evidencia {etiquetarEvidencia(item.nivel_evidencia).toLowerCase()}
                </span>
              </div>

              <div className="calidad-metrica">
                <div className="calidad-metrica-linea">
                  <span>Años consecutivos repetidos</span>
                  <strong className="cifra-tabular">
                    {formatearPorcentaje(item.pct_pares_identicos)}
                  </strong>
                </div>
                <div className="calidad-barra-fondo" aria-hidden="true">
                  <div
                    className={`calidad-barra-relleno barra-${item.nivel_evidencia}`}
                    style={{ width: `${Math.min(100, item.pct_pares_identicos)}%` }}
                  />
                </div>
              </div>

              <div className="calidad-metrica">
                <div className="calidad-metrica-linea">
                  <span>Rendimientos en números redondos</span>
                  <strong className="cifra-tabular">
                    {formatearPorcentaje(item.pct_rendimientos_enteros)}
                  </strong>
                </div>
                <div className="calidad-barra-fondo" aria-hidden="true">
                  <div
                    className={`calidad-barra-relleno barra-${item.nivel_evidencia}`}
                    style={{ width: `${Math.min(100, item.pct_rendimientos_enteros)}%` }}
                  />
                </div>
              </div>

              <p className="calidad-detalle cifra-tabular">
                {formatearEntero(item.series_poco_informativas)} de{" "}
                {formatearEntero(item.series_evaluadas)} series municipales tienen más de la mitad
                de sus años repetidos.
              </p>

              {mpio && totalM > 0 ? (
                <div className="calidad-distribucion">
                  <span className="calidad-dist-titulo">
                    Evidencia municipal ({formatearEntero(totalM)} municipios)
                  </span>
                  <div
                    className="calidad-barra-apilada"
                    role="img"
                    aria-label={`Distribución municipal en ${item.cultivo}: ${mpio.alto} alta, ${mpio.medio} media, ${mpio.bajo} baja`}
                  >
                    <span className="seg-alto" style={{ width: `${pctAlto}%` }} />
                    <span className="seg-medio" style={{ width: `${pctMedio}%` }} />
                    <span className="seg-bajo" style={{ width: `${pctBajo}%` }} />
                  </div>
                  <div className="calidad-dist-cifras cifra-tabular">
                    <span>Alta: {mpio.alto}</span>
                    <span>Media: {mpio.medio}</span>
                    <span>Baja: {mpio.bajo}</span>
                  </div>
                </div>
              ) : null}
            </section>
          );
        })}
      </div>

      <div className="calidad-nota-corte">
        <strong>Cambio de reporte desde 2022:</strong> a partir de 2022 la cosecha de un semestre
        puede registrarse en el semestre siguiente; por eso el área no cosechada se evalúa solo en
        balance anual y nunca por semestre.
      </div>
    </div>
  );
}
