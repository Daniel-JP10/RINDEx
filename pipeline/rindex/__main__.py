"""Punto de entrada unificado para ejecutar todo el pipeline RINDEx y la auditoria independiente."""

import argparse
import subprocess
import sys
import time
from pathlib import Path

from rindex.agregacion import ejecutar_agregacion
from rindex.calidad import ejecutar_diagnostico_calidad
from rindex.evidencia import ejecutar_evidencia
from rindex.exportar import ejecutar_exportacion_web
from rindex.geografia import ejecutar_geografia
from rindex.inferencia import ejecutar_inferencia_completa
from rindex.ingesta import ejecutar_ingesta
from rindex.priorizacion import ejecutar_priorizacion_completa


def ejecutar_pipeline_completo(ruta_config: str | Path) -> float:
    t0 = time.perf_counter()
    ruta_cfg = Path(ruta_config)

    ejecutar_ingesta(ruta_cfg)
    ejecutar_agregacion(ruta_cfg)
    ejecutar_diagnostico_calidad(ruta_cfg)
    ejecutar_inferencia_completa(ruta_cfg)
    ejecutar_priorizacion_completa(ruta_cfg)
    ejecutar_evidencia(ruta_cfg)
    ejecutar_geografia(ruta_cfg)
    ejecutar_exportacion_web(ruta_cfg)

    ruta_auditoria = Path("herramientas/auditoria_independiente.py")
    subprocess.run(
        [sys.executable, str(ruta_auditoria)],
        check=True,
    )

    tiempo_total = time.perf_counter() - t0
    print(f"Pipeline completo y auditoria independiente ejecutados en {tiempo_total:.2f} s.")
    return tiempo_total


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ejecuta el pipeline completo de RINDEx y la auditoria independiente."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Ruta al archivo YAML de configuracion de la edicion.",
    )
    args = parser.parse_args()
    ejecutar_pipeline_completo(args.config)


if __name__ == "__main__":
    main()
