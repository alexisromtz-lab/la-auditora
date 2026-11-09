#!/usr/bin/env python3
"""paginas_articulos.py — el articulo es la fuente, la pagina es su proyeccion.
<!-- HUELLA-PAGINAS-ARTICULOS-PY-20261108 -->

Problema que resuelve: cuatro articulos tecnicos existian en la cola de
publicacion con `link: ""`. Un articulo sin URL no se puede citar, no se puede
enviar a una red y no se puede indexar: es un archivo, no una publicacion.

Aqui el `.md` es la fuente y el `index.html` es lo que se genera de el. La
misma entrada produce la misma salida byte a byte (idempotente), y `--check`
falla cerrado si una pagina quedo vieja respecto de su fuente.

  portafolio/articulos/<slug>/articulo.md    la fuente, y la version copiable
  portafolio/articulos/<slug>/index.html     la proyeccion (generada)
  portafolio/articulos/index.html            el indice (generado)
  portafolio/articulos/articulo.css          la hoja compartida (a mano)

El encabezado del `.md` declara lo que un `<head>` necesita y el cuerpo no
puede dar: titulo, entradilla, fecha y etiquetas. Ningun campo se inventa: el
que falta se publica NO_MEDIDO.

Subconjunto de markdown soportado, medido sobre los cuatro articulos reales:
encabezados 1-4, parrafos, listas ordenadas y no ordenadas, citas, tablas,
vallas de codigo, reglas horizontales, y en linea: code, negrita, italica y
enlaces. Nada mas. Lo que no este aqui no se renderiza: se emite literal, que
es la forma barata de no mentir sobre lo que se soporta.

Uso:
  python3 tools/paginas_articulos.py --raiz . --aplicar
  python3 tools/paginas_articulos.py --raiz . --check      # RC 1 si hay pagina vieja
  python3 tools/paginas_articulos.py --raiz . --listar

Codigos:
  0  paginas al dia / escritas
  1  hay al menos una pagina desincronizada (--check) o un articulo ilegible
  2  NO_MEDIDO: la raiz no existe o no hay ningun articulo
  3  argumentos invalidos
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

DIR_ARTICULOS = Path("portafolio/articulos")
SITIO = "https://alexisromtz-lab.github.io/la-auditora/portafolio/articulos/"
REQUERIDOS = ("title", "lede", "date")
NO_MEDIDO = "NO_MEDIDO"

# ── el subconjunto de markdown ───────────────────────────────────────────────

RE_VALLA = re.compile(r"^```(\w*)\s*$")
RE_ENCABEZADO = re.compile(r"^(#{1,4})\s+(.*)$")
RE_SEPARADOR_TABLA = re.compile(r"^\|[-: |]+\|$")
RE_REGLA = re.compile(r"^(?:---+|\*\*\*+)$")
RE_CITA = re.compile(r"^>\s?(.*)$")
RE_UL = re.compile(r"^[-*]\s+(.*)$")
RE_OL = re.compile(r"^\d+\.\s+(.*)$")
RE_NEGRITA = re.compile(r"\*\*([^*\n]+)\*\*")
RE_ITALICA = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
RE_ENLACE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
RE_CODE = re.compile(r"`([^`\n]+)`")
RE_ESQUEMA = re.compile(r"^(?:https?|mailto|tel):", re.I)
RE_PLACEHOLDER = re.compile(r"^\x00\d+\x00$")


def _inicia_bloque(linea: str) -> bool:
    return bool(
        RE_VALLA.match(linea)
        or RE_ENCABEZADO.match(linea)
        or RE_REGLA.match(linea)
        or RE_CITA.match(linea)
        or RE_UL.match(linea)
        or RE_OL.match(linea)
        or linea.lstrip().startswith("|")
    )


def _enlace(m) -> str:
    """Un articulo publico no enlaza al corpus privado: un destino relativo se
    publica como nombre, nunca como enlace muerto. El canario (`enlaces`) es el
    control negativo de esta regla."""
    etiqueta, destino = m.group(1), m.group(2)
    if RE_ESQUEMA.match(destino) or destino.startswith(("#", "//")):
        return '<a href="%s">%s</a>' % (destino, etiqueta)
    if RE_PLACEHOLDER.match(etiqueta):
        return etiqueta
    return "<code>%s</code>" % etiqueta


def _enlinea(texto: str) -> str:
    """Escapa y aplica el marcado en linea. El code se enmascara primero para que
    ningun asterisco de dentro se convierta en enfasis y para que una negrita
    pueda rodear un `code` sin romperse."""
    texto = html.escape(texto, quote=False)
    guardados = []

    def _guardar(m):
        guardados.append(m.group(1))
        return "\x00%d\x00" % (len(guardados) - 1)

    texto = RE_CODE.sub(_guardar, texto)
    texto = RE_NEGRITA.sub(r"<strong>\1</strong>", texto)
    texto = RE_ITALICA.sub(r"<em>\1</em>", texto)
    texto = RE_ENLACE.sub(_enlace, texto)
    return re.sub("\x00(\\d+)\x00", lambda m: "<code>%s</code>" % guardados[int(m.group(1))], texto)


def _tabla(filas: list) -> str:
    celdas = lambda linea: [c.strip() for c in linea.strip().strip("|").split("|")]
    cabecera = celdas(filas[0])
    cuerpo = [celdas(f) for f in filas[2:]]
    out = ["<table>", "<thead>", "<tr>"]
    out += ["<th>%s</th>" % _enlinea(c) for c in cabecera]
    out += ["</tr>", "</thead>", "<tbody>"]
    for fila in cuerpo:
        out.append("<tr>" + "".join("<td>%s</td>" % _enlinea(c) for c in fila) + "</tr>")
    out += ["</tbody>", "</table>"]
    return "\n".join(out)


def renderizar(cuerpo: str) -> str:
    """Markdown del subconjunto -> HTML. Determinista: sin estado global."""
    lineas = cuerpo.replace("\r\n", "\n").split("\n")
    salida: list = []
    i = 0
    while i < len(lineas):
        linea = lineas[i]

        if not linea.strip():
            i += 1
            continue

        m = RE_VALLA.match(linea)
        if m:
            lenguaje = m.group(1)
            bloque = []
            i += 1
            while i < len(lineas) and not RE_VALLA.match(lineas[i]):
                bloque.append(lineas[i])
                i += 1
            i += 1
            clase = ' class="language-%s"' % lenguaje if lenguaje else ""
            salida.append(
                "<pre><code%s>%s</code></pre>"
                % (clase, html.escape("\n".join(bloque), quote=False))
            )
            continue

        m = RE_ENCABEZADO.match(linea)
        if m:
            nivel = len(m.group(1))
            salida.append("<h%d>%s</h%d>" % (nivel, _enlinea(m.group(2)), nivel))
            i += 1
            continue

        if RE_REGLA.match(linea):
            salida.append("<hr>")
            i += 1
            continue

        if linea.lstrip().startswith("|") and i + 1 < len(lineas) and RE_SEPARADOR_TABLA.match(lineas[i + 1].strip()):
            filas = []
            while i < len(lineas) and lineas[i].lstrip().startswith("|"):
                filas.append(lineas[i])
                i += 1
            salida.append(_tabla(filas))
            continue

        m = RE_CITA.match(linea)
        if m:
            bloque = []
            while i < len(lineas):
                mq = RE_CITA.match(lineas[i])
                if not mq:
                    break
                bloque.append(mq.group(1))
                i += 1
            salida.append("<blockquote><p>%s</p></blockquote>" % _enlinea(" ".join(bloque)))
            continue

        if RE_UL.match(linea) or RE_OL.match(linea):
            ordenada = bool(RE_OL.match(linea))
            patron = RE_OL if ordenada else RE_UL
            etiqueta = "ol" if ordenada else "ul"
            items = []
            while i < len(lineas):
                mm = patron.match(lineas[i])
                if not mm:
                    break
                texto = mm.group(1)
                i += 1
                # continuacion perezosa: la linea siguiente pertenece al item
                while i < len(lineas) and lineas[i].strip() and not _inicia_bloque(lineas[i]):
                    texto += " " + lineas[i].strip()
                    i += 1
                items.append("<li>%s</li>" % _enlinea(texto))
                j = i
                while j < len(lineas) and not lineas[j].strip():
                    j += 1
                if j < len(lineas) and patron.match(lineas[j]):
                    i = j
                    continue
                break
            salida.append("<%s>\n%s\n</%s>" % (etiqueta, "\n".join(items), etiqueta))
            continue

        parrafo = []
        while i < len(lineas) and lineas[i].strip() and not _inicia_bloque(lineas[i]):
            parrafo.append(lineas[i].strip())
            i += 1
        if parrafo:
            salida.append("<p>%s</p>" % _enlinea(" ".join(parrafo)))
    return "\n\n".join(salida)


# ── encabezado del articulo ─────────────────────────────────────────────────

def leer_articulo(ruta: Path) -> dict:
    """Encabezado `clave: valor` entre reglas `---`, y cuerpo. Sin YAML."""
    texto = ruta.read_text(encoding="utf-8")
    lineas = texto.replace("\r\n", "\n").split("\n")
    if not lineas or lineas[0].strip() != "---":
        raise ValueError("%s: falta el encabezado (primera linea tiene que ser ---)" % ruta)
    meta: dict = {}
    fin = None
    for n, linea in enumerate(lineas[1:], start=1):
        if linea.strip() == "---":
            fin = n
            break
        if ":" not in linea:
            raise ValueError("%s:%d: el encabezado no es `clave: valor`" % (ruta, n + 1))
        clave, valor = linea.split(":", 1)
        meta[clave.strip()] = valor.strip()
    if fin is None:
        raise ValueError("%s: el encabezado no cierra con ---" % ruta)
    meta["cuerpo"] = "\n".join(lineas[fin + 1:])
    meta["ruta"] = ruta
    faltan = [c for c in REQUERIDOS if not meta.get(c)]
    if faltan:
        raise ValueError("%s: el encabezado no declara %s" % (ruta, ", ".join(faltan)))
    meta["tags"] = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
    return meta


# ── la plantilla ────────────────────────────────────────────────────────────

CSS = """<link rel="stylesheet" href="%sarticulo.css">"""

PLANTILLA = """<!doctype html>
<!-- HUELLA-PAGINA-ARTICULO-{slug}-20261108 -->
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} | La Auditora</title>
  <meta name="description" content="{lede}">
  <meta name="robots" content="index,follow">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{lede}">
  <meta property="og:url" content="{canonical}">
  <meta property="article:published_time" content="{date}">
  <meta name="twitter:card" content="summary_large_image">
  {css}
