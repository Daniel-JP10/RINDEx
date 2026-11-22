import { useId, useMemo, useState } from "react";
import { usarTiendaRindex } from "../estado/tiendaRindex.ts";

export interface OpcionMunicipio {
  codigo: string;
  nombre: string;
  departamento: string;
}

interface PropsBuscadorMunicipio {
  municipios: readonly OpcionMunicipio[];
}

export function BuscadorMunicipio({
  municipios,
}: PropsBuscadorMunicipio): React.JSX.Element {
  const municipioSeleccionado = usarTiendaRindex((s) => s.municipioSeleccionado);
  const seleccionarMunicipio = usarTiendaRindex((s) => s.seleccionarMunicipio);

  const [texto, setTexto] = useState("");
  const [abierto, setAbierto] = useState(false);
  const [indiceResaltado, setIndiceResaltado] = useState(0);

  const idLista = useId();
  const idEntrada = useId();

  const filtrados = useMemo(() => {
    const q = texto.trim().toLowerCase();
    const base = [...municipios].sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));
    if (!q) {
      return base.slice(0, 12);
    }
    return base
      .filter(
        (m) =>
          m.nombre.toLowerCase().includes(q) ||
          m.departamento.toLowerCase().includes(q) ||
          m.codigo.includes(q),
      )
      .slice(0, 15);
  }, [municipios, texto]);

  const confirmarSeleccion = (opcion: OpcionMunicipio): void => {
    seleccionarMunicipio(opcion.codigo);
    setTexto(`${opcion.nombre} (${opcion.departamento})`);
    setAbierto(false);
  };

  const manejarTeclado = (e: React.KeyboardEvent<HTMLInputElement>): void => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setAbierto(true);
      setIndiceResaltado((prev) =>
        filtrados.length === 0 ? 0 : Math.min(prev + 1, filtrados.length - 1),
      );
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setAbierto(true);
      setIndiceResaltado((prev) => Math.max(prev - 1, 0));
    } else if (e.key === "Enter") {
      const opcion = filtrados[indiceResaltado];
      if (opcion) {
        e.preventDefault();
        confirmarSeleccion(opcion);
      }
    } else if (e.key === "Escape") {
      setAbierto(false);
    }
  };

  const opcionActiva = filtrados[indiceResaltado];

  return (
    <div className="buscador-envoltura">
      <label htmlFor={idEntrada} className="sr-only">
        Buscar municipio del Caribe
      </label>
      <input
        id={idEntrada}
        type="text"
        role="combobox"
        aria-autocomplete="list"
        aria-expanded={abierto}
        aria-controls={idLista}
        aria-activedescendant={
          abierto && opcionActiva ? `${idLista}-${opcionActiva.codigo}` : undefined
        }
        className="buscador-entrada"
        placeholder="Buscar municipio o departamento..."
        value={texto}
        onFocus={() => setAbierto(true)}
        onBlur={() => {
          window.setTimeout(() => setAbierto(false), 120);
        }}
        onChange={(e) => {
          setTexto(e.target.value);
          setIndiceResaltado(0);
          setAbierto(true);
        }}
        onKeyDown={manejarTeclado}
      />
      {abierto && filtrados.length > 0 ? (
        <ul id={idLista} role="listbox" className="buscador-lista">
          {filtrados.map((op, idx) => (
            <li
              key={op.codigo}
              id={`${idLista}-${op.codigo}`}
              role="option"
              aria-selected={
                indiceResaltado === idx || municipioSeleccionado === op.codigo
              }
              className="buscador-opcion"
              onMouseDown={(e) => {
                e.preventDefault();
                confirmarSeleccion(op);
              }}
            >
              <span>{op.nombre}</span>
              <span className="buscador-opcion-depto">{op.departamento}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
