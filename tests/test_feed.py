#!/usr/bin/env python3
"""Falsadores de feed.py: el Atom que consume un publicador automatico.

Cada test construye un portafolio minimo, rompe o comprueba una invariante y
exige que el generador la sostenga. Un feed que "se genera" pero pierde la
mitad de las piezas deja la distribucion apagada sin error visible.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FEED = RAIZ / "tools" / "feed.py"
LECTOR = RAIZ / "tools" / "paginas_articulos.py"

CITATION = """cff-version: 1.2.0
message: "Cite this report"
title: "Fixture del feed"
type: techreport
authors:
  - family-names: "Ejemplo"
    given-names: "Ada"
license: MIT
date-released: 2026-11-09
"""

SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://alexisromtz-lab.github.io/la-auditora/portafolio/auditoria-001-sujeto/</loc><lastmod>2026-11-05</lastmod></url>
</urlset>
"""

FICHA = {
    "sujeto": {"repo": "ejemplo/fixture", "sha": "0" * 40},
    "hallazgo": {"titulo": "Un hallazgo de prueba", "impacto": "Ninguno."},
    "limite": "Mide un fixture, no un sistema.",
    "estado": "verificado",
    "locus": [{"ruta": "index.html", "blob": "0" * 40, "lineas_0x0a": 1}],
    "reproduccion": {"comando": "python3 reproduce.py", "rc": 0, "salida": "ok"},
}


def fuente(titulo: str, lede: str, extra: str = "", lang: str = "") -> str:
    cabecera = ["---", "title: %s" % titulo, "lede: %s" % lede, "date: 2026-11-06"]
    if lang:
        cabecera.append("lang: %s" % lang)
    if extra:
        cabecera.append(extra)
    return "\n".join(cabecera) + "\n---\n\nTexto.\n"


def construir(destino: Path) -> Path:
    """Alfa con gemelo ES/EN, beta solo en ingles, un informe y su sitemap."""
    articulos = destino / "portafolio" / "articulos"
    (articulos / "alfa").mkdir(parents=True)
    (articulos / "alfa" / "articulo.md").write_text(
        fuente("Alfa en espanol", "Lede ES.", "tags: ai, architecture"), encoding="utf-8"
    )
    (articulos / "alfa" / "articulo.en.md").write_text(
        fuente("Alfa in English", "Lede EN.", "tags: ai, architecture", lang="en"),
        encoding="utf-8",
    )
    (articulos / "beta").mkdir()
    (articulos / "beta" / "articulo.en.md").write_text(
        fuente("Beta only English", "Lede beta.", "solo_en: si", lang="en"), encoding="utf-8"
    )
    informe = destino / "portafolio" / "auditoria-001-sujeto"
    informe.mkdir()
    (informe / "ficha.json").write_text(json.dumps(FICHA), encoding="utf-8")
    (destino / "sitemap.xml").write_text(SITEMAP, encoding="utf-8")
    (destino / "CITATION.cff").write_text(CITATION, encoding="utf-8")
    (destino / "tools").mkdir()
    shutil.copy2(FEED, destino / "tools" / "feed.py")
    shutil.copy2(LECTOR, destino / "tools" / "paginas_articulos.py")
    return destino


class FeedFalsable(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = construir(Path(self._tmp.name) / "sitio")
        self.ruta = self.root / "portafolio" / "feed.xml"

    def correr(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(self.root / "tools" / "feed.py"), "--raiz", str(self.root), *args],
            capture_output=True,
            text=True,
        )

    def test_aplicar_escribe_una_entrada_por_pieza(self) -> None:
        proc = self.correr("--aplicar")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        texto = self.ruta.read_text(encoding="utf-8")
        self.assertEqual(texto.count("<entry "), 3, texto)

    def test_gemelo_enlaza_la_pagina_inglesa_una_sola_vez(self) -> None:
        self.correr("--aplicar")
        texto = self.ruta.read_text(encoding="utf-8")
        self.assertIn("/portafolio/articulos/en/alfa/", texto)
        self.assertNotIn("<id>https://alexisromtz-lab.github.io/la-auditora/portafolio/articulos/alfa/</id>", texto)
        self.assertNotIn("Alfa en espanol", texto)

    def test_articulo_solo_en_ingles_publica_su_pagina_en(self) -> None:
        self.correr("--aplicar")
        texto = self.ruta.read_text(encoding="utf-8")
        self.assertIn("/portafolio/articulos/en/beta/", texto)
        self.assertIn("Beta only English", texto)

    def test_informe_toma_la_fecha_del_sitemap(self) -> None:
        self.correr("--aplicar")
        texto = self.ruta.read_text(encoding="utf-8")
        # la URL aparece dos veces por entrada (id y link): se busca la entrada, no el trozo
        bloques = [b for b in texto.split("<entry ")[1:] if "auditoria-001-sujeto" in b]
        self.assertEqual(len(bloques), 1)
        self.assertIn("<published>2026-11-05T00:00:00Z</published>", bloques[0])

    def test_autor_sale_de_citation(self) -> None:
        self.correr("--aplicar")
        self.assertIn("<name>Ada Ejemplo</name>", self.ruta.read_text(encoding="utf-8"))

    def test_check_sin_feed_es_rojo_y_aplicar_lo_pone_verde(self) -> None:
        proc = self.correr("--check")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("FALTA", proc.stdout)
        self.assertEqual(self.correr("--aplicar").returncode, 0)
        proc = self.correr("--check")
        self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_check_ve_el_feed_envejecido(self) -> None:
        self.correr("--aplicar")
        fuente_nueva = self.root / "portafolio" / "articulos" / "gamma"
        fuente_nueva.mkdir()
        (fuente_nueva / "articulo.en.md").write_text(
            fuente("Gamma", "Lede gamma.", "solo_en: si", lang="en"), encoding="utf-8"
        )
        proc = self.correr("--check")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("DESINCRONIZADO", proc.stdout)
        self.assertIn("4 entrada(s) esperadas", proc.stdout)

    def test_front_matter_ilegible_es_no_medido(self) -> None:
        roto = self.root / "portafolio" / "articulos" / "alfa" / "articulo.md"
        roto.write_text(fuente("Alfa", "Lede.", "tags: a, i, r"), encoding="utf-8")
        proc = self.correr("--check")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("NO_MEDIDO", proc.stderr)


if __name__ == "__main__":
    unittest.main()
