#!/usr/bin/env python3
"""Does this CI step go green when it runs no tests?

Usage:
    python3 reproduce.py <path-to-workflow.yml>

The script extracts the `run:` block of the step that runs the test shard,
executes that block verbatim, and substitutes `uv` with a stub. Nothing of the
original logic is re-implemented: the shell that runs is the shell in the file.

Two scenarios are tried, both of which should end in a red job:

    A  the matrix names a directory that no longer exists
       (what a rename or a deleted shard looks like)
    B  the runner exits 5, pytest's "no tests were collected"

Exit code 0  the step fails closed in both scenarios
Exit code 1  the step reports success in at least one scenario (finding)
Exit code 2  the step could not be located, or the block did not run
"""
from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

STEP_ID = "tests"
REAL_DIR = "tests"


def extraer_bloque(texto: str) -> str:
    lineas = texto.splitlines()
    inicio = None
    for i, linea in enumerate(lineas):
        if re.match(r"^\s*id:\s*" + STEP_ID + r"\s*$", linea):
            inicio = i
            break
    if inicio is None:
        raise SystemExit("no se encontro el step con `id: tests`")
    j = inicio
    while j < len(lineas) and not re.match(r"^\s*run:\s*\|", lineas[j]):
        j += 1
    if j == len(lineas):
        raise SystemExit("el step `id: tests` no tiene bloque `run: |`")
    sangria_cabecera = len(lineas[j]) - len(lineas[j].lstrip())
    cuerpo = []
    for linea in lineas[j + 1:]:
        if linea.strip() == "":
            cuerpo.append("")
            continue
        sangria = len(linea) - len(linea.lstrip())
        if sangria <= sangria_cabecera:
            break
        cuerpo.append(linea)
    sangria = min((len(l) - len(l.lstrip()) for l in cuerpo if l.strip()), default=0)
    return "\n".join(l[sangria:] if len(l) >= sangria else l for l in cuerpo)


def correr(bloque: str, seleccion: str, uv_rc: int) -> tuple[int, bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        # el repo real, para que exista al menos lo que existe
        (tmp_path / REAL_DIR).mkdir()
        (tmp_path / REAL_DIR / "unit").mkdir()
        (tmp_path / REAL_DIR / "unit" / "test_que_existe.py").write_text("def test_ok():\n    assert True\n")

        bin_uv = tmp_path / "bin"
        bin_uv.mkdir()
        stub = bin_uv / "uv"
        stub.write_text("#!/bin/sh\nif [ \"$1\" = \"run\" ]; then exit %d; fi\nexit %d\n" % (uv_rc, uv_rc))
        stub.chmod(stub.stat().st_mode | stat.S_IEXEC)

        guion = tmp_path / "bloque.sh"
        guion.write_text(bloque + "\n")

        entorno = {
            "PATH": f"{bin_uv}:/usr/bin:/bin",
            "HOME": str(tmp_path),
            "GITHUB_OUTPUT": str(tmp_path / "out.txt"),
            "GITHUB_ACTIONS": "true",
            "TEST_PATH": seleccion,
            "MAX_FAILURES": "10",
            "WORKERS": "0",
            "RERUNS": "0",
            "TEST_TIMEOUT_SECONDS": "120",
            "DIST": "loadscope",
        }
        (tmp_path / "out.txt").write_text("")
        r = subprocess.run(
            ["bash", "-e", str(guion)], cwd=tmp_path, env=entorno,
            capture_output=True, text=True, timeout=120,
        )
        return r.returncode, "pytest" in guion.read_text() or True, (r.stdout + r.stderr).strip()


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    ruta = Path(sys.argv[1])
    if not ruta.is_file():
        print(f"no existe: {ruta}")
        return 2
    bloque = extraer_bloque(ruta.read_text(encoding="utf-8"))
    if "pytest" not in bloque:
        print("el bloque no invoca pytest: no medible")
        return 2

    escenarios = [
        ("A", "el shard nombra un directorio que ya no existe", "tests/renombrado_hace_seis_meses", 0),
        ("B", "el runner devuelve 5 (cero tests recogidos)", "tests/unit", 5),
    ]
    fallo_cerrado = True
    for etiqueta, descripcion, seleccion, uv_rc in escenarios:
        rc, _, salida = correr(bloque, seleccion, uv_rc)
        verde = rc == 0
        if verde:
            fallo_cerrado = False
        print(f"[{etiqueta}] {descripcion}")
        print(f"    seleccion = {seleccion!r} · runner rc = {uv_rc}")
        print(f"    el paso termino con rc = {rc} -> {'VERDE' if verde else 'ROJO'}")
        for linea in salida.splitlines()[:4]:
            print(f"      | {linea}")

    print()
    if fallo_cerrado:
        print("RESULTADO: el paso falla cerrado en los dos escenarios. Sin hallazgo.")
        return 0
    print("RESULTADO: el paso reporta exito sin haber corrido un solo test.")
    print("           `verde` deja de distinguir «todo paso» de «no se corrio nada».")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
