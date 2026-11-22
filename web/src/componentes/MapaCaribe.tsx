import { useEffect, useMemo, useRef, useState } from "react";
import { geoMercator, geoPath } from "d3-geo";
import { scaleThreshold } from "d3-scale";
import { select } from "d3-selection";
import "d3-transition";
import type { FeatureCollection, Geometry } from "geojson";
import { feature } from "topojson-client";
import type {
  ContratoTopoJsonCaribe,
  MunicipioCultivoItem,
} from "../datos/cargador.ts";
import type { ContratoMunicipiosCultivo } from "../datos/cargador.ts";
import { usarTiendaRindex, type CultivoClave } from "../estado/tiendaRindex.ts";
import { formatearDecimal, formatearPorcentaje } from "../utilidades/formato.ts";

interface PropiedadGeo {
  codigo: string;
  nombre: string;
  departamento: string;
}

export interface PropsMapaCaribe {
  topoJson: ContratoTopoJsonCaribe;
  datosCultivo: ContratoMunicipiosCultivo | null;
  alMedirRender?: (milisegundos: number) => void;
}

const PALETAS_CLARO: Record<CultivoClave, readonly string[]> = {
  "Maíz": ["#DEDAC2", "#C8B994", "#B09B68", "#977D3E", "#7B5F0B"],
  "Yuca": ["#E4D5C4", "#D4B09A", "#C28B71", "#AE674B", "#964125"],
  "Arroz": ["#CFDBCE", "#A5BEB1", "#7CA195", "#53857A", "#22685F"],
};

const PALETAS_OSCURO: Record<CultivoClave, readonly string[]> = {
  "Maíz": ["#333422", "#5A522A", "#847232", "#AF9339", "#DFB83F"],
  "Yuca": ["#332D24", "#5A4031", "#83543E", "#AD684C", "#DC7D5B"],
  "Arroz": ["#22342E", "#30524A", "#3E7268", "#4C9387", "#5AB8AA"],
};

const ETIQUETAS_ESCALA: readonly string[] = [
  "0 % (ref.)",
  "> 0–15 %",
  "15–30 %",
  "30–50 %",
  "> 50 %",
];

const escalaPaso = scaleThreshold<number, number>()
  .domain([0.05, 15, 30, 50])
  .range([0, 1, 2, 3, 4]);

