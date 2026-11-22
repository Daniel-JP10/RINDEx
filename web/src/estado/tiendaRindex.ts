import { create } from "zustand";

export type CultivoClave = "Maíz" | "Yuca" | "Arroz";
export type ModoLectura = "decisor" | "tecnico";
export type TemaVisual = "sistema" | "claro" | "oscuro";

export type IdSeccion =
  | "portada"
  | "panorama"
  | "el_golpe"
  | "mapa_brecha"
  | "por_que_rinde_menos"
  | "lo_que_no_sabemos"
  | "matriz"
  | "simula"
  | "prioriza"
  | "metodologia"
  | "conexion_la_mojana";

export interface EstadoTiendaRindex {
  cultivoActivo: CultivoClave;
  modo: ModoLectura;
  tema: TemaVisual;
  municipioSeleccionado: string | null;
  seccionActiva: IdSeccion;
  establecerCultivo: (cultivo: CultivoClave) => void;
  establecerModo: (modo: ModoLectura) => void;
  establecerTema: (tema: TemaVisual) => void;
  seleccionarMunicipio: (codigo: string | null) => void;
  establecerSeccionActiva: (seccion: IdSeccion) => void;
  reiniciar: () => void;
}

const ESTADO_INICIAL = {
  cultivoActivo: "Maíz" as CultivoClave,
  modo: "decisor" as ModoLectura,
  tema: "sistema" as TemaVisual,
  municipioSeleccionado: null as string | null,
  seccionActiva: "portada" as IdSeccion,
};

export const usarTiendaRindex = create<EstadoTiendaRindex>((set) => ({
  ...ESTADO_INICIAL,
  establecerCultivo: (cultivoActivo) => set({ cultivoActivo }),
  establecerModo: (modo) => set({ modo }),
  establecerTema: (tema) => set({ tema }),
  seleccionarMunicipio: (municipioSeleccionado) => set({ municipioSeleccionado }),
  establecerSeccionActiva: (seccionActiva) => set({ seccionActiva }),
  reiniciar: () => set({ ...ESTADO_INICIAL }),
}));
