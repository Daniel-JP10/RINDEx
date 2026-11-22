import { useEffect, useMemo, useRef, useState } from "react";
import scrollama from "scrollama";
import {
  cargarMunicipiosCultivo,
  cargarTopoJsonCaribe,
  type ContratoMunicipiosCultivo,
  type ContratoTopoJsonCaribe,
} from "../datos/cargador.ts";
import { usarTiendaRindex, type IdSeccion } from "../estado/tiendaRindex.ts";
import { BuscadorMunicipio } from "./BuscadorMunicipio.tsx";
import { FichaMunicipal } from "./FichaMunicipal.tsx";
import { MapaCaribe } from "./MapaCaribe.tsx";

interface DefinicionPaso {
  id: Exclude<IdSeccion, "portada">;
  titulo: string;
  pregunta: string;
  decisor: string;
  tecnico: string;
  marcadorVisual: string;
}

const PASOS_NARRATIVOS: readonly DefinicionPaso[] = [
  {
    id: "panorama",
    titulo: "Tres cultivos en siete departamentos",
    pregunta: "¿Qué peso tiene cada cultivo en toneladas producidas y hectáreas cultivadas?",
    decisor:
      "La yuca lidera el tonelaje regional de alimentos y el maíz concentra la mayor superficie sembrada en el Caribe.",
    tecnico:
      "Marcador de panorama multianual: series ponderadas de regional.json y departamental.json con contraste H4 y marca del quiebre 2022.",
    marcadorVisual: "Sección interactiva en construcción — series regionales",
  },
  {
    id: "el_golpe",
    titulo: "El episodio concentrado de arroz en 2021",
    pregunta: "¿Dónde ocurrió el área no cosechada de arroz en 2021?",
    decisor:
      "Cinco municipios de La Mojana y la depresión momposina concentraron tres cuartas partes del área de arroz no cosechada de todo el Caribe en 2021.",
    tecnico:
      "Marcador descriptivo D8 sobre calidad.json (arroz_2021_concentracion), sin atribución causal climática al índice ONI.",
    marcadorVisual: "Sección interactiva en construcción — concentración 2021",
  },
  {
    id: "mapa_brecha",
    titulo: "Mapa de brecha de rendimiento por municipio",
    pregunta: "¿Dónde está la mayor ganancia respecto al estándar de cada departamento?",
    decisor:
      "Cada municipio se compara con el desempeño de los mejores productores de su propio departamento. El rayado señala zonas con baja precisión de registro.",
    tecnico:
      "Brecha relativa p50 contra P75 departamental por sistema productivo (>= 500 ha y >= 4 años). Carga perezosa del cultivo activo.",
    marcadorVisual: "Mapa activo",
  },
  {
    id: "por_que_rinde_menos",
    titulo: "La brecha tecnológica entre sistemas",
    pregunta: "¿Cuánto explica el sistema productivo dentro de un mismo municipio?",
    decisor:
      "El maíz tecnificado y el arroz mecanizado o bajo riego rinden sustancialmente más que los sistemas tradicionales o manuales dentro del mismo municipio.",
    tecnico:
      "Marcador de gráfico dumbbell sobre sistemas.json con razones Hodges-Lehmann H2 y H3 (Holm, D1, D6 insuficiente en riego vs. mecanizado).",
    marcadorVisual: "Sección interactiva en construcción — mancuernas de sistemas",
  },
  {
    id: "lo_que_no_sabemos",
    titulo: "Calidad de datos y lo que no sabemos",
    pregunta: "¿Qué límites imponen los datos administrativos de EVA?",
    decisor:
      "La repetición de cifras en yuca impide medir su tendencia interanual y exige cautela en campo frente a los cultivos de evidencia alta.",
    tecnico:
      "Marcador de diagnóstico de calidad D7/D9 sobre calidad.json (pares consecutivos idénticos, enteros y quiebre operativo 2022).",
    marcadorVisual: "Sección interactiva en construcción — calidad de series",
  },
  {
    id: "matriz",
    titulo: "Matriz de cuadrantes de decisión",
    pregunta: "¿Qué tipo de intervención corresponde a cada municipio?",
    decisor:
      "Los municipios elegibles se ubican en consolidar, proteger, tecnificar o intervención integral según su rendimiento y estabilidad.",
    tecnico:
      "Marcador de dispersión rendimiento vs. CV interanual con categoría estabilidad_no_medible para series poco informativas.",
    marcadorVisual: "Sección interactiva en construcción — matriz de cuadrantes",
  },
  {
    id: "simula",
    titulo: "Simulador de escenarios S1, S2 y S3",
    pregunta: "¿Cuánto volumen adicional se logra sin sembrar una hectárea más?",
    decisor:
      "Los resultados se expresan como rangos conservadores a optimistas (p10 a p90), separando mejoras productivas de recuperación de área no cosechada.",
    tecnico:
      "Marcador de simulador sin doble conteo max(S1, S2) + S3 desde escenarios.json, con trazo punteado en S2 extrapolado y S3 indicativo.",
    marcadorVisual: "Sección interactiva en construcción — simulador S1-S3",
  },
  {
    id: "prioriza",
    titulo: "Núcleo robusto de priorización",
    pregunta: "¿Qué municipios permanecen en el Top 20 bajo distintas ponderaciones?",
    decisor:
      "Un grupo compacto de municipios mantiene prioridad robusta sin importar el peso asignado a volumen, brecha, estabilidad o confiabilidad.",
    tecnico:
      "Marcador de tabla ordenable con sensibilidad de 2.000 juegos Dirichlet y exportación CSV desde municipios_<cultivo>.json.",
    marcadorVisual: "Sección interactiva en construcción — tabla priorizada",
  },
  {
    id: "conexion_la_mojana",
    titulo: "Conexión entre 2021 y prioridad estructural: La Mojana",
    pregunta: "¿Qué municipios de La Mojana coinciden entre el golpe de 2021 y el Top 20 de arroz?",
    decisor:
      "Guaranda y San Marcos encabezan tanto el pico de área no cosechada de 2021 como el núcleo de prioridad robusta en arroz, junto a Achí, Sucre y San Jacinto del Cauca en el Top 20.",
    tecnico:
      "Cruce bidireccional por código DANE entre calidad.json (arroz_2021_concentracion.top10_municipios) y municipios_arroz.json (priorizacion.rango <= 20).",
    marcadorVisual: "Sección interactiva en construcción — cruce La Mojana",
  },
  {
    id: "metodologia",
    titulo: "Metodología, desviaciones y auditoría independiente",
    pregunta: "¿Cómo se audita y reproduce cada cifra publicada?",
    decisor:
      "Toda cifra proviene de datos abiertos oficiales verificados mediante contratos de esquema y auditoría independiente.",
    tecnico:
      "Marcador de trazabilidad completa: hashes SHA-256 en meta.json, plan preespecificado, desviaciones D1–D9 y auditoría directa desde xlsx.",
    marcadorVisual: "Sección interactiva en construcción — ficha metodológica",
  },
];

