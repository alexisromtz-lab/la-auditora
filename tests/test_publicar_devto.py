"""Falsadores de la publicacion en dev.to.

El instrumento existe porque copiar de una pagina renderizada destruyo una
publicacion entera. Los falsadores que muerden son los de estructura: el
cuerpo que viaja tiene que traer las mismas vallas y las mismas filas de
tabla que el articulo de origen.
"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
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

    def test_un_tag_ilegal_no_llega_a_la_api(self):
        # dev.to responde 422 y aborta la publicacion entera por un solo guion.
        encabezado = dict(self.encabezado, tags="devops, github-actions")
        with self.assertRaises(pd.Config) as capturado:
            pd.payload(encabezado, self.cuerpo, True)
        self.assertIn("github-actions", str(capturado.exception))

    def test_los_tags_de_la_proyeccion_son_legales(self):
        tags = [t.strip() for t in self.encabezado["tags"].split(",") if t.strip()]
        self.assertTrue(tags)
        for tag in tags:
            with self.subTest(tag=tag):
                self.assertRegex(tag, r"^[a-z0-9]+$")

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

    def test_los_dos_nombres_conocidos_se_aceptan(self):
        # El nombre real en la maquina del dueño lleva guion bajo entre DEV y TO.
        for nombre in pd.VARIABLES:
            with self.subTest(nombre=nombre):
                with mock.patch.dict(os.environ, {nombre: "valor-%s" % nombre}, clear=True):
                    valor, origen = pd.clave()
                self.assertEqual(valor, "valor-%s" % nombre)
                self.assertEqual(origen, nombre)

    def test_gana_el_primer_nombre_declarado(self):
        ambos = {nombre: "valor-%s" % nombre for nombre in pd.VARIABLES}
        with mock.patch.dict(os.environ, ambos, clear=True):
            _, origen = pd.clave()
        self.assertEqual(origen, pd.VARIABLES[0])

    def test_un_env_se_lee_por_nombre_y_no_por_posicion(self):
        # Un `.env` no es un archivo de una sola clave: la clave se busca, no se asume.
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / ".env.local"
            ruta.write_text(
                'OTRA=no-soy-yo\nDEV_TO_API_KEY="la-buena"\nTERCERA=tampoco\n',
                encoding="utf-8",
            )
            valor, origen = pd.clave(str(ruta))
        self.assertEqual(valor, "la-buena")
        self.assertTrue(origen.endswith(":DEV_TO_API_KEY"), origen)

    def test_en_el_env_gana_la_ultima_aparicion(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / ".env"
            ruta.write_text("DEV_TO_API_KEY=vieja\nDEV_TO_API_KEY=nueva\n", encoding="utf-8")
            valor, _ = pd.clave(str(ruta))
        self.assertEqual(valor, "nueva")

    def test_un_archivo_con_solo_la_clave_tambien_sirve(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "clave.txt"
            ruta.write_text("abc123\n", encoding="utf-8")
            valor, origen = pd.clave(str(ruta))
        self.assertEqual(valor, "abc123")
        self.assertEqual(origen, str(ruta))

    def test_un_env_sin_la_clave_nombra_las_que_busca(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / ".env"
            ruta.write_text("OTRA=1\n", encoding="utf-8")
            with self.assertRaises(pd.Config) as capturado:
                pd.clave(str(ruta))
        for nombre in pd.VARIABLES:
            self.assertIn(nombre, str(capturado.exception))

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


class Normalizacion(unittest.TestCase):
    """Lo que dev.to reescribe al guardar no es un cambio del autor."""

    def test_la_linea_en_blanco_inicial_no_es_un_desfase(self):
        self.assertEqual(pd.normalizar("\n\nA\n"), pd.normalizar("\nA\n"))

    def test_la_etiqueta_de_valla_que_pone_devto_no_es_un_desfase(self):
        self.assertEqual(pd.normalizar("```\nx\n```\n"), pd.normalizar("```shell\nx\n```\n"))
        self.assertEqual(pd.normalizar("```\nx\n```\n"), pd.normalizar("```python\nx\n```\n"))

    def test_una_valla_ausente_si_es_un_desfase(self):
        # La estructura no se normaliza: perder una valla es perder estructura.
        self.assertNotEqual(
            pd.normalizar("```\nx\n```\n"),
            pd.normalizar("x\n"),
        )

    def test_un_cambio_de_texto_sigue_siendo_un_desfase(self):
        self.assertNotEqual(pd.normalizar("uno\n"), pd.normalizar("dos\n"))

    def test_los_saltos_de_windows_no_son_un_desfase(self):
        self.assertEqual(pd.normalizar("a\r\nb\r\n"), pd.normalizar("a\nb\n"))

    def test_una_valla_en_medio_de_una_linea_no_se_normaliza(self):
        # Solo la linea que es una valla entera lleva etiqueta de la plataforma.
        self.assertEqual(pd.normalizar("texto ```x``` texto\n"), "texto ```x``` texto")


class Cabeceras(unittest.TestCase):
    """dev.to responde 403 al User-Agent por defecto de urllib. Medido, no supuesto."""

    def _peticion(self, metodo="GET", datos=None):
        capturada = {}

        class Respuesta:
            status = 200

            def read(self):
                return b"{}"

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

        def falso_urlopen(peticion, timeout=None):
            capturada["p"] = peticion
            return Respuesta()

        with mock.patch("urllib.request.urlopen", side_effect=falso_urlopen):
            pd.transporte_urllib(metodo, pd.API + "/articles/me/all?per_page=1", "clavedeprueba", datos)
        return capturada["p"]

    def test_el_transporte_se_identifica_con_un_agente_propio(self):
        agente = self._peticion().get_header("User-agent")
        self.assertEqual(agente, pd.AGENTE)
        self.assertNotIn("Python-urllib", agente or "")

    def test_el_transporte_manda_la_clave_en_el_header_api_key(self):
        self.assertEqual(self._peticion().get_header("Api-key"), "clavedeprueba")

    def test_el_transporte_declara_json_al_escribir(self):
        peticion = self._peticion("PUT", {"article": {"body_markdown": "x"}})
        self.assertEqual(peticion.get_method(), "PUT")
        self.assertEqual(peticion.get_header("Content-type"), "application/json")
        self.assertTrue(json.loads(peticion.data.decode("utf-8"))["article"]["body_markdown"])


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

    def test_el_limite_de_tasa_es_transitorio_y_no_se_reintenta_solo(self):
        # Un POST repetido a ciegas publica dos veces: se para y se avisa.
        transporte = Transporte((429, {"error": "Rate limit reached, try again in 30 seconds"}))
        with con_clave():
            rc = pd.main(["--raiz", str(RAIZ), "--slug", SLUG, "--enviar"], transporte=transporte)
        self.assertEqual(rc, 4)
        self.assertEqual(transporte.metodos, ["POST"])

    def test_el_limite_de_tasa_dice_cuanto_esperar(self):
        salida = io.StringIO()
        with mock.patch("sys.stderr", salida):
            rc = pd.fallo_de_api(429, {"error": "Rate limit reached, try again in 45 seconds"})
        self.assertEqual(rc, 4)
        self.assertIn("45 s", salida.getvalue())
        self.assertIn("No se reintenta solo", salida.getvalue())


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

    def test_un_articulo_pegado_a_mano_se_reconoce_por_titulo(self):
        # El articulo vivo nacio del portapapeles: no tiene canonical_url. Buscar
        # solo por canonica lo declaraba inexistente y la reparacion era imposible.
        encabezado, cuerpo, _ = pd.leer(RAIZ, SLUG)
        listado = [{"id": 5005894, "canonical_url": None, "title": encabezado["title"], "body_markdown": "plano"}]
        remoto, por = pd.localizar(listado, encabezado, SLUG)
        self.assertEqual(por, "title")
        self.assertEqual(remoto["id"], 5005894)

    def test_la_canonica_gana_al_titulo(self):
        encabezado, _, _ = pd.leer(RAIZ, SLUG)
        listado = [
            {"id": 1, "canonical_url": None, "title": encabezado["title"], "body_markdown": "plano"},
            {"id": 2, "canonical_url": CANONICA, "title": "otro", "body_markdown": "plano"},
        ]
        remoto, por = pd.localizar(listado, encabezado, SLUG)
        self.assertEqual((remoto["id"], por), (2, "canonical_url"))

    def test_el_id_numerico_localiza_sin_depender_del_titulo(self):
        encabezado, _, _ = pd.leer(RAIZ, SLUG)
        listado = [{"id": 5005894, "canonical_url": None, "title": "otro titulo"}]
        remoto, por = pd.localizar(listado, encabezado, "5005894")
        self.assertEqual((remoto["id"], por), (5005894, "id"))

    def test_un_titulo_parecido_no_es_el_articulo(self):
        encabezado, _, _ = pd.leer(RAIZ, SLUG)
        listado = [{"id": 1, "canonical_url": None, "title": encabezado["title"] + " (parte 2)"}]
        self.assertEqual(pd.localizar(listado, encabezado, SLUG), (None, ""))

    def test_reparacion_de_un_articulo_sin_canonica_la_añade(self):
        encabezado, cuerpo, _ = pd.leer(RAIZ, SLUG)
        listado = [{"id": 5005894, "canonical_url": None, "title": encabezado["title"], "body_markdown": "plano"}]
        transporte = Transporte((200, listado), (200, {"id": 5005894}))
        with con_clave():
            rc = pd.main(["--raiz", str(RAIZ), "--reparar", SLUG, "--enviar"], transporte=transporte)
        self.assertEqual(rc, 0)
        self.assertEqual(transporte.metodos, ["GET", "PUT"])
        _, _, datos = transporte.llamadas[1]
        self.assertEqual(datos["article"]["canonical_url"], CANONICA)
        self.assertEqual(datos["article"]["body_markdown"], cuerpo)

    def test_una_coma_decimal_es_la_misma_cifra_que_un_punto(self):
        self.assertEqual(pd.numeros("12,06 s"), pd.numeros("12.06 s"))

    def test_un_espacio_de_miles_es_la_misma_cifra_que_una_coma(self):
        self.assertEqual(pd.numeros("1 015 imports"), pd.numeros("1,015 imports"))

    def test_una_version_no_se_confunde_con_un_decimal(self):
        self.assertEqual(pd.numeros("3.12.13"), pd.numeros("3.12.13"))


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


class Sustitucion(unittest.TestCase):
    """Traducir un articulo vivo no es republicarlo: es reemplazar su cuerpo."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ruta = Path(self.tmp.name) / "cuerpo.md"

    def remoto(self, cuerpo, titulo="Titulo viejo"):
        return [{"id": 4936293, "body_markdown": cuerpo, "title": titulo, "published_at": "2026-10-28"}]

    def cuerpo(self, texto):
        self.ruta.write_text(texto, encoding="utf-8")
        return str(self.ruta)

    def test_una_traduccion_que_conserva_las_cifras_se_envia(self):
        transporte = Transporte((200, self.remoto("Hola 42 % y 807")), (200, {"id": 4936293, "body_markdown": "Hello 42 % and 807"}))
        with con_clave():
            rc = pd.main(["--sustituir", "4936293", "--cuerpo", self.cuerpo("Hello 42 % and 807"), "--enviar"], transporte=transporte)
        self.assertEqual(rc, 0)
        self.assertEqual(transporte.metodos, ["GET", "PUT"])

    def test_una_traduccion_que_mueve_una_cifra_no_se_envia(self):
        transporte = Transporte((200, self.remoto("Hola 807")))
        with con_clave():
            rc = pd.main(["--sustituir", "4936293", "--cuerpo", self.cuerpo("Hello 806"), "--enviar"], transporte=transporte)
        self.assertEqual(rc, 5)
        self.assertEqual(transporte.metodos, ["GET"])

    def test_la_excusa_declarada_permite_mover_la_cifra(self):
        transporte = Transporte((200, self.remoto("Hola 807")), (200, {"id": 4936293, "body_markdown": "Hello 806"}))
        with con_clave():
            rc = pd.main(
                ["--sustituir", "4936293", "--cuerpo", self.cuerpo("Hello 806"), "--enviar", "--excusa", "corregido"],
                transporte=transporte,
            )
        self.assertEqual(rc, 0)
        self.assertEqual(transporte.metodos, ["GET", "PUT"])

    def test_si_el_cuerpo_ya_es_el_nuevo_no_hay_put(self):
        transporte = Transporte((200, self.remoto("Hello 42 % and 807")))
        with con_clave():
            rc = pd.main(["--sustituir", "4936293", "--cuerpo", self.cuerpo("Hello 42 % and 807"), "--enviar"], transporte=transporte)
        self.assertEqual(rc, 0)
        self.assertEqual(transporte.metodos, ["GET"])

    def test_el_titulo_nuevo_viaja_solo_si_se_declara(self):
        transporte = Transporte((200, self.remoto("Hola 1")), (200, {"id": 4936293, "body_markdown": "Hello 1"}))
        with con_clave():
            pd.main(["--sustituir", "4936293", "--cuerpo", self.cuerpo("Hello 1"), "--enviar"], transporte=transporte)
        _, _, datos = transporte.llamadas[1]
        self.assertNotIn("title", datos["article"])

    def test_un_id_que_no_existe_no_inventa_nada(self):
        transporte = Transporte((200, self.remoto("Hola 1")))
        with con_clave():
            rc = pd.main(["--sustituir", "999", "--cuerpo", self.cuerpo("Hello 1"), "--enviar"], transporte=transporte)
        self.assertEqual(rc, 3)
        self.assertEqual(transporte.metodos, ["GET"])

    def test_sustituir_sin_cuerpo_es_error_de_contrato(self):
        transporte = Transporte((200, self.remoto("Hola 1")))
        with con_clave():
            rc = pd.main(["--sustituir", "4936293", "--enviar"], transporte=transporte)
        self.assertEqual(rc, 2)
        self.assertEqual(transporte.metodos, [])

    def test_en_seco_lee_pero_no_escribe(self):
        transporte = Transporte((200, self.remoto("Hola 42 % y 807")))
        with con_clave():
            rc = pd.main(["--sustituir", "4936293", "--cuerpo", self.cuerpo("Hello 42 % and 807")], transporte=transporte)
        self.assertEqual(rc, 0)
        self.assertEqual(transporte.metodos, ["GET"])


if __name__ == "__main__":
    unittest.main()
