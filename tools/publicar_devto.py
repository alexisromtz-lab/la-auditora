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
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from devto import NOMBRE  # noqa: E402
from paginas_articulos import SITIO_EN, cosechar  # noqa: E402

API = "https://dev.to/api"
VARIABLES = ("DEVTO_API_KEY", "DEV_TO_API_KEY")
MAX_TAGS = 4
AGENTE = "platino-labs-publicar-devto/1 (+https://github.com/alexisromtz-lab/la-auditora)"


class Config(Exception):
    """Falta la clave o la proyeccion no es legible."""


def _del_archivo(ruta: Path, variables) -> tuple[str, str] | None:
    """Ultima aparicion de cualquiera de los nombres en un `.env`.

    Un `.env` no es un archivo de una sola clave: se busca el nombre y se
    devuelve solo su valor. Nada del resto del archivo sale de aqui.
    """
    encontrado = None
    for linea in ruta.read_text(encoding="utf-8", errors="replace").splitlines():
        limpia = linea.strip()
        if not limpia or limpia.startswith("#") or "=" not in limpia:
            continue
        nombre, valor = limpia.split("=", 1)
        nombre = nombre.strip().removeprefix("export ").strip()
        if nombre in variables:
            valor = valor.strip().strip('"').strip("'").strip()
            if valor:
                encontrado = (valor, "%s:%s" % (ruta, nombre))
    if encontrado:
        return encontrado
    # Un archivo que solo contiene la clave, sin `=`. Se exige que no haya
    # ninguna asignacion: un `.env` con otras claves no es un archivo de clave.
    lineas = [
        linea.strip()
        for linea in ruta.read_text(encoding="utf-8", errors="replace").splitlines()
        if linea.strip() and not linea.strip().startswith("#")
    ]
    if len(lineas) == 1 and "=" not in lineas[0]:
        unico = lineas[0].strip('"').strip("'").strip()
        if unico:
            return unico, str(ruta)
    return None


def clave(archivo: str | None = None, variables=VARIABLES) -> tuple[str, str]:
    """La clave y su origen. El valor no sale de aqui."""
    if archivo:
        ruta = Path(archivo).expanduser()
        if not ruta.exists():
            raise Config("no existe el archivo de clave: %s" % archivo)
        hallada = _del_archivo(ruta, variables)
        if not hallada:
            raise Config("en %s no hay ninguna de estas claves: %s" % (ruta, ", ".join(variables)))
        return hallada
    for nombre in variables:
        valor = os.environ.get(nombre, "").strip()
        if valor:
            return valor, nombre
    raise Config(
        "clave ausente (%s). Generala en dev.to/settings/extensions y exportala:\n"
        "  export %s=...   # nunca en el chat, nunca en un commit\n"
        "  o pásala con --clave-archivo <ruta al .env>"
        % (" / ".join(variables), variables[0])
    )


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


TAG_LEGAL = re.compile(r"^[a-z0-9]+$")


def payload(encabezado: dict, cuerpo: str, publicado: bool) -> dict:
    """El cuerpo viaja intacto: es el unico campo que no se puede reconstruir."""
    tags = [t.strip() for t in encabezado.get("tags", "").split(",") if t.strip()]
    ilegales = [t for t in tags if not TAG_LEGAL.match(t)]
    if ilegales:
        # dev.to corta la publicacion entera con 422 por un solo guion en un tag.
        raise Config(
            "tags ilegales para dev.to (solo minusculas y numeros): %s\n"
            "  corre tools/devto.py --raiz . --aplicar para regenerar la proyeccion"
            % ", ".join(ilegales)
        )
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


VALLA = re.compile(r"^```[A-Za-z0-9_+-]*\s*$")


def normalizar(cuerpo: str) -> str:
    """El cuerpo comparable: sin lo que dev.to reescribe al guardar.

    Medido contra el articulo vivo, dev.to hace dos cosas que no hacemos
    nosotros: quita la linea en blanco inicial y etiqueta las vallas
    desnudas (``` -> ```shell / ```python). Comparar byte a byte hacia que
    la reparacion "idempotente" enviara un PUT en cada corrida. Se compara
    todo lo demas, incluida la estructura: una valla ausente sigue siendo
    un desfase.
    """
    lineas = cuerpo.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lineas = ["```" if VALLA.match(l.rstrip()) else l.rstrip() for l in lineas]
    while lineas and not lineas[0]:
        lineas.pop(0)
    while lineas and not lineas[-1]:
        lineas.pop()
    return "\n".join(lineas)


