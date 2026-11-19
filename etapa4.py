"""Etapa 4: generacion de columnas nativa mediante el pricer de SCIP."""

import time
from copy import deepcopy

from pyscipopt import Pricer, SCIP_PARAMSETTING, SCIP_RESULT

from etapa3 import (
    _CONTEXTOS,
    _TOLERANCIA_COSTO_REDUCIDO,
    _crear_modelo,
    _resolver_mip,
    catalogo_inicial,
)


class _PricerGC(Pricer):
    def __init__(self, contexto, catalogo):
        super().__init__()
        self.contexto = contexto
        self.catalogo = catalogo
        self.restricciones = None

    def pricerredcost(self):
        if self.restricciones is None:
            rows = {row.name: row for row in self.model.getLPRowsData()}
            nombres = [
                f"recurso_{i + 1}"
                for i in range(self.contexto["datos"]["m"])
            ]
            self.restricciones = [rows[nombre] for nombre in nombres]

        duales = [
            float(self.model.getDualsolLinear(cons))
            for cons in self.contexto["restricciones"]
        ]
        usados = {d["indice"] for d in self.catalogo}
        mejor = None
        for diseno in self.contexto["datos"]["disenos"]:
            if diseno["indice"] in usados:
                continue
            reducido = diseno["beneficio"] - sum(
                duales[i] * diseno["recursos"][i]
                for i in range(self.contexto["datos"]["m"])
            )
            if reducido > _TOLERANCIA_COSTO_REDUCIDO and (
                mejor is None or reducido > mejor[1]
            ):
                mejor = (diseno, reducido)
        if mejor is None:
            return {"result": SCIP_RESULT.SUCCESS}

        diseno = mejor[0]
        variable = self.model.addVar(
            name=f"x_{diseno['indice']}",
            vtype="CONTINUOUS",
            lb=0,
            ub=diseno["cota"],
            obj=diseno["beneficio"],
            pricedVar=True,
        )
        for i, row in enumerate(self.restricciones):
            self.model.addVarToRow(row, variable, diseno["recursos"][i])
        self.catalogo.append(deepcopy(diseno))
        return {"result": SCIP_RESULT.SUCCESS}


def resolver_GC_nativo_detallado(path_instancia, segundos, imprimir_archivo=False):
    """Retorna el MIP final con los atributos de sus diseños seleccionados."""
    if segundos < 0:
        raise ValueError("segundos debe ser no negativo")

    inicio = time.monotonic()
    catalogo = catalogo_inicial(path_instancia)
    modelo = _crear_modelo(
        path_instancia, "primal", catalogo, modificable=True
    )
    modelo.setPresolve(SCIP_PARAMSETTING.OFF)
    contexto = _CONTEXTOS[modelo]
    contexto["catalogo"] = catalogo
    pricer = _PricerGC(contexto, catalogo)
    modelo.includePricer(
        pricer,
        "gc_pricer",
        "Generacion nativa de columnas",
        delay=False,
    )

    restante = max(0.0, segundos - (time.monotonic() - inicio))
    if restante > 0:
        modelo.setParam("limits/time", restante)
        modelo.optimize()

    restante = max(0.0, segundos - (time.monotonic() - inicio))
    mip = _resolver_mip(
        contexto["datos"],
        catalogo,
        restante,
        imprimir_archivo=imprimir_archivo,
        nombre=path_instancia,
    )
    return mip


def resolver_GC_nativo(path_instancia, segundos, imprimir_archivo=False):
    """Resuelve con pricing nativo y mantiene la tupla publica tradicional."""
    resultado = resolver_GC_nativo_detallado(
        path_instancia, segundos, imprimir_archivo
    )
    return (
        resultado["objetivo"],
        resultado["restricciones"],
        resultado["variables"],
    )
