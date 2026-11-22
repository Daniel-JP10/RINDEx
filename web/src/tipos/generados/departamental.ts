/* Archivo generado automaticamente desde contratos/web/ mediante npm run gen:tipos. */
/* No editar a mano. */

export interface ContratoDepartamental {
  version_esquema: string;
  /**
   * @minItems 1
   */
  registros: {
    codigo_departamento: string;
    departamento: string;
    cultivo: string;
    anio: number;
    area_sembrada_ha: number;
    area_cosechada_ha: number;
    area_no_cosechada_ha: number;
    produccion_t: number;
    rendimiento_tha: number;
    tasa_area_no_cosechada_pct: number | null;
    quiebre_2022: boolean;
    anio_posiblemente_incompleto: boolean;
    clase_enso: "nina" | "nino" | "neutro";
    oni_anual: number;
  }[];
}
