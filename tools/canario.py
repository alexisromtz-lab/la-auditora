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
    """Los articulos publicados: un directorio bajo `portafolio/articulos/` con su fuente."""
    base = root / "portafolio" / "articulos"
    if not base.is_dir():
        return []
    return sorted(d for d in base.iterdir() if d.is_dir() and (d / "articulo.md").is_file())


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
    piezas = articulos(root)
    gemelos = []
    if piezas:
        indice = root / "portafolio" / "articulos" / "index.html"
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
        # el gemelo ingles es opcional, pero si existe tiene que estar cableado
        # igual que su fuente: una version que nadie enlaza no se lee.
        gemelos = [(p, p / "articulo.en.md") for p in piezas if (p / "articulo.en.md").is_file()]
        if gemelos:
            indice_en = indice.parent / "en" / "index.html"
            url = SITE_BASE + indice_en.parent.relative_to(root).as_posix() + "/"
            if not indice_en.is_file():
                fallas.append("%s no existe y hay %d gemelo(s) EN" % (indice_en.relative_to(root), len(gemelos)))
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
            for pieza, _fuente in gemelos:
                en = indice.parent / "en" / pieza.name
                objetivo = en / "index.html"
                url = SITE_BASE + en.relative_to(root).as_posix() + "/"
                if not objetivo.is_file():
                    fallas.append("%s no existe (gemelo de %s)" % (objetivo.relative_to(root), pieza.relative_to(root)))
                    continue
                if url not in locs:
                    fallas.append("sitemap.xml no declara %s" % url)
                if indice_en.is_file() and not _links(indice_en, objetivo, root):
                    fallas.append(
                        "%s no enlaza %s"
                        % (indice_en.relative_to(root), objetivo.relative_to(root))
                    )
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
        "%d informes, %d articulos (%d con gemelo EN), %d URL en sitemap"
        % (len(informes), len(piezas), len(gemelos), len(locs)),
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


CHECKS = (
    ("enlaces", check_enlaces),
    ("grafo", check_grafo),
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
