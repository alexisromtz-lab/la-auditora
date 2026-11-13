#!/usr/bin/env python3
"""Falsadores del canario: un canario que nunca suena no es un canario.

Each test builds a minimal, valid site in a temporary directory, breaks exactly
one invariant, and requires the canary to name that invariant in red. The
healthy fixture must stay green, so a canary stuck on red is caught too.
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
CANARIO = RAIZ / "tools" / "canario.py"
SITE_BASE = "https://alexisromtz-lab.github.io/la-auditora/"
INFORME = "portafolio/auditoria-001-sujeto"
BASE_LOC = "https://alexisromtz-lab.github.io/la-auditora/"

SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{base}</loc></url>
  <url><loc>{base}en/</loc></url>
  <url><loc>{base}{informe}/</loc></url>
</urlset>
"""

CITATION = """cff-version: 1.2.0
message: "Cite this report"
title: "Fixture del canario"
type: techreport
authors:
  - family-names: "Ejemplo"
license: MIT
date-released: 2026-11-09
"""

ZENODO = {
    "title": "Fixture del canario",
    "description": "Sitio minimo para falsar el canario.",
    "creators": [{"name": "Ejemplo, Ada"}],
    "license": "cc-by-4.0",
    "upload_type": "publication",
}

FICHA = {
    "sujeto": {"repo": "ejemplo/fixture", "sha": "0" * 40},
    "hallazgo": {"titulo": "Un hallazgo de prueba", "impacto": "Ninguno."},
    "limite": "Mide un fixture, no un sistema.",
    "estado": "verificado",
    "locus": [{"ruta": "index.html", "blob": "0" * 40, "lineas_0x0a": 1}],
    "reproduccion": {"comando": "python3 reproduce.py", "rc": 0, "salida": "ok"},
}


def construir(destino: Path) -> Path:
    informe = destino / INFORME
    (destino / "en").mkdir(parents=True)
    (destino / "tools").mkdir()
    informe.mkdir(parents=True)
    (destino / "index.html").write_text(
        '<a href="%s/">Informe 001</a>\n' % INFORME, encoding="utf-8"
    )
    (destino / "en" / "index.html").write_text(
        '<a href="../%s/">Report 001</a>\n<a href="/la-auditora/en/">EN</a>\n' % INFORME,
        encoding="utf-8",
    )
    (informe / "index.html").write_text('<a href="../../">Volver</a>\n', encoding="utf-8")
    (informe / "ficha.json").write_text(json.dumps(FICHA), encoding="utf-8")
    (informe / "reproduce.py").write_text(
        'import sys\nprint("RC 0 - fixture")\nsys.exit(0)\n', encoding="utf-8"
    )
    (destino / "sitemap.xml").write_text(
        SITEMAP.format(base=SITE_BASE, informe=INFORME), encoding="utf-8"
    )
    (destino / "CITATION.cff").write_text(CITATION, encoding="utf-8")
    (destino / ".zenodo.json").write_text(json.dumps(ZENODO), encoding="utf-8")
    (destino / "README.md").write_text(
        "Deposito: https://doi.org/10.5281/zenodo.1\n", encoding="utf-8"
    )
    shutil.copy2(CANARIO, destino / "tools" / "canario.py")
    sembrar_feed(destino)
    return destino


FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Fixture del canario</title>
  <id>{base}</id>
  <updated>2026-11-09T00:00:00Z</updated>
{entradas}</feed>
"""

ENTRADA = (
    '  <entry><title>%s</title><id>%s</id>'
    "<link href=\"%s\"/><updated>2026-11-09T00:00:00Z</updated></entry>\n"
)


def sembrar_feed(root: Path) -> None:
    """Feed coherente con el sitemap: si el fixture sano suena por el feed, el test miente."""
    sitemap = (root / "sitemap.xml").read_text(encoding="utf-8")
    locs = [trozo.split("</loc>")[0] for trozo in sitemap.split("<loc>")[1:]]
    entradas = []
    for loc in locs:
        seca = loc.rstrip("/")
        if seca.endswith("/portafolio/articulos") or seca.endswith("/portafolio/articulos/en"):
            continue
        if "/portafolio/auditoria-" in seca or "/portafolio/articulos/" in seca:
            entradas.append(ENTRADA % (seca.rsplit("/", 1)[-1], loc, loc))
    destino = root / "portafolio" / "feed.xml"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(FEED.format(base=BASE_LOC, entradas="".join(entradas)), encoding="utf-8")


def ficha_actualizada(root: Path, **cambios) -> None:
    ruta = root / INFORME / "ficha.json"
    ficha = json.loads(ruta.read_text(encoding="utf-8"))
    ficha.update(cambios)
    ruta.write_text(json.dumps(ficha), encoding="utf-8")


ARTICULO = "portafolio/articulos/un-articulo"


def cablear_articulo(root: Path) -> None:
    """Articulo sano: fuente, pagina y su indice -- las tres piezas del grafo."""
    pieza = root / ARTICULO
    pieza.mkdir(parents=True)
    (pieza / "articulo.md").write_text(
        "---\ntitle: Un articulo\nlede: Fixture.\ndate: 2026-11-06\n---\n\nTexto.\n",
        encoding="utf-8",
    )
    (pieza / "index.html").write_text('<a href="../../../">Volver</a>\n', encoding="utf-8")
    (root / "portafolio" / "articulos" / "index.html").write_text(
        '<a href="un-articulo/">Un articulo</a>\n', encoding="utf-8"
    )
    locs = [
        BASE_LOC,
        BASE_LOC + "en/",
        BASE_LOC + INFORME + "/",
        BASE_LOC + "portafolio/articulos/",
        BASE_LOC + ARTICULO + "/",
    ]
    (root / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join("  <url><loc>%s</loc></url>\n" % u for u in locs)
        + "</urlset>\n",
        encoding="utf-8",
    )
    for portada in ("index.html", "en/index.html"):
        ruta = root / portada
        ruta.write_text(
            ruta.read_text(encoding="utf-8")
            + '<a href="%sportafolio/articulos/">Articulos</a>\n'
            % ("" if portada == "index.html" else "../"),
            encoding="utf-8",
        )
    sembrar_feed(root)


def cablear_gemelo(root: Path) -> None:
    """Gemelo EN sano: fuente, pagina espejo, indice EN y los dos enlaces cruzados."""
    en = root / "portafolio" / "articulos" / "en"
    (en / "un-articulo").mkdir(parents=True)
    (root / ARTICULO / "articulo.en.md").write_text(
        "---\ntitle: An article\nlede: Fixture.\ndate: 2026-11-06\nlang: en\n---\n\nText.\n",
        encoding="utf-8",
    )
    (en / "un-articulo" / "index.html").write_text(
        '<a href="../../un-articulo/">Leer en espanol</a>\n', encoding="utf-8"
    )
    (en / "index.html").write_text('<a href="un-articulo/">An article</a>\n', encoding="utf-8")
    portada_en = root / "en" / "index.html"
    portada_en.write_text(
        portada_en.read_text(encoding="utf-8")
        + '<a href="../portafolio/articulos/en/">Articles (EN)</a>\n',
        encoding="utf-8",
    )
    es = root / ARTICULO / "index.html"
    es.write_text(
        es.read_text(encoding="utf-8") + '<a href="../en/un-articulo/">English</a>\n',
        encoding="utf-8",
    )
    sitemap = root / "sitemap.xml"
    sitemap.write_text(
        sitemap.read_text(encoding="utf-8").replace(
            "</urlset>",
            "  <url><loc>%sportafolio/articulos/en/</loc></url>\n"
            "  <url><loc>%sportafolio/articulos/en/un-articulo/</loc></url>\n</urlset>"
            % (BASE_LOC, BASE_LOC),
        ),
        encoding="utf-8",
    )
    sembrar_feed(root)


class CanarioFalsable(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = construir(Path(self._tmp.name) / "sitio")

    def correr(self, root: Path = None):
        objetivo = self.root if root is None else root
        return subprocess.run(
            [sys.executable, str(objetivo / "tools" / "canario.py")],
            capture_output=True,
            text=True,
            timeout=300,
        )

    def exigir_rojo(self, comprobacion: str, salida: str) -> None:
        self.assertIn("FALLA  %s" % comprobacion, salida)

    def test_fixture_sano_es_verde(self) -> None:
        proc = self.correr()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("CANARIO OK - 6 de 6", proc.stdout)

    def test_enlace_relativo_roto_enciende_enlaces(self) -> None:
        (self.root / "index.html").write_text(
            '<a href="%s/">Informe 001</a>\n<a href="portafolio/informe-fantasma/">X</a>\n'
            % INFORME,
            encoding="utf-8",
        )
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.exigir_rojo("enlaces", proc.stdout)
        self.assertIn("informe-fantasma", proc.stdout)

    def test_escapar_del_repositorio_enciende_enlaces(self) -> None:
        (self.root / INFORME / "index.html").write_text(
            '<a href="../../../../etc/passwd">Volver</a>\n', encoding="utf-8"
        )
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.exigir_rojo("enlaces", proc.stdout)
        self.assertIn("escapa del repositorio", proc.stdout)

    def test_informe_sin_enlace_desde_portada_enciende_grafo(self) -> None:
        (self.root / "en" / "index.html").write_text(
            '<a href="/la-auditora/en/">EN</a>\n', encoding="utf-8"
        )
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.exigir_rojo("grafo", proc.stdout)
        self.assertIn("no enlaza", proc.stdout)

    def test_informe_ausente_del_sitemap_enciende_grafo(self) -> None:
        (self.root / "sitemap.xml").write_text(
            SITEMAP.format(base=SITE_BASE, informe="portafolio/en"), encoding="utf-8"
        )
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.exigir_rojo("grafo", proc.stdout)
        self.assertIn("sitemap.xml no declara", proc.stdout)

    def test_ficha_sin_limite_enciende_triada(self) -> None:
        ficha = dict(FICHA)
        del ficha["limite"]
        (self.root / INFORME / "ficha.json").write_text(json.dumps(ficha), encoding="utf-8")
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.exigir_rojo("triada", proc.stdout)
        self.assertIn("`limite`", proc.stdout)

    def test_informe_sin_reproduce_enciende_triada(self) -> None:
        (self.root / INFORME / "reproduce.py").unlink()
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.exigir_rojo("triada", proc.stdout)
        self.assertIn("reproduce.py falta", proc.stdout)

    def test_zenodo_ilegible_enciende_citas(self) -> None:
        (self.root / ".zenodo.json").write_text("{ no es json", encoding="utf-8")
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.exigir_rojo("citas", proc.stdout)
        self.assertIn("no parsea", proc.stdout)

    def test_readme_sin_doi_enciende_citas(self) -> None:
        (self.root / "README.md").write_text("Sin deposito.\n", encoding="utf-8")
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.exigir_rojo("citas", proc.stdout)
        self.assertIn("doi.org/10.5281", proc.stdout)

    def test_rc_declarado_que_no_coincide_enciende_reproduce(self) -> None:
        ruta = self.root / INFORME / "ficha.json"
        ficha = json.loads(ruta.read_text(encoding="utf-8"))
        ficha["reproduccion"]["rc"] = 1
        ruta.write_text(json.dumps(ficha), encoding="utf-8")
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.exigir_rojo("reproduce", proc.stdout)
        self.assertIn("declara rc=1", proc.stdout)

    def test_sujeto_ausente_declarado_es_no_medido_y_no_rojo(self) -> None:
        ruta = self.root / INFORME / "ficha.json"
        ficha = json.loads(ruta.read_text(encoding="utf-8"))
        ficha["reproduccion"]["comando"] = "python3 reproduce.py objeto/workflow.yml"
        ficha["reproduccion"]["no_medible"] = "el sujeto vive en otro repositorio"
        ruta.write_text(json.dumps(ficha), encoding="utf-8")
        proc = self.correr()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("NO_MEDIDO declarado", proc.stdout)
        self.assertIn("CANARIO OK", proc.stdout)

    # HUELLA-TEST-CANARIO-COMIENDO-METACARACTERES-20261112: el falsador de los
    # dos agujeros del 12-Nov. El primero: `&&` se colaba como ruta inexistente y
    # el caso se saltaba con una nota, asi que el rc nunca se comparaba.
    def test_comando_con_metacaracteres_enciende_reproduce(self) -> None:
        ruta = self.root / INFORME / "ficha.json"
        ficha = json.loads(ruta.read_text(encoding="utf-8"))
        ficha["reproduccion"]["comando"] = "python3 reproduce.py && true"
        ruta.write_text(json.dumps(ficha), encoding="utf-8")
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.exigir_rojo("reproduce", proc.stdout)
        self.assertIn("metacaracteres de shell", proc.stdout)

    def test_sujeto_ausente_sin_declarar_enciende_reproduce(self) -> None:
        ruta = self.root / INFORME / "ficha.json"
        ficha = json.loads(ruta.read_text(encoding="utf-8"))
        ficha["reproduccion"].pop("no_medible", None)
        ficha["reproduccion"]["comando"] = "python3 reproduce.py objeto/workflow.yml"
        ruta.write_text(json.dumps(ficha), encoding="utf-8")
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.exigir_rojo("reproduce", proc.stdout)
        self.assertIn("no declara `reproduccion.no_medible`", proc.stdout)

    def test_articulo_sano_cableado_es_verde(self) -> None:
        cablear_articulo(self.root)
        proc = self.correr()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("1 articulos", proc.stdout)

    def test_articulo_fuera_del_sitemap_enciende_grafo(self) -> None:
        cablear_articulo(self.root)
        sitemap = self.root / "sitemap.xml"
        sitemap.write_text(
            sitemap.read_text(encoding="utf-8").replace(BASE_LOC + ARTICULO + "/", ""),
            encoding="utf-8",
        )
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.exigir_rojo("grafo", proc.stdout)
        self.assertIn("sitemap.xml no declara " + BASE_LOC + ARTICULO, proc.stdout)

    def test_articulo_sin_enlace_desde_el_indice_enciende_grafo(self) -> None:
        cablear_articulo(self.root)
        (self.root / "portafolio" / "articulos" / "index.html").write_text(
            "<p>Ningun enlace.</p>\n", encoding="utf-8"
        )
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.exigir_rojo("grafo", proc.stdout)
        self.assertIn("no enlaza " + ARTICULO, proc.stdout)

    def test_indice_de_articulos_sin_enlace_desde_portada_enciende_grafo(self) -> None:
        cablear_articulo(self.root)
        (self.root / "index.html").write_text(
            '<a href="%s/">Informe 001</a>\n' % INFORME, encoding="utf-8"
        )
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.exigir_rojo("grafo", proc.stdout)
        self.assertIn("no enlaza portafolio/articulos/index.html", proc.stdout)

    # ── el gemelo ingles en el grafo ──────────────────────────────────────

    def test_gemelo_en_cableado_es_verde(self) -> None:
        cablear_articulo(self.root)
        cablear_gemelo(self.root)
        proc = self.correr()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("1 con gemelo EN", proc.stdout)

    def test_gemelo_en_fuera_del_sitemap_enciende_grafo(self) -> None:
        cablear_articulo(self.root)
        cablear_gemelo(self.root)
        sitemap = self.root / "sitemap.xml"
        sitemap.write_text(
            sitemap.read_text(encoding="utf-8").replace(
                BASE_LOC + "portafolio/articulos/en/un-articulo/", ""
            ),
            encoding="utf-8",
        )
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.exigir_rojo("grafo", proc.stdout)
        self.assertIn("sitemap.xml no declara " + BASE_LOC + "portafolio/articulos/en/un-articulo", proc.stdout)

    def test_gemelo_en_sin_pagina_enciende_grafo(self) -> None:
        cablear_articulo(self.root)
        cablear_gemelo(self.root)
        (self.root / "portafolio" / "articulos" / "en" / "un-articulo" / "index.html").unlink()
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.exigir_rojo("grafo", proc.stdout)
        self.assertIn("gemelo de " + ARTICULO, proc.stdout)

    def test_gemelo_en_sin_enlace_reciproco_enciende_grafo(self) -> None:
        cablear_articulo(self.root)
        cablear_gemelo(self.root)
        (self.root / "portafolio" / "articulos" / "en" / "un-articulo" / "index.html").write_text(
            "<p>Sin vuelta atras.</p>\n", encoding="utf-8"
        )
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.exigir_rojo("grafo", proc.stdout)
        self.assertIn("no enlaza su fuente", proc.stdout)

    def test_gemelo_en_sin_enlace_desde_el_indice_en_enciende_grafo(self) -> None:
        cablear_articulo(self.root)
        cablear_gemelo(self.root)
        (self.root / "portafolio" / "articulos" / "en" / "index.html").write_text(
            "<p>Ningun enlace.</p>\n", encoding="utf-8"
        )
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.exigir_rojo("grafo", proc.stdout)
        self.assertIn("portafolio/articulos/en/index.html no enlaza", proc.stdout)


    def test_la_portada_en_sin_enlace_al_indice_en_enciende_grafo(self) -> None:
        cablear_articulo(self.root)
        cablear_gemelo(self.root)
        portada = self.root / "en" / "index.html"
        portada.write_text(
            portada.read_text(encoding="utf-8").replace(
                '<a href="../portafolio/articulos/en/">Articles (EN)</a>\n', ""
            ),
            encoding="utf-8",
        )
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.exigir_rojo("grafo", proc.stdout)
        self.assertIn("en/index.html no enlaza portafolio/articulos/en/index.html", proc.stdout)


    def test_raiz_sin_index_es_no_medido(self) -> None:
        ajeno = Path(self._tmp.name) / "ajeno"
        (ajeno / "tools").mkdir(parents=True)
        shutil.copy2(CANARIO, ajeno / "tools" / "canario.py")
        proc = self.correr(ajeno)
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertIn("NO_MEDIDO", proc.stdout)


if __name__ == "__main__":
    unittest.main()


def cablear_solo_en(root: Path) -> None:
    """Un articulo que solo existe en ingles: fuente EN, pagina EN, indice EN y
    sitemap. No tiene fuente ES ni pagina ES."""
    cablear_articulo(root)
    pieza = root / "portafolio" / "articulos" / "solo-ingles"
    pieza.mkdir(parents=True)
    (pieza / "articulo.en.md").write_text(
        "---\ntitle: Only EN\nlede: Fixture.\ndate: 2026-11-06\nlang: en\nsolo_en: si\n---\n\nText.\n",
        encoding="utf-8",
    )
    en = root / "portafolio" / "articulos" / "en"
    (en / "solo-ingles").mkdir(parents=True)
    (en / "solo-ingles" / "index.html").write_text("<p>Only EN</p>\n", encoding="utf-8")
    (en / "index.html").write_text('<a href="solo-ingles/">Only EN</a>\n', encoding="utf-8")
    (root / "en" / "index.html").write_text(
        '<a href="../portafolio/auditoria-001-sujeto/index.html">Audit 001</a>\n'
        '<a href="../portafolio/articulos/index.html">Articles</a>\n'
        '<a href="../portafolio/articulos/en/">Articles (EN)</a>\n',
        encoding="utf-8",
    )
    sitemap = root / "sitemap.xml"
    sitemap.write_text(
        sitemap.read_text(encoding="utf-8").replace(
            "</urlset>",
            "  <url><loc>%sportafolio/articulos/en/</loc></url>\n"
            "  <url><loc>%sportafolio/articulos/en/solo-ingles/</loc></url>\n</urlset>"
            % (BASE_LOC, BASE_LOC),
        ),
        encoding="utf-8",
    )
    sembrar_feed(root)



class FeedFalsable(unittest.TestCase):
    """El feed es lo que un publicador automatico consume: si envejece, la
    distribucion se apaga sin que nadie vea un error."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = construir(Path(self._tmp.name) / "sitio")
        cablear_articulo(self.root)
        self.feed = self.root / "portafolio" / "feed.xml"

    def correr(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(self.root / "tools" / "canario.py"), "--root", str(self.root)],
            capture_output=True,
            text=True,
        )

    def test_feed_sano_es_verde(self) -> None:
        proc = self.correr()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("feed", proc.stdout)

    def test_feed_ausente_enciende_feed(self) -> None:
        self.feed.unlink()
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("portafolio/feed.xml no existe", proc.stdout)

    def test_feed_ilegible_enciende_feed(self) -> None:
        self.feed.write_text("<feed><entry>", encoding="utf-8")
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("no es XML valido", proc.stdout)

    def test_feed_sin_el_articulo_enciende_feed(self) -> None:
        texto = self.feed.read_text(encoding="utf-8")
        self.feed.write_text(
            texto.replace("/portafolio/articulos/un-articulo/", "/portafolio/articulos/otro/"),
            encoding="utf-8",
        )
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("el feed no declara el articulo un-articulo", proc.stdout)

    def test_feed_con_pieza_no_publicada_enciende_feed(self) -> None:
        texto = self.feed.read_text(encoding="utf-8")
        entrada = (
            '  <entry><title>fantasma</title>'
            "<id>%sportafolio/articulos/fantasma/</id>"
            '<link href="%sportafolio/articulos/fantasma/"/>'
            "<updated>2026-11-09T00:00:00Z</updated></entry>\n"
            % (BASE_LOC, BASE_LOC)
        )
        self.feed.write_text(texto.replace("</feed>", entrada + "</feed>"), encoding="utf-8")
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("que el sitemap no publica", proc.stdout)
        self.assertIn("fantasma", proc.stdout)


class SoloEnIngles(unittest.TestCase):
    """El universo del grafo es `todo directorio con fuente`, no `con fuente ES`:
    un articulo solo en ingles tambien puede quedar huerfano."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = construir(Path(self._tmp.name) / "sitio")
        cablear_solo_en(self.root)

    def correr(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(self.root / "tools" / "canario.py"), "--root", str(self.root)],
            capture_output=True,
            text=True,
            timeout=120,
        )

    def test_un_articulo_solo_en_ingles_bien_cableado_no_enciende_nada(self) -> None:
        proc = self.correr()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("solo en ingles", proc.stdout)

    def test_un_articulo_solo_en_ingles_fuera_del_sitemap_enciende_grafo(self) -> None:
        sitemap = self.root / "sitemap.xml"
        sitemap.write_text(
            sitemap.read_text(encoding="utf-8").replace(
                "<url><loc>%sportafolio/articulos/en/solo-ingles/</loc></url>\n" % BASE_LOC, ""
            ),
            encoding="utf-8",
        )
        proc = self.correr()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("grafo", proc.stdout)
        self.assertIn("sitemap.xml no declara", proc.stdout)
        self.assertIn("solo-ingles", proc.stdout)
