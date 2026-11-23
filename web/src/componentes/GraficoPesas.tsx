/* Grafico de pesas (dumbbell) comparando rendimiento por sistema productivo */

import { useMemo } from "react";
import type { ContratoHallazgos } from "../tipos/generados/hallazgos.ts";
import type { ContratoSistemas } from "../tipos/generados/sistemas.ts";
import {
  etiquetarSistema,
  formatearDecimal,
  formatearMultiplicador,
} from "../utilidades/formato.ts";

interface PropsGraficoPesas {
  sistemas: ContratoSistemas | null;
  hallazgos: ContratoHallazgos | null;
}

interface FilaMaiz {
  departamento: string;
  tradicional: number;
  tecnificado: number;
}

interface FilaArroz {
  departamento: string;
  secanoManual: number | null;
  secanoMecanizado: number | null;
  riego: number | null;
}

export function GraficoPesas({
  sistemas,
  hallazgos,
}: PropsGraficoPesas): React.JSX.Element {
  const razones = useMemo(() => {
    const buscar = (id: string): number | null => {
      const t = hallazgos?.tarjetas.find((x) => x.id === id);
      return t ? t.cifra : null;
    };
    return {
      maiz: buscar("h2_maiz_tecnificado"),
      arrozRiegoManual: buscar("h3_arroz_riego_vs_manual"),
      arrozMecManual: buscar("h3_arroz_mecanizado_vs_manual"),
      arrozRiegoMecN:
        hallazgos?.tarjetas.find((x) => x.id === "h3_arroz_riego_vs_mecanizado")?.n ?? 5,
    };
  }, [hallazgos]);

  const filasMaiz = useMemo<FilaMaiz[]>(() => {
    if (!sistemas) {
      return [];
    }
    const lista: FilaMaiz[] = [];
    for (const d of sistemas.departamentos) {
      if (d.cultivo !== "Maíz") {
        continue;
      }
      const trad = d.sistemas["tradicional"]?.rendimiento_tha ?? null;
      const tec = d.sistemas["tecnificado"]?.rendimiento_tha ?? null;
      if (trad !== null && tec !== null) {
        lista.push({
          departamento: d.departamento,
          tradicional: trad,
          tecnificado: tec,
        });
      }
    }
    return lista.sort((a, b) => b.tecnificado - a.tecnificado);
  }, [sistemas]);

  const filasArroz = useMemo<FilaArroz[]>(() => {
    if (!sistemas) {
      return [];
    }
    const lista: FilaArroz[] = [];
    for (const d of sistemas.departamentos) {
      if (d.cultivo !== "Arroz") {
        continue;
      }
      const man = d.sistemas["secano_manual"]?.rendimiento_tha ?? null;
      const mec = d.sistemas["secano_mecanizado"]?.rendimiento_tha ?? null;
      const rie = d.sistemas["riego"]?.rendimiento_tha ?? null;
      const presentes = [man, mec, rie].filter((v) => v !== null).length;
      if (presentes >= 2) {
        lista.push({
          departamento: d.departamento,
          secanoManual: man,
          secanoMecanizado: mec,
          riego: rie,
        });
      }
    }
    return lista.sort(
      (a, b) =>
        Math.max(b.riego ?? 0, b.secanoMecanizado ?? 0, b.secanoManual ?? 0) -
        Math.max(a.riego ?? 0, a.secanoMecanizado ?? 0, a.secanoManual ?? 0),
    );
  }, [sistemas]);

  if (!sistemas) {
    return (
      <div className="pesas-contenedor">
        <p className="texto-secundario">Cargando comparación entre sistemas productivos...</p>
      </div>
    );
  }

  const maxMaiz = Math.max(
    5.5,
    ...filasMaiz.flatMap((f) => [f.tradicional, f.tecnificado]),
  );
  const maxArroz = Math.max(
    7.5,
    ...filasArroz.flatMap((f) => [
      f.secanoManual ?? 0,
      f.secanoMecanizado ?? 0,
      f.riego ?? 0,
    ]),
  );

  const anchoSvg = 540;
  const margenIzq = 104;
  const margenDer = 42;
  const anchoUtil = anchoSvg - margenIzq - margenDer;
  const altoFila = 28;

  const xMaiz = (v: number): number => margenIzq + (v / maxMaiz) * anchoUtil;
  const xArroz = (v: number): number => margenIzq + (v / maxArroz) * anchoUtil;

  const altoSvgMaiz = Math.max(120, filasMaiz.length * altoFila + 28);
  const altoSvgArroz = Math.max(120, filasArroz.length * altoFila + 28);

  return (
    <div className="pesas-contenedor" data-testid="grafico-pesas">
      <div className="pesas-bloque">
        <div className="pesas-cabecera">
          <div>
            <h3 className="pesas-titulo">Maíz: tradicional frente a tecnificado</h3>
            <span className="pesas-subtitulo">Rendimiento departamental en t/ha</span>
          </div>
          {razones.maiz !== null ? (
            <span className="pesas-multiplicador pesas-multiplicador-maiz cifra-tabular">
              {formatearMultiplicador(razones.maiz)}
            </span>
          ) : null}
        </div>

        <svg
          className="pesas-svg"
          viewBox={`0 0 ${anchoSvg} ${altoSvgMaiz}`}
          role="img"
          aria-label="Gráfico de pesas comparando rendimiento de maíz tradicional y tecnificado por departamento"
        >
          {[0, 2, 4].map((marca) => (
            <g key={`m-${marca}`}>
              <line
                x1={xMaiz(marca)}
                x2={xMaiz(marca)}
                y1={8}
                y2={altoSvgMaiz - 18}
                className="pesas-guia"
              />
              <text
                x={xMaiz(marca)}
                y={altoSvgMaiz - 4}
                textAnchor="middle"
                className="pesas-eje-texto"
              >
                {marca} t/ha
              </text>
            </g>
          ))}

          {filasMaiz.map((f, idx) => {
            const y = 20 + idx * altoFila;
            const x1 = xMaiz(f.tradicional);
            const x2 = xMaiz(f.tecnificado);
            return (
              <g key={f.departamento}>
                <text x={margenIzq - 10} y={y + 4} textAnchor="end" className="pesas-depto">
                  {f.departamento}
                </text>
                <line x1={x1} x2={x2} y1={y} y2={y} className="pesas-barra pesas-barra-maiz" />
                <circle cx={x1} cy={y} r={5.5} className="pesas-punto-base" />
                <circle cx={x2} cy={y} r={6.5} className="pesas-punto-maiz" />
                <text x={x2 + 10} y={y + 4} className="pesas-valor cifra-tabular">
                  {formatearDecimal(f.tecnificado, 1)}
                </text>
              </g>
            );
          })}
        </svg>

        <div className="pesas-leyenda">
          <span className="pesas-leyenda-item">
            <span className="pesas-muestra pesas-muestra-base" aria-hidden="true" />
            {etiquetarSistema("tradicional")}
          </span>
          <span className="pesas-leyenda-item">
            <span className="pesas-muestra pesas-muestra-maiz" aria-hidden="true" />
            {etiquetarSistema("tecnificado")}
          </span>
        </div>
      </div>

      <div className="pesas-bloque">
        <div className="pesas-cabecera">
          <div>
            <h3 className="pesas-titulo">Arroz: manual, mecanizado y riego</h3>
            <span className="pesas-subtitulo">Rendimiento departamental en t/ha</span>
          </div>
          <div className="pesas-multiplicadores-grupo">
            {razones.arrozRiegoManual !== null ? (
              <span
                className="pesas-multiplicador pesas-multiplicador-arroz cifra-tabular"
                title="Razón riego frente a secano manual"
              >
                {formatearMultiplicador(razones.arrozRiegoManual)}
              </span>
            ) : null}
            {razones.arrozMecManual !== null ? (
              <span
                className="pesas-multiplicador pesas-multiplicador-arroz-sec cifra-tabular"
                title="Razón secano mecanizado frente a secano manual"
              >
                {formatearMultiplicador(razones.arrozMecManual)}
              </span>
            ) : null}
          </div>
        </div>

        <svg
          className="pesas-svg"
          viewBox={`0 0 ${anchoSvg} ${altoSvgArroz}`}
          role="img"
          aria-label="Gráfico de pesas comparando rendimiento de arroz en secano manual, mecanizado y riego por departamento"
        >
          {[0, 2, 4, 6].map((marca) => (
            <g key={`a-${marca}`}>
              <line
                x1={xArroz(marca)}
                x2={xArroz(marca)}
                y1={8}
                y2={altoSvgArroz - 18}
                className="pesas-guia"
              />
              <text
                x={xArroz(marca)}
                y={altoSvgArroz - 4}
                textAnchor="middle"
                className="pesas-eje-texto"
              >
                {marca} t/ha
              </text>
            </g>
          ))}

          {filasArroz.map((f, idx) => {
            const y = 20 + idx * altoFila;
            const vals = [f.secanoManual, f.secanoMecanizado, f.riego].filter(
              (v): v is number => v !== null,
            );
            const minV = Math.min(...vals);
            const maxV = Math.max(...vals);
            return (
              <g key={f.departamento}>
                <text x={margenIzq - 10} y={y + 4} textAnchor="end" className="pesas-depto">
                  {f.departamento}
                </text>
                <line
                  x1={xArroz(minV)}
                  x2={xArroz(maxV)}
                  y1={y}
                  y2={y}
                  className="pesas-barra pesas-barra-arroz"
                />
                {f.secanoManual !== null ? (
                  <circle cx={xArroz(f.secanoManual)} cy={y} r={5.5} className="pesas-punto-base" />
                ) : null}
                {f.secanoMecanizado !== null ? (
                  <circle
                    cx={xArroz(f.secanoMecanizado)}
                    cy={y}
                    r={6}
                    className="pesas-punto-arroz-mec"
                  />
                ) : null}
                {f.riego !== null ? (
                  <circle cx={xArroz(f.riego)} cy={y} r={6.5} className="pesas-punto-arroz-riego" />
                ) : null}
                <text x={xArroz(maxV) + 10} y={y + 4} className="pesas-valor cifra-tabular">
                  {formatearDecimal(maxV, 1)}
                </text>
              </g>
            );
          })}
        </svg>

        <div className="pesas-leyenda">
          <span className="pesas-leyenda-item">
            <span className="pesas-muestra pesas-muestra-base" aria-hidden="true" />
            {etiquetarSistema("secano_manual")}
          </span>
          <span className="pesas-leyenda-item">
            <span className="pesas-muestra pesas-muestra-arroz-mec" aria-hidden="true" />
            {etiquetarSistema("secano_mecanizado")}
          </span>
          <span className="pesas-leyenda-item">
            <span className="pesas-muestra pesas-muestra-arroz-riego" aria-hidden="true" />
            {etiquetarSistema("riego")}
          </span>
        </div>

        <p className="pesas-nota">
          La comparación directa entre riego y secano mecanizado cuenta solo con{" "}
          {razones.arrozRiegoMecN} municipios comparables, por debajo de la regla de muestra mínima.
        </p>
      </div>
    </div>
  );
}
