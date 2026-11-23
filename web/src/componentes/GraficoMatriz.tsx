/* Grafico interactivo de matriz de decision: rendimiento vs variabilidad interanual */

import { useMemo, useState } from "react";
import type { ContratoMunicipiosCultivo, MunicipioCultivoItem } from "../datos/cargador.ts";
import { usarTiendaRindex } from "../estado/tiendaRindex.ts";
import {
  etiquetarCuadrante,
  formatearDecimal,
  formatearEntero,
  formatearPorcentaje,
} from "../utilidades/formato.ts";
import { coincideFiltrosMunicipio } from "../utilidades/tablero.ts";

interface PropsGraficoMatriz {
  datosCultivo: ContratoMunicipiosCultivo | null;
  departamentoFiltro: string | null;
  cuadranteFiltro: string | null;
}

const COLOR_CUADRANTE: Record<string, string> = {
  consolidar: "#186B42",
  proteger: "#C77C02",
  tecnificar: "#17A398",
  intervencion_integral: "#E4572E",
  estabilidad_no_medible: "#7D8778",
};

function calcularMediana(valores: readonly number[]): number {
  if (valores.length === 0) {
    return 0;
  }
  const ordenados = [...valores].sort((a, b) => a - b);
  const mitad = Math.floor(ordenados.length / 2);
  if (ordenados.length % 2 === 1) {
    return ordenados[mitad] ?? 0;
  }
  return ((ordenados[mitad - 1] ?? 0) + (ordenados[mitad] ?? 0)) / 2;
}

