#!/usr/bin/env python3
"""Proyeccion dev.to de un articulo en ingles.

dev.to lee Jekyll front matter con nombres propios (`description`, `published`,
`canonical_url`); el articulo de origen usa los del sitio (`lede`, `date`,
`fuente`). Este instrumento es la unica traduccion entre los dos idiomas de
encabezado, y **no toca el cuerpo**: lo copia byte a byte.

El archivo que emite no lleva ninguna valla alrededor. Envolver markdown en un
bloque ```text lo corrompe -- una valla que contiene vallas se cierra en la
primera interna, y todo lo que sigue se lee como codigo. Ese defecto costo una
publicacion entera: la pagina salio con 1 bloque de codigo en vez de 8, 0 tablas
en vez de 4 y 1 titular en vez de 11, porque los `##` no sobrevivieron al viaje.

Uso:
    python3 tools/devto.py --raiz .            # escribe los devto.md
    python3 tools/devto.py --raiz . --check    # RC 1 si el disco no coincide
    python3 tools/devto.py --raiz . --listar
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paginas_articulos import SITIO_EN, cosechar, leer_articulo  # noqa: E402

NOMBRE = "devto.md"
# Claves del encabezado del sitio que no significan nada para dev.to. Si alguna
# se filtra, el archivo publicado declara un vocabulario que su lector no lee.
CLAVES_AJENAS = ("lede", "fecha", "date", "fuente", "cola_slug", "lang")


def canonical(slug: str) -> str:
    return "%s%s/" % (SITIO_EN, slug)


def escalar(valor: str) -> str:
    """El valor entre comillas dobles.

    Un `: ` dentro de un escalar YAML sin comillas no es texto: es el inicio de
    otro mapeo, y el parser de dev.to no lee el nuestro. Lo mismo con ` #`, que
    abre un comentario. Titulos como `...SUCCESS: a reproducible audit...` no
    sobreviven sin comillas.
    """
    return '"%s"' % valor.replace("\\", "\\\\").replace('"', '\\"')


def proyectar(meta: dict) -> str:
    """El encabezado de dev.to mas el cuerpo intacto del articulo."""
    if meta["lang"] != "en":
        raise ValueError(
            "%s: dev.to publica en ingles; este articulo declara %s"
            % (meta["ruta"], meta["lang"])
        )
    encabezado = [
        "---",
        "title: %s" % escalar(meta["title"]),
        "published: false",
        "description: %s" % escalar(meta["lede"]),
        "tags: %s" % ", ".join(meta["tags"]),
        "canonical_url: %s" % escalar(canonical(meta["slug"])),
        "---",
    ]
    cuerpo = meta["cuerpo"].lstrip("\n").rstrip("\n")
    return "\n".join(encabezado) + "\n\n" + cuerpo + "\n"


def destino(meta: dict) -> Path:
    return meta["ruta"].parent / NOMBRE


def aplicar(raiz: Path, escribir: bool) -> int:
    todas, errores = cosechar(raiz)
    for e in errores:
        print("ENCABEZADO ILEGIBLE: %s" % e, file=sys.stderr)
    if errores:
        return 2
    metas = [m for m in todas if m["lang"] == "en"]
    if not metas:
        print("SIN ARTICULOS EN INGLES: no hay nada que proyectar", file=sys.stderr)
        return 2
    malos = []
    for meta in metas:
        ruta = destino(meta)
        esperado = proyectar(meta)
        actual = ruta.read_text(encoding="utf-8") if ruta.exists() else None
        if actual == esperado:
            estado = "sin cambio"
        elif actual is None:
            estado = "alta"
            malos.append(ruta)
        else:
            estado = "desfase"
            malos.append(ruta)
        if not escribir and actual != esperado:
            continue
        if actual != esperado:
            ruta.write_text(esperado, encoding="utf-8")
        print("%-11s %s" % (estado, ruta.relative_to(raiz)))
    if not escribir and malos:
        print(
            "\nDESFASE: %d proyeccion(es) no coinciden con su fuente. "
            "Corre sin --check para escribir." % len(malos),
            file=sys.stderr,
        )
        return 1
    print("\n%d articulo(s) en ingles, %d proyeccion(es)." % (len(metas), len(metas)))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raiz", default=".", help="raiz del repositorio")
    p.add_argument("--check", action="store_true", help="no escribe; RC 1 si hay desfase")
    p.add_argument("--listar", action="store_true", help="solo lista, sin escribir")
    args = p.parse_args(argv)
    raiz = Path(args.raiz).resolve()
    if args.listar:
        metas, errores = cosechar(raiz)
        for e in errores:
            print("ENCABEZADO ILEGIBLE: %s" % e, file=sys.stderr)
        for meta in metas:
            if meta["lang"] != "en":
                continue
            print("%-52s %s" % (meta["slug"], destino(meta).relative_to(raiz)))
        return 2 if errores else 0
    return aplicar(raiz, escribir=not args.check)


if __name__ == "__main__":
    raise SystemExit(main())
