---
title: "How to find import bugs in Tor using AST graphs"
published: false
description: "Un ciclo de importación en stem (Tor) que solo falla según el punto de entrada, detectado con un grafo AST antes de leer una sola línea de código."
tags: p, y, t, h
canonical_url: "https://alexisromtz-lab.github.io/la-auditora/portafolio/articulos/en/como-encontrar-bugs-de-importacion-en-tor-usando-grafos-ast-49cn/"
---

# How to find import bugs in Tor using AST graphs

There is a class of bug that tests do not catch and linters do not see: the module works, but **the order in which you import it decides whether it starts**. The code is not broken; the dependency graph is.  The same pattern later appeared in a much bigger repo: an environment with 117 packages where `uv pip check` answered `All installed packages are compatible` and **12.06 s later the same interpreter** raised `ModuleNotFoundError: No module named 'prisma'`. Six import hops to a package that the installed extra does not declare. I wrote it up with the exact lines: [Coherence is not completeness](https://doi.org/10.5281/zenodo.23955654) · the measurement rules behind it, published in [`corpus-medido`](https://github.com/alexisromtz-lab/corpus-medido) · and the upstream thread in [`astral-sh/uv#13963`](https://github.com/astral-sh/uv/issues/13963).

This is the record of a real one, found in [`torproject/stem`](https://github.com/torproject/stem) — the Python library for controlling a Tor daemon — and reported in [torproject/stem#160](https://github.com/torproject/stem/issues/160).

## Step 1 — Clone the subject and declare the universe

```bash
git clone --depth 50 https://github.com/torproject/stem.git stem_art
cd stem_art && git rev-parse HEAD
# d5012a1039f05c69ebe832723ce96ecbe8f79fe1
```

The universe is **only `.py` files**. Any number published afterwards has to declare that universe: a tree without Python produces no graph, and an empty graph is not a clean graph.

## Step 2 — Build the import graph from the AST

The tool does not run the code: it parses every `.py` with `ast`, extracts the `import`/`from ... import` statements, resolves them to modules of the corpus, and splits two subgraphs:

- **eager**: the statement runs when the module is imported (module body, including the body of a `class`).
- **deferred**: it lives inside a function; it does not run on import.

That separation is the whole method. A deferred cycle cannot close on import. An **eager** cycle can.

```bash
python3 tools/grafo_ciclos_tt_metal_20261026.py --root /tmp/stem_art --raices-no-resueltas
```

Output, measured on `d5012a1`:

```text
archivos python     : 219
aristas import      : 611
  eager (al importar): 594
  diferidas          : 17
SCC total           : 5
SCC eager           : 5
  ciclo(11): stem/connection.py, stem/control.py, stem/response/__init__.py,
             stem/response/authchallenge.py, stem/response/events.py,
             stem/response/getconf.py, stem/response/getinfo.py,
             stem/response/mapaddress.py, stem/response/onion_client_auth.py,
             stem/response/protocolinfo.py, stem/socket.py
  CICLO EAGER(2): stem/response/__init__.py, stem/socket.py
```

Five strongly connected components, and **all five contain at least one eager edge**. The smallest one is the interesting one: `stem/response/__init__.py` ↔ `stem/socket.py`.

## Step 3 — Turn the suspicion into a two-command reproduction

An eager cycle is a hypothesis, not a finding. The cheapest falsifier is two fresh processes, with different entry points:

```bash
python -c 'import stem.response'   # entry through the package
python -c 'import stem.socket'     # entry through the other end
```

Measured with Python 3.12.13:

```text
--- import stem.response:  RC=1
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "stem/response/__init__.py", line 37, in <module>
    import stem.socket
  File "stem/socket.py", line 105, in <module>
    class BaseSocket(object):
  File "stem/socket.py", line 253, in BaseSocket
    async def _recv(self, handler: Callable[[asyncio.StreamReader], Awaitable[stem.response.ControlMessage]]) -> stem.response.ControlMessage:
                                                                              ^^^^^^^^^^^^^
AttributeError: cannot access submodule 'response' of module 'stem' (most likely due to a circular import)

--- import stem.socket:    RC=0
```

The same code, two opposite results depending on where you enter. That is the signature of a **load-order** defect, not of a badly written function.

## Why this is a load-order defect

Three facts, each one verifiable in the file:

1. `stem/response/__init__.py:37` does `import stem.socket` **while `stem.response` is still being initialised**. At that instant, `stem.response` exists in `sys.modules`, but the `response` attribute of the `stem` package — the one that makes `stem.response.ControlMessage` work — is not bound yet.
2. `stem/socket.py:105` opens `class BaseSocket(object):`. A class body **runs on import**, and `stem/socket.py` has no `from __future__ import annotations`.
3. That is why the annotation on `stem/socket.py:253` is evaluated immediately, at the exact moment when the name `stem.response` is not reachable as an attribute.

The annotation is not code that runs; it is metadata that Python 3 evaluates eagerly unless told otherwise. And `stem/socket.py:90` (`import stem.response`) closes the circle: the two modules need each other, and **which one finishes first decides whether the annotation resolves**.

When you enter through `stem.socket`, `stem.socket` initialises first, its `import stem.response` runs to the end, and by the time the annotation is evaluated the name already exists. When you enter through `stem.response`, the order reverses and it blows up.

## The fix

Either of the two breaks the ordering dependency:

```python
from __future__ import annotations   # at the top of stem/socket.py
```

or quoting the affected annotation (`'stem.response.ControlMessage'`). Both leave `typing.get_type_hints()` working, because the names resolve once the package is loaded.

Measured, not assumed: with the line added, `import stem.response` exits **RC 0**; with the line reverted, it goes back to **RC 1** with the same `AttributeError`. The defect and its closure live in the same pair of commands.

## Why an AST graph and not a linter

- An import linter looks at one file; the bug **is not in a file**, it is in the pair.
- The `stem` tests do not see it because each test module imports what it needs in whatever order suits it: the accidental order of the test masks the real order of the user.
- The graph costs seconds and does not execute the subject. It produces a **ranking**: 5 SCCs, all with an eager edge. That shrinks the search space from "219 files" to "one pair".

The real cost is in name resolution, not in parsing: on this checkout, **1,015 imports did not resolve** (913 from `STDLIB`, 102 from external dependencies such as `cryptography`), and **211 edges into the `__init__` of an ancestor package were discarded** on purpose — the package is already in `sys.modules` when the child runs, so counting them fabricates cycles the runtime never walks. An engine that does not declare those two decisions publishes false cycles with complete ease.

## Scope and limits

- **No security claim.** It is an import-time defect: it shows up as a hard `AttributeError` instead of an import that works.
- **It was not tested against a running Tor daemon.** Only the import, in a clean interpreter.
- The bug belongs to the subject, not to the method: the method only made it visible without reading `stem/socket.py` top to bottom first.

## Evidence

- Open issue: [torproject/stem#160 — *AttributeError on class-body annotation evaluation in stem/socket.py when importing stem.response first*](https://github.com/torproject/stem/issues/160)
- Observed and reproducible on `d5012a1039f05c69ebe832723ce96ecbe8f79fe1`, Python 3.12.13, macOS.

If you maintain a library whose packages import each other, the experiment costs you two commands: build the graph, separate eager from deferred, and test every small cycle with two opposite entry points. The one that fails one way and not the other is your bug.
