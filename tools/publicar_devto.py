#!/usr/bin/env python3
"""Publicacion determinista en dev.to: el cuerpo viaja como body_markdown.

Copiar de una pagina renderizada destruye el markdown -- `##`, `|`, vallas y
`---` son markup y no viajan en el portapapeles; lo que llega es el texto
visible, y `## 3.` degrada a lista ordenada. Este instrumento manda la
proyeccion `devto.md` tal cual en una peticion HTTP, asi que no hay viaje que
pueda perder estructura.

Por defecto **no envia nada**: imprime el payload, su tamano y la huella del
cuerpo. `--enviar` es el unico camino que escribe en la red, y exige la clave
en el entorno (`DEVTO_API_KEY`) o en un archivo. La clave nunca se imprime: se
publica nombre, longitud y prefijo de 4 caracteres.

Uso:
    python3 tools/publicar_devto.py --raiz .                      # seco, todo
    python3 tools/publicar_devto.py --raiz . --slug <slug> --enviar
    python3 tools/publicar_devto.py --reparar <slug> --enviar     # PUT idempotente
    python3 tools/publicar_devto.py --listar                      # id | titulo

RC: 0 sin cambio o publicado · 1 desfase en --check · 2 configuracion
(clave ausente, proyeccion ilegible) · 3 error de la API · 20 argumentos.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from devto import NOMBRE  # noqa: E402
from paginas_articulos import SITIO_EN, cosechar  # noqa: E402

API = "https://dev.to/api"
VARIABLE = "DEVTO_API_KEY"
MAX_TAGS = 4


class Config(Exception):
    """Falta la clave o la proyeccion no es legible."""


def clave(archivo: str | None = None) -> tuple[str, str]:
    """La clave y su origen. El valor no sale de aqui."""
    if archivo:
        ruta = Path(archivo)
        if not ruta.exists():
            raise Config("no existe el archivo de clave: %s" % archivo)
        valor, origen = ruta.read_text(encoding="utf-8").strip(), str(ruta)
    else:
        valor, origen = os.environ.get(VARIABLE, "").strip(), VARIABLE
    if not valor:
        raise Config(
            "clave ausente (%s). Generala en dev.to/settings/extensions y exportala:\n"
            "  export %s=...   # nunca en el chat, nunca en un commit" % (origen, VARIABLE)
        )
    return valor, origen


def describir_clave(valor: str) -> str:
    return "len=%d prefijo=%s..." % (len(valor), valor[:4])


def separar(texto: str) -> tuple[dict, str]:
    """Encabezado y cuerpo de una proyeccion devto.md."""
    if not texto.startswith("---\n"):
        raise Config("la proyeccion no abre con '---': no es front matter")
    partes = texto.split("\n---\n", 1)
    if len(partes) != 2:
        raise Config("la proyeccion no cierra el front matter")
    cabecera, cuerpo = partes
    encabezado = {}
    for linea in cabecera.lstrip("-\n").split("\n"):
        if not linea.strip():
            continue
        if ": " not in linea:
            raise Config("linea de encabezado ilegible: %r" % linea)
        nombre, valor = linea.split(": ", 1)
        if len(valor) >= 2 and valor[0] == '"' and valor[-1] == '"':
            valor = valor[1:-1].replace('\\\\', '\\').replace('\\"', '"')
        encabezado[nombre] = valor
    return encabezado, cuerpo


def payload(encabezado: dict, cuerpo: str, publicado: bool) -> dict:
    """El cuerpo viaja intacto: es el unico campo que no se puede reconstruir."""
    tags = [t.strip() for t in encabezado.get("tags", "").split(",") if t.strip()]
    return {
        "article": {
            "title": encabezado["title"],
            "published": publicado,
            "body_markdown": cuerpo,
            "description": encabezado.get("description", ""),
            "canonical_url": encabezado.get("canonical_url", ""),
            "tags": tags[:MAX_TAGS],
        }
    }


def huella(cuerpo: str) -> str:
    return hashlib.sha256(cuerpo.encode("utf-8")).hexdigest()[:12]


def transporte_urllib(metodo: str, url: str, clave_api: str, datos: dict | None):
    cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8") if datos is not None else None
    peticion = urllib.request.Request(url, data=cuerpo, method=metodo)
    peticion.add_header("api-key", clave_api)
    peticion.add_header("Content-Type", "application/json")
    peticion.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(peticion, timeout=30) as respuesta:
            return respuesta.status, json.loads(respuesta.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as error:
        crudo = error.read().decode("utf-8", "replace")
        try:
            return error.code, json.loads(crudo)
        except ValueError:
            return error.code, {"error": crudo[:400]}


def leer(raiz: Path, slug: str) -> tuple[dict, str, Path]:
    ruta = raiz / "portafolio" / "articulos" / slug / NOMBRE
    if not ruta.exists():
        raise Config("no existe la proyeccion: %s (corre tools/devto.py --raiz .)" % ruta)
    encabezado, cuerpo = separar(ruta.read_text(encoding="utf-8"))
    for obligatoria in ("title", "canonical_url"):
        if not encabezado.get(obligatoria):
            raise Config("%s: falta %s en el encabezado" % (ruta, obligatoria))
    return encabezado, cuerpo, ruta


def slugs_en(raiz: Path) -> list[str]:
    metas, errores = cosechar(raiz)
    for e in errores:
        print("ENCABEZADO ILEGIBLE: %s" % e, file=sys.stderr)
    if errores:
        raise Config("hay articulos con encabezado ilegible")
    return [m["slug"] for m in metas if m["lang"] == "en"]


def publicar(raiz: Path, slug: str, clave_api: str, transporte, publicado: bool, enviar: bool) -> int:
    encabezado, cuerpo, ruta = leer(raiz, slug)
    datos = payload(encabezado, cuerpo, publicado)
    print("%-56s %s" % (slug, ruta.name))
    print(
        "  titulo=%r\n  cuerpo=%d lineas %d B sha256:%s\n  canonical=%s\n  tags=%s\n  published=%s"
        % (
            encabezado["title"],
            cuerpo.count("\n") + 1,
            len(cuerpo.encode("utf-8")),
            huella(cuerpo),
            encabezado["canonical_url"],
            ", ".join(datos["article"]["tags"]),
            publicado,
        )
    )
    if not enviar:
        print("  SECO: no se envio nada. --enviar para publicar.")
        return 0
    estado, respuesta = transporte("POST", API + "/articles", clave_api, datos)
    if estado not in (200, 201):
        print("  API %d: %s" % (estado, json.dumps(respuesta)[:400]), file=sys.stderr)
        return 3
    print("  PUBLICADO id=%s url=%s" % (respuesta.get("id"), respuesta.get("url")))
    return 0


def reparar(raiz: Path, slug: str, clave_api: str, transporte, publicado: bool, enviar: bool) -> int:
    """PUT idempotente: si el cuerpo remoto ya es el local, no se envia nada."""
    encabezado, cuerpo, _ = leer(raiz, slug)
    estado, listado = transporte("GET", API + "/articles/me/all?per_page=1000", clave_api, None)
    if estado != 200:
        print("API %d al listar: %s" % (estado, json.dumps(listado)[:400]), file=sys.stderr)
        return 3
    canonica = encabezado["canonical_url"]
    propio = [a for a in listado if a.get("canonical_url") == canonica]
    if not propio:
        print("%s: no hay articulo en dev.to con canonical_url %s" % (slug, canonica), file=sys.stderr)
        return 3
    remoto = propio[0]
    if (remoto.get("body_markdown") or "").strip() == cuerpo.strip():
        print("%s: sin cambio (id=%s, sha256:%s)" % (slug, remoto["id"], huella(cuerpo)))
        return 0
    print(
        "%s: DESFASE id=%s remoto=%d B local=%d B sha256:%s"
        % (slug, remoto["id"], len(remoto.get("body_markdown") or ""), len(cuerpo.encode("utf-8")), huella(cuerpo))
    )
    if not enviar:
        print("  SECO: no se envio nada. --enviar para reparar.")
        return 0
    datos = payload(encabezado, cuerpo, publicado)
    estado, respuesta = transporte("PUT", "%s/articles/%s" % (API, remoto["id"]), clave_api, datos)
    if estado not in (200, 201):
        print("  API %d: %s" % (estado, json.dumps(respuesta)[:400]), file=sys.stderr)
        return 3
    print("  REPARADO id=%s url=%s" % (respuesta.get("id"), respuesta.get("url")))
    return 0


def listar(clave_api: str, transporte) -> int:
    estado, listado = transporte("GET", API + "/articles/me/all?per_page=1000", clave_api, None)
    if estado != 200:
        print("API %d al listar: %s" % (estado, json.dumps(listado)[:400]), file=sys.stderr)
        return 3
    for a in sorted(listado, key=lambda x: x.get("published_at") or "", reverse=True):
        print("%-9s %s  %s" % (a.get("id"), (a.get("published_at") or "borrador")[:10], a.get("title", "")[:64]))
    print("\n%d articulo(s)." % len(listado))
    return 0


def main(argv=None, transporte=transporte_urllib) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--raiz", default=".", help="raiz del repositorio")
    p.add_argument("--slug", action="append", default=[], help="slug a publicar (repetible)")
    p.add_argument("--enviar", action="store_true", help="sin esta bandera no se hace ninguna peticion")
    p.add_argument("--listar", action="store_true", help="lista lo que ya vive en dev.to")
    p.add_argument("--reparar", metavar="SLUG", help="PUT idempotente sobre el articulo ya publicado")
    p.add_argument("--borrador", action="store_true", help="publicar como borrador en vez de publico")
    p.add_argument("--clave-archivo", help="archivo con la clave (por defecto, la variable de entorno)")
    try:
        args = p.parse_args(argv)
    except SystemExit as error:
        return 20 if error.code else 0
    publicado = not args.borrador
    # `--reparar` necesita la clave aun en seco: comparar contra el cuerpo remoto
    # exige una lectura. Publicar en seco no abre ninguna conexion.
    necesita_clave = args.enviar or args.listar or bool(args.reparar)
    try:
        if necesita_clave:
            valor, origen = clave(args.clave_archivo)
            print("clave %s %s" % (origen, describir_clave(valor)))
        else:
            valor = ""
            print("SECO: se imprime el payload, no se abre ninguna conexion.")
        if args.listar:
            return listar(valor, transporte)
        raiz = Path(args.raiz).resolve()
        if args.reparar:
            return reparar(raiz, args.reparar, valor, transporte, publicado, args.enviar)
        slugs = args.slug or slugs_en(raiz)
        if not slugs:
            raise Config("no hay articulos en ingles que publicar")
        peor = 0
        for slug in slugs:
            peor = max(peor, publicar(raiz, slug, valor, transporte, publicado, args.enviar))
        return peor
    except Config as error:
        print("CONFIG: %s" % error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
