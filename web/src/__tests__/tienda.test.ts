import { beforeEach, describe, expect, it } from "vitest";
import { usarTiendaRindex } from "../estado/tiendaRindex.ts";

describe("Tienda de estado Zustand de RINDEx", () => {
  beforeEach(() => {
    usarTiendaRindex.getState().reiniciar();
  });

  it("actualiza el cultivo activo, el modo, el tema y el municipio seleccionado", () => {
    const estadoInicial = usarTiendaRindex.getState();
    expect(estadoInicial.cultivoActivo).toBe("Maíz");
    expect(estadoInicial.modo).toBe("decisor");
    expect(estadoInicial.municipioSeleccionado).toBeNull();

    estadoInicial.establecerCultivo("Arroz");
    estadoInicial.establecerModo("tecnico");
    estadoInicial.establecerTema("oscuro");
    estadoInicial.seleccionarMunicipio("70265");
    estadoInicial.establecerSeccionActiva("mapa_brecha");

    const estadoActual = usarTiendaRindex.getState();
    expect(estadoActual.cultivoActivo).toBe("Arroz");
    expect(estadoActual.modo).toBe("tecnico");
    expect(estadoActual.tema).toBe("oscuro");
    expect(estadoActual.municipioSeleccionado).toBe("70265");
    expect(estadoActual.seccionActiva).toBe("mapa_brecha");
  });
});
