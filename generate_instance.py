# -*- coding: utf-8 -*-
"""
Generador aleatorio de instancias de texto para ser
leídos por la función `leer_instancia` requerida en el TP.
Incluye la función que genera los parámetros del trade-off tecnológico.
"""

import os
import numpy as np
from typing import Optional, Tuple, List

# ==========================================
# CONSTANTES DE CONFIGURACIÓN Y VALORES DEFAULT
# ==========================================
DIR_INSTANCIAS = "instancias"

# 1. Instancia estándar / chica
PATH_INSTANCIA_CHICA = os.path.join(DIR_INSTANCIAS, "instancia_chica.txt")
DEFAULT_N = 5
DEFAULT_M = 3
DEFAULT_SEED = 42

# 2. Instancia pesada
PATH_INSTANCIA_PESADA = os.path.join(DIR_INSTANCIAS, "instancia_pesada.txt")
PESADA_N = 80
PESADA_M = 25
PESADA_SEED = 777

# 3. Instancia infactible o sin tiempo para solución (timeout prematuro)
PATH_INSTANCIA_SIN_SOL = os.path.join(DIR_INSTANCIAS, "instancia_sin_solucion.txt")
SINSOL_N = 120
SINSOL_M = 40
SINSOL_SEED = 999

# Rangos para parámetros económicos y de infraestructura
MIN_BETA, MAX_BETA = 0.5, 3.5

# Rangos para recursos disponibles (b_i)
MIN_RECURSO_B, MAX_RECURSO_B = 50, 150

# Rangos por diseño (Beneficio c_j, Potencia w_j, Cota u_j)
MIN_BENEFICIO_C, MAX_BENEFICIO_C = 10, 100
MIN_POTENCIA_W, MAX_POTENCIA_W = 1, 5
MIN_COTA_U, MAX_COTA_U = 20, 50

# Rangos para requerimiento de recursos (a_ij)
MIN_REQ_A, MAX_REQ_A = -2, 30

# ==========================================


def generar_parametros_tecnologicos(
    n: int,
    m: int,
    b: List[int],
    U: int,
    c: List[int],
    k0: float = 1.0,
    delta: float = 1.2,
    seed: Optional[int] = 42	# mejor: None
) -> Tuple[np.ndarray, float, np.ndarray]:
    """
    Genera los parámetros constantes para el trade-off tecnológico asegurando
    rompimiento de simetría y heterogeneidad de forma determinista si se provee seed.

    Parámetros:
    - n: número de diseños base
    - m: número de recursos
    - b: array/lista con la disponibilidad de cada recurso i (tam: m)
    - U: cota superior teórica de potencia
    - c: array/lista con el beneficio unitario de cada diseño j (tam: n)
    - k0: parámetro global de exigencia tecnológica
    - delta: parámetro de sensibilidad tecnológica (>= 1)
    - seed: semilla para reproducibilidad
    """
    if seed is not None:
        np.random.seed(seed)

    # 1. Disponibilidad media de los recursos
    b_bar = np.mean(b)

    # 2. Factores de especialización xi_ij en [0.8, 1.2] para romper simetría
    xi = np.random.uniform(0.8, 1.2, size=(m, n))

    # 3. Pesos de los recursos alpha_ij (matriz m x n)
    alpha = np.zeros((m, n))
    for i in range(m):
        alpha[i, :] = (b_bar / b[i]) * xi[i, :]

    # 4. Coeficiente de potencia gamma (escalar global)
    gamma = 1.0 / U if U > 0 else 1.0

    # 5. Beneficio promedio c_bar
    c_bar = np.mean(c) if len(c) > 0 else 1.0

    # 6. Factor de dificultad tecnológica k_j (vector de tamaño n)
    k = k0 * (np.array(c, dtype=float) / c_bar) ** delta

    return alpha, gamma, k


