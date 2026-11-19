"""Generacion manual y nativa de columnas para las etapas 3 y 4."""

import os
import time
from copy import deepcopy
from weakref import WeakKeyDictionary

from pyscipopt import Model, Pricer, SCIP_PARAMSETTING, SCIP_RESULT

from leer_instancia import leer_instancia_gc


_CONTEXTOS = WeakKeyDictionary()
_TOLERANCIA_COSTO_REDUCIDO = 1e-7


def _leer_datos(path_instancia):
    n, m, b, c, u, a, alpha, k = leer_instancia_gc(path_instancia)
    if any(valor < 0 for valor in b):
        raise ValueError("Las disponibilidades de recursos deben ser no negativas")
    disenos = []
    for j in range(n):
        consumo = tuple(a[i][j] for i in range(m))
        if any(valor < 0 for valor in consumo):
            continue
        if c[j] < 0 or u[j] < 0:
            continue
        esfuerzo_tecnico = sum(alpha[i][j] * consumo[i] for i in range(m))
        if esfuerzo_tecnico < k[j] * c[j]:
            continue
        disenos.append({
            "indice": j + 1,
            "beneficio": c[j],
            "recursos": consumo,
            "cota": u[j],
        })
    return {"n": n, "m": m, "b": b, "disenos": disenos}


def _catalogo_normalizado(datos, catalogo):
    por_indice = {d["indice"]: d for d in datos["disenos"]}
    resultado = []
    vistos = set()
    for entrada in catalogo:
        indice = entrada["indice"] if isinstance(entrada, dict) else int(entrada)
        if indice not in por_indice:
            raise ValueError(f"El diseno {indice} no es valido para esta instancia")
        if indice not in vistos:
            resultado.append(deepcopy(por_indice[indice]))
            vistos.add(indice)
    return resultado


def catalogo_inicial(path_instancia):
    """Retorna el diseño técnicamente válido de mayor beneficio como catálogo base."""
    datos = _leer_datos(path_instancia)
    if not datos["disenos"]:
        return []
    return [deepcopy(max(datos["disenos"], key=lambda d: d["beneficio"]))]


def _crear_modelo(path_instancia, variante, catalogo, mip=False, modificable=False):
    if variante not in {"primal", "dual"}:
        raise ValueError("variante debe ser 'primal' o 'dual'")
    datos = _leer_datos(path_instancia)
    catalogo = _catalogo_normalizado(datos, catalogo)
    model = Model("generacion_columnas")
    model.setParam("display/verblevel", 0)
    if variante == "primal":
        model.setPresolve(SCIP_PARAMSETTING.OFF)
        if modificable:
            model.setParam("separating/maxrounds", 0)
        variables = {}
        holguras = [
            model.addVar(name=f"holgura_{i + 1}", lb=0, obj=0)
            for i in range(datos["m"])
        ]
        restricciones = [
            model.addCons(
                holguras[i] <= datos["b"][i],
                name=f"recurso_{i + 1}",
                modifiable=modificable,
            )
            for i in range(datos["m"])
        ]
        for diseno in catalogo:
            tipo = "INTEGER" if mip else "CONTINUOUS"
            variable = model.addVar(
                name=f"x_{diseno['indice']}",
                vtype=tipo,
                lb=0,
                ub=diseno["cota"],
                obj=diseno["beneficio"],
            )
            variables[diseno["indice"]] = variable
            for i, consumo in enumerate(diseno["recursos"]):
                if consumo:
                    model.addConsCoeff(restricciones[i], variable, consumo)
        model.setObjective(
            sum(
                d["beneficio"] * variables[d["indice"]]
                for d in catalogo
            ),
            "maximize",
        )
        contexto = {
            "datos": datos,
            "variante": variante,
            "catalogo": catalogo,
            "variables": variables,
            "restricciones": restricciones,
            "resuelto": False,
        }
    else:
        variables = [
            model.addVar(name=f"y_{i + 1}", lb=0, obj=datos["b"][i])
            for i in range(datos["m"])
        ]
        variables_z = {}
        restricciones = {}
        for diseno in catalogo:
            z = model.addVar(
                name=f"z_{diseno['indice']}",
                lb=0,
                obj=diseno["cota"],
            )
            variables_z[diseno["indice"]] = z
            restricciones[diseno["indice"]] = model.addCons(
                sum(
                    diseno["recursos"][i] * variables[i]
                    for i in range(datos["m"])
                ) + z >= diseno["beneficio"],
                name=f"diseno_{diseno['indice']}",
            )
        model.setObjective(
            sum(datos["b"][i] * variables[i] for i in range(datos["m"]))
            + sum(
                d["cota"] * variables_z[d["indice"]]
                for d in catalogo
            ),
            "minimize",
        )
        contexto = {
            "datos": datos,
            "variante": variante,
            "catalogo": catalogo,
            "variables": variables,
            "variables_z": variables_z,
            "restricciones": restricciones,
            "resuelto": False,
        }
    _CONTEXTOS[model] = contexto
    return model


