/* Tabla interactiva ordenable de priorizacion robusta con exportacion CSV */

import { useMemo, useState } from "react";
import type { ContratoMunicipiosCultivo, MunicipioCultivoItem } from "../datos/cargador.ts";
import { usarTiendaRindex } from "../estado/tiendaRindex.ts";
import {
  etiquetarCuadrante,
  etiquetarEvidencia,
  formatearDecimal,
  formatearEntero,
  formatearPorcentaje,
} from "../utilidades/formato.ts";
import { coincideFiltrosMunicipio } from "../utilidades/tablero.ts";

interface PropsTablaPrioridad {
  datosCultivo: ContratoMunicipiosCultivo | null;
  departamentoFiltro: string | null;
  cuadranteFiltro: string | null;
}

type ColumnaOrden = "rango" | "nombre" | "indice" | "brecha" | "ganancia" | "top20";

export function TablaPrioridad({
  datosCultivo,
  departamentoFiltro,
  cuadranteFiltro,
}: PropsTablaPrioridad): React.JSX.Element {
  const cultivoActivo = usarTiendaRindex((s) => s.cultivoActivo);
  const municipioSeleccionado = usarTiendaRindex((s) => s.municipioSeleccionado);
  const seleccionarMunicipio = usarTiendaRindex((s) => s.seleccionarMunicipio);

  const [columnaOrden, setColumnaOrden] = useState<ColumnaOrden>("rango");
  const [ascendente, setAscendente] = useState<boolean>(true);
  const [soloRobustos, setSoloRobustos] = useState<boolean>(false);

  const filas = useMemo(() => {
    if (!datosCultivo) {
      return [] as MunicipioCultivoItem[];
    }
    const base = datosCultivo.municipios.filter(
      (m) =>
        m.elegible &&
        m.priorizacion.rango !== null &&
        coincideFiltrosMunicipio(m, departamentoFiltro, cuadranteFiltro) &&
        (!soloRobustos || m.priorizacion.prioridad_robusta),
    );

    const factor = ascendente ? 1 : -1;
    return [...base].sort((a, b) => {
      switch (columnaOrden) {
        case "nombre":
          return a.nombre.localeCompare(b.nombre, "es") * factor;
        case "indice":
          return (
            ((a.priorizacion.indice_prioridad ?? 0) - (b.priorizacion.indice_prioridad ?? 0)) *
            factor
          );
        case "brecha":
          return (
            ((a.brecha.brecha_relativa_pct ?? 0) - (b.brecha.brecha_relativa_pct ?? 0)) * factor
          );
        case "ganancia":
          return ((a.brecha.ganancia_p50_t ?? 0) - (b.brecha.ganancia_p50_t ?? 0)) * factor;
        case "top20":
          return (
            ((a.priorizacion.proporcion_top20_pct ?? 0) -
              (b.priorizacion.proporcion_top20_pct ?? 0)) *
            factor
          );
        case "rango":
        default:
          return ((a.priorizacion.rango ?? 999) - (b.priorizacion.rango ?? 999)) * factor;
      }
    });
  }, [datosCultivo, departamentoFiltro, cuadranteFiltro, soloRobustos, columnaOrden, ascendente]);

  const totalRobustos = useMemo(
    () => filas.filter((f) => f.priorizacion.prioridad_robusta).length,
    [filas],
  );

  const alternarOrden = (col: ColumnaOrden): void => {
    if (columnaOrden === col) {
      setAscendente((prev) => !prev);
    } else {
      setColumnaOrden(col);
      setAscendente(col === "rango" || col === "nombre");
    }
  };

  const descargarCsv = (): void => {
    const encabezados = [
      "Puesto",
      "Codigo",
      "Municipio",
      "Departamento",
      "Indice prioridad",
      "Rango p10",
      "Rango p90",
      "Porcentaje en los 20 primeros",
      "Nucleo robusto",
      "Brecha relativa (%)",
      "Ganancia mediana anual (t)",
      "Cuadrante",
      "Evidencia",
    ];
    const lineas = [
      encabezados.join(","),
      ...filas.map((m) =>
        [
          m.priorizacion.rango ?? "",
          m.codigo,
          `"${m.nombre}"`,
          `"${m.departamento}"`,
          m.priorizacion.indice_prioridad ?? "",
          m.priorizacion.rango_p10 ?? "",
          m.priorizacion.rango_p90 ?? "",
          m.priorizacion.proporcion_top20_pct ?? "",
          m.priorizacion.prioridad_robusta ? "Si" : "No",
          m.brecha.brecha_relativa_pct ?? "",
          m.brecha.ganancia_p50_t ?? "",
          `"${etiquetarCuadrante(m.priorizacion.cuadrante)}"`,
          `"${etiquetarEvidencia(m.nivel_evidencia)}"`,
        ].join(","),
      ),
    ];
    const blob = new Blob([lineas.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement("a");
    enlace.href = url;
    enlace.download = `rindex-prioridad-${cultivoActivo.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")}.csv`;
    enlace.click();
    URL.revokeObjectURL(url);
  };

  if (!datosCultivo) {
    return (
      <div className="panel-analitico">
        <p className="texto-secundario">Cargando tabla de priorización...</p>
      </div>
    );
  }

  return (
    <div className="tabla-prioridad-bloque" data-testid="tabla-prioridad">
      <div className="tabla-prioridad-barra">
        <label className="simulador-check">
          <input
            type="checkbox"
            checked={soloRobustos}
            onChange={(e) => setSoloRobustos(e.target.checked)}
          />
          <span>
            Mostrar solo núcleo robusto ({formatearEntero(totalRobustos)})
          </span>
        </label>

        <button
          type="button"
          className="boton-descargar-csv"
          onClick={descargarCsv}
          disabled={filas.length === 0}
        >
          Exportar CSV ({formatearEntero(filas.length)})
        </button>
      </div>

      <div className="tabla-prioridad-scroll">
        <table className="tabla-prioridad">
          <thead>
            <tr>
              <th>
                <button type="button" className="boton-orden" onClick={() => alternarOrden("rango")}>
                  Puesto
                </button>
              </th>
              <th>
                <button type="button" className="boton-orden" onClick={() => alternarOrden("nombre")}>
                  Municipio
                </button>
              </th>
              <th>
                <button type="button" className="boton-orden" onClick={() => alternarOrden("indice")}>
                  Índice
                </button>
              </th>
              <th>
                <button type="button" className="boton-orden" onClick={() => alternarOrden("brecha")}>
                  Brecha
                </button>
              </th>
              <th>
                <button
                  type="button"
                  className="boton-orden"
                  onClick={() => alternarOrden("ganancia")}
                >
                  Ganancia mediana
                </button>
              </th>
              <th>
                <button type="button" className="boton-orden" onClick={() => alternarOrden("top20")}>
                  En los 20 primeros
                </button>
              </th>
              <th>Cuadrante</th>
            </tr>
          </thead>
          <tbody>
            {filas.slice(0, 40).map((m) => {
              const sel = municipioSeleccionado === m.codigo;
              return (
                <tr
                  key={m.codigo}
                  className={sel ? "fila-prioridad fila-seleccionada" : "fila-prioridad"}
                  onClick={() => seleccionarMunicipio(m.codigo)}
                >
                  <td className="cifra-tabular">
                    <strong>#{m.priorizacion.rango}</strong>
                    {m.priorizacion.prioridad_robusta ? (
                      <span className="insignia-robusto" title="Núcleo de prioridad robusta">
                        Robusto
                      </span>
                    ) : null}
                  </td>
                  <td>
                    <span className="tabla-mpio-nombre">{m.nombre}</span>
                    <span className="tabla-mpio-depto">{m.departamento}</span>
                  </td>
                  <td className="cifra-tabular">
                    {m.priorizacion.indice_prioridad !== null
                      ? formatearDecimal(m.priorizacion.indice_prioridad, 1)
                      : "N/D"}
                  </td>
                  <td className="cifra-tabular">
                    {m.brecha.brecha_relativa_pct !== null
                      ? formatearPorcentaje(m.brecha.brecha_relativa_pct)
                      : "N/D"}
                  </td>
                  <td className="cifra-tabular">
                    {m.brecha.ganancia_p50_t !== null
                      ? `${formatearEntero(m.brecha.ganancia_p50_t)} t`
                      : "N/D"}
                  </td>
                  <td className="cifra-tabular">
                    {m.priorizacion.proporcion_top20_pct !== null
                      ? formatearPorcentaje(m.priorizacion.proporcion_top20_pct)
                      : "N/D"}
                    {m.priorizacion.rango_p10 !== null && m.priorizacion.rango_p90 !== null ? (
                      <span className="tabla-rango-p">
                        ({Math.round(m.priorizacion.rango_p10)}–{Math.round(m.priorizacion.rango_p90)})
                      </span>
                    ) : null}
                  </td>
                  <td>{etiquetarCuadrante(m.priorizacion.cuadrante)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
