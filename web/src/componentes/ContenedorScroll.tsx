import { useEffect, useMemo, useRef, useState } from "react";
import {
  cargarCalidad,
  cargarEscenarios,
  cargarHallazgos,
  cargarMeta,
  cargarMunicipiosCultivo,
  cargarRegional,
  cargarSistemas,
  cargarTopoJsonCaribe,
  type ContratoMunicipiosCultivo,
  type ContratoTopoJsonCaribe,
} from "../datos/cargador.ts";
import { usarTiendaRindex, type CultivoClave, type IdSeccion } from "../estado/tiendaRindex.ts";
import type { ContratoCalidad } from "../tipos/generados/calidad.ts";
import type { ContratoEscenarios } from "../tipos/generados/escenarios.ts";
import type { ContratoHallazgos } from "../tipos/generados/hallazgos.ts";
import type { ContratoMeta } from "../tipos/generados/meta.ts";
import type { ContratoRegional } from "../tipos/generados/regional.ts";
import type { ContratoSistemas } from "../tipos/generados/sistemas.ts";
import {
  formatearDecimal,
  formatearEntero,
  formatearMultiplicador,
  formatearPorcentaje,
} from "../utilidades/formato.ts";
import {
  ANIOS_TABLERO,
  CUADRANTES_FILTRO,
  DEPARTAMENTOS_CARIBE,
  calcularKpisTablero,
  coincideFiltrosMunicipio,
} from "../utilidades/tablero.ts";
import { BuscadorMunicipio } from "./BuscadorMunicipio.tsx";
import { FichaMunicipal } from "./FichaMunicipal.tsx";
import { GraficoMatriz } from "./GraficoMatriz.tsx";
import { GraficoPesas } from "./GraficoPesas.tsx";
import { MapaCaribe, type ModoMapaCaribe } from "./MapaCaribe.tsx";
import { PanelCalidad } from "./PanelCalidad.tsx";
import { PanelMetodologia } from "./PanelMetodologia.tsx";
import { SimuladorEscenarios } from "./SimuladorEscenarios.tsx";
import { TablaPrioridad } from "./TablaPrioridad.tsx";

const CODIGOS_MOJANA_TOP5: readonly string[] = [
  "70429",
  "23068",
  "13006",
  "70265",
  "70708",
];
const CODIGOS_CIERRE_MOJANA: readonly string[] = ["70265", "70708"];
const MUNICIPIOS_CRUCE_MOJANA: ReadonlyArray<{ codigo: string; nombre: string }> = [
  { codigo: "70265", nombre: "Guaranda" },
  { codigo: "70708", nombre: "San Marcos" },
  { codigo: "13006", nombre: "Achí" },
  { codigo: "70771", nombre: "Sucre" },
  { codigo: "13655", nombre: "San Jacinto del Cauca" },
];

type VistaPanelActivo =
  | "mapa"
  | "pesas"
  | "calidad"
  | "matriz"
  | "simulador"
  | "prioridad"
  | "metodologia";

interface PasoNarrativoRender {
  id: Exclude<IdSeccion, "portada">;
  capitulo: string;
  etiquetaCorta: string;
  titulo: string;
  cifraHero?: {
    texto: string;
    tono: "maiz" | "yuca" | "arroz" | "marca";
    etiqueta?: string;
  };
  lineasDecisor: readonly string[];
  textoTecnico: string;
  mostrarEnlaceMetodologia?: boolean;
}

