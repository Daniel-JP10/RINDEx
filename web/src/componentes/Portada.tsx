import { useEffect, useMemo, useState } from "react";
import { geoMercator, geoPath } from "d3-geo";
import type { FeatureCollection, Geometry } from "geojson";
import { feature, merge } from "topojson-client";
import {
  cargarHallazgos,
  cargarSistemas,
  cargarTopoJsonCaribe,
  type ContratoTopoJsonCaribe,
} from "../datos/cargador.ts";
import { usarTiendaRindex, type CultivoClave } from "../estado/tiendaRindex.ts";
import type { ContratoHallazgos } from "../tipos/generados/hallazgos.ts";
import type { ContratoSistemas } from "../tipos/generados/sistemas.ts";
import { formatearEntero } from "../utilidades/formato.ts";
import { LogoRindex } from "./LogoRindex.tsx";

interface PropiedadGeo {
  codigo: string;
  nombre: string;
  departamento: string;
}

export interface PropsPortada {
  hallazgosIniciales?: ContratoHallazgos;
  sistemasIniciales?: ContratoSistemas;
  topoJsonInicial?: ContratoTopoJsonCaribe;
}

const COLOR_CULTIVO_CSS: Record<CultivoClave, string> = {
  "Maíz": "var(--color-maiz)",
  "Yuca": "var(--color-yuca)",
  "Arroz": "var(--color-arroz)",
};

