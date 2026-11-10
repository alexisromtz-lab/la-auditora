#!/usr/bin/env python3
"""feed.xml — el Atom de lo publicado, para que un lector automatico lo consuma.

Un publicador (Postiz u otro) solo puede reaccionar a lo que existe de forma
legible por maquina. Sin feed, cada difusion es manual o inventada: el tablero
apunta a una URL y nadie comprueba que la URL exista.

Una entrada por pieza, no una por idioma. La pieza que tiene gemelo enlaza la
pagina inglesa: el texto que se difunde es el publicado en ingles, y la version
espanola queda como alternate en su propia pagina.

El lector es `paginas_articulos.cosechar`: el mismo que escribe las paginas. Dos
lectores del mismo front matter serian dos universos, y dos universos divergen.

Uso:
    python3 tools/feed.py --raiz . --check      # RC 1 si feed.xml no coincide
    python3 tools/feed.py --raiz . --aplicar    # escribe portafolio/feed.xml
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paginas_articulos as articulos  # noqa: E402

BASE = "https://alexisromtz-lab.github.io/la-auditora"
FEED = BASE + "/portafolio/feed.xml"
TITULO = "La Auditora — reproducible audits and measurements"
AUTOR_DEFECTO = "Platino Labs"


def autor(raiz: Path) -> str:
    """El nombre sale de CITATION.cff: una sola fuente para la firma."""
    ruta = raiz / "CITATION.cff"
    if not ruta.is_file():
        return AUTOR_DEFECTO
    texto = ruta.read_text(encoding="utf-8")
    familia = re.search(r'family-names:\s*"([^"]+)"', texto)
    pila = re.search(r'given-names:\s*"([^"]+)"', texto)
    if familia and pila:
        return "%s %s" % (pila.group(1), familia.group(1))
    return AUTOR_DEFECTO


def escapar(texto: str) -> str:
    return (
        texto.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _lastmod(raiz: Path) -> dict:
    """Las fechas de los informes ya viven en el sitemap; no se inventan aqui."""
    ruta = raiz / "sitemap.xml"
    if not ruta.is_file():
        return {}
    pares = re.findall(r"<loc>([^<]+)</loc><lastmod>([^<]+)</lastmod>", ruta.read_text(encoding="utf-8"))
    return {loc: fecha for loc, fecha in pares}


def informes(raiz: Path, fechas: dict) -> list:
    salida = []
    for ficha in sorted((raiz / "portafolio").glob("auditoria-*/ficha.json")):
        datos = json.loads(ficha.read_text(encoding="utf-8"))
        url = "%s/portafolio/%s/" % (BASE, ficha.parent.name)
        salida.append(
            {
                "url": url,
                "titulo": datos.get("hallazgo", {}).get("titulo", ficha.parent.name),
                "resumen": datos.get("hallazgo", {}).get("impacto", ""),
                "fecha": fechas.get(url, "1970-01-01"),
                "lang": "es",
                "tags": [],
            }
        )
    return salida


def entradas(raiz: Path) -> tuple:
    metas, errores = articulos.cosechar(raiz)
    fechas = _lastmod(raiz)
    por_slug = {}
    for meta in metas:
        actual = por_slug.get(meta["slug"])
        # el ingles gana la entrada: es el texto que se difunde
        if actual is None or (actual["lang"] == "es" and meta["lang"] == "en"):
            por_slug[meta["slug"]] = meta
    salida = []
    for slug, meta in por_slug.items():
        url = "%s/portafolio/articulos/%s%s/" % (
            BASE,
            "" if meta["lang"] == "es" else "en/",
            slug,
        )
        salida.append(
            {
                "url": url,
                "titulo": meta["title"],
                "resumen": meta["lede"],
                "fecha": meta["date"],
                "lang": meta["lang"],
                "tags": meta["tags"],
            }
        )
    salida.extend(informes(raiz, fechas))
    salida.sort(key=lambda e: (e["fecha"], e["url"]), reverse=True)
    return salida, errores


def _iso(fecha: str) -> str:
    fecha = fecha.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", fecha):
        return fecha + "T00:00:00Z"
    return fecha


def construir(raiz: Path) -> tuple:
    piezas, errores = entradas(raiz)
    if errores:
        return "", errores
    firma = autor(raiz)
    lineas = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en">',
        "  <title>%s</title>" % escapar(TITULO),
        "  <id>%s/</id>" % BASE,
        "  <updated>%s</updated>" % (_iso(piezas[0]["fecha"]) if piezas else "1970-01-01T00:00:00Z"),
        '  <link rel="self" type="application/atom+xml" href="%s"/>' % FEED,
        '  <link rel="alternate" type="text/html" href="%s/portafolio/articulos/en/"/>' % BASE,
        "  <author><name>%s</name></author>" % escapar(firma),
        "  <rights>CC BY 4.0 sobre el texto; MIT sobre el codigo</rights>",
    ]
    for pieza in piezas:
        lineas.append('  <entry xml:lang="%s">' % pieza["lang"])
        lineas.append("    <id>%s</id>" % escapar(pieza["url"]))
        lineas.append("    <title>%s</title>" % escapar(pieza["titulo"]))
        lineas.append('    <link rel="alternate" type="text/html" href="%s"/>' % escapar(pieza["url"]))
        lineas.append("    <published>%s</published>" % _iso(pieza["fecha"]))
        lineas.append("    <updated>%s</updated>" % _iso(pieza["fecha"]))
        lineas.append("    <summary>%s</summary>" % escapar(pieza["resumen"]))
        for tag in pieza["tags"]:
            lineas.append('    <category term="%s"/>' % escapar(tag))
        lineas.append("    <author><name>%s</name></author>" % escapar(firma))
        lineas.append("  </entry>")
    lineas.append("</feed>")
    return "\n".join(lineas) + "\n", []


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--raiz", default=".", help="raiz del repositorio")
    p.add_argument("--aplicar", action="store_true", help="escribe portafolio/feed.xml")
    p.add_argument("--check", action="store_true", help="RC 1 si el feed no coincide")
    args = p.parse_args(argv)
    raiz = Path(args.raiz).resolve()
    texto, errores = construir(raiz)
    if errores:
        for e in errores:
            print(e, file=sys.stderr)
        print("FEED NO_MEDIDO: %d error(es) en el front matter" % len(errores), file=sys.stderr)
        return 2
    destino = raiz / "portafolio" / "feed.xml"
    actual = destino.read_text(encoding="utf-8") if destino.is_file() else ""
    entradas_n = texto.count("<entry ")
    if args.aplicar:
        if actual == texto:
            print("FEED AL DIA: %d entrada(s). Cero cambios." % entradas_n)
            return 0
        destino.write_text(texto, encoding="utf-8")
        print("escrito %s: %d entrada(s)" % (destino.relative_to(raiz), entradas_n))
        return 0
    if not destino.is_file():
        print("FALTA %s: %d entrada(s) sin publicar" % (destino.relative_to(raiz), entradas_n))
        return 1
    if actual != texto:
        print("FEED DESINCRONIZADO: %d entrada(s) esperadas" % entradas_n)
        return 1
    print("FEED AL DIA: %d entrada(s). Cero cambios." % entradas_n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
