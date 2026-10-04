import time
from pyscipopt import Model
from leer_instancia import leer_instancia
from generate_instance_a import DIR_INSTANCIAS
import os


def busqueda_tau(path_instancia: str, segundos: float):
    """
    Busca el valor de tau que maximiza el beneficio neto.

    Parámetros:
        path_instancia (str): ruta de la instancia.
        segundos (float): tiempo total disponible.

    Retorna:
        dict con la mejor solución encontrada.
    """

    # --------------------------------------------------
    # 1. Leer la instancia
    # --------------------------------------------------
    n, m, beta, b, c, w, u, a = leer_instancia(path_instancia)

    # --------------------------------------------------
    # 2. Calcular el máximo tau posible
    # --------------------------------------------------
    U = sum(
        w[j] * u[j]
        for j in range(n)
    )

    # --------------------------------------------------
    # 3. Crear el modelo una sola vez
    # --------------------------------------------------
    model = Model("busqueda_tau")

    # Variables
    x = []

    for j in range(n):
        variable = model.addVar(
            name=f"x_{j + 1}",
            vtype="INTEGER",
            lb=0,
            ub=u[j]
        )

        x.append(variable)

    # --------------------------------------------------
    # 4. Restricciones de recursos
    # --------------------------------------------------
    for i in range(m):

        consumo_recurso = sum(
            a[i][j] * x[j]
            for j in range(n)
        )

        model.addCons(
            consumo_recurso <= b[i],
            name=f"recurso_{i + 1}"
        )

    # --------------------------------------------------
    # 5. Restricción de potencia
    # --------------------------------------------------
    consumo_potencia = sum(
        w[j] * x[j]
        for j in range(n)
    )

    restriccion_tau = model.addCons(
        consumo_potencia <= 0,
        name="capacidad_potencia"
    )

    # --------------------------------------------------
    # 6. Función objetivo
    # --------------------------------------------------
    beneficio = sum(
        c[j] * x[j]
        for j in range(n)
    )

    model.setObjective(
        beneficio,
        "maximize"
    )

    # --------------------------------------------------
    # 7. Variables para guardar la mejor solución
    # --------------------------------------------------
    mejor_tau = None
    mejor_beneficio_neto = None
    mejor_beneficio_operativo = None
    mejor_solucion = None
    mejor_es_optimo = False

    # --------------------------------------------------
    # 8. Comenzar a medir el tiempo global
    # --------------------------------------------------
    inicio = time.monotonic()

    # --------------------------------------------------
    # 9. Recorrer los posibles valores de tau
    # --------------------------------------------------
    for tau in range(U + 1):

        # Tiempo transcurrido
        transcurrido = time.monotonic() - inicio

        # Tiempo restante
        restante = segundos - transcurrido

        # Si ya no queda tiempo, terminamos
        if restante <= 0:
            break

        # --------------------------------------------------
        # 10. Actualizar tau sin reconstruir el modelo
        # --------------------------------------------------
        model.freeTransform()

        model.chgRhs(
            restriccion_tau,
            tau
        )

        # --------------------------------------------------
        # 11. Darle a SCIP el tiempo restante
        # --------------------------------------------------
        model.setParam(
            "limits/time",
            restante
        )

        # --------------------------------------------------
        # 12. Resolver
        # --------------------------------------------------
        model.optimize()

        # --------------------------------------------------
        # 13. Verificar si encontramos una solución
        # --------------------------------------------------
        if model.getNSols() == 0:
            continue

        # Obtener mejor solución
        sol = model.getBestSol()

        solucion = [
            model.getSolVal(sol, x[j])
            for j in range(n)
        ]

        # Beneficio operativo Pi(tau)
        beneficio_operativo = sum(
            c[j] * solucion[j]
            for j in range(n)
        )

        # Costo de infraestructura
        costo = beta * (tau ** 2)

        # Beneficio neto
        beneficio_neto = beneficio_operativo - costo

        # --------------------------------------------------
        # 14. Guardar si es la mejor solución
        # --------------------------------------------------
        if (
            mejor_beneficio_neto is None
            or beneficio_neto > mejor_beneficio_neto
        ):

            mejor_tau = tau
            mejor_beneficio_neto = beneficio_neto
            mejor_beneficio_operativo = beneficio_operativo
            mejor_solucion = solucion

            mejor_es_optimo = (
                model.getStatus() == "optimal"
            )

    # --------------------------------------------------
    # 15. Tiempo total utilizado
    # --------------------------------------------------
    tiempo_utilizado = time.monotonic() - inicio

    # --------------------------------------------------
    # 16. Resultado final
    # --------------------------------------------------
    return {
        "tau": mejor_tau,
        "solucion": mejor_solucion,
        "beneficio_operativo": mejor_beneficio_operativo,
        "beneficio_neto": mejor_beneficio_neto,
        "es_optimo": mejor_es_optimo,
        "tiempo": tiempo_utilizado
    }

if __name__ == "__main__":
    print(busqueda_tau(os.path.join(DIR_INSTANCIAS, "instancia_chica.txt"), 100))