def transporte_urllib(metodo: str, url: str, clave_api: str, datos: dict | None):
    cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8") if datos is not None else None
    peticion = urllib.request.Request(url, data=cuerpo, method=metodo)
    peticion.add_header("api-key", clave_api)
    peticion.add_header("Content-Type", "application/json")
    peticion.add_header("Accept", "application/json")
    # dev.to responde 403 al User-Agent por defecto de urllib: un cliente que no
    # se identifica no pasa el filtro. Medido, no supuesto.
    peticion.add_header("User-Agent", AGENTE)
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
        return fallo_de_api(estado, respuesta)
    print("  PUBLICADO id=%s url=%s" % (respuesta.get("id"), respuesta.get("url")))
    return 0


def localizar(listado, encabezado: dict, slug: str):
    """El articulo remoto y la clave por la que se reconocio.

    El articulo publicado a mano en el editor web no tiene `canonical_url`, asi
    que buscar solo por canonica lo declara inexistente. Se degrada a titulo,
    nunca a «el primero que haya».
    """
    canonica = encabezado["canonical_url"]
    for a in listado:
        if a.get("canonical_url") == canonica:
            return a, "canonical_url"
    if slug.isdigit():
        for a in listado:
            if str(a.get("id")) == slug:
                return a, "id"
    titulo = (encabezado.get("title") or "").strip()
    if titulo:
        for a in listado:
            if (a.get("title") or "").strip() == titulo:
                return a, "title"
    return None, ""


SEGUNDOS = re.compile(r"try again in (\d+) seconds?")


def fallo_de_api(estado: int, respuesta) -> int:
    """El RC de una respuesta que no es 200/201. 429 no es lo mismo que un 422.

    dev.to limita la creacion de articulos: el 429 es una condicion del
    transporte y llega con los segundos que hay que esperar. Tratarlo como un
    fallo del payload invita a reescribirlo, que es justo lo que no hay que
    hacer. No se reintenta solo: un POST reintentado a ciegas puede publicar dos
    veces.
    """
    texto = json.dumps(respuesta)[:400]
    if estado == 429:
        espera = SEGUNDOS.search(json.dumps(respuesta))
        print(
            "  LIMITE DE LA API (429): %s\n"
            "  No se reintenta solo: un POST repetido a ciegas publica dos veces. "
            "Espera %s s y vuelve a correr el mismo comando."
            % (texto, espera.group(1) if espera else "unos 30"),
            file=sys.stderr,
        )
        return 4
    print("  API %d: %s" % (estado, texto), file=sys.stderr)
    return 3


def reparar(raiz: Path, slug: str, clave_api: str, transporte, publicado: bool, enviar: bool) -> int:
    """PUT idempotente: si el cuerpo remoto ya es el local, no se envia nada."""
    encabezado, cuerpo, _ = leer(raiz, slug)
    estado, listado = transporte("GET", API + "/articles/me/all?per_page=1000", clave_api, None)
    if estado != 200:
        print("API %d al listar: %s" % (estado, json.dumps(listado)[:400]), file=sys.stderr)
        return 3
    canonica = encabezado["canonical_url"]
    remoto, por = localizar(listado, encabezado, slug)
    if remoto is None:
        print("%s: no hay articulo en dev.to con canonical_url ni con titulo %s" % (slug, canonica), file=sys.stderr)
        return 3
    print("%s: reconocido por %s (id=%s)" % (slug, por, remoto.get("id")))
    if not remoto.get("canonical_url"):
        print("  WARN: el articulo remoto no declara canonica; el PUT la añade (%s)" % canonica)
    if normalizar(remoto.get("body_markdown") or "") == normalizar(cuerpo):
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
        return fallo_de_api(estado, respuesta)
    print("  REPARADO id=%s url=%s" % (respuesta.get("id"), respuesta.get("url")))
    return 0


NUMERO = re.compile(r"\d+(?:[.,\s]\d+)*\s*%?")
MILES = re.compile(r"[.,](?=\d{3}$)")


def _canonico(hallado: str) -> str:
    """Una cifra sin su formato: '1 015' y '1,015' son el mismo numero."""
    limpio = hallado.replace(" ", "")
    limpio = MILES.sub("", limpio)
    return limpio.replace(",", ".")


def numeros(texto: str) -> dict:
    """El multiconjunto de cifras de un cuerpo. Una traduccion no puede cambiarlo."""
    cuenta: dict = {}
    for hallado in NUMERO.findall(texto):
        clave = _canonico(hallado)
        cuenta[clave] = cuenta.get(clave, 0) + 1
    return cuenta