</head>
<body>
<a class="skip" href="#contenido">Saltar al contenido</a>
<div class="wrap">
  <header>
    <a class="brand" href="../../">La Auditora</a>
    <nav>
      <a href="../">Articulos</a>
      <a href="../../">Auditorias</a>
      <a href="../../en/">English</a>
      <a href="articulo.md">Fuente .md</a>
    </nav>
  </header>

  <main id="contenido">
    <p class="eyebrow">Articulo · {date}</p>
    <h1>{title}</h1>
    <p class="lede">{lede}</p>
    <div class="proof">{pruebas}</div>

{cuerpo}

    <section class="cta">
      <p><strong>Todo lo que hay aqui se puede medir otra vez.</strong></p>
      <p>Las cifras viajan con el comando o el <code>archivo:linea</code> que las produce. Si algo no cuadra,
      la respuesta no es un argumento: es el instrumento, en
      <a href="../../auditoria-002-economia-contexto/">el informe reproducible</a> y en
      <a href="https://github.com/alexisromtz-lab/la-auditora">el repositorio</a>.</p>
    </section>
  </main>

  <footer>
    <p>La Auditora · Platino Labs · <a href="../">mas articulos</a> · <a href="../../">auditorias</a></p>
  </footer>
</div>
</body>
</html>
"""

INDICE = """<!doctype html>
<!-- HUELLA-PAGINA-ARTICULOS-INDICE-20261108 -->
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Articulos | La Auditora</title>
  <meta name="description" content="Los articulos de La Auditora: cada cifra con el comando que la produce, cada pieza reproducible desde el repositorio.">
  <meta name="robots" content="index,follow">
  <link rel="canonical" href="https://alexisromtz-lab.github.io/la-auditora/portafolio/articulos/">
  {css}
