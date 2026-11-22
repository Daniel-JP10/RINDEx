/* Archivo generado automaticamente desde contratos/web/ mediante npm run gen:tipos. */
/* No editar a mano. */

export interface ContratoHallazgos {
  version_esquema: string;
  /**
   * @minItems 15
   */
  tarjetas: {
    id: string;
    cultivo: string;
    texto_decisor: string;
    texto_tecnico: string;
    cifra: number;
    unidad: string;
    /**
     * @minItems 2
     * @maxItems 2
     */
    intervalo: number[] | null;
    n: number;
    prueba: string;
    p_ajustado: number | null;
    robustez: string;
    nivel_evidencia: "alto" | "medio" | "bajo";
    origen: {
      parquet: string;
      funcion: string;
      columna_cifra: string;
      filtro?: string;
    };
  }[];
}
