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
    return destino


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
        self.assertIn("CANARIO OK - 5 de 5", proc.stdout)

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

    def test_sujeto_ausente_es_no_medido_y_no_rojo(self) -> None:
        ruta = self.root / INFORME / "ficha.json"
        ficha = json.loads(ruta.read_text(encoding="utf-8"))
        ficha["reproduccion"]["comando"] = "python3 reproduce.py objeto/workflow.yml"
        ruta.write_text(json.dumps(ficha), encoding="utf-8")
        proc = self.correr()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("NO_MEDIDO", proc.stdout)
        self.assertIn("CANARIO OK", proc.stdout)

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


    def test_raiz_sin_index_es_no_medido(self) -> None:
        ajeno = Path(self._tmp.name) / "ajeno"
        (ajeno / "tools").mkdir(parents=True)
        shutil.copy2(CANARIO, ajeno / "tools" / "canario.py")
        proc = self.correr(ajeno)
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertIn("NO_MEDIDO", proc.stdout)


if __name__ == "__main__":
    unittest.main()