def crear_modelo_gc(path_instancia, variante="primal", catalogo=None):
    """Crea el maestro relajado para uso y prueba de las funciones de GC."""
    if catalogo is None:
        catalogo = catalogo_inicial(path_instancia)
    return _crear_modelo(path_instancia, variante, catalogo)


def _incorporar_diseno(modelo, contexto, diseno):
    if any(d["indice"] == diseno["indice"] for d in contexto["catalogo"]):
        return
    if contexto["resuelto"]:
        modelo.freeTransform()
        contexto["resuelto"] = False

    if contexto["variante"] == "primal":
        variable = modelo.addVar(
            name=f"x_{diseno['indice']}",
            vtype="CONTINUOUS",
            lb=0,
            ub=diseno["cota"],
            obj=diseno["beneficio"],
        )
        for i, consumo in enumerate(diseno["recursos"]):
            if consumo:
                modelo.addConsCoeff(
                    contexto["restricciones"][i], variable, consumo
                )
        contexto["variables"][diseno["indice"]] = variable
    else:
        z = modelo.addVar(
            name=f"z_{diseno['indice']}",
            lb=0,
            obj=diseno["cota"],
        )
        contexto["variables_z"][diseno["indice"]] = z
        contexto["restricciones"][diseno["indice"]] = modelo.addCons(
            sum(
                diseno["recursos"][i] * contexto["variables"][i]
                for i in range(contexto["datos"]["m"])
            ) + z >= diseno["beneficio"],
            name=f"diseno_{diseno['indice']}",
        )
    contexto["catalogo"].append(deepcopy(diseno))


def _resolver_dual_explicito(datos, catalogo, segundos):
    """Obtiene duales aun si SCIP resuelve el primal sin conservar sus filas LP."""
    if segundos <= 0:
        return None
    modelo = Model("dual_auxiliar_gc")
    modelo.setParam("display/verblevel", 0)
    modelo.setParam("limits/time", segundos)
    y = [
        modelo.addVar(name=f"y_{i + 1}", lb=0, obj=datos["b"][i])
        for i in range(datos["m"])
    ]
    z = []
    for diseno in catalogo:
        variable_z = modelo.addVar(
            name=f"z_{diseno['indice']}", lb=0, obj=diseno["cota"]
        )
        z.append(variable_z)
        modelo.addCons(
            sum(
                diseno["recursos"][i] * y[i]
                for i in range(datos["m"])
            ) + variable_z >= diseno["beneficio"]
        )
    modelo.setObjective(
        sum(datos["b"][i] * y[i] for i in range(datos["m"]))
        + sum(
            diseno["cota"] * z[j]
            for j, diseno in enumerate(catalogo)
        ),
        "minimize",
    )
    modelo.optimize()
    if str(modelo.getStatus()) != "optimal":
        return None
    return [float(modelo.getVal(variable)) for variable in y]


def resolver_GC_relajado(modelo, catalogo):
    """Resuelve el maestro LP y retorna duales, estado, solución y objetivo."""
    if modelo not in _CONTEXTOS:
        raise ValueError("El modelo no fue creado por crear_modelo_gc")
    contexto = _CONTEXTOS[modelo]
    for diseno in _catalogo_normalizado(contexto["datos"], catalogo):
        _incorporar_diseno(modelo, contexto, diseno)

    inicio = time.monotonic()
    limite = float(modelo.getParam("limits/time"))
    modelo.optimize()
    contexto["resuelto"] = True
    estado = str(modelo.getStatus())
    objetivo = None
    solucion = {}
    valores_duales = None
    if estado == "optimal":
        objetivo = float(modelo.getObjVal())
        if contexto["variante"] == "primal":
            solucion = {
                indice: float(modelo.getVal(variable))
                for indice, variable in contexto["variables"].items()
            }
            restante = max(0.0, limite - (time.monotonic() - inicio))
            valores_duales = _resolver_dual_explicito(
                contexto["datos"], contexto["catalogo"], restante
            )
        else:
            solucion = {
                indice: float(modelo.getVal(variable))
                for indice, variable in contexto["variables_z"].items()
            }
            valores_duales = [
                float(modelo.getVal(variable))
                for variable in contexto["variables"]
            ]
    return {
        "estado": estado,
        "objetivo": objetivo,
        "solucion": solucion,
        "valores_duales": valores_duales,
        "restricciones": modelo.getNConss(),
        "variables": modelo.getNVars(),
    }