export function ContenedorScroll(): React.JSX.Element {
  const cultivoActivo = usarTiendaRindex((s) => s.cultivoActivo);
  const modo = usarTiendaRindex((s) => s.modo);
  const seccionActiva = usarTiendaRindex((s) => s.seccionActiva);
  const municipioSeleccionado = usarTiendaRindex((s) => s.municipioSeleccionado);
  const departamentoFiltro = usarTiendaRindex((s) => s.departamentoFiltro);
  const cuadranteFiltro = usarTiendaRindex((s) => s.cuadranteFiltro);
  const anioActivo = usarTiendaRindex((s) => s.anioActivo);

  const establecerCultivo = usarTiendaRindex((s) => s.establecerCultivo);
  const establecerSeccionActiva = usarTiendaRindex((s) => s.establecerSeccionActiva);
  const seleccionarMunicipio = usarTiendaRindex((s) => s.seleccionarMunicipio);
  const establecerDepartamentoFiltro = usarTiendaRindex((s) => s.establecerDepartamentoFiltro);
  const establecerCuadranteFiltro = usarTiendaRindex((s) => s.establecerCuadranteFiltro);
  const establecerAnioActivo = usarTiendaRindex((s) => s.establecerAnioActivo);
  const limpiarFiltros = usarTiendaRindex((s) => s.limpiarFiltros);

  const [topoJson, setTopoJson] = useState<ContratoTopoJsonCaribe | null>(null);
  const [datosCultivo, setDatosCultivo] = useState<ContratoMunicipiosCultivo | null>(null);
  const [hallazgos, setHallazgos] = useState<ContratoHallazgos | null>(null);
  const [regional, setRegional] = useState<ContratoRegional | null>(null);
  const [calidad, setCalidad] = useState<ContratoCalidad | null>(null);
  const [sistemas, setSistemas] = useState<ContratoSistemas | null>(null);
  const [escenarios, setEscenarios] = useState<ContratoEscenarios | null>(null);
  const [meta, setMeta] = useState<ContratoMeta | null>(null);
  const [errorDatos, setErrorDatos] = useState<string | null>(null);
  const [ultimoRenderMs, setUltimoRenderMs] = useState<number | null>(null);

  const rielPasosRef = useRef<HTMLDivElement | null>(null);
  const seccionPreviaRef = useRef<IdSeccion>(seccionActiva);
  const bloquearObserverHastaRef = useRef<number>(0);

  useEffect(() => {
    let cancelado = false;
    Promise.all([
      cargarTopoJsonCaribe(),
      cargarHallazgos(),
      cargarRegional(),
      cargarCalidad(),
      cargarSistemas(),
    ])
      .then(([t, h, r, c, s]) => {
        if (!cancelado) {
          setTopoJson(t);
          setHallazgos(h);
          setRegional(r);
          setCalidad(c);
          setSistemas(s);
        }
      })
      .catch((err: unknown) => {
        if (!cancelado) {
          setErrorDatos(
            err instanceof Error
              ? err.message
              : "No fue posible cargar los datos territoriales del Caribe.",
          );
        }
      });
    return () => {
      cancelado = true;
    };
  }, []);

  useEffect(() => {
    let cancelado = false;
    setErrorDatos(null);
    cargarMunicipiosCultivo(cultivoActivo)
      .then((datos) => {
        if (!cancelado) {
          setDatosCultivo(datos);
        }
      })
      .catch((err: unknown) => {
        if (!cancelado) {
          setErrorDatos(
            err instanceof Error
              ? err.message
              : `No fue posible cargar los municipios de ${cultivoActivo}.`,
          );
        }
      });
    return () => {
      cancelado = true;
    };
  }, [cultivoActivo]);

  useEffect(() => {
    const previa = seccionPreviaRef.current;
    seccionPreviaRef.current = seccionActiva;
    if (
      seccionActiva !== previa &&
      (seccionActiva === "el_golpe" || seccionActiva === "conexion_la_mojana")
    ) {
      establecerCultivo("Arroz");
      establecerAnioActivo(null);
      establecerDepartamentoFiltro(null);
    }
  }, [seccionActiva, establecerCultivo, establecerAnioActivo, establecerDepartamentoFiltro]);

  /* Carga perezosa: escenarios solo al abrir simulador y meta solo en metodologia */
  useEffect(() => {
    let cancelado = false;
    if (seccionActiva === "simula" && !escenarios) {
      cargarEscenarios()
        .then((datos) => {
          if (!cancelado) {
            setEscenarios(datos);
          }
        })
        .catch((err: unknown) => {
          if (!cancelado) {
            setErrorDatos(
              err instanceof Error ? err.message : "No fue posible cargar los escenarios.",
            );
          }
        });
    }
    if (seccionActiva === "metodologia" && !meta) {
      cargarMeta()
        .then((datos) => {
          if (!cancelado) {
            setMeta(datos);
          }
        })
        .catch((err: unknown) => {
          if (!cancelado) {
            setErrorDatos(
              err instanceof Error ? err.message : "No fue posible cargar la ficha metodológica.",
            );
          }
        });
    }
    return () => {
      cancelado = true;
    };
  }, [seccionActiva, escenarios, meta]);

  /* Sincroniza el paso activo al desplazar el riel interno en escritorio */
  useEffect(() => {
    const riel = rielPasosRef.current;
    if (!riel || typeof IntersectionObserver === "undefined") {
      return undefined;
    }

    const pasos = Array.from(riel.querySelectorAll<HTMLElement>(".paso-narrativo"));
    if (pasos.length === 0) {
      return undefined;
    }

    const observador = new IntersectionObserver(
      (entradas) => {
        if (window.innerWidth <= 960 || Date.now() < bloquearObserverHastaRef.current) {
          return;
        }
        let mejor: IntersectionObserverEntry | null = null;
        for (const ent of entradas) {
          if (ent.isIntersecting) {
            if (!mejor || ent.intersectionRatio > mejor.intersectionRatio) {
              mejor = ent;
            }
          }
        }
        if (mejor) {
          const id = mejor.target.getAttribute("data-seccion") as IdSeccion | null;
          if (id) {
            establecerSeccionActiva(id);
          }
        }
      },
      {
        root: riel,
        rootMargin: "-15% 0px -45% 0px",
        threshold: [0.25, 0.55, 0.85],
      },
    );

    for (const paso of pasos) {
      observador.observe(paso);
    }
    return () => observador.disconnect();
  }, [establecerSeccionActiva]);

  const metricasNarrativa = useMemo(() => {
    let pctToneladasYuca = 52.8;
    let pctHectareasMaiz = 48.3;
    if (regional && regional.registros.length > 0) {
      const prodPorCult = new Map<string, number>();
      const areaPorCult = new Map<string, number>();
      let prodTot = 0;
      let areaTot = 0;
      for (const r of regional.registros) {
        prodPorCult.set(r.cultivo, (prodPorCult.get(r.cultivo) ?? 0) + r.produccion_t);
        areaPorCult.set(r.cultivo, (areaPorCult.get(r.cultivo) ?? 0) + r.area_sembrada_ha);
        prodTot += r.produccion_t;
        areaTot += r.area_sembrada_ha;
      }
      if (prodTot > 0) {
        pctToneladasYuca = ((prodPorCult.get("Yuca") ?? 0) / prodTot) * 100;
      }
      if (areaTot > 0) {
        pctHectareasMaiz = ((areaPorCult.get("Maíz") ?? 0) / areaTot) * 100;
      }
    }

    const buscarCifra = (id: string, respaldo: number): number =>
      hallazgos?.tarjetas.find((t) => t.id === id)?.cifra ?? respaldo;

    const tasaRegional2021 = calidad?.arroz_2021_concentracion.tasa_regional_pct ?? 23.6;
    const top5Pct2021 = calidad?.arroz_2021_concentracion.top5_pct_regional ?? 75.4;
    const ayapel = calidad?.arroz_2021_concentracion.top10_municipios.find(
      (m) => m.codigo === "23068",
    );
    const tasaAyapel2021 = ayapel?.tasa_propia_pct ?? 85.3;

    const yucaCalidad = calidad?.por_cultivo.find((c) => c.cultivo === "Yuca");
    const pctEnterosYuca = yucaCalidad?.pct_rendimientos_enteros ?? 91.1;

    return {
      pctToneladasYuca,
      pctHectareasMaiz,
      tasaRegional2021,
      top5Pct2021,
      tasaAyapel2021,
      pctEnterosYuca,
      h2Maiz: buscarCifra("h2_maiz_tecnificado", 1.67),
      h3RiegoManual: buscarCifra("h3_arroz_riego_vs_manual", 2.02),
      h3MecManual: buscarCifra("h3_arroz_mecanizado_vs_manual", 1.62),
      pctMaizTradicional: buscarCifra("pct_area_maiz_tradicional", 73.5),
    };
  }, [regional, calidad, hallazgos]);

  const pasosNarrativos = useMemo<readonly PasoNarrativoRender[]>(() => {
    const m = metricasNarrativa;
    const deCadaDiezYuca = Math.round(m.pctEnterosYuca / 10);

    return [
      {
        id: "panorama",
        capitulo: "Panorama regional",
        etiquetaCorta: "Panorama",
        titulo: "Tres cultivos sostienen la mesa del Caribe",
        cifraHero: {
          texto: formatearPorcentaje(m.pctToneladasYuca),
          tono: "yuca",
          etiqueta: "del volumen cosechado es yuca",
        },
        lineasDecisor: [
          `La yuca pone el peso: ${formatearPorcentaje(m.pctToneladasYuca)} de lo que se cosecha.`,
          `El maíz pone la tierra: ${formatearPorcentaje(m.pctHectareasMaiz)} del área sembrada.`,
          "En siete años, ninguno de los tres muestra una mejora medible en su rendimiento.",
        ],
        textoTecnico:
          "Series regionales ponderadas (producción total sobre área cosechada) entre 2019 y 2025. Las pendientes municipales de Theil-Sen contrastadas con Wilcoxon y corrección de Holm no muestran tendencia regional creciente en ninguno de los tres cultivos.",
        mostrarEnlaceMetodologia: true,
      },
      {
        id: "el_golpe",
        capitulo: "Arroz en 2021",
        etiquetaCorta: "Arroz 2021",
        titulo: "2021, el año en que el arroz se quedó en el campo",
        cifraHero: {
          texto: formatearPorcentaje(m.tasaRegional2021),
          tono: "arroz",
          etiqueta: "del arroz sembrado no se cosechó",
        },
        lineasDecisor: [
          `El ${formatearPorcentaje(m.tasaRegional2021)} del arroz sembrado no se cosechó.`,
          `No pasó en todo el Caribe: cinco municipios de La Mojana concentran el ${formatearPorcentaje(m.top5Pct2021)} de esa área.`,
          `En Ayapel se quedó en el campo el ${formatearPorcentaje(m.tasaAyapel2021)} de lo sembrado.`,
        ],
        textoTecnico:
          "Análisis descriptivo de concentración espacial en 2021: cinco municipios de La Mojana y la depresión momposina reúnen tres cuartas partes del área no cosechada regional, sin atribución causal directa al índice climático anual.",
        mostrarEnlaceMetodologia: true,
      },
      {
        id: "mapa_brecha",
        capitulo: "Brecha de rendimiento",
        etiquetaCorta: "Brecha",
        titulo: "Con la misma tierra, no todos cosechan igual",
        lineasDecisor: [
          "Cada municipio se compara con los mejores de su propio departamento.",
          "Entre más intenso el color, más cosecha le falta.",
          "El rayado indica dónde los datos son menos precisos.",
        ],
        textoTecnico:
          "Brecha relativa mediana calculada contra el percentil 75 departamental dentro del mismo sistema productivo para municipios elegibles (al menos 500 hectáreas cosechadas y cuatro años con registro), mediante bootstrap de dos niveles.",
        mostrarEnlaceMetodologia: true,
      },
      {
        id: "por_que_rinde_menos",
        capitulo: "Sistemas productivos",
        etiquetaCorta: "Sistemas ×",
        titulo: "La diferencia cabe en una letra: ×",
        cifraHero: {
          texto: formatearMultiplicador(m.h2Maiz),
          tono: "maiz",
          etiqueta: "más rinde el maíz tecnificado frente al tradicional",
        },
        lineasDecisor: [
          `En el mismo municipio, el maíz tecnificado rinde ${formatearMultiplicador(m.h2Maiz)} lo que rinde el tradicional.`,
          `El arroz con riego rinde ${formatearMultiplicador(m.h3RiegoManual)} el de secano manual; el mecanizado, ${formatearMultiplicador(m.h3MecManual)}.`,
          `Y aun así, ${formatearDecimal(m.pctMaizTradicional, 1)} de cada 100 hectáreas de maíz siguen en el sistema tradicional.`,
        ],
        textoTecnico:
          "Estimador de Hodges-Lehmann con intervalo bootstrap de 5.000 réplicas a nivel municipal y corrección de Holm. El contraste directo entre riego y secano mecanizado queda fuera por la regla de muestra mínima (solo cinco municipios comparables).",
        mostrarEnlaceMetodologia: true,
      },
      {
        id: "lo_que_no_sabemos",
        capitulo: "Calidad del registro",
        etiquetaCorta: "Calidad",
        titulo: "Lo que los datos no alcanzan a decir",
        cifraHero: {
          texto: `${deCadaDiezYuca} de cada 10`,
          tono: "yuca",
          etiqueta: "rendimientos de yuca son números redondos",
        },
        lineasDecisor: [
          `${deCadaDiezYuca} de cada 10 rendimientos de yuca son números redondos: son estimaciones, no mediciones.`,
          "Por eso la yuca aparece con rayado: sirve para orientar, no para firmar un contrato.",
          "Desde 2022 cambió la forma de reportar la cosecha, y lo tratamos con cuidado.",
        ],
        textoTecnico:
          "Diagnóstico de repetición interanual y concentración en valores enteros exactos. El cambio de reporte operativo desde 2022 impide evaluar el área no cosechada por semestre y exige restringirla al balance anual.",
        mostrarEnlaceMetodologia: true,
      },
      {
        id: "matriz",
        capitulo: "Matriz de decisión",
        etiquetaCorta: "Matriz",
        titulo: "Cuatro municipios, cuatro decisiones",
        lineasDecisor: [
          "Consolidar: rinde bien y de forma estable.",
          "Proteger: rinde bien, pero sube y baja.",
          "Tecnificar: rinde poco, pero de forma estable.",
          "Intervención integral: rinde poco y es inestable.",
        ],
        textoTecnico:
          "Tipología construida cruzando el rendimiento relativo frente a la mediana departamental contra la mediana del coeficiente de variación interanual. Las series poco informativas se separan como estabilidad no medible.",
        mostrarEnlaceMetodologia: true,
      },
      {
        id: "simula",
        capitulo: "Simulación de escenarios",
        etiquetaCorta: "Escenarios",
        titulo: "Mueve las palancas",
        lineasDecisor: [
          "Cierra la brecha, tecnifica o recupera lo que no se cosecha.",
          "El resultado siempre es un rango, porque el dato no permite prometer una cifra exacta.",
        ],
        textoTecnico:
          "Simulación por bootstrap de dos niveles con 5.000 réplicas y suma réplica a réplica para los totales regionales, combinando cierre de brecha, tecnificación y área no cosechada sin doble conteo.",
        mostrarEnlaceMetodologia: true,
      },
      {
        id: "prioriza",
        capitulo: "Priorización robusta",
        etiquetaCorta: "Prioridad",
        titulo: "Por dónde empezar",
        cifraHero: {
          texto: "2.000",
          tono: "marca",
          etiqueta: "ponderaciones distintas evaluadas",
        },
        lineasDecisor: [
          "Probamos 2.000 formas distintas de pesar los criterios. Estos municipios quedaron arriba casi siempre.",
        ],
        textoTecnico:
          "Sensibilidad multicriterio con 2.000 juegos de pesos muestreados de una distribución Dirichlet uniforme. Un municipio entra al núcleo robusto cuando permanece entre los veinte primeros en al menos 80 % de los escenarios.",
        mostrarEnlaceMetodologia: true,
      },
      {
        id: "conexion_la_mojana",
        capitulo: "Cierre territorial",
        etiquetaCorta: "La Mojana",
        titulo: "Donde se perdió la cosecha, está la oportunidad",
        lineasDecisor: [
          "Guaranda y San Marcos fueron de los más golpeados en 2021, y hoy están en el núcleo de prioridad del arroz.",
        ],
        textoTecnico:
          "Cruce por código municipal entre los diez municipios con mayor área no cosechada de arroz en 2021 y los veinte primeros del índice de prioridad: Guaranda y San Marcos cumplen además el criterio de prioridad robusta.",
        mostrarEnlaceMetodologia: true,
      },
      {
        id: "metodologia",
        capitulo: "Metodología y auditoría",
        etiquetaCorta: "Metodología",
        titulo: "Cómo se calculan y auditan las cifras",
        lineasDecisor: [
          "Cada número proviene de datos abiertos oficiales de producción agrícola, cartografía oficial y series climáticas públicas.",
          "Una auditoría independiente recalcula los indicadores desde la fuente original antes de publicarlos.",
        ],
        textoTecnico:
          "Plan de análisis preespecificado con pruebas no paramétricas por defecto, bootstrap de dos niveles con semilla fija, corrección por comparaciones múltiples de Holm, suma réplica a réplica en agregados regionales y auditoría independiente directa desde la base oficial.",
        mostrarEnlaceMetodologia: false,
      },
    ];
  }, [metricasNarrativa]);

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

  const kpisTablero = useMemo(() => {
    if (!datosCultivo) {
      return null;
    }
    return calcularKpisTablero(
      datosCultivo.municipios,
      departamentoFiltro,
      cuadranteFiltro,
      anioActivo,
    );
  }, [datosCultivo, departamentoFiltro, cuadranteFiltro, anioActivo]);

  const opcionesBuscador = useMemo(() => {
    if (!datosCultivo) {
      return [];
    }
    return datosCultivo.municipios
      .filter((m) => coincideFiltrosMunicipio(m, departamentoFiltro, cuadranteFiltro))
      .map((m) => ({
        codigo: m.codigo,
        nombre: m.nombre,
        departamento: m.departamento,
      }));
  }, [datosCultivo, departamentoFiltro, cuadranteFiltro]);

  const totalElegibles = useMemo(() => {
    if (!datosCultivo) {
      return 0;
    }
    return datosCultivo.municipios.filter((m) => m.elegible).length;
  }, [datosCultivo]);

  const fichaActiva = useMemo(() => {
    if (!datosCultivo || !municipioSeleccionado) {
      return null;
    }
    return datosCultivo.municipios.find((m) => m.codigo === municipioSeleccionado) ?? null;
  }, [datosCultivo, municipioSeleccionado]);

  const seccionVisual: Exclude<IdSeccion, "portada"> =
    seccionActiva === "portada" ? "panorama" : seccionActiva;

  const nombreDeptoActivo = useMemo(() => {
    if (!departamentoFiltro) {
      return "Caribe";
    }
    return (
      DEPARTAMENTOS_CARIBE.find((d) => d.codigo === departamentoFiltro)?.nombre ?? "Caribe"
    );
  }, [departamentoFiltro]);

  const estadoPanel = useMemo<{
    vista: VistaPanelActivo;
    modoMapa: ModoMapaCaribe;
    titulo: string;
    subtitulo: string;
    codigosResaltados: readonly string[];
    acercarACodigos: readonly string[];
  }>(() => {
    if (anioActivo !== null) {
      return {
        vista: "mapa",
        modoMapa: "anio",
        titulo: `Rendimiento en ${anioActivo} — ${cultivoActivo}`,
        subtitulo: `Distribución municipal en ${nombreDeptoActivo} para el año ${anioActivo}`,
        codigosResaltados: [],
        acercarACodigos: [],
      };
    }

    switch (seccionVisual) {
      case "panorama":
        return {
          vista: "mapa",
          modoMapa: "dominante",
          titulo: "Cultivo dominante en el Caribe",
          subtitulo: "Mayor producción acumulada por municipio entre 2019 y 2025",
          codigosResaltados: [],
          acercarACodigos: [],
        };
      case "el_golpe":
        return {
          vista: "mapa",
          modoMapa: "arroz_2021",
          titulo: "Arroz sin cosechar en 2021 — La Mojana",
          subtitulo:
            "Tasa municipal de área no cosechada y foco en los cinco municipios principales",
          codigosResaltados: CODIGOS_MOJANA_TOP5,
          acercarACodigos: CODIGOS_MOJANA_TOP5,
        };
      case "por_que_rinde_menos":
        return {
          vista: "pesas",
          modoMapa: "brecha",
          titulo: "Rendimiento por sistema productivo",
          subtitulo: "Comparación departamental e intramunicipal con multiplicadores ×",
          codigosResaltados: [],
          acercarACodigos: [],
        };
      case "lo_que_no_sabemos":
        return {
          vista: "calidad",
          modoMapa: "brecha",
          titulo: "Calidad de registro y niveles de evidencia",
          subtitulo: "Repetición interanual, valores redondos y cambio de reporte desde 2022",
          codigosResaltados: [],
          acercarACodigos: [],
        };
      case "matriz":
        return {
          vista: "matriz",
          modoMapa: "brecha",
          titulo: `Matriz de decisión — ${cultivoActivo}`,
          subtitulo: "Rendimiento medio frente a variabilidad interanual (tamaño según producción)",
          codigosResaltados: [],
          acercarACodigos: [],
        };
      case "simula":
        return {
          vista: "simulador",
          modoMapa: "brecha",
          titulo: `Simulador de escenarios — ${cultivoActivo}`,
          subtitulo: "Rangos conservadores a optimistas sin doble conteo sobre la superficie actual",
          codigosResaltados: [],
          acercarACodigos: [],
        };
      case "prioriza":
        return {
          vista: "prioridad",
          modoMapa: "prioriza",
          titulo: `Prioridad municipal — ${cultivoActivo}`,
          subtitulo:
            "Núcleo robusto que se mantiene en los primeros puestos bajo 2.000 ponderaciones",
          codigosResaltados: [],
          acercarACodigos: [],
        };
      case "conexion_la_mojana":
        return {
          vista: "mapa",
          modoMapa: "cierre",
          titulo: "Cruce en La Mojana — Arroz",
          subtitulo:
            "Guaranda y San Marcos coinciden entre el golpe de 2021 y la prioridad estructural",
          codigosResaltados: CODIGOS_CIERRE_MOJANA,
          acercarACodigos: CODIGOS_MOJANA_TOP5,
        };
      case "metodologia":
        return {
          vista: "metodologia",
          modoMapa: "brecha",
          titulo: "Metodología, fuentes oficiales y reproducibilidad",
          subtitulo: "Parámetros preespecificados, reglas de muestra y verificación criptográfica",
          codigosResaltados: [],
          acercarACodigos: [],
        };
      case "mapa_brecha":
      default:
        return {
          vista: "mapa",
          modoMapa: "brecha",
          titulo: `Brecha de rendimiento — ${cultivoActivo}`,
          subtitulo: "Diferencia frente a los mejores municipios del mismo departamento",
          codigosResaltados: [],
          acercarACodigos: [],
        };
    }
  }, [seccionVisual, cultivoActivo, anioActivo, nombreDeptoActivo]);

  const hayFiltros =
    departamentoFiltro !== null || cuadranteFiltro !== null || anioActivo !== null;

  const activarCapitulo = (id: Exclude<IdSeccion, "portada">): void => {
    bloquearObserverHastaRef.current = Date.now() + 800;
    establecerSeccionActiva(id);
    if (
      id === "por_que_rinde_menos" ||
      id === "lo_que_no_sabemos" ||
      id === "matriz" ||
      id === "simula" ||
      id === "prioriza" ||
      id === "metodologia"
    ) {
      establecerAnioActivo(null);
    }
    const destino = document.getElementById(id);
    if (destino && rielPasosRef.current && window.innerWidth > 960) {
      const riel = rielPasosRef.current;
      riel.scrollTo({
        top: Math.max(0, destino.offsetTop - riel.offsetTop - 12),
        behavior: "smooth",
      });
    }
  };

  return (
    <main id="narrativa-caribe" className="tablero-seccion">
      <div className="tablero-marco" data-testid="tablero-marco">
        {/* Barra superior estilo tablero BI: filtros y linea de tiempo */}
        <div className="tablero-barra-superior" aria-label="Controles del tablero territorial">
          <div className="tablero-filtros-fila">
            <label className="tablero-filtro-grupo">
              <span className="tablero-filtro-etiqueta">Departamento</span>
              <select
                className="tablero-select"
                aria-label="Filtrar por departamento"
                data-testid="filtro-departamento"
                value={departamentoFiltro ?? ""}
                onChange={(e) =>
                  establecerDepartamentoFiltro(e.target.value === "" ? null : e.target.value)
                }
              >
                <option value="">Todos (7 deptos.)</option>
                {DEPARTAMENTOS_CARIBE.map((d) => (
                  <option key={d.codigo} value={d.codigo}>
                    {d.nombre}
                  </option>
                ))}
              </select>
            </label>

            <label className="tablero-filtro-grupo">
              <span className="tablero-filtro-etiqueta">Cuadrante</span>
              <select
                className="tablero-select"
                aria-label="Filtrar por cuadrante de decisión"
                data-testid="filtro-cuadrante"
                value={cuadranteFiltro ?? ""}
                onChange={(e) =>
                  establecerCuadranteFiltro(e.target.value === "" ? null : e.target.value)
                }
              >
                <option value="">Todos los cuadrantes</option>
                {CUADRANTES_FILTRO.map((c) => (
                  <option key={c.clave} value={c.clave}>
                    {c.etiqueta}
                  </option>
                ))}
              </select>
            </label>

            <div
              className="tablero-linea-tiempo"
              role="group"
              aria-label="Línea de tiempo anual 2019 a 2025"
              data-testid="linea-tiempo"
            >
              <span className="tablero-filtro-etiqueta">Línea de tiempo</span>
              <div className="linea-tiempo-botones">
                <button
                  type="button"
                  className="boton-anio"
                  aria-pressed={anioActivo === null}
                  onClick={() => establecerAnioActivo(null)}
                >
                  2019–2025
                </button>
                {ANIOS_TABLERO.map((anio) => (
                  <button
                    key={anio}
                    type="button"
                    className="boton-anio cifra-tabular"
                    aria-pressed={anioActivo === anio}
                    onClick={() => establecerAnioActivo(anio)}
                  >
                    {anio}
                  </button>
                ))}
              </div>
            </div>

            {hayFiltros ? (
              <button
                type="button"
                className="boton-limpiar-filtros"
                onClick={limpiarFiltros}
              >
                Limpiar filtros
              </button>
            ) : null}
          </div>

          {kpisTablero ? (
            <div className="tablero-kpis" data-testid="tablero-kpis">
              <div className="kpi-tarjeta">
                <span className="kpi-etiqueta">
                  Producción · {cultivoActivo} ({anioActivo ?? "2019–2025"})
                </span>
                <strong className="kpi-valor cifra-tabular" data-testid="kpi-produccion">
                  {formatearEntero(kpisTablero.produccionTotalT)} t
                </strong>
              </div>
              <div className="kpi-tarjeta">
                <span className="kpi-etiqueta">Área cosechada · {nombreDeptoActivo}</span>
                <strong className="kpi-valor cifra-tabular" data-testid="kpi-area">
                  {formatearEntero(kpisTablero.areaCosechadaTotalHa)} ha
                </strong>
              </div>
              <div className="kpi-tarjeta">
                <span className="kpi-etiqueta">Rendimiento ponderado</span>
                <strong className="kpi-valor cifra-tabular" data-testid="kpi-rendimiento">
                  {kpisTablero.rendimientoPonderadoTha !== null
                    ? `${formatearDecimal(kpisTablero.rendimientoPonderadoTha)} t/ha`
                    : "Sin dato"}
                </strong>
              </div>
              <div className="kpi-tarjeta">
                <span className="kpi-etiqueta">
                  {anioActivo !== null
                    ? `Municipios con cosecha (${anioActivo})`
                    : "Municipios elegibles"}
                </span>
                <strong className="kpi-valor cifra-tabular" data-testid="kpi-municipios">
                  {anioActivo !== null
                    ? formatearEntero(kpisTablero.municipiosConDato)
                    : `${formatearEntero(kpisTablero.municipiosElegibles)} de ${formatearEntero(
                        kpisTablero.municipiosConDato,
                      )}`}
                </strong>
              </div>
            </div>
          ) : null}
        </div>

        {/* Navegacion rapida por capitulos */}
        <nav className="tablero-capitulos-nav" aria-label="Capítulos de la historia">
          {pasosNarrativos.map((paso) => (
            <button
              key={`nav-${paso.id}`}
              type="button"
              className="boton-capitulo"
              aria-current={seccionVisual === paso.id ? "step" : undefined}
              onClick={() => activarCapitulo(paso.id)}
            >
              {paso.etiquetaCorta}
            </button>
          ))}
        </nav>

        {/* Cuerpo del tablero en dos paneles encerrados en el rectangulo */}
        <div className="tablero-cuerpo">
          <div className="columna-pasos tablero-narrativa" ref={rielPasosRef}>
            {pasosNarrativos.map((paso) => {
              const activo = seccionVisual === paso.id;
              return (
                <article
                  key={paso.id}
                  id={paso.id}
                  data-seccion={paso.id}
                  data-activo={activo ? "true" : "false"}
                  className="paso-narrativo"
                  onClick={() => activarCapitulo(paso.id)}
                >
                  <span className="paso-capitulo">{paso.capitulo}</span>
                  <h2 className="paso-titulo">{paso.titulo}</h2>

                  {paso.cifraHero ? (
                    <div className="paso-cifra-bloque">
                      <span
                        className={`paso-cifra-grande paso-cifra-${paso.cifraHero.tono} cifra-tabular`}
                      >
                        {paso.cifraHero.texto}
                      </span>
                      {paso.cifraHero.etiqueta ? (
                        <span className="paso-cifra-etiqueta">{paso.cifraHero.etiqueta}</span>
                      ) : null}
                    </div>
                  ) : null}

                  {modo === "decisor" ? (
                    <div className="paso-cuerpo">
                      {paso.lineasDecisor.map((linea, idx) => (
                        <p key={idx} className="paso-texto">
                          {linea}
                        </p>
                      ))}
                    </div>
                  ) : (
                    <p className="paso-texto">
                      {paso.textoTecnico}{" "}
                      {paso.mostrarEnlaceMetodologia ? (
                        <a
                          href="#metodologia"
                          className="enlace-metodologia"
                          onClick={(e) => {
                            e.preventDefault();
                            activarCapitulo("metodologia");
                          }}
                        >
                          Ver metodología
                        </a>
                      ) : null}
                    </p>
                  )}
                </article>
              );
            })}
          </div>

          <section
            className="panel-fijo tablero-visual"
            data-testid="panel-fijo"
            data-seccion-panel={seccionVisual}
            aria-label="Panel visual activo"
          >
            <div className="barra-herramientas-mapa">
              <div className="panel-encabezado-texto">
                <h2 className="panel-titulo">{estadoPanel.titulo}</h2>
                <span className="panel-subtitulo" data-testid="panel-subtitulo">
                  {estadoPanel.subtitulo}
                </span>
              </div>
              {estadoPanel.vista === "mapa" ||
              estadoPanel.vista === "matriz" ||
              estadoPanel.vista === "simulador" ||
              estadoPanel.vista === "prioridad" ? (
                <BuscadorMunicipio municipios={opcionesBuscador} />
              ) : null}
            </div>

            {errorDatos ? (
              <div className="estado-error" role="alert">
                {errorDatos}
              </div>
            ) : null}

            {estadoPanel.vista === "mapa" && seccionVisual === "conexion_la_mojana" ? (
              <div className="mojana-cruce-pills" aria-label="Municipios del cruce en La Mojana">
                {MUNICIPIOS_CRUCE_MOJANA.map((m) => (
                  <button
                    key={m.codigo}
                    type="button"
                    className="boton-cruce-mojana"
                    aria-pressed={municipioSeleccionado === m.codigo}
                    onClick={() => {
                      establecerCultivo("Arroz");
                      seleccionarMunicipio(m.codigo);
                    }}
                  >
                    {m.nombre}
                  </button>
                ))}
              </div>
            ) : null}

            {estadoPanel.vista === "pesas" ? (
              <GraficoPesas sistemas={sistemas} hallazgos={hallazgos} />
            ) : estadoPanel.vista === "calidad" ? (
              <PanelCalidad calidad={calidad} />
            ) : estadoPanel.vista === "simulador" ? (
              <SimuladorEscenarios escenarios={escenarios} />
            ) : estadoPanel.vista === "metodologia" ? (
              <PanelMetodologia meta={meta} />
            ) : estadoPanel.vista === "matriz" ? (
              <div
                className={
                  fichaActiva ? "area-mapa-y-ficha area-con-ficha" : "area-mapa-y-ficha"
                }
              >
                <GraficoMatriz
                  datosCultivo={datosCultivo}
                  departamentoFiltro={departamentoFiltro}
                  cuadranteFiltro={cuadranteFiltro}
                />
                <FichaMunicipal
                  municipio={fichaActiva}
                  totalElegibles={totalElegibles}
                  anioActivo={anioActivo}
                />
              </div>
            ) : estadoPanel.vista === "prioridad" ? (
              <div
                className={
                  fichaActiva ? "area-mapa-y-ficha area-con-ficha" : "area-mapa-y-ficha"
                }
              >
                <TablaPrioridad
                  datosCultivo={datosCultivo}
                  departamentoFiltro={departamentoFiltro}
                  cuadranteFiltro={cuadranteFiltro}
                />
                <FichaMunicipal
                  municipio={fichaActiva}
                  totalElegibles={totalElegibles}
                  anioActivo={anioActivo}
                />
              </div>
            ) : (
              <div
                className={
                  fichaActiva ? "area-mapa-y-ficha area-con-ficha" : "area-mapa-y-ficha"
                }
              >
                {topoJson ? (
                  <MapaCaribe
                    topoJson={topoJson}
                    datosCultivo={datosCultivo}
                    modoVisual={estadoPanel.modoMapa}
                    cultivosDominantes={cultivosDominantes}
                    codigosResaltados={estadoPanel.codigosResaltados}
                    acercarACodigos={estadoPanel.acercarACodigos}
                    departamentoFiltro={departamentoFiltro}
                    cuadranteFiltro={cuadranteFiltro}
                    anioActivo={anioActivo}
                    alMedirRender={setUltimoRenderMs}
                  />
                ) : (
                  <div className="mapa-contenedor">
                    <p className="texto-secundario" style={{ padding: "16px" }}>
                      Cargando cartografía del Caribe...
                    </p>
                  </div>
                )}

                <FichaMunicipal
                  municipio={fichaActiva}
                  totalElegibles={totalElegibles}
                  anioActivo={anioActivo}
                />
              </div>
            )}

            {modo === "tecnico" && estadoPanel.vista === "mapa" && ultimoRenderMs !== null ? (
              <div className="panel-nota-rendimiento cifra-tabular">
                Proyección vectorial de 195 municipios y 7 departamentos en{" "}
                {ultimoRenderMs.toFixed(1)} ms.
              </div>
            ) : null}
          </section>
        </div>
      </div>
    </main>
  );
}
