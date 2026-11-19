import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import main


class TestMain(unittest.TestCase):
    def test_lista_instancias_ordenadas(self):
        with tempfile.TemporaryDirectory() as carpeta:
            open(os.path.join(carpeta, "b.txt"), "w").close()
            open(os.path.join(carpeta, "a.txt"), "w").close()
            open(os.path.join(carpeta, "ignorado.lp"), "w").close()
            result = main.listar_instancias(carpeta)
        self.assertEqual(
            [os.path.basename(path) for path in result],
            ["a.txt", "b.txt"],
        )

    def test_ejecucion_muestra_resultado(self):
        salida = io.StringIO()
        with redirect_stdout(salida):
            ok = main.ejecutar_run(
                "Etapa 3 primal",
                lambda path, segundos, **kwargs: {
                    "objetivo": 123,
                    "restricciones": 2,
                    "variables": 4,
                    "disenos_seleccionados": [
                        {
                            "indice": 3,
                            "cantidad": 2,
                            "beneficio_unitario": 12,
                            "beneficio_total": 24,
                            "recursos_unitarios": [4, 1],
                        }
                    ],
                },
                "instancia.txt",
                5,
            )
        texto = salida.getvalue()
        self.assertTrue(ok)
        self.assertIn("objetivo=123", texto)
        self.assertIn("restricciones=2", texto)
        self.assertIn("variables_mip=4", texto)
        self.assertIn("Variables MIP=4; disenos seleccionados=1", texto)
        self.assertIn("Diseno 3", texto)
        self.assertIn("beneficio unitario=12.00", texto)
        self.assertIn("cantidad=2", texto)

    def test_ejecucion_reporta_error(self):
        salida = io.StringIO()

        def falla(path, segundos, **kwargs):
            raise ValueError("instancia invalida")

        with redirect_stdout(salida):
            ok = main.ejecutar_run(
                "Etapa 4 nativa",
                falla,
                "instancia.txt",
                5,
            )
        self.assertFalse(ok)
        self.assertIn("error", salida.getvalue())
        self.assertIn("instancia invalida", salida.getvalue())

    def test_sin_instancias_devuelve_error(self):
        salida = io.StringIO()
        with patch("sys.argv", ["main.py", "--instancias", ".carpeta_inexistente"]):
            with redirect_stdout(salida):
                codigo = main.main()
        self.assertEqual(codigo, 1)
        self.assertIn("No se encontraron instancias", salida.getvalue())


if __name__ == "__main__":
    unittest.main()
