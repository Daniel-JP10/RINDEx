/* Archivo generado automaticamente desde contratos/web/ mediante npm run gen:tipos. */
/* No editar a mano. */

export interface ContratoMunicipiosMaiz {
  version_esquema: string;
  cultivo: string;
  nivel_evidencia_cultivo: "alto" | "medio" | "bajo";
  /**
   * @minItems 195
   * @maxItems 195
   */
  municipios: {
    codigo: string;
    nombre: string;
    codigo_departamento: string;
    departamento: string;
    con_datos: boolean;
    elegible: boolean;
    anios_con_dato: number;
    area_sembrada_ha: number;
    area_cosechada_ha: number;
    produccion_t: number;
    rendimiento_tha: number | null;
    tasa_area_no_cosechada_pct: number | null;
    cv_interanual_pct: number | null;
    nivel_evidencia: "alto" | "medio" | "bajo" | "sin_datos";
    calidad: {
      proporcion_repetidos_pct: number;
      serie_poco_informativa: boolean;
      filas_atipicas: number;
      excluido_d4: boolean;
    };
    rendimiento_por_sistema: {
      [k: string]: (number | null) | undefined;
    };
    serie_anual: {
      anio: number;
      area_sembrada_ha: number;
      area_cosechada_ha: number;
      produccion_t: number;
      rendimiento_tha: number | null;
    }[];
    brecha: {
      brecha_relativa_pct: number | null;
      brecha_p10_tha: number | null;
      brecha_p50_tha: number | null;
      brecha_p90_tha: number | null;
      ganancia_p10_t: number | null;
      ganancia_p50_t: number | null;
      ganancia_p90_t: number | null;
    };
    priorizacion: {
      cuadrante: string | null;
      indice_prioridad: number | null;
      rango: number | null;
      rango_p10: number | null;
      rango_p90: number | null;
      proporcion_top20_pct: number | null;
      prioridad_robusta: boolean;
    };
  }[];
}