export function ContenedorScroll(): React.JSX.Element {
  const cultivoActivo = usarTiendaRindex((s) => s.cultivoActivo);
  const modo = usarTiendaRindex((s) => s.modo);
  const seccionActiva = usarTiendaRindex((s) => s.seccionActiva);
  const municipioSeleccionado = usarTiendaRindex((s) => s.municipioSeleccionado);
  const establecerSeccionActiva = usarTiendaRindex((s) => s.establecerSeccionActiva);

  const [topoJson, setTopoJson] = useState<ContratoTopoJsonCaribe | null>(null);
  const [datosCultivo, setDatosCultivo] = useState<ContratoMunicipiosCultivo | null>(null);
  const [errorDatos, setErrorDatos] = useState<string | null>(null);
  const [ultimoRenderMs, setUltimoRenderMs] = useState<number | null>(null);

  const listaPasosRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let cancelado = false;
    cargarTopoJsonCaribe()
      .then((t) => {
        if (!cancelado) {
          setTopoJson(t);
        }
      })
      .catch((err: unknown) => {
        if (!cancelado) {
          setErrorDatos(
            err instanceof Error ? err.message : "Error al cargar la topología del Caribe.",
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
    const elCont = listaPasosRef.current;
    if (!elCont) {
      return undefined;
    }
    try {
      const scroller = scrollama();
      scroller
        .setup({
          step: ".paso-narrativo",
          offset: 0.5,
        })
        .onStepEnter((resp) => {
          const id = resp.element.getAttribute("data-seccion") as IdSeccion | null;
          if (id) {
            establecerSeccionActiva(id);
          }
        });

      const manejarResize = (): void => {
        scroller.resize();
      };
      window.addEventListener("resize", manejarResize);
      return () => {
        window.removeEventListener("resize", manejarResize);
        scroller.destroy();
      };
    } catch {
      return undefined;
    }
  }, [establecerSeccionActiva]);

  const opcionesBuscador = useMemo(() => {
    if (!datosCultivo) {
      return [];
    }
    return datosCultivo.municipios.map((m) => ({
      codigo: m.codigo,
      nombre: m.nombre,
      departamento: m.departamento,
    }));
  }, [datosCultivo]);

  const fichaActiva = useMemo(() => {
    if (!datosCultivo || !municipioSeleccionado) {
      return null;
    }
    return datosCultivo.municipios.find((m) => m.codigo === municipioSeleccionado) ?? null;
  }, [datosCultivo, municipioSeleccionado]);

  const pasoActual = PASOS_NARRATIVOS.find((p) => p.id === seccionActiva);

  return (
    <main id="narrativa-caribe" className="scroll-contenedor">
      <div className="columna-pasos" ref={listaPasosRef}>
        {PASOS_NARRATIVOS.map((paso) => {
          const activo =
            seccionActiva === paso.id ||
            (seccionActiva === "portada" && paso.id === "panorama");
          return (
            <article
              key={paso.id}
              id={paso.id}
              data-seccion={paso.id}
              data-activo={activo ? "true" : "false"}
              className="paso-narrativo"
            >
              <span className="paso-etiqueta-id">{paso.id}</span>
              <h2 className="paso-titulo">{paso.titulo}</h2>
              <p className="paso-texto">
                {modo === "decisor" ? paso.decisor : paso.tecnico}
              </p>
              <div className="paso-meta-marcador">
                <strong>Pregunta:</strong> {paso.pregunta}
                {paso.id !== "mapa_brecha" ? (
                  <div>
                    <em>{paso.marcadorVisual}</em>
                  </div>
                ) : null}
              </div>
            </article>
          );
        })}
      </div>

      <section className="panel-fijo" aria-label="Panel visual activo">
        <div className="barra-herramientas-mapa">
          <div>
            <h2>Mapa del Caribe — {cultivoActivo}</h2>
            <span className="buscador-opcion-depto">
              {pasoActual && pasoActual.id !== "mapa_brecha"
                ? `${pasoActual.titulo} · Vista base territorial`
                : "Brecha relativa p50 respecto al P75 departamental por sistema"}
            </span>
          </div>
          <BuscadorMunicipio municipios={opcionesBuscador} />
        </div>

        {errorDatos ? (
          <div className="estado-error" role="alert">
            {errorDatos}
          </div>
        ) : null}

        <div className="area-mapa-y-ficha">
          {topoJson ? (
            <MapaCaribe
              topoJson={topoJson}
              datosCultivo={datosCultivo}
              alMedirRender={setUltimoRenderMs}
            />
          ) : (
            <div className="mapa-contenedor">
              <p className="portada-nota" style={{ padding: "16px" }}>
                Cargando cartografía del Caribe...
              </p>
            </div>
          )}

          <FichaMunicipal municipio={fichaActiva} />
        </div>

        {modo === "tecnico" && ultimoRenderMs !== null ? (
          <div className="buscador-opcion-depto cifra-tabular">
            Proyección SVG de 195 municipios y 7 departamentos calculada en{" "}
            {ultimoRenderMs.toFixed(1)} ms.
          </div>
        ) : null}
      </section>
    </main>
  );
}
