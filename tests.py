import os
import tempfile
import unittest

from generate_instance_a import generar_instancia
from leer_instancia import leer_instancia
from resolver_modelo import resolver_modelo
from busqueda_tau import busqueda_tau

class TestLeerInstancia(unittest.TestCase):

    # Usamos un generados de instancias a parte del geerate_instance_a.py para los tests
    def crear_instancia(self, contenido):
        archivo = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False,
            encoding="utf-8"
        )
        archivo.write(contenido)
        archivo.close()
        self.addCleanup(os.remove, archivo.name)
        return archivo.name

    def test_instancia_valida(self):
        contenido = """
        N 3
        M 2
        BETA 1.5
        B 1 100
        B 2 80
        DISENO 1 20 2 10
        DISENO 2 30 3 20
        DISENO 3 40 1 15
        A 1 1 5
        A 1 2 10
        A 1 3 8
        A 2 1 4
        A 2 2 6
        A 2 3 3
        """

        resultado = leer_instancia(self.crear_instancia(contenido))

        n, m, beta, b, c, w, u, a = resultado

        self.assertEqual(n, 3)
        self.assertEqual(m, 2)
        self.assertEqual(beta, 1.5)

        self.assertEqual(b, [100, 80])
        self.assertEqual(c, [20, 30, 40])
        self.assertEqual(w, [2, 3, 1])
        self.assertEqual(u, [10, 20, 15])

        self.assertEqual(
            a,
            [
                [5, 10, 8],
                [4, 6, 3]
            ]
        )

    def test_instancia_inexistente(self):
        with self.assertRaises(FileNotFoundError):
            leer_instancia("archivo_que_no_existe.txt")

    def test_instancia_incompleta(self):
        contenido = """
        N 3
        M 2
        BETA 1.5
        B 1 100
        """

        with self.assertRaises(ValueError):
            leer_instancia(self.crear_instancia(contenido))

class TestResolverModelo(unittest.TestCase):

    def crear_instancia(self):
        file_nam = "TestResolverModelo.txt"
        generar_instancia(file_nam, 3, 2)

        self.addCleanup(os.remove, file_nam)

        return file_nam

    # Comentamos este test ya que para una instancia pequeña siempre encuentra la optima, no se puede conseguir una factible no optima
    # def test_devuelve_solucion_factible(self):
    #     path = self.crear_instancia()
    #
    #     resultado = resolver_modelo(
    #         path,
    #         segundos=10,
    #         tau=20
    #     )
    #
    #     self.assertFalse(resultado["es_optimo"])

    def test_solucion_optima_en_instancia_pequena(self):
        path = self.crear_instancia()

        resultado = resolver_modelo(
            path,
            segundos=10,
            tau=20
        )

        self.assertEqual(resultado["estado"], "optimal")
        self.assertTrue(resultado["es_optimo"])

    def test_solucion_respeta_tau(self):
        path = self.crear_instancia()

        resultado = resolver_modelo(
            path,
            segundos=10,
            tau=10
        )

        _, _, _, _, _, w, u, _ = leer_instancia(path)

        self.assertIsNotNone(resultado["solucion"])

        solucion = resultado["solucion"]

        consumo = (
            w[0] * solucion[0]
            + w[1] * solucion[1]
            + w[2] * solucion[2]
        )

        self.assertLessEqual(consumo, 10)

    def test_estado_timelimit_robusto(self):
        file_name = "test_estado_timelimit_robusto_rm"
        generar_instancia(file_name, 120, 40, 999, True)
        resultado = resolver_modelo(
            file_name,
            segundos=1,
            tau=1000
        )

        self.addCleanup(os.remove, file_name)
        self.assertEqual("timelimit", resultado["estado"])

    def test_estado_optimal_robusto(self):
        file_name = "test_estado_optimal_robusto_rm"
        generar_instancia(file_name, 50, 20, 777)
        resultado = resolver_modelo(
            file_name,
            segundos=3,
            tau=100
        )

        self.addCleanup(os.remove, file_name)
        self.assertEqual("optimal", resultado["estado"])

class TestBusquedaTau(unittest.TestCase):

    def crear_instancia(self):
        file_nam = "TestBusquedaTau.txt"
        generar_instancia(file_nam, 3, 2)

        self.addCleanup(os.remove, file_nam)

        return file_nam

    def test_encuentra_una_solucion(self):
        path = self.crear_instancia()

        resultado = busqueda_tau(
            path,
            segundos=10
        )

        self.assertIsNotNone(resultado["tau"])
        self.assertIsNotNone(resultado["solucion"])

    def test_tiempo_global(self):
        path = self.crear_instancia()

        resultado = busqueda_tau(
            path,
            segundos=2
        )

        # Se permite un pequeño margen por el overhead del sistema.
        self.assertLess(resultado["tiempo_utilizado"], 3)

    def test_tau_es_valido(self):
        path = self.crear_instancia()

        resultado = busqueda_tau(
            path,
            segundos=10
        )

        tau = resultado["tau"]

        _, _, _, _, _, w, u, _ = leer_instancia(path)

        U = sum(
            w[j] * u[j]
            for j in range(len(w))
        )

        self.assertGreaterEqual(tau, 0)
        self.assertLessEqual(tau, U)

    def test_estado_timelimit_robusto(self):
        file_name = "test_estado_timelimit_robusto_bt"
        generar_instancia(file_name, 120, 40, 999, True)
        resultado = busqueda_tau(
            file_name,
            segundos=1
        )

        self.addCleanup(os.remove, file_name)
        self.assertEqual("timelimit", resultado["estado"])

    def test_estado_optimal_robusto(self):
        file_name = "test_estado_optimal_robusto_bt"
        generar_instancia(file_name, 50, 20, 777)
        resultado = busqueda_tau(
            file_name,
            segundos=3
        )

        self.addCleanup(os.remove, file_name)
        self.assertEqual("optimal", resultado["estado"])




if __name__ == "__main__":
    unittest.main()