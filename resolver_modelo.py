import time
from pyscipopt import Model
from leer_instancia import leer_instancia
from generate_instance_a import DIR_INSTANCIAS
import os


def resolver_modelo(path_instancia: str, segundos: float, tau: int):
    """
    Resuelve el modelo de producción para una capacidad fija tau.

    Parámetros:
        path_instancia (str): ruta de la instancia.
        segundos (float): límite de tiempo para SCIP.
        tau (int): capacidad de potencia fijada.

    Retorna:
        dict con:
            estado
            solucion
            beneficio
            es_optimo
            tiempo
            tau
    """

    # 1. Leer la instancia
    n, m, beta, b, c, w, u, a = leer_instancia(path_instancia)

    # 2. Crear el modelo
    model = Model("produccion_paneles")

    # 3. Crear variables x_j
    x = []

    for j in range(n):
        variable = model.addVar(
            name=f"x_{j + 1}",
            vtype="INTEGER",
            lb=0,   #lower bound
            ub=u[j] #upper bound
        )

        x.append(variable)

    # 4. Restricciones de recursos
    for i in range(m):

        consumo_recurso = sum(
            a[i][j] * x[j]
            for j in range(n)
        )

        model.addCons(
            consumo_recurso <= b[i],
            name=f"recurso_{i + 1}"
        )

    # 5. Restricción de potencia
    consumo_potencia = sum(
        w[j] * x[j]
        for j in range(n)
    )

    restriccion_tau = model.addCons(
        consumo_potencia <= tau,
        name="capacidad_potencia"
    )

    # 6. Función objetivo
    beneficio = sum(
        c[j] * x[j]
        for j in range(n)
    )

    # Restar el costo operativo no cambia la busqueda de la solucion optima porque es un monto fijo
    model.setObjective(
        beneficio,
        "maximize"
    )

    # 7. Límite de tiempo de SCIP
    model.setParam(
        "limits/time",
        segundos
    )

    # 8. Resolver y medir tiempo
    inicio = time.monotonic()

    model.optimize()

    fin = time.monotonic()

    tiempo_utilizado = fin - inicio

    # 9. Obtener estado del solver
    estado = model.getStatus()

    # 10. Analizar si existe una solución factible
    solucion = None
    beneficio_obtenido = None
    es_optimo = False

    if model.getNSols() > 0:

        sol = model.getBestSol()

        # Tiene un array con las cantidad producidas de los diseños para llegar a la mejor solucion
        solucion = [
            int(round(float(model.getSolVal(sol, x[j]))))
            for j in range(n)
        ]

        beneficio_obtenido = sum(
            c[j] * solucion[j]
            for j in range(n)
        )

        # Solo consideramos garantía de optimalidad
        # cuando SCIP terminó en estado optimal.
        es_optimo = (estado == "optimal")

    # 11. Devolver resultados
    # Las variables comentadas se usaron para el testeo manual/inicial del modelo
    return {
        "estado": estado, # Agregado para cumplir con los tests de manejo de estados del solver
        "solucion": solucion,
        #"beneficio": beneficio_obtenido,
        "es_optimo": es_optimo,
        "tiempo_solicitado": segundos,
        "tiempo_utilizado": tiempo_utilizado,
        "tau": tau
    }