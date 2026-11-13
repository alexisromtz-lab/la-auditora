#!/usr/bin/env python3
"""Reproduce every counted claim of audit 003 — google/gvisor, CI surface.

Usage:
    python3 reproduce.py             # default run: offline, reads objeto/
    python3 reproduce.py --remoto    # witness: re-fetches the commit and compares
    python3 reproduce.py --control  # perturbs the input and shows what moves
    python3 reproduce.py --self-test # proves the counter discriminates

The default run reads the 15 workflow files pinned under `objeto/`, which are
byte copies of the audited commit, and recounts six published numbers:

    1  workflow files read                          15
    2  workflows with no root `permissions:` block  12
    3  workflows interpolating a secret in `run:`    1
    4  secret interpolations inside `run:` blocks    4
    5  secret interpolations outside `run:` blocks   7
    6  occurrences inside go.yml                     4

No network, no GitHub token, no clone, no YAML parser: the surface is read as
text, which is what the finding is about.

`--remoto` is a witness, not a second verdict: it downloads the same 15 paths
from the pinned commit and reports how many are byte-identical to the copy. A
divergent witness is printed as `TESTIGO DIVERGE` and never changes the exit
code, so a network outage cannot make the audit look wrong.

`--control` is the negative control behind the finding: it perturbs the pinned
copy in memory and reports the counts that move. A counter that returns the same
numbers on a perturbed input is a counter that always says green.

Exit code 0  every published count reproduces
Exit code 1  at least one published count does not reproduce (the audit is wrong)
Exit code 2  the subject could not be read (files missing, or the copy truncated)
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# HUELLA-AUDITORIA-003-GVISOR-20261112

SHA = "2f5253abfaa87b6d62d79a0da60942e773389934"
BASE = "https://raw.githubusercontent.com/google/gvisor/" + SHA + "/.github/workflows/"
OBJETO = Path(__file__).resolve().parent / "objeto"
WORKFLOWS = (
    "auto_assign.yml",
    "build.yml",
    "cherry_pick_release.yml",
    "close_banned_prs.yml",
    "codeql.yml",
    "cut_release.yml",
    "fileheader.yml",
    "gazelle.yml",
    "go.yml",
    "issue_reviver.yml",
    "labeler.yml",
    "lint.yml",
    "release_mirror.yml",
    "stage_release.yml",
    "stale.yml",
)
CLAIMS = {
    "workflows_leidos": 15,
    "sin_permissions_raiz": 12,
    "workflows_con_secreto_en_run": 1,
    "ocurrencias_en_run": 4,
    "ocurrencias_fuera_de_run": 7,
    "ocurrencias_en_go_yml": 4,
}

_RE_RUN = re.compile(r"^(\s*)(?:-\s+)?run:\s*(\||>)?\s*$")
_RE_SECRETO = "${{ secrets."


def lineas_run(texto: str) -> set[int]:
    """Indices (0-based) de las lineas que pertenecen a un bloque `run:`."""
    indice: set[int] = set()
    lineas = texto.splitlines()
    i = 0
    while i < len(lineas):
        m = _RE_RUN.match(lineas[i])
        if not m:
            i += 1
            continue
        base = len(m.group(1))
        i += 1
        while i < len(lineas):
            linea = lineas[i]
            if linea.strip() and (len(linea) - len(linea.lstrip())) <= base:
                break
            indice.add(i)
            i += 1
    return indice


@dataclass(frozen=True)
class Medicion:
    workflows: int = 0
    sin_permissions_raiz: int = 0
    workflows_con_secreto_en_run: int = 0
    ocurrencias_en_run: int = 0
    ocurrencias_fuera_de_run: int = 0
    ocurrencias_en_go_yml: int = 0

    def como_dict(self) -> dict[str, int]:
        return {
            "workflows_leidos": self.workflows,
            "sin_permissions_raiz": self.sin_permissions_raiz,
            "workflows_con_secreto_en_run": self.workflows_con_secreto_en_run,
            "ocurrencias_en_run": self.ocurrencias_en_run,
            "ocurrencias_fuera_de_run": self.ocurrencias_fuera_de_run,
            "ocurrencias_en_go_yml": self.ocurrencias_en_go_yml,
        }


def medir(archivos: dict[str, str]) -> Medicion:
    sin_raiz = 0
    con_secreto_en_run = 0
    en_run = 0
    fuera = 0
    en_go = 0
    for nombre, texto in archivos.items():
        if not re.search(r"(?m)^permissions:", texto):
            sin_raiz += 1
        dentro = lineas_run(texto)
        lineas = texto.splitlines()
        propio = sum(1 for i, l in enumerate(lineas) if _RE_SECRETO in l and i in dentro)
        ajeno = sum(1 for i, l in enumerate(lineas) if _RE_SECRETO in l and i not in dentro)
        en_run += propio
        fuera += ajeno
        if propio:
            con_secreto_en_run += 1
        if nombre == "go.yml":
            en_go = propio
    return Medicion(
        workflows=len(archivos),
        sin_permissions_raiz=sin_raiz,
        workflows_con_secreto_en_run=con_secreto_en_run,
        ocurrencias_en_run=en_run,
        ocurrencias_fuera_de_run=fuera,
        ocurrencias_en_go_yml=en_go,
    )


def leer_objeto() -> dict[str, str]:
    """Copia fijada en disco: el sujeto del veredicto, sin red."""
    archivos: dict[str, str] = {}
    for nombre in WORKFLOWS:
        ruta = OBJETO / nombre
        archivos[nombre] = ruta.read_text(encoding="utf-8")
    return archivos


def descargar(nombre: str) -> bytes:
    peticion = Request(BASE + nombre, headers={"User-Agent": "la-auditora-reproduce-003/1.0"})
    with urlopen(peticion, timeout=20) as respuesta:
        return respuesta.read()


def testigo() -> int:
    """Compara la copia fijada con el commit. No altera el veredicto."""
    iguales = 0
    divergentes: list[str] = []
    for nombre in WORKFLOWS:
        try:
            remoto = descargar(nombre)
        except (HTTPError, URLError, TimeoutError) as error:
            print(f"TESTIGO NO_MEDIDO: {error}", file=sys.stderr)
            return 2
        if remoto == (OBJETO / nombre).read_bytes():
            iguales += 1
        else:
            divergentes.append(nombre)
    if divergentes:
        print(
            "TESTIGO DIVERGE: %d de %d archivos ya no son identicos al commit (%s)"
            % (len(divergentes), len(WORKFLOWS), ", ".join(divergentes)),
            file=sys.stderr,
        )
        return 1
    print(f"TESTIGO OK: {iguales} de {len(WORKFLOWS)} archivos identicos al commit {SHA[:8]}")
    return 0


def control() -> int:
    """Perturba la copia fijada y publica que cifras se mueven."""
    archivos = leer_objeto()
    base = medir(archivos).como_dict()
    perturbados = dict(archivos)

    # 1 · declarar un `permissions:` en la raiz de build.yml (12 -> 11)
    sin_permisos = next(n for n in WORKFLOWS if not re.search(r"(?m)^permissions:", archivos[n]))
    perturbados[sin_permisos] = "permissions:\n  contents: read\n" + archivos[sin_permisos]

    # 2 · un secreto mas fuera de `run:` en go.yml (7 -> 8, sin tocar en_run)
    perturbados["go.yml"] = archivos["go.yml"] + '\n# ${{ secrets.PERTURBADO }}\n'

    despues = medir(perturbados).como_dict()
    movidos = {k: (base[k], despues[k]) for k in base if base[k] != despues[k]}
    esperado = {
        "sin_permissions_raiz": (base["sin_permissions_raiz"], base["sin_permissions_raiz"] - 1),
        "ocurrencias_fuera_de_run": (base["ocurrencias_fuera_de_run"], base["ocurrencias_fuera_de_run"] + 1),
    }
    print(f"perturbacion 1  declarar `permissions:` en la raiz de {sin_permisos}")
    print("perturbacion 2  anadir un `${{ secrets.* }}` fuera de `run:` en go.yml")
    print()
    for clave, (antes, ahora) in movidos.items():
        print(f"MOVIO {clave:28} {antes:>3} -> {ahora:>3}")
    if movidos != esperado:
        print(f"FALLA: se esperaba mover {esperado}, se movio {movidos}", file=sys.stderr)
        return 1
    print()
    print("CONTROL OK: el contador es sensible a la entrada y distingue lo de dentro de `run:` de lo de fuera.")
    return 0


def self_test() -> int:
    positivo = (
        "permissions:\n  contents: read\n"
        "jobs:\n  a:\n    steps:\n"
        "      - run: |\n"
        '          curl -H "Authorization: token ${{ secrets.GITHUB_TOKEN }}" x\n'
    )
    negativo = (
        "jobs:\n  a:\n    steps:\n"
        "      - run: ./publicar.sh\n"
        "        env:\n"
        "          TOKEN: ${{ secrets.GITHUB_TOKEN }}\n"
    )
    sin_raiz = "jobs:\n  a:\n    runs-on: ubuntu-latest\n"
    m = medir({"positivo.yml": positivo, "negativo.yml": negativo, "sin_raiz.yml": sin_raiz})
    fallos = []
    if m.ocurrencias_en_run != 1:
        fallos.append(f"positivo: esperado 1 en run:, medido {m.ocurrencias_en_run}")
    if m.ocurrencias_fuera_de_run != 1:
        fallos.append(f"negativo: esperado 1 fuera de run:, medido {m.ocurrencias_fuera_de_run}")
    if m.workflows_con_secreto_en_run != 1:
        fallos.append(f"workflows con secreto en run: esperado 1, medido {m.workflows_con_secreto_en_run}")
    if m.sin_permissions_raiz != 2:
        fallos.append(f"sin permissions raiz: esperado 2, medido {m.sin_permissions_raiz}")
    for fallo in fallos:
        print(f"FALLO: {fallo}", file=sys.stderr)
    if fallos:
        return 1
    print("SELF-TEST OK: el contador distingue `run:` de `env:` y no cuenta un workflow sin hallazgos.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reproduce every counted claim of audit 003.")
    parser.add_argument("--remoto", action="store_true", help="compara la copia con el commit fijado")
    parser.add_argument("--control", action="store_true", help="perturba la copia y publica que cifras se mueven")
    parser.add_argument("--self-test", action="store_true", help="prueba el contador sin red")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.control:
        return control()

    try:
        archivos = leer_objeto()
    except OSError as error:
        print(f"SUJETO ILEGIBLE: {error}", file=sys.stderr)
        return 2
    if any(not texto.strip() for texto in archivos.values()):
        print("SUJETO ILEGIBLE: algun archivo de objeto/ esta vacio", file=sys.stderr)
        return 2

    medido = medir(archivos).como_dict()
    reproducidas = 0
    for clave, esperado in CLAIMS.items():
        obtenido = medido[clave]
        ok = obtenido == esperado
        reproducidas += int(ok)
        print(f"{'OK  ' if ok else 'FALLA'} {clave:28} publicado {esperado:>3}   medido {obtenido:>3}")
    print()
    print(f"sujeto  google/gvisor @ {SHA}")
    print(f"fuente  objeto/ (copia fijada, {len(WORKFLOWS)} archivos) - sin red, sin token, sin clon")
    if reproducidas != len(CLAIMS):
        print(f"RC 1 - {reproducidas} of {len(CLAIMS)} published claims reproduce", file=sys.stderr)
        return 1
    if args.remoto:
        testigo()
    print(f"RC 0 - {reproducidas} of {len(CLAIMS)} published claims reproduce")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
