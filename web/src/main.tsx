import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@fontsource-variable/fraunces";
import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/500.css";
import "@fontsource/ibm-plex-sans/600.css";
import "./estilos/tokens.css";
import "./estilos/global.css";
import { App } from "./App.tsx";

const raiz = document.getElementById("root");
if (!raiz) {
  throw new Error("No se encontro el elemento #root para montar RINDEx.");
}

createRoot(raiz).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
