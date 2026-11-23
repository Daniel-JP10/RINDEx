/* Simulador interactivo de escenarios con rangos p10-p50-p90 y sin doble conteo */

import { useMemo, useState } from "react";
import { usarTiendaRindex } from "../estado/tiendaRindex.ts";
import type { ContratoEscenarios } from "../tipos/generados/escenarios.ts";
import { formatearEntero, formatearPorcentaje } from "../utilidades/formato.ts";

interface PropsSimuladorEscenarios {
  escenarios: ContratoEscenarios | null;
}

interface FilaRango {
  id: string;
  titulo: string;
  subtitulo: string;
  p10: number;
  p50: number;
  p90: number;
  punteado: boolean;
  activo: boolean;
}

export function SimuladorEscenarios({
  escenarios,
}: PropsSimuladorEscenarios): React.JSX.Element {
  const cultivoActivo = usarTiendaRindex((s) => s.cultivoActivo);
  const municipioSeleccionado = usarTiendaRindex((s) => s.municipioSeleccionado);

  const [fraccionS1Pct, setFraccionS1Pct] = useState<number>(100);
  const [incluirS2, setIncluirS2] = useState<boolean>(true);
  const [incluirS3, setIncluirS3] = useState<boolean>(true);

  const esYuca = cultivoActivo === "Yuca";

  const resumen = useMemo(() => {
    if (!escenarios) {
      return null;
    }

    const mpioEsc = municipioSeleccionado
      ? escenarios.municipios.find(
          (m) => m.codigo === municipioSeleccionado && m.cultivo === cultivoActivo,
        ) ?? null
      : null;

    const regEsc =
      escenarios.totales_regionales.find((r) => r.cultivo === cultivoActivo) ?? null;

    if (!regEsc) {
      return null;
    }

    const fraccion = fraccionS1Pct / 100;
    const base = mpioEsc ?? regEsc;

    /* Linealidad exacta de cierre de brecha: escalar por x >= 0 escala todos los cuantiles */
    const s1 = {
      p10: Math.round(base.s1_p10_t * fraccion),
      p50: Math.round(base.s1_p50_t * fraccion),
      p90: Math.round(base.s1_p90_t * fraccion),
    };

    const s2Disponible = !esYuca && base.s2_p90_t > 0;
    const s2Activo = s2Disponible && incluirS2;
    const s2 = s2Activo
      ? { p10: base.s2_p10_t, p50: base.s2_p50_t, p90: base.s2_p90_t }
      : { p10: 0, p50: 0, p90: 0 };

    const s3Disponible = !esYuca && base.s3_p90_t > 0;
    const s3Activo = s3Disponible && incluirS3;
    const s3 = s3Activo
      ? { p10: base.s3_p10_t, p50: base.s3_p50_t, p90: base.s3_p90_t }
      : { p10: 0, p50: 0, p90: 0 };

    /* Regla de rigor: a 100 % con las palancas activas usar la distribucion combinada precalculada */
    let combinado: { p10: number; p50: number; p90: number; esExactoPrecalculado: boolean };
    if (fraccionS1Pct === 100 && s2Activo === s2Disponible && s3Activo === s3Disponible) {
      combinado = {
        p10: base.combinado_p10_t,
        p50: base.combinado_p50_t,
        p90: base.combinado_p90_t,
        esExactoPrecalculado: true,
      };
    } else if (!s2Activo && !s3Activo) {
      combinado = { ...s1, esExactoPrecalculado: true };
    } else if (fraccionS1Pct === 0 && s2Activo && !s3Activo) {
      combinado = { ...s2, esExactoPrecalculado: true };
    } else if (fraccionS1Pct === 0 && !s2Activo && s3Activo) {
      combinado = { ...s3, esExactoPrecalculado: true };
    } else {
      combinado = {
        p10: Math.max(s1.p10, s2.p10) + s3.p10,
        p50: Math.max(s1.p50, s2.p50) + s3.p50,
        p90: Math.max(s1.p90, s2.p90) + s3.p90,
        esExactoPrecalculado: false,
      };
    }

    const s2Extrapolado = mpioEsc ? mpioEsc.extrapolado : regEsc.s2_pct_extrapolado > 0;
    const pctS2Extrapolado = mpioEsc
      ? mpioEsc.extrapolado
        ? 100
        : 0
      : regEsc.s2_pct_extrapolado;

    const filas: FilaRango[] = [
      {
        id: "cierre",
        titulo: `Cierre de brecha al ${fraccionS1Pct} %`,
        subtitulo: "Hacia el desempeño de los mejores municipios del mismo departamento",
        p10: s1.p10,
        p50: s1.p50,
        p90: s1.p90,
        punteado: false,
        activo: fraccionS1Pct > 0,
      },
      {
        id: "tecnificacion",
        titulo: "Tecnificación del sistema productivo",
        subtitulo: esYuca
          ? "No aplica en yuca por estructura del registro"
          : s2Extrapolado
            ? `Incluye ${formatearPorcentaje(pctS2Extrapolado)} extrapolado con razón regional`
            : "Calculado con ambos sistemas observados en el mismo municipio",
        p10: s2.p10,
        p50: s2.p50,
        p90: s2.p90,
        punteado: s2Extrapolado,
        activo: s2Activo,
      },
      {
        id: "no-cosechada",
        titulo: "Recuperación de área no cosechada",
        subtitulo: esYuca
          ? "Excluida en yuca por ciclo largo del cultivo"
          : "Indicativo (cambio de reporte desde 2022)",
        p10: s3.p10,
        p50: s3.p50,
        p90: s3.p90,
        punteado: true,
        activo: s3Activo,
      },
    ];

    const maximoGrafico = Math.max(
      1,
      combinado.p90,
      ...filas.map((f) => f.p90),
    );

    return {
      alcanceTexto: mpioEsc
        ? `${mpioEsc.nombre} (${mpioEsc.departamento})`
        : `Total regional Caribe · ${regEsc.municipios_elegibles} municipios elegibles`,
      produccionBase: mpioEsc
        ? mpioEsc.produccion_media_anual_t
        : regEsc.produccion_anual_media_t,
      combinado,
      filas,
      maximoGrafico,
      s2Disponible,
      s3Disponible,
    };
  }, [escenarios, cultivoActivo, municipioSeleccionado, fraccionS1Pct, incluirS2, incluirS3, esYuca]);

  if (!escenarios || !resumen) {
    return (
      <div className="panel-analitico">
        <p className="texto-secundario">Cargando escenarios de simulación...</p>
      </div>
    );
  }

  const pctSobreBase =
    resumen.produccionBase > 0
      ? (resumen.combinado.p50 / resumen.produccionBase) * 100
      : 0;

  return (
    <div className="simulador-bloque" data-testid="simulador-escenarios">
      <div className="simulador-controles">
        <label className="simulador-deslizador-grupo">
          <div className="simulador-deslizador-cabecera">
            <span>Cierre de brecha intradepartamental</span>
            <strong className="cifra-tabular" data-testid="simulador-pct-valor">
              {fraccionS1Pct} %
            </strong>
          </div>
          <input
            type="range"
            min={0}
            max={100}
            step={10}
            value={fraccionS1Pct}
            aria-label="Porcentaje de cierre de brecha"
            data-testid="simulador-deslizador"
            onChange={(e) => setFraccionS1Pct(Number(e.target.value))}
          />
        </label>

        <div className="simulador-palancas">
          <label className="simulador-check">
            <input
              type="checkbox"
              checked={!esYuca && resumen.s2Disponible && incluirS2}
              disabled={!resumen.s2Disponible}
              onChange={(e) => setIncluirS2(e.target.checked)}
            />
            <span>Tecnificación</span>
          </label>
          <label className="simulador-check">
            <input
              type="checkbox"
              checked={!esYuca && resumen.s3Disponible && incluirS3}
              disabled={!resumen.s3Disponible}
              onChange={(e) => setIncluirS3(e.target.checked)}
            />
            <span>Área no cosechada (indicativo)</span>
          </label>
        </div>
      </div>

      <div className="simulador-resumen-combinado">
        <div>
          <span className="simulador-alcance">{resumen.alcanceTexto}</span>
          <div className="simulador-rango-principal cifra-tabular" data-testid="simulador-rango-combinado">
            {formatearEntero(resumen.combinado.p10)} a{" "}
            {formatearEntero(resumen.combinado.p90)} t/año
          </div>
          <span className="texto-secundario cifra-tabular">
            Mediana {formatearEntero(resumen.combinado.p50)} t/año (
            {formatearPorcentaje(pctSobreBase)} de la producción anual media)
          </span>
        </div>
        {!resumen.combinado.esExactoPrecalculado ? (
          <span className="simulador-nota-parcial">
            Cota combinada sin doble conteo para configuración parcial de palancas.
          </span>
        ) : null}
      </div>

      <div className="simulador-barras">
        {resumen.filas.map((fila) => {
          const izq = (fila.p10 / resumen.maximoGrafico) * 100;
          const anchoBarra = Math.max(2, ((fila.p90 - fila.p10) / resumen.maximoGrafico) * 100);
          const posP50 = (fila.p50 / resumen.maximoGrafico) * 100;
          return (
            <div
              key={fila.id}
              className={fila.activo ? "simulador-fila" : "simulador-fila simulador-fila-inactiva"}
            >
              <div className="simulador-fila-texto">
                <strong>{fila.titulo}</strong>
                <span className="cifra-tabular">
                  {fila.activo
                    ? `${formatearEntero(fila.p10)} a ${formatearEntero(fila.p90)} t/año`
                    : "Inactivo"}
                </span>
              </div>
              <span className="simulador-fila-sub">{fila.subtitulo}</span>
              <div className="simulador-pista" aria-hidden="true">
                {fila.activo && fila.p90 > 0 ? (
                  <>
                    <div
                      className={
                        fila.punteado
                          ? "simulador-barra simulador-barra-punteada"
                          : "simulador-barra"
                      }
                      style={{ left: `${izq}%`, width: `${anchoBarra}%` }}
                    />
                    <span className="simulador-mediana-marca" style={{ left: `${posP50}%` }} />
                  </>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>

      <div className="mapa-leyenda" data-testid="mapa-leyenda">
        <span className="leyenda-escala">
          <span className="leyenda-bloque leyenda-sim-solida" />
          Respaldo observado en municipios pares
        </span>
        <span className="leyenda-escala">
          <span className="leyenda-bloque leyenda-sim-punteada" />
          Borde punteado: componente extrapolado o indicativo
        </span>
      </div>
    </div>
  );
}
