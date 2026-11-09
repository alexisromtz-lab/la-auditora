#!/usr/bin/env python3
"""Falsadores de los gemelos ingleses: una traduccion que mueve una cifra no es
una traduccion, es una segunda fuente de verdad.

Tres invariantes, ninguno depende de que el traductor sea honesto:

1. **Las cifras no cambian de valor.** El multiconjunto de numeros del cuerpo ES
   y del cuerpo EN debe ser identico. Normaliza separadores de miles (`1 228`,
   `1,228` y `1228` son el mismo numero) para no confundir formato con dato.
2. **El codigo no se toca.** Cada bloque de valla (```) debe aparecer byte a byte
   en los dos idiomas: es la parte que el lector ejecuta.
3. **El cuerpo EN dejo de ser espanol.** Densidad de marcadores espanoles en EN
   menor que una fraccion de la de ES. Se autocalibra contra el propio ES, asi
   que no hay constante magica que envejezca.
"""

from __future__ import annotations

import re
import unittest
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARTICULOS = RAIZ / "portafolio" / "articulos"

# Palabras y marcas que el ingles no usa. Se compara EN contra ES: lo que
# importa es la caida, no el valor absoluto.
MARCADORES_ES = re.compile(
    r"[ñáéíóú¿¡]|\b(?:que|para|del|los|las|con|una|por|como|esto|esta|más|pero|sin"
    r"|entre|desde|cuando|porque|todo|todos|hay|es|son|fue|sin)\b",
    re.IGNORECASE,
)
UMBRAL_EN = 0.2  # el gemelo conserva como maximo el 20 % de la densidad del ES
VALLA = re.compile(r"```.*?```", re.DOTALL)


def leer(ruta: Path):
    """Devuelve (encabezado, cuerpo). El cuerpo excluye el H1 del titulo."""
    texto = ruta.read_text(encoding="utf-8")
    partes = texto.split("---", 2)
    cabecera = {}
    for linea in partes[1].strip().splitlines():
        if ":" in linea:
            clave, valor = linea.split(":", 1)
            cabecera[clave.strip()] = valor.strip()
    cuerpo = re.sub(r"^\s{0,3}#\s+.*$", "", partes[2], count=1, flags=re.MULTILINE)
    return cabecera, cuerpo


def cifras(cuerpo: str) -> Counter:
    """Multiconjunto de numeros con los separadores de miles normalizados."""
    sin_vallas = VALLA.sub(" ", cuerpo)
    sin_guiones = re.sub(r"(?<=\d)[,.\u00a0 ](?=\d{3}(?!\d))", "", sin_vallas)
    return Counter(re.findall(r"\d+", sin_guiones))


def vallas(cuerpo: str) -> Counter:
    return Counter(m.strip() for m in VALLA.findall(cuerpo))


def pares():
    """(slug, fuente ES, gemelo EN) de cada articulo que tenga los dos."""
    salida = []
    for carpeta in sorted(ARTICULOS.iterdir()):
        es = carpeta / "articulo.md"
        en = carpeta / "articulo.en.md"
        if es.is_file() and en.is_file():
            salida.append((carpeta.name, es, en))
    return salida


class GemelosEnIngles(unittest.TestCase):
    def setUp(self) -> None:
        self.todos = pares()

    def test_hay_al_menos_un_gemelo(self) -> None:
        self.assertTrue(self.todos, "no hay ningun articulo.en.md: NO_MEDIDO")

    def test_el_encabezado_declara_ingles(self) -> None:
        for slug, _, en in self.todos:
            with self.subTest(slug=slug):
                cabecera, _ = leer(en)
                self.assertEqual(
                    cabecera.get("lang"),
                    "en",
                    "%s: el gemelo debe declarar lang: en" % slug,
                )

    def test_las_cifras_no_se_mueven(self) -> None:
        for slug, es, en in self.todos:
            with self.subTest(slug=slug):
                a = cifras(leer(es)[1])
                b = cifras(leer(en)[1])
                self.assertEqual(
                    a - b,
                    Counter(),
                    "%s: cifras del ES que no aparecen en el EN: %s"
                    % (slug, sorted((a - b).items())),
                )
                self.assertEqual(
                    b - a,
                    Counter(),
                    "%s: cifras del EN que no aparecen en el ES: %s"
                    % (slug, sorted((b - a).items())),
                )

    def test_las_vallas_de_codigo_son_identicas(self) -> None:
        for slug, es, en in self.todos:
            with self.subTest(slug=slug):
                a = vallas(leer(es)[1])
                b = vallas(leer(en)[1])
                self.assertEqual(
                    sorted((a - b).elements()),
                    [],
                    "%s: bloques de codigo que se perdieron al traducir" % slug,
                )
                self.assertEqual(
                    sorted((b - a).elements()),
                    [],
                    "%s: bloques de codigo que el gemelo inventó" % slug,
                )

    def test_el_gemelo_dejo_de_ser_espanol(self) -> None:
        for slug, es, en in self.todos:
            with self.subTest(slug=slug):
                es_hits = len(MARCADORES_ES.findall(leer(es)[1]))
                en_hits = len(MARCADORES_ES.findall(leer(en)[1]))
                self.assertGreater(es_hits, 20, "%s: el ES no tiene marcadores" % slug)
                self.assertLessEqual(
                    en_hits,
                    es_hits * UMBRAL_EN,
                    "%s: el gemelo conserva %d marcadores espanoles frente a %d del ES"
                    % (slug, en_hits, es_hits),
                )

    def test_el_titulo_y_el_lede_se_tradujeron(self) -> None:
        for slug, es, en in self.todos:
            with self.subTest(slug=slug):
                a, _ = leer(es)
                b, _ = leer(en)
                self.assertNotEqual(a["title"], b["title"], "%s: titulo sin traducir" % slug)
                self.assertNotEqual(a["lede"], b["lede"], "%s: lede sin traducir" % slug)
                self.assertEqual(a["date"], b["date"], "%s: la fecha no coincide" % slug)


if __name__ == "__main__":
    unittest.main()
