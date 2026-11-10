#!/usr/bin/env python3
"""Falsadores del generador de paginas: una proyeccion que nunca se desincroniza
no es una proyeccion, es una copia.

Cada prueba construye un sitio minimo, rompe una sola cosa y exige que el
generador la nombre. El fixture sano debe quedar verde para que un generador
atascado en rojo tambien se detecte.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
GENERADOR = RAIZ / "tools" / "paginas_articulos.py"

FUENTE = """---
title: Un articulo de fixture
lede: Sirve para falsar el generador, no para publicarse.
date: 2026-11-06
tags: fixture, markdown
---

# Un H1 que la pagina no debe repetir

Un parrafo con `codigo` y **negrita que rodea `codigo`** y un
**negrita que cruza
la linea**.

## Una seccion

| metrica | valor |
|---|---:|
| uno | 1 |

```bash
echo hola
```

> Una cita con una cifra.

- primer item
- segundo item que continua
en la linea siguiente

1. paso uno
2. paso dos

[externo](https://example.org/x) y [interno](ARTICULO_INTERNO.md)
"""


FUENTE_EN = """---
title: A fixture article
lede: It exists to falsify the generator, not to be published.
date: 2026-11-06
tags: fixture, markdown
lang: en
---

# An H1 the page must not repeat

Text that is already English.
"""


def construir(destino: Path, fuente: str = FUENTE) -> Path:
    carpeta = destino / "portafolio" / "articulos" / "un-articulo"
    carpeta.mkdir(parents=True)
    (destino / "tools").mkdir()
    (carpeta / "articulo.md").write_text(fuente, encoding="utf-8")
    shutil.copy2(GENERADOR, destino / "tools" / "paginas_articulos.py")
    return destino


class GeneradorFalsable(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = construir(Path(self._tmp.name) / "sitio")
        self.pagina = self.root / "portafolio" / "articulos" / "un-articulo" / "index.html"
        self.indice = self.root / "portafolio" / "articulos" / "index.html"

    def correr(self, *args: str, root: Path = None) -> subprocess.CompletedProcess:
        objetivo = self.root if root is None else root
        return subprocess.run(
            [sys.executable, str(objetivo / "tools" / "paginas_articulos.py"), "--raiz", str(objetivo)] + list(args),
            capture_output=True,
            text=True,
            timeout=120,
        )

    def html(self) -> str:
        return self.pagina.read_text(encoding="utf-8")

    def test_aplicar_genera_pagina_e_indice(self) -> None:
        proc = self.correr("--aplicar")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(self.pagina.is_file())
        self.assertTrue(self.indice.is_file())
        self.assertIn("un-articulo/", self.indice.read_text(encoding="utf-8"))

    def test_aplicar_es_idempotente_byte_a_byte(self) -> None:
        self.correr("--aplicar")
        antes = (self.html(), self.indice.read_text(encoding="utf-8"))
        proc = self.correr("--aplicar")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("Cero cambios", proc.stdout)
        self.assertEqual(antes, (self.html(), self.indice.read_text(encoding="utf-8")))

    def test_check_detecta_pagina_vieja(self) -> None:
        self.correr("--aplicar")
        self.pagina.write_text(self.html() + "<!-- deriva -->\n", encoding="utf-8")
        proc = self.correr("--check")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("desincronizada", proc.stdout)

    def test_check_no_escribe(self) -> None:
        proc = self.correr("--check")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertFalse(self.pagina.exists())

    def test_front_matter_incompleto_es_error_y_no_cero(self) -> None:
        ruta = self.root / "portafolio" / "articulos" / "un-articulo" / "articulo.md"
        ruta.write_text(FUENTE.replace("lede: Sirve para falsar el generador, no para publicarse.\n", ""), encoding="utf-8")
        proc = self.correr("--aplicar")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("lede", proc.stdout)

    def test_sin_articulos_es_no_medido(self) -> None:
        vacio = Path(self._tmp.name) / "vacio"
        (vacio / "portafolio" / "articulos").mkdir(parents=True)
        (vacio / "tools").mkdir()
        shutil.copy2(GENERADOR, vacio / "tools" / "paginas_articulos.py")
        proc = self.correr("--check", root=vacio)
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertIn("NO_MEDIDO", proc.stdout)

    def test_raiz_sin_directorio_es_no_medido(self) -> None:
        proc = self.correr("--check", root=Path(self._tmp.name))
        self.assertEqual(proc.returncode, 2, proc.stdout)

    def test_el_h1_del_cuerpo_no_se_repite(self) -> None:
        self.correr("--aplicar")
        self.assertEqual(self.html().count("<h1>"), 1, self.html())
        self.assertIn("Un articulo de fixture", self.html())

    def test_la_tabla_se_proyecta_con_cabecera_y_cuerpo(self) -> None:
        self.correr("--aplicar")
        html = self.html()
        self.assertIn("<th>metrica</th>", html)
        self.assertIn("<td>uno</td>", html)
        self.assertNotIn("|---", html)

    def test_la_valla_se_escapa_y_no_se_interpreta(self) -> None:
        self.correr("--aplicar")
        self.assertIn('<pre><code class="language-bash">echo hola</code></pre>', self.html())

    def test_la_cita_y_las_dos_listas(self) -> None:
        self.correr("--aplicar")
        html = self.html()
        self.assertIn("<blockquote>", html)
        self.assertEqual(html.count("<ul>"), 1)
        self.assertEqual(html.count("<ol>"), 1)
        self.assertEqual(html.count("<li>"), 4)

    def test_la_negrita_rodea_un_code_sin_romperse(self) -> None:
        self.correr("--aplicar")
        html = self.html()
        self.assertIn("<strong>negrita que rodea <code>codigo</code></strong>", html)
        self.assertIn("<strong>negrita que cruza la linea</strong>", html)

    def test_un_enlace_relativo_no_se_publica_como_enlace(self) -> None:
        self.correr("--aplicar")
        html = self.html()
        self.assertIn('<a href="https://example.org/x">externo</a>', html)
        self.assertNotIn("ARTICULO_INTERNO.md</a>", html)
        self.assertIn("<code>interno</code>", html)

    def test_el_cuerpo_se_escapa(self) -> None:
        ruta = self.root / "portafolio" / "articulos" / "un-articulo" / "articulo.md"
        ruta.write_text(FUENTE + "\nUn parrafo con <script>alert(1)</script> dentro.\n", encoding="utf-8")
        self.correr("--aplicar")
        self.assertNotIn("<script>", self.html())
        self.assertIn("&lt;script&gt;", self.html())

    # ── el gemelo ingles: opcional, pero consistente ──────────────────────

    def gemelo(self, fuente: str = FUENTE_EN) -> Path:
        return (self.root / "portafolio" / "articulos" / "un-articulo" / "articulo.en.md")

    def test_el_gemelo_genera_pagina_espejo_y_su_indice(self) -> None:
        self.gemelo().write_text(FUENTE_EN, encoding="utf-8")
        proc = self.correr("--aplicar")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        en = self.root / "portafolio" / "articulos" / "en"
        self.assertTrue((en / "un-articulo" / "index.html").is_file(), "falta la pagina EN")
        self.assertTrue((en / "index.html").is_file(), "falta el indice EN")
        self.assertIn('lang="en"', (en / "un-articulo" / "index.html").read_text(encoding="utf-8"))

    def test_el_hreflang_es_reciproco(self) -> None:
        self.gemelo().write_text(FUENTE_EN, encoding="utf-8")
        self.correr("--aplicar")
        en = self.root / "portafolio" / "articulos" / "en" / "un-articulo" / "index.html"
        html_en = en.read_text(encoding="utf-8")
        html_es = self.html()
        self.assertIn('hreflang="es"', html_en)
        self.assertIn('hreflang="en"', html_es)
        self.assertIn("articulos/en/un-articulo/", html_es)
        self.assertIn("articulos/un-articulo/", html_en)
        self.assertEqual(html_en.count('<link rel="alternate"'), 3, "faltan los tres alternates")

    def test_sin_gemelo_no_se_declara_hreflang(self) -> None:
        self.correr("--aplicar")
        self.assertNotIn("hreflang=", self.html())
        self.assertFalse((self.root / "portafolio" / "articulos" / "en").exists())

    def test_el_gemelo_sin_fuente_es_error(self) -> None:
        (self.root / "portafolio" / "articulos" / "un-articulo" / "articulo.md").unlink()
        self.gemelo().write_text(FUENTE_EN, encoding="utf-8")
        proc = self.correr("--aplicar")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("sin fuente ES", proc.stdout)

    def test_el_encabezado_que_contradice_al_nombre_es_error(self) -> None:
        self.gemelo().write_text(FUENTE_EN.replace("lang: en", "lang: es"), encoding="utf-8")
        proc = self.correr("--aplicar")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("el encabezado dice es", proc.stdout)

    def test_las_paginas_en_son_idempotentes(self) -> None:
        self.gemelo().write_text(FUENTE_EN, encoding="utf-8")
        self.correr("--aplicar")
        proc = self.correr("--aplicar")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("Cero cambios", proc.stdout)

    def test_un_articulo_solo_en_ingles_se_genera_si_lo_declara(self) -> None:
        """Un articulo que vive solo en ingles necesita pagina propia: su
        canonica no puede ser dev.to para siempre."""
        (self.root / "portafolio" / "articulos" / "un-articulo" / "articulo.md").unlink()
        self.gemelo().write_text(FUENTE_EN + "", encoding="utf-8")
        fuente = self.gemelo().read_text(encoding="utf-8").replace("lang: en", "lang: en\nsolo_en: si")
        self.gemelo().write_text(fuente, encoding="utf-8")
        proc = self.correr("--aplicar")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        pagina_en = self.root / "portafolio" / "articulos" / "en" / "un-articulo" / "index.html"
        self.assertTrue(pagina_en.is_file())
        self.assertFalse(self.pagina.exists(), "no hay fuente ES: no puede haber pagina ES")
        html_en = pagina_en.read_text(encoding="utf-8")
        self.assertIn('rel="canonical" href="https://alexisromtz-lab.github.io/la-auditora/portafolio/articulos/en/un-articulo/"', html_en)
        self.assertNotIn("hreflang=", html_en, "sin gemelo ES no se declara alternate")

    def test_solo_en_con_valor_que_no_es_si_sigue_siendo_error(self) -> None:
        (self.root / "portafolio" / "articulos" / "un-articulo" / "articulo.md").unlink()
        self.gemelo().write_text(FUENTE_EN.replace("lang: en", "lang: en\nsolo_en: no"), encoding="utf-8")
        proc = self.correr("--aplicar")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("solo_en: si", proc.stdout)


    def test_tags_degenerados_encienden_el_generador(self) -> None:
        origen = self.root / "portafolio" / "articulos" / "un-articulo" / "articulo.md"
        fuente = origen.read_text(encoding="utf-8")
        origen.write_text(
            fuente.replace("tags: fixture, markdown", "tags: f, i, x, ,, ,, m, a, r"),
            encoding="utf-8",
        )
        proc = self.correr("--check")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("degenerados", proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
