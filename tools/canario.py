#!/usr/bin/env python3
"""One command says whether the public site of la-auditora is still whole.

Five checks, all offline and deterministic. Each one exists because a defect
was measured, not because a check looked reasonable:

    enlaces     a relative `href`/`src` whose file is not in the tree
    grafo       a published report that no landing page links and the sitemap
                ignores -- the orphan case that left a page unreachable
    triada      a report without `reproduce.py`, `ficha.json`, or without the
                `limite` that CONTRIBUTING requires to be declared
    citas       `CITATION.cff` or `.zenodo.json` unreadable, or a README with no
                DOI link: the citable edge existed with nothing measuring it
    reproduce   the `rc` that `ficha.json` declares is not the one the script
                returns -- "the name claims more than the code does"

Return-code contract:
    0  all five checks green
    1  at least one check red
    2  nothing measured (the root has no `index.html`: it is not the repository)

Usage:
    python3 tools/canario.py
    python3 tools/canario.py --root /path/to/la-auditora
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

SITE_BASE = "https://alexisromtz-lab.github.io/la-auditora/"
SITE_PREFIX = "/la-auditora"
REPORT_PREFIX = "auditoria-"
LANDINGS = ("index.html", "en/index.html")
TIMEOUT_S = 180

FICHA_REQUIRED = ("sujeto", "hallazgo", "limite", "estado", "locus", "reproduccion")
CITATION_REQUIRED = ("cff-version", "title", "authors", "license", "date-released")
ZENODO_REQUIRED = ("title", "description", "creators", "license", "upload_type")

EXTERNAL_SCHEMES = frozenset(
    {"http", "https", "mailto", "tel", "javascript", "data", "ftp", "news", "sms"}
)


class Refs(HTMLParser):
    """Collects every `href` and `src` with the line it was found on."""

    def __init__(self) -> None:
        super().__init__()
        self.refs: list[tuple[str, str, int]] = []

    def handle_starttag(self, tag, attrs):
        line = self.getpos()[0]
        for key, value in attrs:
            if key in ("href", "src") and value:
                self.refs.append((key, value, line))


def resolve(page: Path, ref: str, root: Path):
    """Return `(target, reason)`; `target` is None when the reference leaves the repository."""
    parts = urlsplit(ref)
    if ref.startswith("//") or parts.scheme.lower() in EXTERNAL_SCHEMES:
        return None, "externo"
    path = unquote(parts.path)
    if not path:
        return None, "ancla"
    if path.startswith("/"):
        if not (path == SITE_PREFIX or path.startswith(SITE_PREFIX + "/")):
            return None, "raiz del dominio"
        path = path[len(SITE_PREFIX):] or "/"
        target = root / path.lstrip("/")
    else:
        target = page.parent / path
    target = Path(os.path.normpath(str(target)))
    if target.is_dir():
        target = target / "index.html"
    return target, ""


def informs(root: Path):
    base = root / "portafolio"
    if not base.is_dir():
        return []
    return sorted(
        d for d in base.iterdir() if d.is_dir() and d.name.startswith(REPORT_PREFIX)
    )


def articulos(root: Path):
    """Los articulos publicados: un directorio bajo `portafolio/articulos/` con
    su fuente, en espanol o solo en ingles. Un directorio sin fuente no es un
    articulo: es un resto."""
    base = root / "portafolio" / "articulos"
    if not base.is_dir():
        return []
    nombres = ("articulo.md", "articulo.en.md")
    return sorted(
        d for d in base.iterdir() if d.is_dir() and any((d / n).is_file() for n in nombres)
    )


def _inside(target: Path, root: Path) -> bool:
    raiz = str(root)
    return str(target) == raiz or str(target).startswith(raiz + os.sep)


def _reads(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _links(portada: Path, objetivo: Path, root: Path) -> bool:
    parser = Refs()
    parser.feed(_reads(portada))
    for _attr, ref, _line in parser.refs:
        target, _reason = resolve(portada, ref, root)
        if target == objetivo:
            return True
    return False


def check_enlaces(root: Path):
    fallas = []
    paginas = sorted(p for p in root.rglob("*.html") if ".git" not in p.parts)
    medidos = 0
    for page in paginas:
        parser = Refs()
        parser.feed(_reads(page))
        for attr, ref, line in parser.refs:
            target, _reason = resolve(page, ref, root)
            if target is None:
                continue
            medidos += 1
            locus = "%s:%d" % (page.relative_to(root), line)
            if not _inside(target, root):
                fallas.append("%s  %s=%s escapa del repositorio" % (locus, attr, ref))
            elif not target.exists():
                fallas.append(
                    "%s  %s=%s -> %s no existe" % (locus, attr, ref, target.relative_to(root))
                )
    return "%d destinos locales en %d paginas" % (medidos, len(paginas)), fallas, []


def check_grafo(root: Path):
    fallas = []
    informes = informs(root)
    sitemap = root / "sitemap.xml"
    locs = set()
    if sitemap.is_file():
        locs = set(re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", _reads(sitemap)))
    else:
        fallas.append("sitemap.xml no existe")
    portadas = [root / rel for rel in LANDINGS if (root / rel).is_file()]
    if not portadas:
        fallas.append("ninguna portada existe (index.html / en/index.html)")
    for informe in informes:
        url = SITE_BASE + informe.relative_to(root).as_posix() + "/"
        if url not in locs:
            fallas.append("sitemap.xml no declara %s" % url)
        objetivo = informe / "index.html"
        for portada in portadas:
            if not _links(portada, objetivo, root):
                fallas.append(
                    "%s no enlaza %s"
                    % (portada.relative_to(root), objetivo.relative_to(root))
                )

    # la familia articulos: el indice es la portada de sus piezas, y el indice
    # se alcanza desde las portadas -- una pieza sin indice es un huerfano igual
    # El universo es "todo directorio con fuente", no "todo directorio con
    # fuente ES": un articulo que vive solo en ingles tambien puede quedar
    # huerfano, y con el universo anterior era invisible para este lector.
    todas = articulos(root)
    piezas = [p for p in todas if (p / "articulo.md").is_file()]
    indice = root / "portafolio" / "articulos" / "index.html"
    if piezas:
        if not indice.is_file():
            fallas.append("portafolio/articulos/index.html no existe y hay %d articulo(s)" % len(piezas))
        else:
            url = SITE_BASE + indice.parent.relative_to(root).as_posix() + "/"
            if url not in locs:
                fallas.append("sitemap.xml no declara %s" % url)
            for portada in portadas:
                if not _links(portada, indice, root):
                    fallas.append(
                        "%s no enlaza %s"
                        % (portada.relative_to(root), indice.relative_to(root))
                    )
            for pieza in piezas:
                url = SITE_BASE + pieza.relative_to(root).as_posix() + "/"
                if url not in locs:
                    fallas.append("sitemap.xml no declara %s" % url)
                objetivo = pieza / "index.html"
                if not _links(indice, objetivo, root):
                    fallas.append(
                        "%s no enlaza %s"
                        % (indice.relative_to(root), objetivo.relative_to(root))
                    )

    # la pagina inglesa, tenga o no fuente ES: una version que nadie enlaza no
    # se lee, y un articulo solo en ingles es una pagina mas que cablear.
    paginas_en = [(p, p / "articulo.en.md") for p in todas if (p / "articulo.en.md").is_file()]
    gemelos = [(p, f) for p, f in paginas_en if (p / "articulo.md").is_file()]
    if paginas_en:
        indice_en = indice.parent / "en" / "index.html"
        url = SITE_BASE + indice_en.parent.relative_to(root).as_posix() + "/"
        if not indice_en.is_file():
            fallas.append("%s no existe y hay %d pagina(s) EN" % (indice_en.relative_to(root), len(paginas_en)))
        elif url not in locs:
            fallas.append("sitemap.xml no declara %s" % url)
        for portada in portadas:
            if not portada.relative_to(root).as_posix().startswith("en/"):
                continue
            if indice_en.is_file() and not _links(portada, indice_en, root):
                fallas.append(
                    "%s no enlaza %s"
                    % (portada.relative_to(root), indice_en.relative_to(root))
                )
        for pieza, _fuente in paginas_en:
            objetivo = indice.parent / "en" / pieza.name / "index.html"
            url = SITE_BASE + objetivo.parent.relative_to(root).as_posix() + "/"
            if not objetivo.is_file():
                parentesco = "gemelo de" if (pieza / "articulo.md").is_file() else "pagina EN de"
                fallas.append(
                    "%s no existe (%s %s)"
                    % (objetivo.relative_to(root), parentesco, pieza.relative_to(root))
                )
                continue
            if url not in locs:
                fallas.append("sitemap.xml no declara %s" % url)
            if indice_en.is_file() and not _links(indice_en, objetivo, root):
                fallas.append(
                    "%s no enlaza %s"
                    % (indice_en.relative_to(root), objetivo.relative_to(root))
                )
            if not (pieza / "articulo.md").is_file():
                continue
            if not _links(pieza / "index.html", objetivo, root):
                fallas.append(
                    "%s no enlaza su gemelo %s"
                    % ((pieza / "index.html").relative_to(root), objetivo.relative_to(root))
                )
            if not _links(objetivo, pieza / "index.html", root):
                fallas.append(
                    "%s no enlaza su fuente %s"
                    % (objetivo.relative_to(root), (pieza / "index.html").relative_to(root))
                )
    return (
        "%d informes, %d articulos (%d con gemelo EN, %d solo en ingles), %d URL en sitemap"
        % (len(informes), len(todas), len(gemelos), len(todas) - len(piezas), len(locs)),
        fallas,
        [],
    )


def check_triada(root: Path):
    fallas = []
    informes = informs(root)
    for informe in informes:
        for nombre in ("index.html", "ficha.json", "reproduce.py"):
            if not (informe / nombre).is_file():
                fallas.append("%s/%s falta" % (informe.relative_to(root), nombre))
        ruta = informe / "ficha.json"
        if not ruta.is_file():
            continue
        try:
            ficha = json.loads(_reads(ruta))
        except (OSError, ValueError) as exc:
            fallas.append("%s no parsea: %s" % (ruta.relative_to(root), exc))
            continue
        if not isinstance(ficha, dict):
            fallas.append("%s no es un objeto JSON" % ruta.relative_to(root))
            continue
        for clave in FICHA_REQUIRED:
            if not ficha.get(clave):
                fallas.append("%s no declara `%s`" % (ruta.relative_to(root), clave))
    return "%d informes con triada y ficha completa" % len(informes), fallas, []


def check_citas(root: Path):
    fallas = []
    cff = root / "CITATION.cff"
    if not cff.is_file():
        fallas.append("CITATION.cff no existe")
    else:
        claves = set(
            re.findall(r"^([A-Za-z][A-Za-z0-9-]*):", _reads(cff), re.MULTILINE)
        )
        for clave in CITATION_REQUIRED:
            if clave not in claves:
                fallas.append("CITATION.cff no declara `%s`" % clave)
    zenodo = root / ".zenodo.json"
    if not zenodo.is_file():
        fallas.append(".zenodo.json no existe")
    else:
        try:
            meta = json.loads(_reads(zenodo))
        except (OSError, ValueError) as exc:
            fallas.append(".zenodo.json no parsea: %s" % exc)
            meta = {}
        if not isinstance(meta, dict):
            fallas.append(".zenodo.json no es un objeto JSON")
            meta = {}
        for clave in ZENODO_REQUIRED:
            if not meta.get(clave):
                fallas.append(".zenodo.json no declara `%s`" % clave)
    readme = root / "README.md"
    if not readme.is_file():
        fallas.append("README.md no existe")
    elif "doi.org/10.5281" not in _reads(readme):
        fallas.append("README.md no enlaza ningun doi.org/10.5281")
    return "CITATION.cff, .zenodo.json y DOI en el README", fallas, []


def check_reproduce(root: Path):
    fallas = []
    notas = []
    ejecutados = 0
    for informe in informs(root):
        rel = informe.relative_to(root)
        ruta = informe / "ficha.json"
        try:
            ficha = json.loads(_reads(ruta))
        except (OSError, ValueError):
            continue
        if not isinstance(ficha, dict):
            continue
        bloque = ficha.get("reproduccion") or {}
        comando = str(bloque.get("comando") or "").strip()
        declarado = bloque.get("rc")
        if not comando or declarado is None:
            fallas.append("%s/ficha.json no declara `reproduccion.comando` y `reproduccion.rc`" % rel)
            continue
        try:
            argv = shlex.split(comando)
        except ValueError as exc:
            fallas.append("%s/ficha.json: comando ilegible (%s)" % (rel, exc))
            continue
        if not argv:
            fallas.append("%s/ficha.json: `reproduccion.comando` vacio" % rel)
            continue
        if argv[0] in ("python", "python3"):
            argv[0] = sys.executable
        ausentes = [
            arg
            for arg in argv[1:]
            if not arg.startswith("-") and not (informe / arg).exists()
        ]
        if ausentes:
            notas.append(
                "%s: el comando exige %s, que no vive en el repositorio -> NO_MEDIDO"
                % (rel, ", ".join(ausentes))
            )
            continue
        try:
            proc = subprocess.run(
                argv,
                cwd=str(informe),
                capture_output=True,
                text=True,
                timeout=TIMEOUT_S,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            fallas.append("%s: no se pudo ejecutar `%s`: %s" % (rel, comando, exc))
            continue
        ejecutados += 1
        if proc.returncode != declarado:
            salida = (proc.stdout or proc.stderr).strip().splitlines()
            cola = salida[-1][:120] if salida else "sin salida"
            fallas.append(
                "%s: la ficha declara rc=%s y el script devolvio rc=%s · %s"
                % (rel, declarado, proc.returncode, cola)
            )
    return "%d informe(s) ejecutado(s) contra su rc declarado" % ejecutados, fallas, notas


def check_feed(root: Path):
    """Seis: el feed declara lo mismo que el sitemap, en las dos direcciones.

    Un feed que solo se regenera a mano envejece en silencio: el publicador
    automatico no ve el articulo nuevo y nadie se entera. La comparacion es
    contra el sitemap, que ya es el universo publico del sitio.
    """
    import xml.etree.ElementTree as ET

    problemas = []
    ruta = root / "portafolio" / "feed.xml"
    if not ruta.is_file():
        return "Atom con lo publicado", ["portafolio/feed.xml no existe"], []
    try:
        raiz_xml = ET.parse(ruta).getroot()
    except ET.ParseError as e:
        return "Atom con lo publicado", ["portafolio/feed.xml no es XML valido: %s" % e], []
    ns = {"a": "http://www.w3.org/2005/Atom"}
    del_feed = set()
    for entrada in raiz_xml.findall("a:entry", ns):
        nodo = entrada.find("a:id", ns)
        texto = (nodo.text or "").strip() if nodo is not None else ""
        if not texto:
            problemas.append("una entrada del feed no declara a:id")
            continue
        del_feed.add(texto.rstrip("/"))

    sitemap = root / "sitemap.xml"
    if not sitemap.is_file():
        return "Atom con lo publicado", ["sitemap.xml no existe: no hay contra que comparar el feed"], []
    publicadas = set(re.findall(r"<loc>([^<]+)</loc>", sitemap.read_text(encoding="utf-8")))
    # el loc del sitemap lleva barra final: sin quitarla, ningun patron con $ casa
    # y el conjunto sale vacio (comparar contra el vacio siempre aprueba)
    secas = {u.rstrip("/") for u in publicadas}
    base = SITE_BASE.rstrip("/")
    indices = {base + "/portafolio/articulos", base + "/portafolio/articulos/en"}

    def slug(u):
        if u in indices:
            return None
        m = re.search(r"/portafolio/articulos/(?:en/)?([^/]+)$", u)
        return m.group(1) if m else None

    articulos_sitemap = {slug(u) for u in secas if slug(u)}
    articulos_feed = {slug(u) for u in del_feed if slug(u)}
    informes_sitemap = {u for u in secas if re.search(r"/portafolio/auditoria-[^/]+$", u)}
    informes_feed = {u for u in del_feed if re.search(r"/portafolio/auditoria-[^/]+$", u)}

    if not articulos_sitemap and not informes_sitemap:
        problemas.append(
            "el sitemap no expone piezas reconocibles: el regex y el sitemap no hablan del mismo universo"
        )
    # articulos_feed son slugs y del_feed son URLs: restarlos mezcla tipos y
    # marca en rojo toda entrada legitima (URL != slug)
    clasificadas = {u for u in del_feed if slug(u)} | informes_feed
    for url in sorted(del_feed - clasificadas):
        problemas.append("el feed declara una entrada que no es articulo ni informe: %s/" % url)
    for titulo in sorted(articulos_sitemap - articulos_feed):
        problemas.append("el feed no declara el articulo %s" % titulo)
    for titulo in sorted(articulos_feed - articulos_sitemap):
        problemas.append("el feed declara el articulo %s, que el sitemap no publica" % titulo)
    for url in sorted(informes_sitemap - informes_feed):
        problemas.append("el feed no declara el informe %s/" % url)
    for url in sorted(informes_feed - informes_sitemap):
        problemas.append("el feed declara el informe %s, que el sitemap no publica" % url)
    detalle = "%d entrada(s): %d articulo(s) + %d informe(s)" % (
        len(del_feed),
        len(articulos_feed),
        len(informes_feed),
    )
    return detalle, problemas, []


CHECKS = (
    ("enlaces", check_enlaces),
    ("grafo", check_grafo),
    ("feed", check_feed),
    ("triada", check_triada),
    ("citas", check_citas),
    ("reproduce", check_reproduce),
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Canario de invariantes de la-auditora.")
    parser.add_argument("--root", default=None, help="raiz del repositorio")
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent
    if not (root / "index.html").is_file():
        print("NO_MEDIDO  %s no tiene index.html: no es la raiz de la-auditora" % root)
        return 2

    rojos = 0
    for nombre, funcion in CHECKS:
        detalle, fallas, notas = funcion(root)
        if fallas:
            rojos += 1
            print("FALLA  %-10s %d problema(s)" % (nombre, len(fallas)))
            for falla in fallas:
                print("       · %s" % falla)
        else:
            print("ok     %-10s %s" % (nombre, detalle))
        for nota in notas:
            print("       · nota: %s" % nota)

    total = len(CHECKS)
    if rojos:
        print("CANARIO FALLA - %d de %d comprobaciones en rojo" % (rojos, total))
        return 1
    print("CANARIO OK - %d de %d comprobaciones en verde" % (total, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
