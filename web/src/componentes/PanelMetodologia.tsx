/* Ficha metodologica, parametros de reproducibilidad y trazabilidad de fuentes oficiales */

import { usarTiendaRindex } from "../estado/tiendaRindex.ts";
import type { ContratoMeta } from "../tipos/generados/meta.ts";
import { formatearEntero, formatearPorcentaje } from "../utilidades/formato.ts";

interface PropsPanelMetodologia {
  meta: ContratoMeta | null;
}

export function PanelMetodologia({ meta }: PropsPanelMetodologia): React.JSX.Element {
  const modo = usarTiendaRindex((s) => s.modo);

  if (!meta) {
    return (
      <div className="panel-analitico">
        <p className="texto-secundario">Cargando ficha metodológica y fuentes oficiales...</p>
      </div>
    );
  }

  return (
    <div className="panel-analitico" data-testid="panel-metodologia">
      <div className="meto-grid">
        <section className="meto-tarjeta">
          <h3>Alcance y reglas de elegibilidad</h3>
          <ul className="meto-lista">
            <li>
              <strong>Edición:</strong> {meta.nombre_visible} ({meta.anios.inicio}–{meta.anios.fin})
            </li>
            <li>
              <strong>Cultivos evaluados:</strong> {meta.cultivos.join(", ")}
            </li>
            <li>
              <strong>Umbral mínimo municipal:</strong>{" "}
              <span className="cifra-tabular">
                {formatearEntero(meta.umbrales.area_cosechada_minima_ha)} ha
              </span>{" "}
              cosechadas acumuladas y{" "}
              <span className="cifra-tabular">{meta.umbrales.anios_minimos_con_dato}</span> años con
              registro
            </li>
            <li>
              <strong>Rendimiento agregado:</strong> siempre producción total dividida por área
              cosechada total, nunca promedio de rendimientos
            </li>
          </ul>
        </section>

        <section className="meto-tarjeta">
          <h3>Parámetros estadísticos y validación</h3>
          <ul className="meto-lista">
            <li>
              <strong>Bootstrap de dos niveles:</strong>{" "}
              <span className="cifra-tabular">
                {formatearEntero(meta.umbrales.replicas_bootstrap)}
              </span>{" "}
              réplicas con suma réplica a réplica en totales regionales
            </li>
            <li>
              <strong>Sensibilidad de prioridad:</strong>{" "}
              <span className="cifra-tabular">
                {formatearEntero(meta.umbrales.juegos_dirichlet)}
              </span>{" "}
              juegos de ponderación y umbral robusto del{" "}
              <span className="cifra-tabular">
                {formatearPorcentaje(meta.umbrales.umbral_robustez_top_pct, 0)}
              </span>{" "}
              entre los {meta.umbrales.top_k} primeros
            </li>
            <li>
              <strong>Pruebas y multiplicidad:</strong> pruebas no paramétricas por defecto con
              corrección de Holm y regla de muestra mínima
            </li>
            {modo === "tecnico" ? (
              <li>
                <strong>Semilla fija reproducible:</strong>{" "}
                <span className="cifra-tabular">{meta.semilla_aleatoria}</span>
              </li>
            ) : null}
          </ul>
        </section>
      </div>

      <section className="meto-tarjeta">
        <h3>Fuentes oficiales verificadas</h3>
        <div className="meto-fuentes">
          {meta.fuentes.map((f) => (
            <div key={f.id} className="meto-fuente-item">
              <strong>{f.nombre}</strong>
              <span className="texto-secundario">{f.licencia}</span>
              {modo === "tecnico" ? (
                <span className="meto-huella cifra-tabular">
                  Huella criptográfica: {f.hash_sha256.slice(0, 16).toLowerCase()}
                </span>
              ) : null}
            </div>
          ))}
        </div>
      </section>

      {meta.departamentos_excluidos.length > 0 ? (
        <div className="calidad-nota-corte">
          <strong>Exclusión territorial documentada:</strong>{" "}
          {meta.departamentos_excluidos
            .map((d) => `${d.nombre} (${d.motivo})`)
            .join("; ")}
          .
        </div>
      ) : null}
    </div>
  );
}
