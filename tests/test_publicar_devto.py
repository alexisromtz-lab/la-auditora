"""Falsadores de la publicacion en dev.to.

El instrumento existe porque copiar de una pagina renderizada destruyo una
publicacion entera. Los falsadores que muerden son los de estructura: el
cuerpo que viaja tiene que traer las mismas vallas y las mismas filas de
tabla que el articulo de origen.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

import publicar_devto as pd  # noqa: E402

SLUG = "auditoria-litellm-46923-el-bug-que-responde-success"
CANONICA = "https://alexisromtz-lab.github.io/la-auditora/portafolio/articulos/en/%s/" % SLUG


class Transporte:
    """Registra las llamadas y devuelve respuestas preparadas."""

    def __init__(self, *respuestas):
        self.llamadas = []
        self.respuestas = list(respuestas)

    def __call__(self, metodo, url, clave, datos):
        self.llamadas.append((metodo, url, datos))
        return self.respuestas.pop(0) if self.respuestas else (200, {})

    @property
    def metodos(self):
        return [m for m, _, _ in self.llamadas]


def con_clave():
    return mock.patch.dict(os.environ, {"DEVTO_API_KEY": "clavedepruebanolaimprimir"})


class Separacion(unittest.TestCase):
    def test_separa_encabezado_y_cuerpo(self):
        encabezado, cuerpo = pd.separar(
            '---\ntitle: "A: b"\npublished: false\n---\n\n## Uno\n\ntexto\n'
        )
        self.assertEqual(encabezado["title"], "A: b")
        self.assertTrue(cuerpo.startswith("\n## Uno"))

    def test_un_documento_sin_encabezado_no_es_proyeccion(self):
        with self.assertRaises(pd.Config):
            pd.separar("## Uno\n")

    def test_el_encabezado_del_repositorio_se_lee(self):
        encabezado, cuerpo, _ = pd.leer(RAIZ, SLUG)
        self.assertEqual(encabezado["canonical_url"], CANONICA)
        self.assertIn("litellm", encabezado["title"])
        self.assertGreater(len(cuerpo), 10000)


class Payload(unittest.TestCase):
    def setUp(self):
        self.encabezado, self.cuerpo, _ = pd.leer(RAIZ, SLUG)

    def test_el_cuerpo_viaja_intacto(self):
        datos = pd.payload(self.encabezado, self.cuerpo, True)
        self.assertEqual(datos["article"]["body_markdown"], self.cuerpo)

    def test_published_se_declara_y_no_se_hereda_del_archivo(self):
        self.assertEqual(self.encabezado["published"], "false")
        self.assertTrue(pd.payload(self.encabezado, self.cuerpo, True)["article"]["published"])
        self.assertFalse(pd.payload(self.encabezado, self.cuerpo, False)["article"]["published"])

    def test_los_tags_son_lista_y_como_maximo_cuatro(self):
        tags = pd.payload(self.encabezado, self.cuerpo, True)["article"]["tags"]
        self.assertIsInstance(tags, list)
        self.assertLessEqual(len(tags), pd.MAX_TAGS)

    def test_la_canonica_apunta_al_sitio_no_al_articulo_de_devto(self):
        datos = pd.payload(self.encabezado, self.cuerpo, True)
        self.assertTrue(datos["article"]["canonical_url"].startswith("https://alexisromtz-lab.github.io/"))


class Clave(unittest.TestCase):
    def test_sin_clave_es_configuracion_y_no_una_excepcion(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(pd.Config):
                pd.clave()

    def test_la_descripcion_no_publica_el_valor(self):
        descripcion = pd.describir_clave("abcdef1234567890")
        self.assertIn("len=16", descripcion)
        self.assertIn("abcd", descripcion)
        self.assertNotIn("1234567890", descripcion)

    def test_main_sin_clave_devuelve_2_y_no_abre_conexion(self):
        transporte = Transporte()
        with mock.patch.dict(os.environ, {}, clear=True):
            rc = pd.main(["--raiz", str(RAIZ), "--reparar", SLUG], transporte=transporte)
        self.assertEqual(rc, 2)
        self.assertEqual(transporte.llamadas, [])


class Seco(unittest.TestCase):
    def test_publicar_en_seco_no_hace_ninguna_peticion(self):
        transporte = Transporte()
        rc = pd.main(["--raiz", str(RAIZ), "--slug", SLUG], transporte=transporte)
        self.assertEqual(rc, 0)
        self.assertEqual(transporte.llamadas, [])

    def test_publicar_en_seco_no_exige_clave(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(pd.main(["--raiz", str(RAIZ), "--slug", SLUG], transporte=Transporte()), 0)


class Envio(unittest.TestCase):
    def test_enviar_hace_un_post_con_el_cuerpo_del_archivo(self):
        transporte = Transporte((201, {"id": 5005894, "url": "https://dev.to/x"}))
        with con_clave():
            rc = pd.main(["--raiz", str(RAIZ), "--slug", SLUG, "--enviar"], transporte=transporte)
        self.assertEqual(rc, 0)
        self.assertEqual(transporte.metodos, ["POST"])
        metodo, url, datos = transporte.llamadas[0]
        self.assertTrue(url.endswith("/api/articles"))
        _, cuerpo, _ = pd.leer(RAIZ, SLUG)
        self.assertEqual(datos["article"]["body_markdown"], cuerpo)

    def test_borrador_no_publica(self):
        transporte = Transporte((201, {"id": 1}))
        with con_clave():
            pd.main(["--raiz", str(RAIZ), "--slug", SLUG, "--enviar", "--borrador"], transporte=transporte)
        self.assertFalse(transporte.llamadas[0][2]["article"]["published"])

    def test_un_error_de_la_api_no_se_lee_como_exito(self):
        transporte = Transporte((422, {"error": "Title is too long"}))
        with con_clave():
            rc = pd.main(["--raiz", str(RAIZ), "--slug", SLUG, "--enviar"], transporte=transporte)
        self.assertEqual(rc, 3)


class Reparacion(unittest.TestCase):
    """El articulo 5005894 ya esta vivo y salio sin estructura."""

    def remoto(self, cuerpo):
        return [{"id": 5005894, "canonical_url": CANONICA, "body_markdown": cuerpo, "title": "x"}]

    def test_si_el_cuerpo_remoto_ya_es_el_local_no_hay_put(self):
        _, cuerpo, _ = pd.leer(RAIZ, SLUG)
        transporte = Transporte((200, self.remoto(cuerpo)))
        with con_clave():
            rc = pd.main(["--raiz", str(RAIZ), "--reparar", SLUG, "--enviar"], transporte=transporte)
        self.assertEqual(rc, 0)
        self.assertEqual(transporte.metodos, ["GET"])

    def test_un_cuerpo_remoto_sin_estructura_dispara_un_put(self):
        transporte = Transporte((200, self.remoto("The bug that answers SUCCESS\n\n1. Intro\n")), (200, {"id": 5005894}))
        with con_clave():
            rc = pd.main(["--raiz", str(RAIZ), "--reparar", SLUG, "--enviar"], transporte=transporte)
        self.assertEqual(rc, 0)
        self.assertEqual(transporte.metodos, ["GET", "PUT"])
        _, url, datos = transporte.llamadas[1]
        self.assertTrue(url.endswith("/api/articles/5005894"))
        _, cuerpo, _ = pd.leer(RAIZ, SLUG)
        self.assertEqual(datos["article"]["body_markdown"], cuerpo)

    def test_reparar_en_seco_dice_desfase_y_no_escribe(self):
        transporte = Transporte((200, self.remoto("sin estructura")))
        with con_clave():
            rc = pd.main(["--raiz", str(RAIZ), "--reparar", SLUG], transporte=transporte)
        self.assertEqual(rc, 0)
        self.assertEqual(transporte.metodos, ["GET"])

    def test_sin_articulo_con_esa_canonica_no_se_inventa_un_id(self):
        transporte = Transporte((200, [{"id": 1, "canonical_url": "https://otro/", "body_markdown": ""}]))
        with con_clave():
            rc = pd.main(["--raiz", str(RAIZ), "--reparar", SLUG, "--enviar"], transporte=transporte)
        self.assertEqual(rc, 3)
        self.assertEqual(transporte.metodos, ["GET"])


class Estructura(unittest.TestCase):
    """Los dos falsadores del defecto real: la pagina salio con 1 valla y 0 tablas."""

    def cuerpo(self):
        """El cuerpo que viaja, no el del disco: el falsador mide el payload."""
        encabezado, cuerpo, _ = pd.leer(RAIZ, SLUG)
        return pd.payload(encabezado, cuerpo, True)["article"]["body_markdown"]

    def test_el_cuerpo_que_viaja_conserva_todas_las_vallas(self):
        self.assertGreaterEqual(self.cuerpo().count("\n```"), 16)

    def test_el_cuerpo_que_viaja_conserva_las_tablas(self):
        self.assertGreaterEqual(self.cuerpo().count("|---"), 4)

    def test_el_cuerpo_que_viaja_conserva_los_titulares_numerados(self):
        self.assertGreaterEqual(self.cuerpo().count("\n## "), 10)


if __name__ == "__main__":
    unittest.main()
