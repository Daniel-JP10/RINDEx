import { useEffect, useMemo, useRef, useState } from "react";
import { geoMercator, geoPath } from "d3-geo";
import { scaleQuantize, scaleThreshold } from "d3-scale";
import { select } from "d3-selection";
import "d3-transition";
import type { FeatureCollection, Geometry } from "geojson";
import { feature } from "topojson-client";
import type {
  ContratoMunicipiosCultivo,
  ContratoTopoJsonCaribe,
  MunicipioCultivoItem,
} from "../datos/cargador.ts";
import { usarTiendaRindex, type CultivoClave } from "../estado/tiendaRindex.ts";
import {
  etiquetarEvidencia,
  formatearDecimal,
  formatearEntero,
  formatearPorcentaje,
} from "../utilidades/formato.ts";
import { coincideFiltrosMunicipio } from "../utilidades/tablero.ts";

interface PropiedadGeo {
  codigo: string;
  nombre: string;
  departamento: string;
}

export type ModoMapaCaribe =
  | "brecha"
  | "dominante"
  | "arroz_2021"
  | "prioriza"
  | "cierre"
  | "anio";

export interface PropsMapaCaribe {
  topoJson: ContratoTopoJsonCaribe;
  datosCultivo: ContratoMunicipiosCultivo | null;
  modoVisual?: ModoMapaCaribe;
  cultivosDominantes?: ReadonlyMap<string, CultivoClave>;
  codigosResaltados?: readonly string[];
  acercarACodigos?: readonly string[];
  departamentoFiltro?: string | null;
  cuadranteFiltro?: string | null;
  anioActivo?: number | null;
  alMedirRender?: (milisegundos: number) => void;
}

/* Escalas secuenciales vibrantes de 5 pasos con giro de tono (identicas en claro y oscuro) */
const PALETAS_SECUENCIALES: Record<CultivoClave, readonly string[]> = {
  "Maíz": ["#FFF4CC", "#FFD84D", "#F2B705", "#C77C02", "#7A4A00"],
  "Yuca": ["#FDE4DA", "#F7A47F", "#E4572E", "#B23A1B", "#6E2410"],
  "Arroz": ["#D6F5F0", "#7FD8CB", "#17A398", "#0E7469", "#08443E"],
};

const COLORES_DOMINANTES: Record<CultivoClave, string> = {
  "Maíz": "#F2B705",
  "Yuca": "#E4572E",
  "Arroz": "#17A398",
};

const ETIQUETAS_ESCALA_BRECHA: readonly string[] = [
  "0 % (referencia)",
  "> 0–15 %",
  "15–30 %",
  "30–50 %",
  "> 50 %",
];

const ETIQUETAS_ESCALA_2021: readonly string[] = [
  "0–5 %",
  "5–15 %",
  "15–30 %",
  "30–50 %",
  "> 50 %",
];

const escalaPasoBrecha = scaleThreshold<number, number>()
  .domain([0.05, 15, 30, 50])
  .range([0, 1, 2, 3, 4]);

const escalaPaso2021 = scaleThreshold<number, number>()
  .domain([5, 15, 30, 50])
  .range([0, 1, 2, 3, 4]);

function obtenerTasaNoCosechada2021(mData: MunicipioCultivoItem | undefined): {
  tasaPct: number | null;
  noCosechadaHa: number | null;
} {
  if (!mData) {
    return { tasaPct: null, noCosechadaHa: null };
  }
  const fila21 = mData.serie_anual.find((s) => s.anio === 2021);
  if (!fila21 || fila21.area_sembrada_ha <= 0) {
    return { tasaPct: null, noCosechadaHa: null };
  }
  const diff = Math.max(0, fila21.area_sembrada_ha - fila21.area_cosechada_ha);
  const tasaPct = (diff / fila21.area_sembrada_ha) * 100;
  return { tasaPct, noCosechadaHa: diff };
}

function obtenerRegistroAnual(
  mData: MunicipioCultivoItem | undefined,
  anio: number | null,
) {
  if (!mData || anio === null) {
    return null;
  }
  return mData.serie_anual.find((s) => s.anio === anio) ?? null;
}

