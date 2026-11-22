import { CultivoClave, ModoLectura, TemaVisual, usarTiendaRindex } from "../estado/tiendaRindex.ts";
import { LogoRindex } from "./LogoRindex.tsx";

const CULTIVOS: readonly CultivoClave[] = ["Maíz", "Yuca", "Arroz"];

export function Encabezado(): React.JSX.Element {
  const cultivoActivo = usarTiendaRindex((s) => s.cultivoActivo);
  const modo = usarTiendaRindex((s) => s.modo);
  const tema = usarTiendaRindex((s) => s.tema);
  const establecerCultivo = usarTiendaRindex((s) => s.establecerCultivo);
  const establecerModo = usarTiendaRindex((s) => s.establecerModo);
  const establecerTema = usarTiendaRindex((s) => s.establecerTema);

  const siguienteTema: Record<TemaVisual, TemaVisual> = {
    sistema: "oscuro",
    oscuro: "claro",
    claro: "sistema",
  };

  const etiquetaTema: Record<TemaVisual, string> = {
    sistema: "Tema: sistema",
    claro: "Tema: claro",
    oscuro: "Tema: oscuro",
  };

  return (
    <header className="encabezado" role="banner">
      <div className="encabezado-interior">
        <div className="encabezado-marca">
          <a href="#portada" className="logo-rindex">
            <LogoRindex />
          </a>
          <span className="etiqueta-edicion">Caribe 2019–2025</span>
        </div>

        <nav className="pildoras-cultivo" aria-label="Cultivo activo">
          {CULTIVOS.map((cultivo) => (
            <button
              key={cultivo}
              type="button"
              className="pildora-cultivo"
              data-cultivo={cultivo}
              aria-pressed={cultivoActivo === cultivo}
              onClick={() => establecerCultivo(cultivo)}
            >
              <span className="pildora-punto" aria-hidden="true" />
              <span>{cultivo}</span>
            </button>
          ))}
        </nav>

        <div className="controles-derecha">
          <div
            className="interruptor-modo"
            role="radiogroup"
            aria-label="Modo de lectura"
          >
            {(["decisor", "tecnico"] as const).map((opcion: ModoLectura) => (
              <button
                key={opcion}
                type="button"
                role="radio"
                className="boton-modo"
                aria-checked={modo === opcion}
                onClick={() => establecerModo(opcion)}
              >
                {opcion === "decisor" ? "Decisor" : "Técnico"}
              </button>
            ))}
          </div>

          <button
            type="button"
            className="boton-tema"
            onClick={() => establecerTema(siguienteTema[tema])}
            aria-label="Cambiar tema visual"
          >
            {etiquetaTema[tema]}
          </button>
        </div>
      </div>
    </header>
  );
}
