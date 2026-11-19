"""Ejecuta las etapas 3 y 4 sobre todas las instancias disponibles."""

import argparse
import glob
import os
import time

from etapa3 import resolver_GC
from etapa4 import resolver_GC_nativo


def listar_instancias(carpeta):
    patron = os.path.join(carpeta, "*.txt")
    return sorted(glob.glob(patron))


def ejecutar_run(nombre, funcion, instancia, segundos, **kwargs):
    inicio = time.monotonic()
    try:
        objetivo, restricciones, variables = funcion(
            instancia,
            segundos,
            **kwargs,
        )
        estado = "ok"
        error = None
    except Exception as exc:
        objetivo = None
        restricciones = None
        variables = None
        estado = "error"
        error = str(exc)
    transcurrido = time.monotonic() - inicio

    print(
        f"{nombre:18} | objetivo={objetivo if objetivo is not None else '-'}"
        f" | restricciones={restricciones if restricciones is not None else '-'}"
        f" | variables={variables if variables is not None else '-'}"
        f" | tiempo={transcurrido:.3f}s"
        f" | {estado}"
        + (f" | {error}" if error else "")
    )
    return estado == "ok"


def main():
    parser = argparse.ArgumentParser(
        description="Prueba las etapas 3 y 4 sobre instancias GC."
    )
    parser.add_argument(
        "--instancias",
        default="instancias",
        help="Directorio que contiene las instancias .txt.",
    )
    parser.add_argument(
        "--segundos",
        type=float,
        default=60.0,
        help="Limite de tiempo por ejecucion.",
    )
    parser.add_argument(
        "--etapa",
        choices=("3", "4", "ambas"),
        default="ambas",
        help="Etapa a ejecutar.",
    )
    parser.add_argument(
        "--variante",
        choices=("primal", "dual", "ambas"),
        default="ambas",
        help="Variante manual de la etapa 3.",
    )
    parser.add_argument(
        "--exportar",
        action="store_true",
        help="Exporta el modelo MIP y su solucion.",
    )
    args = parser.parse_args()

    if args.segundos < 0:
        parser.error("--segundos debe ser no negativo")

    instancias = listar_instancias(args.instancias)
    if not instancias:
        print(f"No se encontraron instancias .txt en '{args.instancias}'.")
        return 1

    print(
        f"Instancias: {len(instancias)} | "
        f"limite por run: {args.segundos:.3f}s | "
        f"etapa: {args.etapa}"
    )
    ejecuciones = 0
    exitos = 0

    for instancia in instancias:
        print(f"\n[{os.path.basename(instancia)}]")

        if args.etapa in ("3", "ambas"):
            variantes = (
                ("primal", "dual")
                if args.variante == "ambas"
                else (args.variante,)
            )
            for variante in variantes:
                ejecuciones += 1
                exitos += ejecutar_run(
                    f"Etapa 3 {variante}",
                    resolver_GC,
                    instancia,
                    args.segundos,
                    variante=variante,
                    imprimir_archivo=args.exportar,
                )

        if args.etapa in ("4", "ambas"):
            ejecuciones += 1
            exitos += ejecutar_run(
                "Etapa 4 nativa",
                resolver_GC_nativo,
                instancia,
                args.segundos,
                imprimir_archivo=args.exportar,
            )

    print(f"\nResumen: {exitos}/{ejecuciones} ejecuciones completadas.")
    return 0 if exitos == ejecuciones else 1


if __name__ == "__main__":
    raise SystemExit(main())