export function MapaCaribe({
  topoJson,
  datosCultivo,
  modoVisual = "brecha",
  cultivosDominantes,
  codigosResaltados = [],
  acercarACodigos = [],
  departamentoFiltro = null,
  cuadranteFiltro = null,
  anioActivo = null,
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
    ancho: 680,
    alto: 420,
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
        const altoCalc = Math.round(Math.max(240, Math.min(440, anchoMedido * 0.62)));
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

  const modoEfectivo: ModoMapaCaribe = anioActivo !== null ? "anio" : modoVisual;

  const paleta =
    modoEfectivo === "arroz_2021" || modoEfectivo === "cierre"
      ? PALETAS_SECUENCIALES["Arroz"]
      : PALETAS_SECUENCIALES[cultivoActivo];

  const conjuntoResaltados = useMemo(() => new Set(codigosResaltados), [codigosResaltados]);

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

  const rangoRendimientoAnual = useMemo(() => {
    if (anioActivo === null || !datosCultivo) {
      return { min: 0, max: 10 };
    }
    const valores: number[] = [];
    for (const m of datosCultivo.municipios) {
      const reg = m.serie_anual.find((s) => s.anio === anioActivo);
      if (reg && reg.rendimiento_tha !== null && reg.area_cosechada_ha > 0) {
        valores.push(reg.rendimiento_tha);
      }
    }
    if (valores.length === 0) {
      return { min: 0, max: 10 };
    }
    const minVal = Math.min(...valores);
    const maxVal = Math.max(...valores);
    return {
      min: minVal,
      max: maxVal > minVal ? maxVal : minVal + 1,
    };
  }, [anioActivo, datosCultivo]);

  const escalaPasoAnual = useMemo(
    () =>
      scaleQuantize<number>()
        .domain([rangoRendimientoAnual.min, rangoRendimientoAnual.max])
        .range([0, 1, 2, 3, 4]),
    [rangoRendimientoAnual],
  );

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

  const { rutasMunicipios, rutasDepartamentos, tiempoGeoMs, generadorRuta } = useMemo(() => {
    const t0 = typeof performance !== "undefined" ? performance.now() : Date.now();
    const proyeccion = geoMercator().fitExtent(
      [
        [14, 14],
        [dimensiones.ancho - 14, dimensiones.alto - 14],
      ],
      objetoAjuste as never,
    );
    const generador = geoPath(proyeccion).digits(1);

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
      generadorRuta: generador,
    };
  }, [colMpios, colDeptos, objetoAjuste, dimensiones.ancho, dimensiones.alto]);

  const codigosZoomEfectivos = useMemo(() => {
    if (departamentoFiltro !== null) {
      return colMpios.features
        .filter((f) => f.properties.departamento === departamentoFiltro)
        .map((f) => f.properties.codigo);
    }
    return acercarACodigos;
  }, [departamentoFiltro, acercarACodigos, colMpios]);

  const transformCamara = useMemo(() => {
    if (codigosZoomEfectivos.length === 0) {
      return "translate(0px, 0px) scale(1)";
    }
    const conjuntoZoom = new Set(codigosZoomEfectivos);
    let minX = Number.POSITIVE_INFINITY;
    let minY = Number.POSITIVE_INFINITY;
    let maxX = Number.NEGATIVE_INFINITY;
    let maxY = Number.NEGATIVE_INFINITY;

    for (const feat of colMpios.features) {
      if (conjuntoZoom.has(feat.properties.codigo)) {
        const [[x0, y0], [x1, y1]] = generadorRuta.bounds(feat);
        if (Number.isFinite(x0) && Number.isFinite(y0)) {
          minX = Math.min(minX, x0);
          minY = Math.min(minY, y0);
          maxX = Math.max(maxX, x1);
          maxY = Math.max(maxY, y1);
        }
      }
    }

    if (!Number.isFinite(minX) || !Number.isFinite(maxX) || maxX <= minX || maxY <= minY) {
      return "translate(0px, 0px) scale(1)";
    }
    const dx = maxX - minX;
    const dy = maxY - minY;
    const cx = (minX + maxX) / 2;
    const cy = (minY + maxY) / 2;
    const factorMargen = departamentoFiltro !== null ? 0.72 : 0.56;
    const escala = Math.min(
      3.2,
      Math.max(1.25, factorMargen / Math.max(dx / dimensiones.ancho, dy / dimensiones.alto)),
    );
    const tx = dimensiones.ancho / 2 - escala * cx;
    const ty = dimensiones.alto / 2 - escala * cy;
    return `translate(${tx.toFixed(1)}px, ${ty.toFixed(1)}px) scale(${escala.toFixed(3)})`;
  }, [
    codigosZoomEfectivos,
    colMpios,
    generadorRuta,
    dimensiones.ancho,
    dimensiones.alto,
    departamentoFiltro,
  ]);

  useEffect(() => {
    alMedirRender?.(tiempoGeoMs);
  }, [tiempoGeoMs, alMedirRender]);

  const nivelEvidenciaCultivo = datosCultivo?.nivel_evidencia_cultivo ?? "alto";
  const colorNoElegible = esTemaOscuro ? "#3C5447" : "#C9CEBE";
  const hayFiltroActivo = departamentoFiltro !== null || cuadranteFiltro !== null;

  const infoVisualPorCodigo = useMemo(() => {
    const mapa = new Map<
      string,
      {
        rellenoSolido: string;
        usaPatronBaja: boolean;
        pasoIndice: number;
        esRobusto: boolean;
        atenuadoPorFiltro: boolean;
      }
    >();

    for (const mGeo of rutasMunicipios) {
      const mData = mapaMunicipiosDatos.get(mGeo.codigo);
      const pasaFiltro = mData
        ? coincideFiltrosMunicipio(mData, departamentoFiltro, cuadranteFiltro)
        : departamentoFiltro === null || mGeo.departamento === departamentoFiltro;
      const atenuadoPorFiltro = hayFiltroActivo && !pasaFiltro;

      if (modoEfectivo === "anio" && anioActivo !== null) {
        const regAnio = obtenerRegistroAnual(mData, anioActivo);
        if (!regAnio || regAnio.rendimiento_tha === null || regAnio.area_cosechada_ha <= 0) {
          mapa.set(mGeo.codigo, {
            rellenoSolido: colorNoElegible,
            usaPatronBaja: false,
            pasoIndice: -1,
            esRobusto: false,
            atenuadoPorFiltro,
          });
          continue;
        }
        const paso = escalaPasoAnual(regAnio.rendimiento_tha);
        mapa.set(mGeo.codigo, {
          rellenoSolido: paleta[paso] ?? paleta[0] ?? colorNoElegible,
          usaPatronBaja: false,
          pasoIndice: paso,
          esRobusto: false,
          atenuadoPorFiltro,
        });
        continue;
      }

      if (modoEfectivo === "dominante") {
        const dom = cultivosDominantes?.get(mGeo.codigo);
        mapa.set(mGeo.codigo, {
          rellenoSolido: dom ? COLORES_DOMINANTES[dom] : colorNoElegible,
          usaPatronBaja: false,
          pasoIndice: -1,
          esRobusto: false,
          atenuadoPorFiltro,
        });
        continue;
      }

      if (modoEfectivo === "arroz_2021") {
        const { tasaPct } = obtenerTasaNoCosechada2021(mData);
        if (tasaPct === null) {
          mapa.set(mGeo.codigo, {
            rellenoSolido: colorNoElegible,
            usaPatronBaja: false,
            pasoIndice: -1,
            esRobusto: false,
            atenuadoPorFiltro,
          });
          continue;
        }
        const paso = escalaPaso2021(tasaPct);
        mapa.set(mGeo.codigo, {
          rellenoSolido: paleta[paso] ?? paleta[0] ?? colorNoElegible,
          usaPatronBaja: false,
          pasoIndice: paso,
          esRobusto: false,
          atenuadoPorFiltro,
        });
        continue;
      }

      if (!mData || !mData.elegible || mData.brecha.brecha_relativa_pct === null) {
        mapa.set(mGeo.codigo, {
          rellenoSolido: colorNoElegible,
          usaPatronBaja: false,
          pasoIndice: -1,
          esRobusto: false,
          atenuadoPorFiltro,
        });
        continue;
      }
      const paso = escalaPasoBrecha(mData.brecha.brecha_relativa_pct);
      const color = paleta[paso] ?? paleta[0] ?? colorNoElegible;
      const esBaja =
        modoEfectivo !== "cierre" &&
        (mData.nivel_evidencia === "bajo" || nivelEvidenciaCultivo === "bajo");
      mapa.set(mGeo.codigo, {
        rellenoSolido: color,
        usaPatronBaja: esBaja,
        pasoIndice: paso,
        esRobusto: Boolean(mData.priorizacion.prioridad_robusta),
        atenuadoPorFiltro,
      });
    }
    return mapa;
  }, [
    rutasMunicipios,
    modoEfectivo,
    anioActivo,
    escalaPasoAnual,
    cultivosDominantes,
    mapaMunicipiosDatos,
    colorNoElegible,
    paleta,
    nivelEvidenciaCultivo,
    departamentoFiltro,
    cuadranteFiltro,
    hayFiltroActivo,
  ]);

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
    const duracion = reduceMov ? 0 : 450;

    try {
      const sel = select(svgEl).selectAll<SVGPathElement, unknown>(".municipio-ruta");
      if (duracion > 0) {
        sel.transition("cambio-cultivo").duration(duracion).attr("fill", function () {
          const cod = this.getAttribute("data-codigo") ?? "";
          const info = infoVisualPorCodigo.get(cod);
          if (!info) {
            return colorNoElegible;
          }
          return info.usaPatronBaja && info.pasoIndice >= 0
            ? `url(#patron-evidencia-baja-${info.pasoIndice})`
            : info.rellenoSolido;
        });
      }
    } catch {
      // En entornos sin transicion SVG (p. ej. jsdom) React mantiene el atributo fill actualizado.
    }
  }, [cultivoActivo, modoEfectivo, anioActivo, infoVisualPorCodigo, colorNoElegible]);

  const detalleHover = municipioHover
    ? mapaMunicipiosDatos.get(municipioHover) ?? null
    : null;
  const domHover = municipioHover ? cultivosDominantes?.get(municipioHover) ?? null : null;
  const info2021Hover =
    modoEfectivo === "arroz_2021" ? obtenerTasaNoCosechada2021(detalleHover ?? undefined) : null;
  const infoAnioHover =
    modoEfectivo === "anio" ? obtenerRegistroAnual(detalleHover ?? undefined, anioActivo) : null;

  return (
    <div className="mapa-bloque" data-modo-mapa={modoEfectivo}>
      <div className="mapa-contenedor" ref={contenedorRef}>
        <svg
          ref={svgRef}
          className="mapa-svg"
          viewBox={`0 0 ${dimensiones.ancho} ${dimensiones.alto}`}
          role="img"
          aria-labelledby="mapa-caribe-titulo mapa-caribe-desc"
        >
          <title id="mapa-caribe-titulo">
            Mapa territorial de {cultivoActivo} en la Región Caribe (2019–2025)
          </title>
          <desc id="mapa-caribe-desc">
            Mapa vectorial de los 195 municipios de los 7 departamentos continentales del Caribe.
            Municipios no elegibles en gris de contexto y zonas con menor precisión de registro
            marcadas con patrón rayado.
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
                  stroke="#1F2A22"
                  strokeOpacity="0.34"
                  strokeWidth="1.15"
                />
              </pattern>
            ))}
          </defs>

          <g
            className="mapa-camara"
            style={{ transform: transformCamara }}
            data-zoom-activo={codigosZoomEfectivos.length > 0 ? "true" : "false"}
          >
            <g className="capa-municipios">
              {rutasMunicipios.map((mGeo) => {
                const info = infoVisualPorCodigo.get(mGeo.codigo);
                const relleno =
                  info && info.usaPatronBaja && info.pasoIndice >= 0
                    ? `url(#patron-evidencia-baja-${info.pasoIndice})`
                    : (info?.rellenoSolido ?? colorNoElegible);
                const estaResaltado =
                  modoEfectivo !== "anio" && conjuntoResaltados.has(mGeo.codigo);
                const esRobustoDestacado =
                  modoEfectivo === "prioriza" && Boolean(info?.esRobusto);
                const clases = [
                  "municipio-ruta",
                  estaResaltado ? "municipio-pulso" : "",
                  esRobustoDestacado ? "municipio-robusto" : "",
                  info?.atenuadoPorFiltro ? "municipio-atenuado" : "",
                ]
                  .filter(Boolean)
                  .join(" ");

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
                    data-resaltado={estaResaltado ? "true" : "false"}
                    data-atenuado={info?.atenuadoPorFiltro ? "true" : "false"}
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
          </g>
        </svg>

        {detalleHover ? (
          <div className="mapa-tooltip" role="status" aria-live="polite">
            <strong>{detalleHover.nombre}</strong> ({detalleHover.departamento})
            <br />
            {modoEfectivo === "anio" && anioActivo !== null ? (
              infoAnioHover && infoAnioHover.rendimiento_tha !== null ? (
                <span className="cifra-tabular">
                  {anioActivo}: {formatearDecimal(infoAnioHover.rendimiento_tha)} t/ha ·{" "}
                  {formatearEntero(infoAnioHover.produccion_t)} t
                </span>
              ) : (
                <span>Sin cosecha registrada en {anioActivo}</span>
              )
            ) : modoEfectivo === "dominante" ? (
              <span>
                Cultivo dominante: <strong>{domHover ?? "Sin datos"}</strong>
              </span>
            ) : modoEfectivo === "arroz_2021" && info2021Hover ? (
              info2021Hover.tasaPct !== null ? (
                <span className="cifra-tabular">
                  Sin cosechar en 2021: {formatearPorcentaje(info2021Hover.tasaPct)} (
                  {formatearEntero(info2021Hover.noCosechadaHa ?? 0)} ha)
                </span>
              ) : (
                <span>Sin registro de arroz en 2021</span>
              )
            ) : detalleHover.elegible && detalleHover.brecha.brecha_relativa_pct !== null ? (
              <span className="cifra-tabular">
                Brecha mediana: {formatearPorcentaje(detalleHover.brecha.brecha_relativa_pct)} (
                {formatearDecimal(detalleHover.brecha.brecha_p50_tha ?? 0)} t/ha)
              </span>
            ) : (
              <span>No elegible (menos de 500 ha o menos de 4 años)</span>
            )}
          </div>
        ) : null}
      </div>

      <div className="mapa-leyenda" data-testid="mapa-leyenda" aria-label="Leyenda del mapa">
        {modoEfectivo === "anio" && anioActivo !== null ? (
          <>
            <div className="leyenda-escala">
              <span>
                Rendimiento {anioActivo} ({cultivoActivo}):
              </span>
              <div className="leyenda-bloques">
                {paleta.map((hex) => (
                  <span
                    key={hex}
                    className="leyenda-bloque"
                    style={{ backgroundColor: hex }}
                  />
                ))}
              </div>
              <span className="cifra-tabular">
                {formatearDecimal(rangoRendimientoAnual.min, 1)} a{" "}
                {formatearDecimal(rangoRendimientoAnual.max, 1)} t/ha
              </span>
            </div>
            <div className="leyenda-escala">
              <span
                className="leyenda-bloque"
                style={{ backgroundColor: colorNoElegible }}
              />
              <span>Sin registro en {anioActivo}</span>
            </div>
          </>
        ) : modoEfectivo === "dominante" ? (
          <>
            <span className="leyenda-escala">
              <span
                className="leyenda-bloque"
                style={{ backgroundColor: COLORES_DOMINANTES["Maíz"] }}
              />
              Maíz dominante
            </span>
            <span className="leyenda-escala">
              <span
                className="leyenda-bloque"
                style={{ backgroundColor: COLORES_DOMINANTES["Yuca"] }}
              />
              Yuca dominante
            </span>
            <span className="leyenda-escala">
              <span
                className="leyenda-bloque"
                style={{ backgroundColor: COLORES_DOMINANTES["Arroz"] }}
              />
              Arroz dominante
            </span>
          </>
        ) : modoEfectivo === "arroz_2021" ? (
          <>
            <div className="leyenda-escala">
              <span>Área no cosechada 2021 (Arroz):</span>
              <div className="leyenda-bloques">
                {paleta.map((hex, i) => (
                  <span
                    key={hex}
                    className="leyenda-bloque"
                    style={{ backgroundColor: hex }}
                    title={ETIQUETAS_ESCALA_2021[i]}
                  />
                ))}
              </div>
              <span>0 % a &gt; 50 %</span>
            </div>
            <div className="leyenda-escala">
              <span className="leyenda-bloque leyenda-bloque-resaltado" />
              <span>5 municipios de La Mojana</span>
            </div>
          </>
        ) : (
          <>
            <div className="leyenda-escala">
              <span>
                Brecha relativa ({modoEfectivo === "cierre" ? "Arroz" : cultivoActivo}):
              </span>
              <div className="leyenda-bloques">
                {paleta.map((hex, i) => (
                  <span
                    key={hex}
                    className="leyenda-bloque"
                    style={{ backgroundColor: hex }}
                    title={ETIQUETAS_ESCALA_BRECHA[i]}
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
              <span>No elegible</span>
            </div>

            {modoEfectivo === "cierre" ? (
              <div className="leyenda-escala">
                <span className="leyenda-bloque leyenda-bloque-resaltado" />
                <span>Guaranda y San Marcos</span>
              </div>
            ) : (
              <div className="leyenda-escala">
                <svg width="20" height="12" aria-hidden="true">
                  <rect
                    width="20"
                    height="12"
                    rx="2"
                    fill="url(#patron-evidencia-baja-2)"
                    stroke="var(--color-linea)"
                  />
                </svg>
                <span>Rayado: datos menos precisos</span>
              </div>
            )}
          </>
        )}
      </div>

      {datosCultivo ? (
        <div className="sr-only">
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
                <th>Brecha relativa (%)</th>
                <th>Evidencia</th>
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
                      : "No disponible"}
                  </td>
                  <td>{etiquetarEvidencia(m.nivel_evidencia)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
