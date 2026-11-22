import { useEffect, useMemo, useState } from "react";
import { geoMercator, geoPath } from "d3-geo";
import type { FeatureCollection, Geometry } from "geojson";
import { feature } from "topojson-client";
import {
  cargarHallazgos,
  cargarSistemas,
  cargarTopoJsonCaribe,
  type ContratoTopoJsonCaribe,
} from "../datos/cargador.ts";
import { usarTiendaRindex, type CultivoClave } from "../estado/tiendaRindex.ts";
import type { ContratoHallazgos } from "../tipos/generados/hallazgos.ts";
import type { ContratoSistemas } from "../tipos/generados/sistemas.ts";
import { formatearEntero, formatearRangoToneladas } from "../utilidades/formato.ts";

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

const IDS_COMBINADOS: readonly string[] = [
  "combinado_arroz",
  "combinado_maiz",
  "combinado_yuca",
];

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

  const rangoCombinado = useMemo(() => {
    if (!hallazgos) {
      return null;
    }
    let sumaP10 = 0;
    let sumaP50 = 0;
    let sumaP90 = 0;
    let tarjetasEncontradas = 0;

    for (const id of IDS_COMBINADOS) {
      const tarjeta = hallazgos.tarjetas.find((t) => t.id === id);
      if (tarjeta && tarjeta.intervalo && tarjeta.intervalo.length === 2) {
        sumaP10 += tarjeta.intervalo[0] ?? 0;
        sumaP50 += tarjeta.cifra;
        sumaP90 += tarjeta.intervalo[1] ?? 0;
        tarjetasEncontradas += 1;
      }
    }

    if (tarjetasEncontradas === 0) {
      return null;
    }
    return { p10: sumaP10, p50: sumaP50, p90: sumaP90 };
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

  const trazosFondo = useMemo(() => {
    if (!topoJson) {
      return [];
    }
    const colMpios = feature(
      topoJson as never,
      topoJson.objects.municipios as never,
    ) as unknown as FeatureCollection<Geometry, PropiedadGeo>;

    const proyeccion = geoMercator().fitExtent(
      [
        [16, 16],
        [784, 584],
      ],
      colMpios,
    );
    const generadorRuta = geoPath(proyeccion);

    return colMpios.features.map((feat) => {
      const codigo = feat.properties.codigo;
      const dom = cultivosDominantes.get(codigo);
      return {
        codigo,
        ruta: generadorRuta(feat) ?? "",
        relleno: dom ? COLOR_CULTIVO_CSS[dom] : "var(--color-contexto-gris)",
      };
    });
  }, [topoJson, cultivosDominantes]);

  return (
    <section id="portada" className="portada" aria-labelledby="titulo-portada">
      <div className="portada-mapa-fondo" aria-hidden="true">
        {trazosFondo.length > 0 ? (
          <svg viewBox="0 0 800 600" role="presentation">
            {trazosFondo.map((t) => (
              <path
                key={t.codigo}
                d={t.ruta}
                fill={t.relleno}
                stroke="var(--color-fondo)"
                strokeWidth="0.6"
              />
            ))}
          </svg>
        ) : null}
      </div>

      <div className="portada-contenido">
        <article className="portada-tarjeta">
          <span className="paso-etiqueta-id">
            Región Caribe 2019–2025 · Maíz, Yuca y Arroz
          </span>
          <h1 id="titulo-portada" className="portada-subtitulo">
            Dónde está la cosecha que falta
          </h1>

          {errorCarga ? (
            <p className="estado-error" role="alert">
              {errorCarga}
            </p>
          ) : rangoCombinado ? (
            <>
              <p className="portada-gancho" data-testid="frase-gancho-portada">
                Sin sembrar una hectárea más, la región podría sumar entre{" "}
                <strong className="cifra-tabular">
                  {formatearRangoToneladas(rangoCombinado.p10, rangoCombinado.p90)}
                </strong>{" "}
                (mediana{" "}
                <span className="cifra-tabular">
                  {formatearEntero(rangoCombinado.p50)} t/año
                </span>
                ) cerrando brechas de rendimiento y recuperando área no cosechada.
              </p>
              <p className="portada-nota">
                {modo === "decisor"
                  ? "Rango regional calculado sumando los escenarios combinados sin doble conteo de arroz, maíz y yuca publicados en hallazgos.json."
                  : "Estimación bootstrap (5.000 réplicas, rango p10 a p90) obtenida mediante max(S1, S2) + S3 sobre municipios elegibles en hallazgos.json."}
              </p>
            </>
          ) : (
            <p className="portada-gancho">
              Cargando estimaciones regionales desde hallazgos.json...
            </p>
          )}

          <div
            className="portada-leyenda-dominante"
            aria-label="Cultivo dominante por tonelaje en el mapa de fondo"
          >
            <span className="portada-item-leyenda">
              <span
                className="pildora-punto"
                style={{ backgroundColor: "var(--color-maiz)" }}
                aria-hidden="true"
              />
              Maíz dominante (t)
            </span>
            <span className="portada-item-leyenda">
              <span
                className="pildora-punto"
                style={{ backgroundColor: "var(--color-yuca)" }}
                aria-hidden="true"
              />
              Yuca dominante (t)
            </span>
            <span className="portada-item-leyenda">
              <span
                className="pildora-punto"
                style={{ backgroundColor: "var(--color-arroz)" }}
                aria-hidden="true"
              />
              Arroz dominante (t)
            </span>
          </div>

          <a href="#narrativa-caribe" className="portada-indicador-scroll">
            <span>Desliza para recorrer la historia</span>
            <span aria-hidden="true">↓</span>
          </a>
        </article>
      </div>
    </section>
  );
}
