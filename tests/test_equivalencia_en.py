import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

import equivalencia_en as eq  # noqa: E402


class SelfTest(unittest.TestCase):
    def test_el_falsador_muerde_en_los_nueve_casos(self):
        self.assertEqual(eq.self_test(), [])

    def test_sin_argumentos_rc_2(self):
        self.assertEqual(eq.main([]), 2)

    def test_ruta_inexistente_rc_2(self):
        self.assertEqual(eq.main(["/no/existe_es.md", "/no/existe_en.md"]), 2)


class Cifras(unittest.TestCase):
    def test_coma_decimal_y_punto_son_la_misma_cifra(self):
        self.assertEqual(eq.numeros("15,2 %") , eq.numeros("15.2 %"))

    def test_miles_con_punto_y_con_coma(self):
        self.assertEqual(eq.numeros("959.216"), eq.numeros("959,216"))

    def test_miles_con_espacio(self):
        self.assertEqual(eq.numeros("959 216"), eq.numeros("959,216"))

    def test_una_cifra_que_se_mueve_no_es_equivalente(self):
        problemas, _, _ = eq.comparar("807 observaciones", "808 observations")
        self.assertTrue(problemas)
        self.assertIn("NUMEROS", problemas[0])

    def test_el_porcentaje_sin_espacio_cuenta(self):
        self.assertEqual(eq.numeros("14.2%"), eq.numeros("14.2 %"))

    def test_version_con_tres_niveles_sobrevive(self):
        self.assertEqual(eq.numeros("3.12.13"), eq.numeros("3.12.13"))


class Enlaces(unittest.TestCase):
    def test_una_url_perdida_es_fallo(self):
        problemas, _, _ = eq.comparar(
            "ver https://a.mx/x fin", "see fin"
        )
        self.assertTrue(any(p.startswith("URLS") for p in problemas))

    def test_la_puntuacion_final_de_la_url_no_cuenta(self):
        self.assertEqual(eq.urls("https://a.mx/x."), eq.urls("https://a.mx/x"))


class Codigo(unittest.TestCase):
    def test_el_comentario_traducido_no_rompe_el_bloque(self):
        es = "```\n# hola\nx = 1\n```"
        en = "```\n# hello\nx = 1\n```"
        self.assertEqual(eq.comparar(es, en)[0], [])

    def test_el_codigo_traducido_si_rompe_el_bloque(self):
        problemas, _, _ = eq.comparar("```\nx = 1\n```", "```\nx = 2\n```")
        self.assertTrue(any(p.startswith("BLOQUE") for p in problemas))

    def test_el_numero_de_bloques_se_compara(self):
        problemas, _, _ = eq.comparar("```\na\n```", "```\na\n```\n```\nb\n```")
        self.assertTrue(any(p.startswith("BLOQUES") for p in problemas))


class Forma(unittest.TestCase):
    def test_un_encabezado_perdido_es_fallo(self):
        problemas, _, _ = eq.comparar("## A\n## B", "## A")
        self.assertTrue(any(p.startswith("FORMA h2") for p in problemas))

    def test_una_vineta_perdida_es_fallo(self):
        problemas, _, _ = eq.comparar("- uno\n- dos", "- one")
        self.assertTrue(any(p.startswith("FORMA vinetas") for p in problemas))

    def test_las_negritas_cuentan(self):
        self.assertEqual(eq.forma("**a** **b**")["negritas"], 2)


if __name__ == "__main__":
    unittest.main()