export function MapaCaribe({
  topoJson,
  datosCultivo,
  alMedirRender,
}: PropsMapaCaribe): React.JSX.Element {
  const cultivoActivo = usarTiendaRindex((s) => s.cultivoActivo);
  const tema = usarTiendaRindex((s) => s.tema);
  const municipioSeleccionado = usarTiendaRindex((s) => s.municipioSeleccionado);
  const seleccionarMunicipio = usarTiendaRindex((s) => s.seleccionarMunicipio);

  const contenedorRef = useRef<HTMLDivElement | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const primerMontajeRef = useRef(true);

  const [dimensiones, setDimensiones] = useState<{ ancho: number; alto: number }>({
    ancho: 760,
    alto: 520,
  });
  const [municipioHover, setMunicipioHover] = useState<string | null>(null);

  useEffect(() => {
    const el = contenedorRef.current;
    if (!el || typeof ResizeObserver === "undefined") {
      return undefined;
    }
    const actualizar = (): void => {
      const anchoMedido = el.clientWidth;
      if (anchoMedido > 120) {
        const altoCalc = Math.round(Math.max(380, Math.min(580, anchoMedido * 0.68)));
        setDimensiones({ ancho: anchoMedido, alto: altoCalc });
      }
    };
    actualizar();
    const observer = new ResizeObserver(actualizar);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const esTemaOscuro = useMemo(() => {
    if (tema === "oscuro") {
      return true;
    }
    if (tema === "claro") {
      return false;
    }
    if (typeof window !== "undefined" && typeof window.matchMedia === "function") {
      return window.matchMedia("(prefers-color-scheme: dark)").matches;
    }
    return false;
  }, [tema]);

  const paleta = esTemaOscuro ? PALETAS_OSCURO[cultivoActivo] : PALETAS_CLARO[cultivoActivo];

  const mapaMunicipiosDatos = useMemo(() => {
    const mapa = new Map<string, MunicipioCultivoItem>();
    if (!datosCultivo) {
      return mapa;
    }
    for (const m of datosCultivo.municipios) {
      mapa.set(m.codigo, m);
    }
    return mapa;
  }, [datosCultivo]);

  const { colMpios, colDeptos, objetoAjuste } = useMemo(() => {
    const mpiosCol = feature(
      topoJson as never,
      topoJson.objects.municipios as never,
    ) as unknown as FeatureCollection<Geometry, PropiedadGeo>;
    const deptosCol = feature(
      topoJson as never,
      topoJson.objects.departamentos as never,
    ) as unknown as FeatureCollection<Geometry, PropiedadGeo>;

    const bbox = topoJson.bbox;
    const ajuste: Geometry | FeatureCollection<Geometry, PropiedadGeo> =
      bbox && bbox.length >= 4
        ? {
            type: "MultiPoint",
            coordinates: [
              [bbox[0] ?? -77.5, bbox[1] ?? 7.0],
              [bbox[2] ?? -71.0, bbox[3] ?? 12.6],
            ],
          }
        : mpiosCol;

    return { colMpios: mpiosCol, colDeptos: deptosCol, objetoAjuste: ajuste };
  }, [topoJson]);

  const { rutasMunicipios, rutasDepartamentos, tiempoGeoMs } = useMemo(() => {
    const t0 = typeof performance !== "undefined" ? performance.now() : Date.now();
    const proyeccion = geoMercator().fitExtent(
      [
        [18, 18],
        [dimensiones.ancho - 18, dimensiones.alto - 18],
      ],
      objetoAjuste as never,
    );
    const generador = geoPath(proyeccion);

    const mpios = colMpios.features.map((feat) => ({
      codigo: feat.properties.codigo,
      nombre: feat.properties.nombre,
      departamento: feat.properties.departamento,
      d: generador(feat) ?? "",
    }));
    const deptos = colDeptos.features.map((feat) => ({
      codigo: feat.properties.codigo,
      nombre: feat.properties.nombre,
      d: generador(feat) ?? "",
    }));

    const t1 = typeof performance !== "undefined" ? performance.now() : Date.now();
    return {
      rutasMunicipios: mpios,
      rutasDepartamentos: deptos,
      tiempoGeoMs: t1 - t0,
    };
  }, [colMpios, colDeptos, objetoAjuste, dimensiones.ancho, dimensiones.alto]);

  useEffect(() => {
    alMedirRender?.(tiempoGeoMs);
  }, [tiempoGeoMs, alMedirRender]);

  const nivelEvidenciaCultivo = datosCultivo?.nivel_evidencia_cultivo ?? "alto";
  const colorNoElegible = esTemaOscuro ? "#5A635D" : "#B9BFAE";

  const infoVisualPorCodigo = useMemo(() => {
    const mapa = new Map<
      string,
      {
        rellenoSolido: string;
        usaPatronBaja: boolean;
        pasoIndice: number;
        extrapolado: boolean;
      }
    >();

    for (const mGeo of rutasMunicipios) {
      const mData = mapaMunicipiosDatos.get(mGeo.codigo);
      if (!mData || !mData.elegible || mData.brecha.brecha_relativa_pct === null) {
        mapa.set(mGeo.codigo, {
          rellenoSolido: colorNoElegible,
          usaPatronBaja: false,
          pasoIndice: -1,
          extrapolado: false,
        });
        continue;
      }
      const paso = escalaPaso(mData.brecha.brecha_relativa_pct);
      const color = paleta[paso] ?? paleta[0] ?? colorNoElegible;
      const esBaja =
        mData.nivel_evidencia === "bajo" || nivelEvidenciaCultivo === "bajo";
      mapa.set(mGeo.codigo, {
        rellenoSolido: color,
        usaPatronBaja: esBaja,
        pasoIndice: paso,
        extrapolado: mData.calidad.excluido_d4,
      });
    }
    return mapa;
  }, [rutasMunicipios, mapaMunicipiosDatos, colorNoElegible, paleta, nivelEvidenciaCultivo]);

  useEffect(() => {
    const svgEl = svgRef.current;
    if (!svgEl) {
      return;
    }
    if (primerMontajeRef.current) {
      primerMontajeRef.current = false;
      return;
    }
    const reduceMov =
      typeof window !== "undefined" &&
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const duracion = reduceMov ? 0 : 600;

    try {
      const sel = select(svgEl).selectAll<SVGPathElement, unknown>(".municipio-ruta");
      if (duracion > 0) {
        sel.transition("cambio-cultivo").duration(duracion).attr("fill", function () {
          const cod = this.getAttribute("data-codigo") ?? "";
          const info = infoVisualPorCodigo.get(cod);
          if (!info) {
            return colorNoElegible;
          }
          return info.usaPatronBaja
            ? `url(#patron-evidencia-baja-${info.pasoIndice})`
            : info.rellenoSolido;
        });
      }
    } catch {
      // En entornos sin transicion SVG (p. ej. jsdom) React mantiene el atributo fill actualizado.
    }
  }, [cultivoActivo, infoVisualPorCodigo, colorNoElegible]);

  const detalleHover = municipioHover
    ? mapaMunicipiosDatos.get(municipioHover) ?? null
    : null;

  return (
    <div className="mapa-bloque">
      <div className="mapa-contenedor" ref={contenedorRef}>
        <svg
          ref={svgRef}
          className="mapa-svg"
          viewBox={`0 0 ${dimensiones.ancho} ${dimensiones.alto}`}
          role="img"
          aria-labelledby="mapa-caribe-titulo mapa-caribe-desc"
        >
          <title id="mapa-caribe-titulo">
            Mapa de brecha de rendimiento en {cultivoActivo} en la Región Caribe (2019–2025)
          </title>
          <desc id="mapa-caribe-desc">
            Mapa coroplético de los 195 municipios de los 7 departamentos continentales del Caribe
            coloreados según su brecha relativa p50. Municipios no elegibles en gris de contexto y
            municipios con evidencia baja marcados con patrón rayado.
          </desc>

          <defs>
            {paleta.map((colorPaso, idx) => (
              <pattern
                key={`patron-${idx}`}
                id={`patron-evidencia-baja-${idx}`}
                width="8"
                height="8"
                patternUnits="userSpaceOnUse"
              >
                <rect width="8" height="8" fill={colorPaso} />
                <path
                  d="M-2,2 l4,-4 M0,8 l8,-8 M6,10 l4,-4"
                  stroke="var(--color-tinta)"
                  strokeOpacity="0.34"
                  strokeWidth="1.2"
                />
              </pattern>
            ))}
          </defs>

          <g className="capa-municipios">
            {rutasMunicipios.map((mGeo) => {
              const info = infoVisualPorCodigo.get(mGeo.codigo);
              const relleno =
                info && info.usaPatronBaja && info.pasoIndice >= 0
                  ? `url(#patron-evidencia-baja-${info.pasoIndice})`
                  : (info?.rellenoSolido ?? colorNoElegible);
              const clases = info?.extrapolado
                ? "municipio-ruta trazo-indicativo"
                : "municipio-ruta";
              const mData = mapaMunicipiosDatos.get(mGeo.codigo);
              const etiqueta = mData
                ? `${mData.nombre} (${mData.departamento}): ${
                    mData.elegible && mData.brecha.brecha_relativa_pct !== null
                      ? formatearPorcentaje(mData.brecha.brecha_relativa_pct)
                      : "no elegible"
                  }`
                : mGeo.nombre;

              return (
                <path
                  key={mGeo.codigo}
                  d={mGeo.d}
                  className={clases}
                  fill={relleno}
                  data-codigo={mGeo.codigo}
                  data-departamento={mGeo.departamento}
                  data-seleccionado={municipioSeleccionado === mGeo.codigo ? "true" : "false"}
                  tabIndex={0}
                  aria-label={etiqueta}
                  onMouseEnter={() => setMunicipioHover(mGeo.codigo)}
                  onMouseLeave={() => setMunicipioHover(null)}
                  onFocus={() => setMunicipioHover(mGeo.codigo)}
                  onBlur={() => setMunicipioHover(null)}
                  onClick={() => seleccionarMunicipio(mGeo.codigo)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      seleccionarMunicipio(mGeo.codigo);
                    }
                  }}
                />
              );
            })}
          </g>

          <g className="capa-departamentos">
            {rutasDepartamentos.map((dGeo) => (
              <path
                key={dGeo.codigo}
                d={dGeo.d}
                className="departamento-ruta"
                data-codigo={dGeo.codigo}
              />
            ))}
          </g>
        </svg>

        {detalleHover ? (
          <div className="mapa-tooltip" role="status" aria-live="polite">
            <strong>{detalleHover.nombre}</strong> ({detalleHover.departamento})
            <br />
            {detalleHover.elegible && detalleHover.brecha.brecha_relativa_pct !== null ? (
              <span className="cifra-tabular">
                Brecha p50: {formatearPorcentaje(detalleHover.brecha.brecha_relativa_pct)} (
                {formatearDecimal(detalleHover.brecha.brecha_p50_tha ?? 0)} t/ha)
              </span>
            ) : (
              <span>No elegible (&lt; 500 ha o &lt; 4 años)</span>
            )}
          </div>
        ) : null}
      </div>

      <div className="mapa-leyenda" aria-label="Leyenda del mapa">
        <div className="leyenda-escala">
          <span>Brecha relativa ({cultivoActivo}):</span>
          <div className="leyenda-bloques">
            {paleta.map((hex, i) => (
              <span
                key={hex}
                className="leyenda-bloque"
                style={{ backgroundColor: hex }}
                title={ETIQUETAS_ESCALA[i]}
              />
            ))}
          </div>
          <span>0 % a &gt; 50 %</span>
        </div>

        <div className="leyenda-escala">
          <span
            className="leyenda-bloque"
            style={{ backgroundColor: colorNoElegible }}
          />
          <span>No elegible (&lt; 500 ha)</span>
        </div>

        <div className="leyenda-escala">
          <svg width="22" height="12" aria-hidden="true">
            <rect
              width="22"
              height="12"
              rx="2"
              fill={`url(#patron-evidencia-baja-2)`}
              stroke="var(--color-linea)"
            />
          </svg>
          <span>Rayado: evidencia baja (datos repetidos o redondeados)</span>
        </div>
      </div>

      {datosCultivo ? (
        <table className="sr-only" aria-label={`Datos municipales de ${cultivoActivo}`}>
          <caption>
            Brecha relativa de rendimiento y nivel de evidencia por municipio en {cultivoActivo}
          </caption>
          <thead>
            <tr>
              <th>Código DANE</th>
              <th>Municipio</th>
              <th>Departamento</th>
              <th>Elegible</th>
              <th>Brecha relativa p50 (%)</th>
              <th>Nivel de evidencia</th>
            </tr>
          </thead>
          <tbody>
            {datosCultivo.municipios.map((m) => (
              <tr key={m.codigo}>
                <td>{m.codigo}</td>
                <td>{m.nombre}</td>
                <td>{m.departamento}</td>
                <td>{m.elegible ? "Sí" : "No"}</td>
                <td>
                  {m.brecha.brecha_relativa_pct !== null
                    ? formatearPorcentaje(m.brecha.brecha_relativa_pct)
                    : "N/D"}
                </td>
                <td>{m.nivel_evidencia}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </div>
  );
}