</head>
<body>
<a class="skip" href="#contenido">Saltar al contenido</a>
<div class="wrap">
  <header>
    <a class="brand" href="../">La Auditora</a>
    <nav>
      <a href="../">Auditorias</a>
      <a href="../en/">English</a>
    </nav>
  </header>

  <main id="contenido">
    <p class="eyebrow">Articulos</p>
    <h1>Lo que medimos, escrito para que se pueda rehacer</h1>
    <p class="lede">Ninguna cifra de estas piezas se escribe a mano: cada una lleva el comando o el
    <code>archivo:linea</code> que la produce, y la que no tiene denominador declarado no se publica.</p>
    <ul class="lista">
{entradas}
    </ul>
  </main>

  <footer>
    <p>La Auditora · Platino Labs · <a href="../">auditorias</a></p>
  </footer>
</div>
</body>
</html>
"""


def _pruebas(meta: dict) -> str:
    piezas = ["<span>%s</span>" % html.escape(t) for t in meta["tags"]]
    return "".join(piezas)


def pagina(meta: dict) -> str:
    slug = meta["ruta"].parent.name
    cuerpo = re.sub(r"^\s{0,3}#\s+.*$", "", meta["cuerpo"], count=1, flags=re.MULTILINE)
    return PLANTILLA.format(
        slug=slug,
        title=html.escape(meta["title"], quote=True),
        lede=html.escape(meta["lede"], quote=True),
        date=html.escape(meta["date"]),
        canonical=SITIO + slug + "/",
        css=CSS % "../",
        pruebas=_pruebas(meta),
        cuerpo=renderizar(cuerpo).rstrip(),
    )


def indice(metas: list) -> str:
    entradas = []
    for m in metas:
        slug = m["ruta"].parent.name
        entradas.append(
            '      <li><a href="%s/">%s</a> <span class="fecha">%s</span><br>%s</li>'
            % (slug, html.escape(m["title"]), html.escape(m["date"]), html.escape(m["lede"]))
        )
    return INDICE.format(css=CSS % "", entradas="\n".join(entradas))


# ── el acto ─────────────────────────────────────────────────────────────────

def cosechar(raiz: Path) -> list:
    base = raiz / DIR_ARTICULOS
    metas, errores = [], []
    for ruta in sorted(base.glob("*/articulo.md")):
        try:
            metas.append(leer_articulo(ruta))
        except ValueError as e:
            errores.append(str(e))
    return metas, errores


def aplicar(raiz: Path, escribir: bool):
    """Devuelve (cambios, errores). Un articulo ilegible es un error, no un
    cambio: no se mezclan, o un front matter roto devolveria RC 0 en --aplicar."""
    base = raiz / DIR_ARTICULOS
    metas, errores = cosechar(raiz)
    cambios = []
    if not metas:
        return cambios, errores

    objetivos = [(m["ruta"].parent / "index.html", pagina(m)) for m in metas]
    objetivos.append((base / "index.html", indice(metas)))

    for destino, contenido in objetivos:
        contenido += "\n"
        actual = destino.read_text(encoding="utf-8") if destino.is_file() else None
        if actual == contenido:
            continue
        rel = destino.relative_to(raiz)
        if escribir:
            destino.write_text(contenido, encoding="utf-8")
            cambios.append("%s: escrita" % rel)
        else:
            cambios.append("%s: desincronizada" % rel)
    return cambios, errores


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Un articulo en markdown, una pagina generada.")
    p.add_argument("--raiz", default=".", help="raiz del repositorio del sitio")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--aplicar", action="store_true", help="escribe las paginas")
    g.add_argument("--check", action="store_true", help="solo mide (RC 1 si hay desfase)")
    g.add_argument("--listar", action="store_true", help="lista los articulos y su estado")
    a = p.parse_args(argv)

    raiz = Path(a.raiz).resolve()
    if not (raiz / DIR_ARTICULOS).is_dir():
        print("NO_MEDIDO: no existe %s bajo %s" % (DIR_ARTICULOS, raiz))
        return 2

    metas, errores = cosechar(raiz)
    if not metas and not errores:
        print("NO_MEDIDO: no hay articulos en %s" % DIR_ARTICULOS)
        return 2
    if a.listar:
        for m in metas:
            slug = m["ruta"].parent.name
            pagina_ = (m["ruta"].parent / "index.html").is_file()
            print(
                "%-52s %s  pagina=%s  tags=%d"
                % (slug, m["date"], "si" if pagina_ else "NO", len(m["tags"]))
            )
        for e in errores:
            print("FALLA " + e)
        return 1 if errores else 0

    cambios, errores = aplicar(raiz, escribir=a.aplicar)
    for c in cambios:
        print(("escrito " if a.aplicar else "FALLA ") + c)
    for e in errores:
        print("FALLA " + e)
    if errores:
        return 1
    if cambios:
        return 0 if a.aplicar else 1
    print("PAGINAS AL DIA: %d articulo(s). Cero cambios." % len(metas))
    return 0


if __name__ == "__main__":
    sys.exit(main())