export function GraficoMatriz({
  datosCultivo,
  departamentoFiltro,
  cuadranteFiltro,
}: PropsGraficoMatriz): React.JSX.Element {
  const cultivoActivo = usarTiendaRindex((s) => s.cultivoActivo);
  const municipioSeleccionado = usarTiendaRindex((s) => s.municipioSeleccionado);
  const seleccionarMunicipio = usarTiendaRindex((s) => s.seleccionarMunicipio);
  const [hoverMpio, setHoverMpio] = useState<MunicipioCultivoItem | null>(null);

  const { puntos, noMedibles, medianaRend, medianaCv, maxRend, maxCv, maxProd } = useMemo(() => {
    if (!datosCultivo) {
      return {
        puntos: [] as MunicipioCultivoItem[],
        noMedibles: 0,
        medianaRend: 0,
        medianaCv: 0,
        maxRend: 10,
        maxCv: 50,
        maxProd: 1,
      };
    }

    const elegibles = datosCultivo.municipios.filter(
      (m) =>
        m.elegible &&
        m.rendimiento_tha !== null &&
        coincideFiltrosMunicipio(m, departamentoFiltro, cuadranteFiltro),
    );
    const conCv = elegibles.filter(
      (m) =>
        m.cv_interanual_pct !== null &&
        m.priorizacion.cuadrante !== "estabilidad_no_medible",
    );
    const sinEstabilidad = elegibles.length - conCv.length;

    const rends = conCv.map((m) => m.rendimiento_tha ?? 0);
    const cvs = conCv.map((m) => m.cv_interanual_pct ?? 0);
    const prods = conCv.map((m) => m.produccion_t);

    return {
      puntos: conCv,
      noMedibles: sinEstabilidad,
      medianaRend: calcularMediana(rends),
      medianaCv: calcularMediana(cvs),
      maxRend: Math.max(1, ...rends) * 1.1,
      maxCv: Math.max(10, ...cvs) * 1.1,
      maxProd: Math.max(1, ...prods),
    };
  }, [datosCultivo, departamentoFiltro, cuadranteFiltro]);

  if (!datosCultivo) {
    return (
      <div className="panel-analitico">
        <p className="texto-secundario">Cargando matriz de decisión...</p>
      </div>
    );
  }

  const ancho = 560;
  const alto = 320;
  const mIzq = 52;
  const mDer = 22;
  const mSup = 24;
  const mInf = 42;
  const anchoUtil = ancho - mIzq - mDer;
  const altoUtil = alto - mSup - mInf;

  const coordX = (rend: number): number => mIzq + (rend / maxRend) * anchoUtil;
  const coordY = (cv: number): number => alto - mInf - (cv / maxCv) * altoUtil;
  const radio = (prod: number): number => 4 + Math.sqrt(prod / maxProd) * 11;

  const xMed = coordX(medianaRend);
  const yMed = coordY(medianaCv);

  return (
    <div className="matriz-bloque" data-testid="grafico-matriz">
      <div className="matriz-lienzo">
        <svg
          className="matriz-svg"
          viewBox={`0 0 ${ancho} ${alto}`}
          role="img"
          aria-label={`Matriz de decisión para ${cultivoActivo}: rendimiento medio frente a variabilidad interanual`}
        >
          {/* Cuadrantes de referencia */}
          <line x1={mIzq} x2={ancho - mDer} y1={alto - mInf} y2={alto - mInf} className="matriz-eje" />
          <line x1={mIzq} x2={mIzq} y1={mSup} y2={alto - mInf} className="matriz-eje" />

          {puntos.length > 0 ? (
            <>
              <line x1={xMed} x2={xMed} y1={mSup} y2={alto - mInf} className="matriz-mediana" />
              <line x1={mIzq} x2={ancho - mDer} y1={yMed} y2={yMed} className="matriz-mediana" />

              <text x={mIzq + 6} y={mSup + 12} className="matriz-rotulo-cuadrante">
                Intervención integral
              </text>
              <text
                x={ancho - mDer - 6}
                y={mSup + 12}
                textAnchor="end"
                className="matriz-rotulo-cuadrante"
              >
                Proteger
              </text>
              <text x={mIzq + 6} y={alto - mInf - 8} className="matriz-rotulo-cuadrante">
                Tecnificar
              </text>
              <text
                x={ancho - mDer - 6}
                y={alto - mInf - 8}
                textAnchor="end"
                className="matriz-rotulo-cuadrante"
              >
                Consolidar
              </text>
            </>
          ) : null}

          {puntos.map((m) => {
            const cx = coordX(m.rendimiento_tha ?? 0);
            const cy = coordY(m.cv_interanual_pct ?? 0);
            const r = radio(m.produccion_t);
            const cuad = m.priorizacion.cuadrante ?? "tecnificar";
            const color = COLOR_CUADRANTE[cuad] ?? "#17A398";
            const seleccionado = municipioSeleccionado === m.codigo;
            return (
              <circle
                key={m.codigo}
                cx={cx}
                cy={cy}
                r={r}
                fill={color}
                fillOpacity={seleccionado ? 0.96 : 0.72}
                stroke={seleccionado ? "var(--color-tinta)" : "#FFFFFF"}
                strokeWidth={seleccionado ? 2.2 : 1}
                className="matriz-punto"
                data-codigo={m.codigo}
                tabIndex={0}
                aria-label={`${m.nombre} (${m.departamento}): ${etiquetarCuadrante(cuad)}, ${formatearDecimal(m.rendimiento_tha ?? 0)} t/ha`}
                onMouseEnter={() => setHoverMpio(m)}
                onMouseLeave={() => setHoverMpio(null)}
                onFocus={() => setHoverMpio(m)}
                onBlur={() => setHoverMpio(null)}
                onClick={() => seleccionarMunicipio(m.codigo)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    seleccionarMunicipio(m.codigo);
                  }
                }}
              />
            );
          })}

          <text
            x={mIzq + anchoUtil / 2}
            y={alto - 8}
            textAnchor="middle"
            className="matriz-eje-titulo"
          >
            Rendimiento medio (t/ha) →
          </text>
          <text
            x={14}
            y={mSup + altoUtil / 2}
            textAnchor="middle"
            transform={`rotate(-90 14 ${mSup + altoUtil / 2})`}
            className="matriz-eje-titulo"
          >
            Variabilidad interanual (%) →
          </text>
        </svg>

        {hoverMpio ? (
          <div className="mapa-tooltip" role="status" aria-live="polite">
            <strong>{hoverMpio.nombre}</strong> ({hoverMpio.departamento})
            <br />
            <span className="cifra-tabular">
              {etiquetarCuadrante(hoverMpio.priorizacion.cuadrante)} ·{" "}
              {formatearDecimal(hoverMpio.rendimiento_tha ?? 0)} t/ha · variabilidad{" "}
              {formatearPorcentaje(hoverMpio.cv_interanual_pct ?? 0)}
            </span>
          </div>
        ) : null}
      </div>

      <div className="mapa-leyenda" data-testid="mapa-leyenda">
        {(
          [
            ["consolidar", "Consolidar"],
            ["proteger", "Proteger"],
            ["tecnificar", "Tecnificar"],
            ["intervencion_integral", "Intervención integral"],
          ] as const
        ).map(([clave, texto]) => (
          <span key={clave} className="leyenda-escala">
            <span
              className="leyenda-bloque"
              style={{ backgroundColor: COLOR_CUADRANTE[clave] }}
            />
            {texto}
          </span>
        ))}
        {noMedibles > 0 ? (
          <span className="leyenda-escala cifra-tabular">
            Estabilidad no medible excluidos del gráfico: {formatearEntero(noMedibles)}
          </span>
        ) : null}
      </div>
    </div>
  );
}
