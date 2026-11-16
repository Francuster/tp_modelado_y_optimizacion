import os
import tempfile
import unittest

from generacion_columnas import (
    catalogo_inicial,
    crear_modelo_gc,
    resolver_GC,
    resolver_GC_nativo,
    resolver_GC_pricing,
    resolver_GC_relajado,
)
from leer_instancia import leer_instancia_gc


INSTANCIA = """\
N 4
M 2
BETA 1.0
GAMMA 9
B 1 5
B 2 5
DISENO 1 3 2 2
DISENO 2 4 7 3
DISENO 3 6 1 2
DISENO 4 7 4 2
A 1 1 2
A 1 2 1
A 1 3 3
A 1 4 -1
A 2 1 1
A 2 2 3
A 2 3 2
A 2 4 2
ALPHA 1 1 1
ALPHA 2 1 1
K 1 1
ALPHA 1 2 2
ALPHA 2 2 1
K 2 1
ALPHA 1 3 1
ALPHA 2 3 2
K 3 1
ALPHA 1 4 1
ALPHA 2 4 1
K 4 1
"""


class TestGeneracionColumnas(unittest.TestCase):
    def setUp(self):
        archivo = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        )
        archivo.write(INSTANCIA)
        archivo.close()
        self.path = archivo.name
        self.addCleanup(os.remove, self.path)

    def test_catalogo_filtra_tradeoff_y_consumos_negativos(self):
        catalogo = catalogo_inicial(self.path)
        self.assertEqual(len(catalogo), 1)
        self.assertEqual(catalogo[0]["indice"], 3)
        self.assertTrue(all(x >= 0 for x in catalogo[0]["recursos"]))

    def test_lectura_gc_separa_datos_tecnologicos(self):
        n, m, b, c, u, a, alpha, k = leer_instancia_gc(self.path)
        self.assertEqual((n, m), (4, 2))
        self.assertEqual((alpha[0][1], k[1]), (2, 1))
        self.assertEqual((b[0], c[1], u[1], a[0][1]), (5, 4, 3, 1))

    def test_pricing_devuelve_candidato_y_none_al_agotar(self):
        modelo = crear_modelo_gc(self.path, "primal", catalogo=[3])
        candidato = resolver_GC_pricing(modelo, [0, 0])
        self.assertEqual(candidato["indice"], 2)
        self.assertGreater(candidato["costo_reducido"], 0)

        modelo_completo = crear_modelo_gc(
            self.path, "primal", catalogo=[1, 2, 3]
        )
        self.assertIsNone(resolver_GC_pricing(modelo_completo, [100, 100]))

    def test_relajaciones_primal_y_dual_son_equivalentes(self):
        catalogo = [1, 2, 3]
        valores = []
        for variante in ("primal", "dual"):
            modelo = crear_modelo_gc(self.path, variante, catalogo=[])
            resultado = resolver_GC_relajado(modelo, catalogo)
            self.assertEqual(resultado["estado"], "optimal")
            valores.append(resultado["objetivo"])
        self.assertAlmostEqual(valores[0], valores[1], places=6)

    def test_resolucion_manual_y_nativa_entera(self):
        primal = resolver_GC(self.path, 10, "primal")
        dual = resolver_GC(self.path, 10, "dual")
        nativo = resolver_GC_nativo(self.path, 10)
        self.assertEqual(primal[0], dual[0])
        self.assertEqual(primal[0], nativo[0])
        self.assertEqual(primal[1:], dual[1:])

    def test_w_no_afecta_las_etapas_gc(self):
        original = resolver_GC(self.path, 10)
        contenido = INSTANCIA.replace("DISENO 2 4 7 3", "DISENO 2 4 900 3")
        archivo = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        )
        archivo.write(contenido)
        archivo.close()
        self.addCleanup(os.remove, archivo.name)
        self.assertEqual(original, resolver_GC(archivo.name, 10))

    def test_limite_cero_devuelve_el_plan_factible_vacio(self):
        resultado = resolver_GC(self.path, 0)
        self.assertEqual(resultado[0], 0)


if __name__ == "__main__":
    unittest.main()
