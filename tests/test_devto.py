#!/usr/bin/env python3
"""Falsadores de la proyeccion dev.to.

El defecto que estos falsadores existen para negar ya ocurrio una vez y costo
una publicacion entera: el cuerpo se envolvio en una valla ```text para "que se
pudiera copiar", la valla se cerro en la primera valla interna, y la pagina
publicada salio con 1 bloque de codigo en vez de 8, 0 tablas en vez de 4 y 1
titular en vez de 11. El markdown no se habia perdido al escribirlo: se habia
perdido al envolverlo.

Cada prueba construye un sitio minimo, rompe una sola cosa y exige que el
instrumento la nombre.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
INSTRUMENTO = RAIZ / "tools" / "devto.py"

FUENTE_EN = """---
title: A fixture article
lede: It exists to falsify the projection, not to be published.
date: 2026-11-06
tags: fixture, markdown
fuente: DEPARTAMENTOS/comercial/NO_EXISTE.md
lang: en
---

## 1. A numbered heading that becomes a list if the hashes are lost

Text with `inline code` and __dunder__ that a fence must protect.

| arm | result |
|---|---|
| A | RAISED |
| B | SUCCESS |

```bash
echo hola
```
"""

FUENTE_ES = """---
title: Un articulo de fixture
lede: Sirve para falsar la proyeccion.
date: 2026-11-06
tags: fixture
---