def sustituir(
    identificador: str,
    cuerpo_nuevo: Path,
    clave_api: str,
    transporte,
    enviar: bool,
    titulo: str | None = None,
    excusa: str | None = None,
) -> int:
    """Reemplaza el cuerpo de un articulo vivo. Rechaza una traduccion que mueva una cifra."""
    nuevo = cuerpo_nuevo.read_text(encoding="utf-8")
    estado, listado = transporte("GET", API + "/articles/me/all?per_page=1000", clave_api, None)
    if estado != 200:
        print("API %d al listar: %s" % (estado, json.dumps(listado)[:400]), file=sys.stderr)
        return 3
    remoto = next((a for a in listado if str(a.get("id")) == str(identificador)), None)
    if remoto is None:
        print("no hay articulo con id %s" % identificador, file=sys.stderr)
        return 3
    viejo = remoto.get("body_markdown") or ""
    print("id=%s titulo remoto: %s" % (remoto["id"], remoto.get("title")))
    print("  cuerpo remoto %d B -> nuevo %d B" % (len(viejo.encode("utf-8")), len(nuevo.encode("utf-8"))))
    if normalizar(viejo) == normalizar(nuevo):
        print("  sin cambio (sha256:%s)" % huella(nuevo))
        return 0
    antes, despues = numeros(viejo), numeros(nuevo)
    if antes != despues and not excusa:
        solo_viejo = {k: v for k, v in antes.items() if despues.get(k) != v}
        solo_nuevo = {k: v for k, v in despues.items() if antes.get(k) != v}
        print("  NO SE ENVIA: las cifras no coinciden.", file=sys.stderr)
        print("    solo en el remoto: %s" % solo_viejo, file=sys.stderr)
        print("    solo en el nuevo:   %s" % solo_nuevo, file=sys.stderr)
        print("  Si el cambio de cifra es el proposito, dilo: --excusa \"<razon>\"", file=sys.stderr)
        return 5
    if excusa:
        print("  EXCUSA declarada: %s" % excusa)
    datos: dict = {"body_markdown": nuevo}
    if titulo:
        datos["title"] = titulo
    if not enviar:
        print("  SECO: no se envio nada. --enviar para sustituir.")
        return 0
    estado, respuesta = transporte("PUT", "%s/articles/%s" % (API, remoto["id"]), clave_api, {"article": datos})
    if estado not in (200, 201):
        return fallo_de_api(estado, respuesta)
    print("  SUSTITUIDO id=%s url=%s" % (respuesta.get("id"), respuesta.get("url")))
    guardado = respuesta.get("body_markdown") or ""
    print(
        "  guardado %d B | vallas=%d | h2=%d | vinetas=%d"
        % (
            len(guardado.encode("utf-8")),
            guardado.count("```") // 2,
            len(re.findall(r"^## ", guardado, re.M)),
            len(re.findall(r"^[-*] ", guardado, re.M)),
        )
    )
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
    p.add_argument("--sustituir", metavar="ID", help="reemplaza el cuerpo de un articulo vivo por --cuerpo")
    p.add_argument("--cuerpo", help="archivo con el cuerpo nuevo (para --sustituir)")
    p.add_argument("--titulo", help="titulo nuevo (para --sustituir)")
    p.add_argument("--excusa", help="razon por la que las cifras cambian; sin ella, se rechaza")
    p.add_argument("--borrador", action="store_true", help="publicar como borrador en vez de publico")
    p.add_argument("--clave-archivo", help="archivo con la clave (por defecto, la variable de entorno)")
    try:
        args = p.parse_args(argv)
    except SystemExit as error:
        return 20 if error.code else 0
    publicado = not args.borrador
    # `--reparar` necesita la clave aun en seco: comparar contra el cuerpo remoto
    # exige una lectura. Publicar en seco no abre ninguna conexion.
    necesita_clave = args.enviar or args.listar or bool(args.reparar) or bool(args.sustituir)
    try:
        if args.sustituir and not args.cuerpo:
            raise Config("--sustituir exige --cuerpo <archivo>")
        if necesita_clave:
            valor, origen = clave(args.clave_archivo)
            print("clave %s %s" % (origen, describir_clave(valor)))
        else:
            valor = ""
            print("SECO: se imprime el payload, no se abre ninguna conexion.")
        if args.listar:
            return listar(valor, transporte)
        if args.sustituir:
            return sustituir(
                args.sustituir,
                Path(args.cuerpo).expanduser(),
                valor,
                transporte,
                args.enviar,
                args.titulo,
                args.excusa,
            )
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
