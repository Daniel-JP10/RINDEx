/* Archivo generado automaticamente desde contratos/web/ mediante npm run gen:tipos. */
/* No editar a mano. */

export interface ContratoSistemas {
  version_esquema: string;
  /**
   * @minItems 1
   */
  departamentos: {
    codigo_departamento: string;
    departamento: string;
    cultivo: string;
    sistemas: {
      [k: string]:
        | {
            area_cosechada_ha: number;
            produccion_t: number;
            rendimiento_tha: number | null;
            municipios_con_dato: number;
          }
        | undefined;
    };
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
    elegible: boolean;
    sistemas: {
      [k: string]:
        | {
            area_cosechada_ha: number;
            produccion_t: number;
            rendimiento_tha: number | null;
            anios_con_dato: number;
          }
        | undefined;
    };
  }[];
}
