/* Archivo generado automaticamente desde contratos/web/ mediante npm run gen:tipos. */
/* No editar a mano. */

export interface ContratoMeta {
  version_esquema: string;
  id_edicion: string;
  nombre_visible: string;
  region: string;
  anios: {
    inicio: number;
    fin: number;
  };
  /**
   * @minItems 1
   */
  cultivos: string[];
  departamentos: {
    [k: string]: string | undefined;
  };
  departamentos_excluidos: {
    codigo: string;
    nombre: string;
    motivo: string;
  }[];
  commit_hash: string;
  fecha_generacion: string;
  semilla_aleatoria: number;
  umbrales: {
    area_cosechada_minima_ha: number;
    anios_minimos_con_dato: number;
    replicas_bootstrap: number;
    juegos_dirichlet: number;
    top_k: number;
    umbral_robustez_top_pct: number;
  };
  /**
   * @minItems 3
   */
  fuentes: {
    id: string;
    nombre: string;
    url: string;
    licencia: string;
    hash_sha256: string;
    version?: string;
  }[];
}
