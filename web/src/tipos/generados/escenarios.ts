/* Archivo generado automaticamente desde contratos/web/ mediante npm run gen:tipos. */
/* No editar a mano. */

export interface ContratoEscenarios {
  version_esquema: string;
  /**
   * @minItems 3
   */
  totales_regionales: {
    cultivo: string;
    municipios_elegibles: number;
    produccion_anual_media_t: number;
    s1_p10_t: number;
    s1_p50_t: number;
    s1_p90_t: number;
    s1_p50_pct_prod: number;
    s2_p10_t: number;
    s2_p50_t: number;
    s2_p90_t: number;
    s2_p50_pct_prod: number;
    s2_pct_extrapolado: number;
    s3_p10_t: number;
    s3_p50_t: number;
    s3_p90_t: number;
    s3_p50_pct_prod: number;
    combinado_p10_t: number;
    combinado_p50_t: number;
    combinado_p90_t: number;
    combinado_p50_pct_prod: number;
  }[];
  /**
   * @minItems 1
   */
  municipios: {
    codigo: string;
    nombre: string;
    codigo_departamento: string;
    departamento: string;
    cultivo: string;
    area_cosechada_media_anual_ha: number;
    produccion_media_anual_t: number;
    rendimiento_tha: number;
    s1_p10_t: number;
    s1_p50_t: number;
    s1_p90_t: number;
    s2_area_convertible_ha: number;
    s2_p10_t: number;
    s2_p50_t: number;
    s2_p90_t: number;
    extrapolado: boolean;
    s3_p10_t: number;
    s3_p50_t: number;
    s3_p90_t: number;
    indicativo: boolean;
    excluido_d4: boolean;
    combinado_p10_t: number;
    combinado_p50_t: number;
    combinado_p90_t: number;
  }[];
}