export function Portada({
  hallazgosIniciales,
  sistemasIniciales,
  topoJsonInicial,
}: PropsPortada): React.JSX.Element {
  const modo = usarTiendaRindex((s) => s.modo);
  const [hallazgosCargados, setHallazgosCargados] = useState<ContratoHallazgos | null>(null);
  const [sistemasCargados, setSistemasCargados] = useState<ContratoSistemas | null>(null);
  const [topoJsonCargado, setTopoJsonCargado] = useState<ContratoTopoJsonCaribe | null>(null);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);

  const hallazgos = hallazgosIniciales ?? hallazgosCargados;
  const sistemas = sistemasIniciales ?? sistemasCargados;
  const topoJson = topoJsonInicial ?? topoJsonCargado;

  useEffect(() => {
    let cancelado = false;
    if (hallazgos && sistemas && topoJson) {
      return undefined;
    }
    Promise.all([
      hallazgos ? Promise.resolve(hallazgos) : cargarHallazgos(),
      sistemas ? Promise.resolve(sistemas) : cargarSistemas(),
      topoJson ? Promise.resolve(topoJson) : cargarTopoJsonCaribe(),
    ])
      .then(([h, s, t]) => {
        if (!cancelado) {
          setHallazgosCargados(h);
          setSistemasCargados(s);
          setTopoJsonCargado(t);
        }
      })
      .catch((err: unknown) => {
        if (!cancelado) {
          setErrorCarga(
            err instanceof Error ? err.message : "No fue posible cargar la portada.",
          );
        }
      });
    return () => {
      cancelado = true;
    };
  }, [hallazgos, sistemas, topoJson]);

  const rangoTotal = useMemo(() => {
    const t = hallazgos?.tarjetas.find((x) => x.id === "combinado_region_total");
    if (!t || !t.intervalo || t.intervalo.length !== 2) {
      return null;
    }
    return {
      p10: t.intervalo[0] ?? 0,
      p50: t.cifra,
      p90: t.intervalo[1] ?? 0,
    };
  }, [hallazgos]);

  const rangoEvidenciaAlta = useMemo(() => {
    const t = hallazgos?.tarjetas.find((x) => x.id === "combinado_region_evidencia_alta");
    if (!t || !t.intervalo || t.intervalo.length !== 2) {
      return null;
    }
    return {
      p10: t.intervalo[0] ?? 0,
      p50: t.cifra,
      p90: t.intervalo[1] ?? 0,
    };
  }, [hallazgos]);

  const cultivosDominantes = useMemo(() => {
    const mapa = new Map<string, CultivoClave>();
    if (!sistemas) {
      return mapa;
    }
    const porMunicipio = new Map<string, Map<CultivoClave, number>>();
    for (const item of sistemas.municipios) {
      const cult = item.cultivo as CultivoClave;
      let totalProd = 0;
      for (const sis of Object.values(item.sistemas)) {
        if (sis) {
          totalProd += sis.produccion_t;
        }
      }
      const acum = porMunicipio.get(item.codigo) ?? new Map<CultivoClave, number>();
      acum.set(cult, (acum.get(cult) ?? 0) + totalProd);
      porMunicipio.set(item.codigo, acum);
    }
    for (const [codigo, totales] of porMunicipio.entries()) {
      let mejorCultivo: CultivoClave = "Maíz";
      let mejorProd = -1;
      for (const [cult, prod] of totales.entries()) {
        if (prod > mejorProd) {
          mejorProd = prod;
          mejorCultivo = cult;
        }
      }
      mapa.set(codigo, mejorCultivo);
    }
    return mapa;
  }, [sistemas]);

  const { trazosMunicipios, contornoRegional } = useMemo(() => {
    if (!topoJson) {
      return { trazosMunicipios: [], contornoRegional: "" };
    }
    const colMpios = feature(
      topoJson as never,
      topoJson.objects.municipios as never,
    ) as unknown as FeatureCollection<Geometry, PropiedadGeo>;

    const proyeccion = geoMercator().fitExtent(
      [
        [24, 24],
        [736, 596],
      ],
      colMpios,
    );
    const generadorRuta = geoPath(proyeccion).digits(1);

    const mpios = colMpios.features.map((feat) => {
      const codigo = feat.properties.codigo;
      const dom = cultivosDominantes.get(codigo);
      return {
        codigo,
        ruta: generadorRuta(feat) ?? "",
        relleno: dom ? COLOR_CULTIVO_CSS[dom] : "#3C5447",
      };
    });

    let contorno = "";
    try {
      const fusion = merge(
        topoJson as never,
        topoJson.objects.municipios.geometries as never,
      );
      contorno = generadorRuta(fusion as never) ?? "";
    } catch {
      contorno = "";
    }

    return { trazosMunicipios: mpios, contornoRegional: contorno };
  }, [topoJson, cultivosDominantes]);

  return (
    <section id="portada" className="portada" aria-labelledby="titulo-portada">
      <div className="portada-rejilla">
        <div className="portada-columna-texto" data-testid="portada-bloque-texto">
          <div className="portada-marca-linea">
            <LogoRindex sobreOscuro />
            <span className="portada-etiqueta">Región Caribe · 2019–2025</span>
          </div>

          <h1 id="titulo-portada" className="portada-titulo">
            Dónde está la cosecha que falta
          </h1>

          {errorCarga ? (
            <p className="estado-error" role="alert">
              {errorCarga}
            </p>
          ) : rangoTotal ? (
            <>
              <p className="portada-gancho" data-testid="frase-gancho-portada">
                Sin sembrar una hectárea más, el Caribe podría cosechar entre{" "}
                <strong className="portada-cifra-destacada cifra-tabular">
                  {formatearEntero(rangoTotal.p10)}
                </strong>{" "}
                y{" "}
                <strong className="portada-cifra-destacada cifra-tabular">
                  {formatearEntero(rangoTotal.p90)}
                </strong>{" "}
                toneladas más al año.
              </p>

              {rangoEvidenciaAlta ? (
                <p className="portada-evidencia-alta" data-testid="frase-evidencia-alta">
                  Solo en arroz y maíz, los dos cultivos con evidencia alta, el potencial está
                  entre{" "}
                  <strong className="cifra-tabular">
                    {formatearEntero(rangoEvidenciaAlta.p10)}
                  </strong>{" "}
                  y{" "}
                  <strong className="cifra-tabular">
                    {formatearEntero(rangoEvidenciaAlta.p90)}
                  </strong>{" "}
                  toneladas al año.
                </p>
              ) : null}

              <p className="portada-apoyo">
                {modo === "decisor" ? (
                  "Siete años de datos oficiales de 195 municipios cuentan dónde está esa cosecha y quién puede recuperarla primero."
                ) : (
                  <>
                    Percentiles del 10 al 90 obtenidos por suma réplica a réplica sobre 5.000
                    réplicas de bootstrap de dos niveles sin doble conteo entre brecha,
                    tecnificación y área no cosechada.{" "}
                    <a href="#metodologia" className="enlace-oscuro">
                      Ver metodología
                    </a>
                    .
                  </>
                )}
              </p>
            </>
          ) : (
            <p className="portada-gancho">Cargando estimaciones regionales...</p>
          )}

          <a href="#narrativa-caribe" className="portada-indicador-scroll">
            <span>Desliza para recorrer la historia</span>
            <span aria-hidden="true">↓</span>
          </a>
        </div>

        <div className="portada-columna-mapa" data-testid="portada-bloque-mapa">
          {trazosMunicipios.length > 0 ? (
            <svg
              className="portada-mapa-svg"
              viewBox="0 0 760 620"
              role="img"
              aria-label="Mapa del Caribe colombiano coloreado por cultivo dominante en cada municipio"
            >
              <defs>
                <filter
                  id="brillo-caribe-portada"
                  x="-12%"
                  y="-12%"
                  width="124%"
                  height="124%"
                >
                  <feDropShadow
                    dx="0"
                    dy="0"
                    stdDeviation="7"
                    floodColor="#34D27B"
                    floodOpacity="0.34"
                  />
                </filter>
              </defs>

              {contornoRegional ? (
                <path
                  d={contornoRegional}
                  fill="#0B2E1F"
                  stroke="#34D27B"
                  strokeOpacity="0.45"
                  strokeWidth="2"
                  filter="url(#brillo-caribe-portada)"
                />
              ) : null}

              <g>
                {trazosMunicipios.map((t) => (
                  <path
                    key={`relleno-${t.codigo}`}
                    d={t.ruta}
                    fill={t.relleno}
                    stroke="none"
                  />
                ))}
              </g>

              <g>
                {trazosMunicipios.map((t) => (
                  <path
                    key={`trazo-${t.codigo}`}
                    d={t.ruta}
                    fill="none"
                    className="portada-limite-mpio"
                    pathLength={1}
                  />
                ))}
              </g>
            </svg>
          ) : null}

          <div
            className="portada-leyenda-dominante"
            aria-label="Cultivo dominante por tonelaje en el mapa de portada"
          >
            <span className="portada-item-leyenda">
              <span
                className="pildora-punto"
                style={{ backgroundColor: "var(--color-maiz)" }}
                aria-hidden="true"
              />
              Maíz dominante
            </span>
            <span className="portada-item-leyenda">
              <span
                className="pildora-punto"
                style={{ backgroundColor: "var(--color-yuca)" }}
                aria-hidden="true"
              />
              Yuca dominante
            </span>
            <span className="portada-item-leyenda">
              <span
                className="pildora-punto"
                style={{ backgroundColor: "var(--color-arroz)" }}
                aria-hidden="true"
              />
              Arroz dominante
            </span>
          </div>
        </div>
      </div>

      <div className="portada-degradado-salida" aria-hidden="true" />
    </section>
  );
}
