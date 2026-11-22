/* Archivo generado automaticamente desde contratos/web/ mediante npm run gen:tipos. */
/* No editar a mano. */

export interface ContratoCalidad {
  version_esquema: string;
  /**
   * @minItems 3
   */
  por_cultivo: {
    cultivo: string;
    series_evaluadas: number;
    pares_consecutivos: number;
    pares_identicos: number;
    pct_pares_identicos: number;
    series_poco_informativas: number;
    filas_semestrales: number;
    filas_enteras_semestral: number;
    pct_rendimientos_enteros: number;
    pct_enteros_anual: number;
    nivel_evidencia: "alto" | "medio" | "bajo";
  }[];
  /**
   * @minItems 3
   */
  resumen_evidencia_municipal: {
    cultivo: string;
    alto: number;
    medio: number;
    bajo: number;
    total_con_datos: number;
  }[];
  arroz_2021_concentracion: {
    area_sembrada_regional_ha: number;
    area_cosechada_regional_ha: number;
    area_no_cosechada_regional_ha: number;
    tasa_regional_pct: number;
    top5_area_no_cosechada_ha: number;
    top5_pct_regional: number;
    top10_area_no_cosechada_ha: number;
    top10_pct_regional: number;
    /**
     * @minItems 10
     * @maxItems 10
     */
    top10_municipios: {
      rango: number;
      codigo: string;
      nombre: string;
      departamento: string;
      area_sembrada_ha: number;
      area_cosechada_ha: number;
      area_no_cosechada_ha: number;
      tasa_propia_pct: number;
      pct_total_regional: number;
    }[];
  };
}