def resolver_GC_pricing(modelo, valores_duales):
    """Retorna el diseño no usado de mayor costo reducido positivo, o None."""
    if modelo not in _CONTEXTOS:
        raise ValueError("El modelo no fue creado por crear_modelo_gc")
    contexto = _CONTEXTOS[modelo]
    datos = contexto["datos"]
    if valores_duales is None:
        raise ValueError("No hay valores duales disponibles para el pricing")
    if isinstance(valores_duales, dict):
        duales = [
            float(valores_duales[i + 1])
            for i in range(datos["m"])
        ]
    else:
        duales = [float(valor) for valor in valores_duales]
    if len(duales) != datos["m"]:
        raise ValueError("Se requiere un valor dual por cada recurso")

    usados = {d["indice"] for d in contexto["catalogo"]}
    mejor = None
    for diseno in datos["disenos"]:
        if diseno["indice"] in usados:
            continue
        costo_reducido = diseno["beneficio"] - sum(
            duales[i] * diseno["recursos"][i]
            for i in range(datos["m"])
        )
        if costo_reducido > _TOLERANCIA_COSTO_REDUCIDO and (
            mejor is None or costo_reducido > mejor["costo_reducido"]
        ):
            mejor = deepcopy(diseno)
            mejor["costo_reducido"] = costo_reducido
    return mejor


def _resolver_mip(datos, catalogo, segundos, imprimir_archivo=False, nombre="gc"):
    inicio = time.monotonic()
    catalogo = _catalogo_normalizado(datos, catalogo)
    model = Model(f"{nombre}_entero")
    model.setParam("display/verblevel", 0)
    variables = []
    variable_cero = None
    if not catalogo:
        variable_cero = model.addVar(
            name="gc_cero", vtype="INTEGER", lb=0, ub=0, obj=0
        )
    for diseno in catalogo:
        variables.append(model.addVar(
            name=f"x_{diseno['indice']}",
            vtype="INTEGER",
            lb=0,
            ub=diseno["cota"],
            obj=diseno["beneficio"],
        ))
    for i in range(datos["m"]):
        expresion = sum(
            diseno["recursos"][i] * variables[j]
            for j, diseno in enumerate(catalogo)
        )
        if variable_cero is not None:
            expresion += variable_cero
        model.addCons(
            expresion <= datos["b"][i],
            name=f"recurso_{i + 1}",
        )
    model.setObjective(
        sum(
            d["beneficio"] * variables[j]
            for j, d in enumerate(catalogo)
        ),
        "maximize",
    )
    restante = max(0.0, float(segundos) - (time.monotonic() - inicio))
    model.setParam("limits/time", restante)

    if restante > 0:
        model.optimize()
    estado = str(model.getStatus())
    objetivo = None
    solucion = None
    if model.getNSols() > 0:
        sol = model.getBestSol()
        solucion = {
            d["indice"]: int(round(float(model.getSolVal(sol, variables[j]))))
            for j, d in enumerate(catalogo)
        }
        objetivo = sum(
            d["beneficio"] * solucion[d["indice"]]
            for d in catalogo
        )
    else:
        solucion = {d["indice"]: 0 for d in catalogo}
        objetivo = 0

    if imprimir_archivo:
        base = os.path.splitext(os.path.abspath(nombre))[0]
        model.writeProblem(base + "_gc.lp")
        if model.getNSols() > 0:
            model.writeBestSol(base + "_gc.sol")
        else:
            sol = model.createSol()
            for variable in variables:
                model.setSolVal(sol, variable, 0)
            if variable_cero is not None:
                model.setSolVal(sol, variable_cero, 0)
            model.writeSol(sol, base + "_gc.sol")

    return {
        "estado": estado if restante > 0 else "not_started",
        "objetivo": objetivo,
        "solucion": solucion,
        "restricciones": datos["m"],
        "variables": len(catalogo),
    }


def resolver_GC_entero(modelo, catalogo, segundos):
    """Resuelve el maestro MIP con las columnas acumuladas."""
    if modelo not in _CONTEXTOS:
        raise ValueError("El modelo no fue creado por crear_modelo_gc")
    return _resolver_mip(
        _CONTEXTOS[modelo]["datos"],
        catalogo,
        segundos,
    )


def _resolver_GC(path_instancia, segundos, variante, imprimir_archivo):
    inicio = time.monotonic()
    catalogo = catalogo_inicial(path_instancia)
    modelo = crear_modelo_gc(path_instancia, variante, catalogo)
    datos = _CONTEXTOS[modelo]["datos"]

    while True:
        restante = segundos - (time.monotonic() - inicio)
        if restante <= 0:
            break
        modelo.setParam("limits/time", restante)
        relajado = resolver_GC_relajado(modelo, catalogo)
        if (
            relajado["estado"] != "optimal"
            or relajado["valores_duales"] is None
        ):
            break
        candidato = resolver_GC_pricing(modelo, relajado["valores_duales"])
        if candidato is None:
            break
        catalogo.append(candidato)

    restante = max(0.0, segundos - (time.monotonic() - inicio))
    mip = _resolver_mip(
        datos,
        catalogo,
        restante,
        imprimir_archivo=imprimir_archivo,
        nombre=path_instancia,
    )
    return mip["objetivo"], mip["restricciones"], mip["variables"]


def resolver_GC(path_instancia, segundos, variante="primal", imprimir_archivo=False):
    """Resuelve mediante generación manual primal o dual."""
    if segundos < 0:
        raise ValueError("segundos debe ser no negativo")
    return _resolver_GC(path_instancia, segundos, variante, imprimir_archivo)


