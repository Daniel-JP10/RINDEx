import { useEffect } from "react";
import { ContenedorScroll } from "./componentes/ContenedorScroll.tsx";
import { Encabezado } from "./componentes/Encabezado.tsx";
import { PiePagina } from "./componentes/PiePagina.tsx";
import { Portada } from "./componentes/Portada.tsx";
import { usarTiendaRindex } from "./estado/tiendaRindex.ts";

export function App(): React.JSX.Element {
  const tema = usarTiendaRindex((s) => s.tema);

  useEffect(() => {
    const raiz = document.documentElement;
    if (tema === "sistema") {
      raiz.removeAttribute("data-tema");
    } else {
      raiz.setAttribute("data-tema", tema);
    }
  }, [tema]);

  return (
    <div className="aplicacion-rindex">
      <Encabezado />
      <Portada />
      <ContenedorScroll />
      <PiePagina />
    </div>
  );
}
