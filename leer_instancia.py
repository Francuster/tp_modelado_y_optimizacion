import math


def leer_instancia(path_instancia: str):
    """
    Lee una instancia del problema desde un archivo de texto.

    Parametros:
        path_instancia (str): ruta al archivo de instancia.

    Retorna:
        tuple:
            n, m, beta, b, c, w, u, a

        donde:
            n    = cantidad de diseños
            m    = cantidad de recursos
            beta = factor de costo de infraestructura
            b    = disponibilidad de cada recurso
            c    = beneficio unitario de cada diseño
            w    = consumo de potencia de cada diseño
            u    = cota superior de produccion de cada diseño
            a    = matriz de requerimientos a[i][j]
    """

    try:
        with open(path_instancia, "r", encoding="utf-8") as archivo:
            lineas = archivo.readlines()

    except FileNotFoundError:
        raise FileNotFoundError(
            f"No existe el archivo de instancia: {path_instancia}"
        )

    n = None
    m = None
    beta = None

    b = []
    c = []
    w = []
    u = []
    a = None

    for linea in lineas:

        linea = linea.strip()

        # Ignorar lineas vacias y comentarios
        if not linea or linea.startswith("#"):
            continue

        partes = linea.split()
        tipo = partes[0]

        if tipo == "N":
            if len(partes) != 2:
                raise ValueError("Formato invalido en linea N")

            n = int(partes[1])

        elif tipo == "M":
            if len(partes) != 2:
                raise ValueError("Formato invalido en linea M")

            m = int(partes[1])

        elif tipo == "BETA":
            if len(partes) != 2:
                raise ValueError("Formato invalido en linea BETA")

            beta = float(partes[1])

        elif tipo == "B":
            if len(partes) != 3:
                raise ValueError("Formato invalido en linea B")

            i = int(partes[1])
            valor = int(partes[2])

            b.append((i, valor))

        elif tipo == "DISENO":
            if len(partes) != 5:
                raise ValueError("Formato invalido en linea DISENO")

            j = int(partes[1])
            beneficio = int(partes[2])
            potencia = int(partes[3])
            cota = int(partes[4])

            c.append((j, beneficio))
            w.append((j, potencia))
            u.append((j, cota))

        elif tipo == "A":
            if len(partes) != 4:
                raise ValueError("Formato invalido en linea A")

            i = int(partes[1])
            j = int(partes[2])
            valor = int(partes[3])

            # La matriz se crea cuando conocemos n y m
            if a is None:
                if n is None or m is None:
                    raise ValueError(
                        "N y M deben aparecer antes de las lineas A"
                    )

                a = [[0 for _ in range(n)] for _ in range(m)]

            # El archivo usa indices desde 1
            # Python usa indices desde 0
            a[i - 1][j - 1] = valor

        elif tipo in {"ALPHA", "GAMMA", "K"}:
            # Parametros opcionales para generacion de columnas. La lectura
            # tradicional mantiene su tupla de retorno y los valida la
            # funcion leer_instancia_gc.
            continue

        else:
            raise ValueError(f"Tipo de linea desconocido: {tipo}")

    # Verificaciones basicas
    if n is None:
        raise ValueError("Falta el parametro N")

    if m is None:
        raise ValueError("Falta el parametro M")

    if beta is None:
        raise ValueError("Falta el parametro BETA")

    if len(b) != m:
        raise ValueError(
            f"Se esperaban {m} recursos B, pero se encontraron {len(b)}"
        )

    if len(c) != n or len(w) != n or len(u) != n:
        raise ValueError(
            "La cantidad de diseños no coincide con N"
        )

    if a is None:
        raise ValueError("No se encontraron requerimientos A")

    if len(a) != m or any(len(fila) != n for fila in a):
        raise ValueError("Dimensiones incorrectas de la matriz A")

    # Ordenar segun indice para que Python tenga:
    # b[0] -> recurso 1
    # c[0] -> diseño 1
    # etc.
    b = [valor for _, valor in sorted(b)]
    c = [valor for _, valor in sorted(c)]
    w = [valor for _, valor in sorted(w)]
    u = [valor for _, valor in sorted(u)]

    return n, m, beta, b, c, w, u, a


def leer_instancia_gc(path_instancia: str):
    """
    Lee los datos necesarios para las etapas 3 y 4.

    Retorna ``n, m, b, c, u, a, alpha, k``. ``w``, ``beta`` y ``gamma`` no
    forman parte de estas etapas.

    n    = cantidad de diseños
    m    = cantidad de recursos
    beta = factor de costo de infraestructura
    b    = disponibilidad de cada recurso
    c    = beneficio unitario de cada diseño
    w    = consumo de potencia de cada diseño
    u    = cota superior de produccion de cada diseño
    a    = matriz de requerimientos a[i][j]
    alpha = factores de ponderación que penalizan el consumo de los recursos internos i más escasos de la planta para un diseño j
    """
    n, m, _, b, c, _, u, a = leer_instancia(path_instancia)

    alpha = [[None for _ in range(n)] for _ in range(m)]
    k = [None for _ in range(n)]

    with open(path_instancia, "r", encoding="utf-8") as archivo:
        for numero_linea, linea in enumerate(archivo, start=1):
            partes = linea.split()
            if not partes or partes[0].startswith("#"):
                continue

            tipo = partes[0]
            if tipo == "ALPHA":
                if len(partes) != 4:
                    raise ValueError(
                        f"Formato invalido en linea ALPHA ({numero_linea})"
                    )
                i, j = map(int, partes[1:3])
                valor = float(partes[3])
                if not 1 <= i <= m or not 1 <= j <= n:
                    raise ValueError(
                        f"Indice fuera de rango en linea ALPHA ({numero_linea})"
                    )
                if alpha[i - 1][j - 1] is not None:
                    raise ValueError(f"Parametro ALPHA duplicado en linea {numero_linea}")
                alpha[i - 1][j - 1] = valor
            elif tipo == "K":
                if len(partes) != 3:
                    raise ValueError(f"Formato invalido en linea K ({numero_linea})")
                j = int(partes[1])
                valor = float(partes[2])
                if not 1 <= j <= n:
                    raise ValueError(
                        f"Indice fuera de rango en linea K ({numero_linea})"
                    )
                if k[j - 1] is not None:
                    raise ValueError(f"Parametro K duplicado en linea {numero_linea}")
                k[j - 1] = valor
            elif tipo == "GAMMA":
                if len(partes) != 2:
                    raise ValueError(
                        f"Formato invalido en linea GAMMA ({numero_linea})"
                    )
                float(partes[1])

    if any(valor is None for fila in alpha for valor in fila):
        raise ValueError("Faltan parametros ALPHA para la instancia")
    if any(valor is None for valor in k):
        raise ValueError("Faltan parametros K para la instancia")
    if any(not math.isfinite(valor) for fila in alpha for valor in fila):
        raise ValueError("Los parametros ALPHA deben ser finitos")
    if any(not math.isfinite(valor) for valor in k):
        raise ValueError("Los parametros K deben ser finitos")
    if any(valor < 0 for fila in alpha for valor in fila):
        raise ValueError("Los parametros ALPHA deben ser no negativos")
    if any(valor < 0 for valor in k):
        raise ValueError("Los parametros K deben ser no negativos")

    return n, m, b, c, u, a, alpha, k