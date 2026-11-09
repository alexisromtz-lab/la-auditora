"""Falsador de traduccion: compara el cuerpo ES de un articulo contra su EN.

No juzga la prosa — eso no se mide. Juzga lo que un lector puede comprobar sin
saber ingles, que es justo lo que una traduccion puede romper en silencio:

  1. el multiconjunto de numeros (una cifra que cambia es una mentira)
  2. el conjunto de URLs (un enlace que desaparece rompe la evidencia)
  3. los bloques de codigo, identicos ignorando comentarios
  4. la forma: encabezados por nivel, vinetas, negritas y vallas

Uso:
    python3 tools/equivalencia_en.py ES.md EN.md      # RC 0 equivalente, RC 1 no
    python3 tools/equivalencia_en.py --self-test      # RC 0 si el falsador muerde
"""
import re
import sys
from collections import Counter
from pathlib import Path

NUM = re.compile(r"\d+(?:[.,\s]\d+)*\s*%?")
MILES = re.compile(r"[.,](?=\d{3}$)")
URL = re.compile(r"https?://[^\s\)\]\">]+")


def numeros(texto):
    """Multiconjunto normalizado: 959.216 ES y 959,216 EN son la misma cifra."""
    return Counter(
        MILES.sub("", n.replace(" ", "")).replace(",", ".") for n in NUM.findall(texto)
    )


def urls(texto):
    return Counter(u.rstrip(".,;:") for u in URL.findall(texto))


def codigo_sin_comentarios(bloque):
    """El comentario de un bloque cambia al traducir; el codigo no."""
    lineas = []
    for linea in bloque.split("\n"):
        corte = linea.find("#")
        lineas.append(linea[:corte].rstrip() if corte >= 0 else linea.rstrip())
    return [l for l in lineas if l.strip()]


def bloques(texto):
    trozos = texto.split("```")
    return [trozos[i] for i in range(1, len(trozos), 2)]


def forma(texto):
    return {
        "h1": len(re.findall(r"^# ", texto, re.M)),
        "h2": len(re.findall(r"^## ", texto, re.M)),
        "h3": len(re.findall(r"^### ", texto, re.M)),
        "vinetas": len(re.findall(r"^[-*] ", texto, re.M)),
        "negritas": len(re.findall(r"\*\*[^*]+\*\*", texto)),
        "vallas": texto.count("```"),
    }


def comparar(es, en):
    fallos = []
    ne, nn = numeros(es), numeros(en)
    if ne != nn:
        fallos.append("NUMEROS faltan=%s sobran=%s" % (dict(ne - nn), dict(nn - ne)))
    ue, un = urls(es), urls(en)
    if ue != un:
        fallos.append("URLS faltan=%s sobran=%s" % (dict(ue - un), dict(un - ue)))
    be = bloques(es)
    bn = bloques(en)
    if len(be) != len(bn):
        fallos.append("BLOQUES %d -> %d" % (len(be), len(bn)))
    else:
        for i, (a, b) in enumerate(zip(be, bn)):
            a = a.split("\n", 1)[-1]
            b = b.split("\n", 1)[-1]
            if codigo_sin_comentarios(a) != codigo_sin_comentarios(b):
                fallos.append("BLOQUE %d distinto" % i)
    fe, fn = forma(es), forma(en)
    for clave in fe:
        if fe[clave] != fn[clave]:
            fallos.append("FORMA %s %d -> %d" % (clave, fe[clave], fn[clave]))
    return fallos, fe, fn


CASOS = [
    # (nombre, ES, EN, ¿debe pasar?)
    ("identico", "## A\n\n807 casos, 15.2 %.", "## A\n\n807 cases, 15.2 %.", True),
    (
        "coma decimal",
        "0,240 y 1,498 y 959.216",
        "0.240 and 1.498 and 959,216",
        True,
    ),
    ("cifra movida", "807 casos", "808 cases", False),
    ("cifra perdida", "del 807 al 612", "from 807", False),
    ("url perdida", "ver https://a.mx/x y fin", "see fin", False),
    ("forma h2", "## A\n## B", "## A", False),
    ("vineta perdida", "- uno\n- dos", "- one", False),
    (
        "codigo igual con comentario traducido",
        "```\n# hola\nx = 1\n```",
        "```\n# hello\nx = 1\n```",
        True,
    ),
    (
        "codigo cambiado",
        "```\nx = 1\n```",
        "```\nx = 2\n```",
        False,
    ),
]


def self_test():
    fallos = []
    for nombre, es, en, debe_pasar in CASOS:
        problemas, _, _ = comparar(es, en)
        if bool(problemas) == debe_pasar:
            fallos.append(
                "%s: esperaba %s, obtuve %s"
                % (nombre, "EQUIVALENTE" if debe_pasar else "FALLO", problemas)
            )
    return fallos


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--self-test"]:
        fallos = self_test()
        for f in fallos:
            print("FALLO:", f)
        if fallos:
            return 1
        print("SELF-TEST OK: %d casos, el falsador muerde" % len(CASOS))
        return 0
    if len(argv) != 2:
        print("uso: equivalencia_en.py ES.md EN.md | --self-test", file=sys.stderr)
        return 2
    rutas = [Path(a).expanduser() for a in argv]
    for ruta in rutas:
        if not ruta.is_file():
            print("CONFIG: no existe %s" % ruta, file=sys.stderr)
            return 2
    es, en = (r.read_text(encoding="utf-8") for r in rutas)
    problemas, fe, fn = comparar(es, en)
    print("ES", fe)
    print("EN", fn)
    for f in problemas:
        print("FALLO:", f)
    if problemas:
        return 1
    print("EQUIVALENTE: numeros, urls, bloques y forma coinciden")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
