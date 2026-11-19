import os
import tempfile
import unittest

from etapa3 import resolver_GC
from etapa4 import resolver_GC_nativo
from generate_instance import generar_instancia
from leer_instancia import leer_instancia_gc


class TestEtapa4(unittest.TestCase):
    def setUp(self):
        archivo = tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False
        )
        archivo.close()
        self.path = archivo.name
        self.addCleanup(os.remove, self.path)
        generar_instancia(
            self.path,
            N=8,
            M=3,
            seed=1,
            incluir_tradeoff=True,
        )

    def test_instancia_generada_incluye_disenos_validos(self):
        n, m, _, _, _, _, alpha, k = leer_instancia_gc(self.path)
        self.assertEqual((n, m), (8, 3))
        self.assertEqual(len(alpha), m)
        self.assertEqual(len(alpha[0]), n)
        self.assertEqual(len(k), n)
        self.assertTrue(any(isinstance(valor, float) for fila in alpha for valor in fila))

    def test_pricer_nativo_resuelve_el_maestro_entero(self):
        manual = resolver_GC(self.path, 10, variante="primal")
        nativo = resolver_GC_nativo(self.path, 10)
        self.assertIsNotNone(nativo[0])
        self.assertEqual(manual[0], nativo[0])
        self.assertEqual(nativo[1], 3)
        self.assertGreater(nativo[2], 1)

    def test_etapa4_maneja_presupuesto_cero(self):
        self.assertEqual(resolver_GC_nativo(self.path, 0)[0], 0)


if __name__ == "__main__":
    unittest.main()
