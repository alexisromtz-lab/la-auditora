#!/usr/bin/env python3
# HUELLA-TEST-PORTAFOLIO-GEMELOS-20261112
"""Falsadores de los gemelos del portafolio: la mitad que el canario no lee.

`tools/canario.py` mide un informe contra `sitemap.xml` y contra las dos portadas
de la raiz (`LANDINGS`). No lee `portafolio/sitemap.xml` ni las dos portadas de
`portafolio/`. Un caso puede estar enlazado desde la raiz y faltar justo donde un
lector que navega informes aterriza, y el canario seguiria verde: ese es el hueco
que este lector nombra, y solo ese. Lo que el canario ya mide no se repite aqui.

Universo declarado: todo directorio `portafolio/auditoria-*`. Un universo vacio
aprueba cualquier cosa, asi que se cuenta y se compara contra su numero.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

RAIZ = Path(__file__).resolve().parent.parent

SITEMAP = "portafolio/sitemap.xml"
PORTADAS = ("portafolio/index.html", "portafolio/en/index.html")
SITE = "https://alexisromtz-lab.github.io/la-auditora/"
CASOS_ESPERADOS = 3


def casos(raiz: Path) -> list[str]:
    return sorted(p.name for p in (raiz / "portafolio").glob("auditoria-*") if p.is_dir())


def defectos(raiz: Path) -> list[str]:
    salida: list[str] = []
    ruta_sitemap = raiz / SITEMAP
    if not ruta_sitemap.is_file():
        return [f"falta {SITEMAP}"]
    locs = set(re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", ruta_sitemap.read_text(encoding="utf-8")))
    for portada in PORTADAS:
        if not (raiz / portada).is_file():
            salida.append(f"falta {portada}")
    for caso in casos(raiz):
        url = f"{SITE}portafolio/{caso}/"
        if url not in locs:
            salida.append(f"{SITEMAP} no declara {url}")
        for portada in PORTADAS:
            ruta = raiz / portada
            if ruta.is_file() and caso not in ruta.read_text(encoding="utf-8"):
                salida.append(f"{portada} no enlaza {caso}")
    return salida


class PortafolioGemelosTest(unittest.TestCase):
    def test_01_los_gemelos_del_portafolio_declaran_cada_caso(self) -> None:
        # El universo se cuenta: un universo vacio pasa este test sin medir nada.
        self.assertEqual(len(casos(RAIZ)), CASOS_ESPERADOS, casos(RAIZ))
        self.assertEqual(defectos(RAIZ), [])

    def test_02_un_caso_ausente_de_los_gemelos_se_nombra(self) -> None:
        with TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            (raiz / "portafolio" / "auditoria-999-huerfano").mkdir(parents=True)
            (raiz / SITEMAP).parent.mkdir(parents=True, exist_ok=True)
            (raiz / SITEMAP).write_text("<urlset></urlset>", encoding="utf-8")
            for portada in PORTADAS:
                (raiz / portada).parent.mkdir(parents=True, exist_ok=True)
                (raiz / portada).write_text("sin enlaces", encoding="utf-8")

            encontrados = defectos(raiz)

        self.assertEqual(
            encontrados,
            [
                f"{SITEMAP} no declara {SITE}portafolio/auditoria-999-huerfano/",
                "portafolio/index.html no enlaza auditoria-999-huerfano",
                "portafolio/en/index.html no enlaza auditoria-999-huerfano",
            ],
        )

    def test_03_una_portada_ausente_no_se_lee_como_verde(self) -> None:
        with TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            (raiz / SITEMAP).parent.mkdir(parents=True, exist_ok=True)
            (raiz / SITEMAP).write_text("<urlset></urlset>", encoding="utf-8")

            encontrados = defectos(raiz)

        self.assertIn("falta portafolio/index.html", encontrados)
        self.assertIn("falta portafolio/en/index.html", encontrados)


if __name__ == "__main__":
    unittest.main(verbosity=2)