## Una seccion
"""


def construir(destino: Path, fuente: str = FUENTE_EN, nombre: str = "articulo.en.md") -> Path:
    carpeta = destino / "portafolio" / "articulos" / "un-articulo"
    carpeta.mkdir(parents=True)
    (destino / "tools").mkdir()
    (carpeta / nombre).write_text(fuente, encoding="utf-8")
    shutil.copy2(INSTRUMENTO, destino / "tools" / "devto.py")
    shutil.copy2(RAIZ / "tools" / "paginas_articulos.py", destino / "tools" / "paginas_articulos.py")
    return destino


def estructura(texto: str) -> dict:
    return {
        "h2": len(re.findall(r"^## ", texto, re.M)),
        "h3": len(re.findall(r"^### ", texto, re.M)),
        "vallas": texto.count("```") // 2,
        "filas_de_tabla": len(re.findall(r"^\|", texto, re.M)),
    }


class ProyeccionFalsable(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = construir(Path(self._tmp.name) / "sitio")
        self.origen = self.root / "portafolio" / "articulos" / "un-articulo" / "articulo.en.md"
        self.destino = self.root / "portafolio" / "articulos" / "un-articulo" / "devto.md"

    def correr(self, *args: str, root: Path = None) -> subprocess.CompletedProcess:
        objetivo = self.root if root is None else root
        return subprocess.run(
            [sys.executable, str(objetivo / "tools" / "devto.py"), "--raiz", str(objetivo)] + list(args),
            capture_output=True,
            text=True,
            timeout=120,
        )

    def texto(self) -> str:
        return self.destino.read_text(encoding="utf-8")

    def cuerpo(self) -> str:
        return self.texto().split("---", 2)[2]

    # ── el camino sano ────────────────────────────────────────────────────

    def test_la_proyeccion_se_escribe_y_pasa_check(self) -> None:
        proc = self.correr()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(self.destino.exists())
        proc = self.correr("--check")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_check_es_idempotente_byte_a_byte(self) -> None:
        self.correr()
        primero = self.destino.read_bytes()
        self.correr()
        self.assertEqual(primero, self.destino.read_bytes())

    def test_el_cuerpo_es_byte_a_byte_el_del_origen(self) -> None:
        self.correr()
        origen = self.origen.read_text(encoding="utf-8").split("---", 2)[2]
        self.assertEqual(origen.strip("\n"), self.cuerpo().strip("\n"))
        self.assertIn("__dunder__", self.cuerpo())

    def test_description_es_el_lede_y_canonical_es_la_url_publica(self) -> None:
        self.correr()
        self.assertIn(
            'description: "It exists to falsify the projection, not to be published."',
            self.texto(),
        )
        self.assertIn(
            'canonical_url: "https://alexisromtz-lab.github.io/la-auditora/portafolio/articulos/en/un-articulo/"',
            self.texto(),
        )

    def test_published_es_false(self) -> None:
        """Una proyeccion no publica sola: publicar es un acto del dueno."""
        self.correr()
        self.assertIn("published: false", self.texto())
        self.assertNotIn("published: true", self.texto())

    def test_la_estructura_sobrevive_al_viaje(self) -> None:
        self.correr()
        origen = estructura(self.origen.read_text(encoding="utf-8").split("---", 2)[2])
        self.assertEqual(origen, estructura(self.cuerpo()))
        self.assertEqual(origen["vallas"], 1)
        self.assertEqual(origen["filas_de_tabla"], 4)
        self.assertEqual(origen["h2"], 1)

    # ── lo que tiene que morder ───────────────────────────────────────────

    def test_la_proyeccion_no_lleva_valla_alrededor(self) -> None:
        """El defecto real: envolver el markdown en ```text lo corrompe, porque
        la valla externa se cierra en la primera interna y todo lo que sigue se
        lee como codigo. La proyeccion no agrega ni una valla a las del cuerpo."""
        self.correr()
        origen = self.origen.read_text(encoding="utf-8")
        self.assertEqual(
            self.texto().count("```"),
            origen.count("```"),
            "la proyeccion agrega vallas: el markdown quedo envuelto",
        )

    def test_una_valla_alrededor_parte_el_cuerpo_en_dos(self) -> None:
        """El mecanismo, medido: con una valla externa, la primera valla interna
        la cierra a ella. Las regiones cercadas pasan de una (el bloque de
        codigo) a dos, y la segunda queda vacia porque el cierre del envoltorio
        se leyo como apertura."""
        self.correr()
        envuelto = "```text\n" + self.texto() + "\n```\n"
        regiones = re.findall(r"```[^\n]*\n(.*?)```", envuelto, re.S)
        self.assertEqual(len(regiones), 2, "la valla externa no se cerro en la primera interna")
        self.assertEqual(regiones[1].strip(), "", "el cuerpo no quedo partido en dos regiones")
        self.assertNotIn("echo hola", regiones[0])

    def test_el_encabezado_no_lleva_claves_del_sitio(self) -> None:
        self.correr()
        encabezado = self.texto().split("---")[1]
        for ajena in ("lede:", "fecha:", "date:", "fuente:", "cola_slug:", "lang:"):
            self.assertNotIn(ajena, encabezado, "se filtro %s al encabezado de dev.to" % ajena)

    def test_un_dos_puntos_dentro_del_valor_va_entre_comillas(self) -> None:
        """`title: algo: otra cosa` no es un titulo: es un mapeo anidado, y el
        parser de dev.to no lee el nuestro. El fixture ya trae ese caso."""
        self.origen.write_text(
            self.origen.read_text(encoding="utf-8").replace(
                "title: A fixture article", "title: Success: a fixture article"
            ),
            encoding="utf-8",
        )
        self.correr()
        encabezado = self.texto().split("---")[1]
        for linea in encabezado.strip().split("\n"):
            clave, valor = linea.split(": ", 1)
            if ": " in valor or " #" in valor:
                self.assertTrue(
                    valor.startswith('"') and valor.endswith('"'),
                    "%s: valor sin comillas que un parser YAML corta: %s" % (clave, valor),
                )

    def test_check_detecta_proyeccion_vieja(self) -> None:
        self.correr()
        self.destino.write_text(self.texto().replace("A fixture article", "Otro titulo"), encoding="utf-8")
        proc = self.correr("--check")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("DESFASE", proc.stderr)

    def test_check_no_escribe(self) -> None:
        proc = self.correr("--check")
        self.assertEqual(proc.returncode, 1)
        self.assertFalse(self.destino.exists())

    def test_check_detecta_fuente_editada_y_proyeccion_no(self) -> None:
        self.correr()
        self.origen.write_text(
            self.origen.read_text(encoding="utf-8").replace("echo hola", "echo adios"),
            encoding="utf-8",
        )
        proc = self.correr("--check")
        self.assertEqual(proc.returncode, 1, proc.stdout)

    # ── no medido ─────────────────────────────────────────────────────────

    def test_un_articulo_en_espanol_no_se_proyecta(self) -> None:
        """dev.to recibe ingles; un ES proyectado seria un articulo sin lector."""
        solo_es = construir(Path(self._tmp.name) / "solo-es", FUENTE_ES, nombre="articulo.md")
        proc = self.correr("--check", root=solo_es)
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertIn("SIN ARTICULOS EN INGLES", proc.stderr)

    def test_un_encabezado_ilegible_es_error(self) -> None:
        self.origen.write_text("titulo sin reglas\n", encoding="utf-8")
        proc = self.correr("--check")
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertIn("ENCABEZADO ILEGIBLE", proc.stderr)


if __name__ == "__main__":
    unittest.main()