def generar_instancia(
    filename: str,
    N: int,
    M: int,
    seed: Optional[int] = None,
    restrictiva: bool = False,
    incluir_tradeoff: bool = False,
    k0: float = 1.0,
    delta: float = 1.2
) -> None:
    """
    Genera un archivo de instancia aleatorio con control de complejidad
    y serializa opcionalmente los parámetros fijos del trade-off tecnológico.

    Parámetros:
    - filename: Ruta o nombre del archivo de salida.
    - N: Cantidad de diseños de paneles acústicos.
    - M: Cantidad de recursos internos limitados.
    - seed: Semilla para la reproducibilidad (opcional).
    - restrictiva: True para instancias difíciles
    """
    if seed is not None:
        np.random.seed(seed)

    beta = round(np.random.uniform(MIN_BETA, MAX_BETA), 2)

    # Si es restrictiva, bajamos los recursos b_i para asfixiar el espacio de soluciones
    divisor_b = 2 if restrictiva else 1

    # Recursos disponibles b_i (para cada i en M)
    b = [np.random.randint(MIN_RECURSO_B, MAX_RECURSO_B + 1) // divisor_b for _ in range(M)]

    # Datos por diseño j en N (c_j, w_j, u_j, y consumo de recursos a_ij)
    c: List[int] = []  # Beneficio unitario
    w: List[int] = []  # Consumo de potencia unitario
    u: List[int] = []  # Cota superior de fabricación
    a: List[List[int]] = [[0] * N for _ in range(M)]  # Requerimiento de recursos

    for j in range(N):
        c.append(np.random.randint(MIN_BENEFICIO_C, MAX_BENEFICIO_C + 1))
        w.append(np.random.randint(MIN_POTENCIA_W, MAX_POTENCIA_W + 1))
        u.append(np.random.randint(MIN_COTA_U, MAX_COTA_U + 1))

        # Generar requerimientos de recursos a_ij enteros
        for i in range(M):
            a[i][j] = np.random.randint(MIN_REQ_A, MAX_REQ_A + 1)

    # Cálculo del trade-off tecnológico fijo ligado a la semilla de la instancia
    alpha, gamma, k = None, None, None
    if incluir_tradeoff:
        U = sum(w[j] * u[j] for j in range(N))
        seed_tradeoff = seed if seed is not None else 42
        alpha, gamma, k = generar_parametros_tecnologicos(
            n=N, m=M, b=b, U=U, c=c, k0=k0, delta=delta, seed=seed_tradeoff
        )

    # Escritura del archivo de instancia
#    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# Instancia generada (N={N}, M={M}, restrictiva={restrictiva}, tradeoff={incluir_tradeoff})\n")
        f.write(f"N {N}\n")
        f.write(f"M {M}\n")
        f.write(f"BETA {beta}\n")

        f.write("\n# Recursos disponibles (b_i)\n")
        for i in range(M):
            f.write(f"B {i + 1} {b[i]}\n")

        f.write("\n# Datos por diseño (Beneficio c_j, Potencia w_j, Cota u_j)\n")
        for j in range(N):
            f.write(f"DISENO {j + 1} {c[j]} {w[j]} {u[j]}\n")

        f.write("\n# Requerimiento de recursos (a_ij por recurso i y diseño j)\n")
        for i in range(M):
            for j in range(N):
                f.write(f"A {i + 1} {j + 1} {a[i][j]}\n")

        # Serialización opcional de los parámetros tecnológicos fijos
        if incluir_tradeoff:
            f.write("\n# Parametros de trade-off tecnologico fijos\n")
            f.write(f"GAMMA {gamma}\n")
            for i in range(M):
                for j in range(N):
                    f.write(f"ALPHA {i + 1} {j + 1} {alpha[i, j]}\n")
            for j in range(N):
                f.write(f"K {j + 1} {k[j]}\n")

    print(f"Instancia generada: '{filename}' (N={N}, M={M}, beta={beta}, tradeoff={incluir_tradeoff})")


if __name__ == "__main__":
    os.makedirs(DIR_INSTANCIAS, exist_ok=True)

    # 1. Instancia Chica (con trade-off incluido para testear expansión)
    generar_instancia(
        filename=PATH_INSTANCIA_CHICA,
        N=DEFAULT_N,
        M=DEFAULT_M,
        seed=DEFAULT_SEED,
        restrictiva=False,
        incluir_tradeoff=True
    )

    # 2. Instancia Pesada: Con N=80 y M=25, para un tau medio-bajo,
    # SCIP tardará varios minutos (o no cerrará el gap) en 60 segundos.
    generar_instancia(
        filename=PATH_INSTANCIA_PESADA,
        N=PESADA_N,
        M=PESADA_M,
        seed=PESADA_SEED,
        restrictiva=False,
        incluir_tradeoff=True
    )

    # 3. Instancia Sin Solución a tiempo corto: Con N=120, M=40 y recursos muy acotados (restrictiva=True),
    # a SCIP le costará encontrar *incluso la primera solución factible*.
    # Si le pones un límite estricto de *2 o 3 segundos* (`model.setParam('limits/time', 3)`),
    # expirará el tiempo antes de hallar unfeasible/optimal o cualquier solución inicial.
    generar_instancia(
        filename=PATH_INSTANCIA_SIN_SOL,
        N=SINSOL_N,
        M=SINSOL_M,
        seed=SINSOL_SEED,
        restrictiva=True,
        incluir_tradeoff=True
    )
