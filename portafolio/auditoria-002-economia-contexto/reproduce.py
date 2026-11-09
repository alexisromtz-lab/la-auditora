#!/usr/bin/env python3
"""Reproduce "Economia de contexto: el 99 % que se paga antes de hablar".

Every figure in the report is derived from two medians that the instrument
`tools/reporte_tokens.py` publishes for a corpus snapshot: the median total
tokens per task (`T_total`) and the median completion tokens per task
(`T_completion`).  The report claims that the ratio between them is a property
of the instrument and not of the corpus size.  This script recomputes every
published figure from the declared tuples and prints them next to the claim.

    python3 reproduce.py
    python3 reproduce.py --repo /path/to/platino-labs

Contract of return codes:
    0  every published claim reproduces within its declared tolerance
    1  at least one published claim diverges
    2  the measurement could not be taken (input illegible, git unavailable)

`--repo` is an optional second witness: it re-reads the three declared blobs
with `git cat-file` and reports whether the source object still matches the
declared tuple.  A snapshot that has moved does NOT fail the report — the
published claim is arithmetic over a declared tuple, not a claim about where
the file lives today — so the re-read never changes the return code.  It is
printed as information only.

No external dependencies, no network, no writes.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

# Snapshot, publication time, and the medians the instrument published.
# `blob` is the Git object id, abbreviated to 8 hex chars as cited in the report.
GENERATIONS = (
    {
        "blob": "bb7190b0",
        "utc": "2026-10-30T19:32:05Z",
        "n": 10,
        "t_total": 18024682.5,
        "t_completion": 141574.5,
        "calls": 217.5,
    },
    {
        "blob": "03e9072b",
        "utc": "2026-10-30T19:50:22Z",
        "n": 10,
        "t_total": 23105392.5,
        "t_completion": 167397.0,
        "calls": 276.5,
    },
    {
        "blob": "8f45a996",
        "utc": "2026-11-08",
        "n": 19,
        "t_total": 55451483.0,
        "t_completion": 465220.0,
        "calls": 669.0,
    },
)

# The published claims, each with the tolerance it was published under.
# `drag` figures are percent; `drag_spread` and `quotient_drift` are
# percentage points and percent respectively.
CLAIMS = (
    ("drag(bb7190b0) = 99.2146 %", "drag", 0, 99.2146, 0.0001),
    ("drag(03e9072b) = 99.2755 %", "drag", 1, 99.2755, 0.0001),
    ("drag(8f45a996) = 99.1610 %", "drag", 2, 99.1610, 0.0001),
    ("drag spread across the three generations <= 0.2 pp", "drag_spread", None, 0.2, 0.0),
    ("total tokens grew by at least 3x between the extremes", "growth", None, 3.0, 0.0),
    ("population grew by at least 1.5x between the extremes", "population_growth", None, 1.5, 0.0),
    ("quotient t_total/calls drifts <= 0.1 % between the extremes", "quotient_drift", None, 0.1, 0.0),
)


def drag(generation):
    """Completion tokens as a fraction of total tokens, in percent."""
    return 100.0 * (1.0 - generation["t_completion"] / generation["t_total"])


def quotient(generation):
    """Median total tokens divided by median model calls: a quotient of medians."""
    return generation["t_total"] / generation["calls"]


def measure():
    """Every derived figure the claims consume."""
    drags = [drag(g) for g in GENERATIONS]
    first, last = GENERATIONS[0], GENERATIONS[-1]
    return {
        "drags": drags,
        "drag_spread": max(drags) - min(drags),
        "growth": last["t_total"] / first["t_total"],
        "population_growth": last["n"] / first["n"],
        "quotient_drift": abs(quotient(last) / quotient(first) - 1.0) * 100.0,
    }


def evaluate():
    """(name, measured, low, high, ok) for every published claim."""
    m = measure()
    rows = []
    for name, key, index, bound, tol in CLAIMS:
        if key == "drag":
            value = m["drags"][index]
            rows.append((name, value, bound - tol, bound + tol, abs(value - bound) <= tol))
        elif key in ("growth", "population_growth"):
            value = m[key]
            rows.append((name, value, bound, float("inf"), value >= bound))
        else:  # an upper bound, no lower bound
            value = m[key]
            rows.append((name, value, 0.0, bound, value <= bound))
    return rows


def reread(repo, generation):
    """The declared tuple as the repository holds it now, or None if illegible."""
    try:
        raw = subprocess.run(
            ["git", "-C", repo, "cat-file", "-p", generation["blob"]],
            capture_output=True,
            check=True,
            timeout=30,
        ).stdout
        block = json.loads(raw)["agregados"]["global"]
        return {
            "t_total": float(block["T_total"]["mediana"]),
            "t_completion": float(block["T_completion"]["mediana"]),
            "calls": float(block["N_llamadas_modelo"]["mediana"]),
        }
    except (subprocess.SubprocessError, OSError, KeyError, TypeError, ValueError):
        return None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--repo",
        metavar="DIR",
        help="optional second witness: re-read the declared blobs from this git repository",
    )
    args = parser.parse_args(argv)

    print("generation   utc                      n      t_total       t_completion    calls    drag %   t_total/calls")
    for g in GENERATIONS:
        print(
            "%-12s %-22s %3d %13s %15s %8s %9.4f %15.2f"
            % (
                g["blob"],
                g["utc"],
                g["n"],
                "{:,.2f}".format(g["t_total"]),
                "{:,.2f}".format(g["t_completion"]),
                "{:,.1f}".format(g["calls"]),
                drag(g),
                quotient(g),
            )
        )

    print()
    rows = evaluate()
    for name, value, low, high, ok in rows:
        if high == float("inf"):
            window = ">= %.4f" % low
        elif low == 0.0:
            window = "<= %.4f" % high
        else:
            window = "%.4f .. %.4f" % (low, high)
        print("%-5s %-62s measured %12.4f   window %s" % ("ok" if ok else "FAIL", name, value, window))

    if args.repo:
        print()
        print("second witness: git -C %s cat-file -p <blob>" % args.repo)
        for g in GENERATIONS:
            now = reread(args.repo, g)
            if now is None:
                print("  %s  illegible (object absent, or not a report snapshot)" % g["blob"])
                continue
            same = (
                now["t_total"] == g["t_total"]
                and now["t_completion"] == g["t_completion"]
                and now["calls"] == g["calls"]
            )
            print(
                "  %s  %-6s t_total=%s  t_completion=%s  calls=%s"
                % (
                    g["blob"],
                    "MATCH" if same else "MOVED",
                    "{:,.2f}".format(now["t_total"]),
                    "{:,.2f}".format(now["t_completion"]),
                    "{:,.1f}".format(now["calls"]),
                )
            )
        print("  informational only: the published claims are arithmetic over the declared")
        print("  tuple, so a moved snapshot does not fail the report.")

    failures = sum(1 for row in rows if not row[4])
    print()
    if failures:
        print("RC 1 - %d of %d published claims diverge" % (failures, len(rows)))
        return 1
    print("RC 0 - %d of %d published claims reproduce" % (len(rows), len(rows)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # fail closed: an unmeasurable run is not a green run
        print("RC 2 - cannot measure: %s: %s" % (type(exc).__name__, exc), file=sys.stderr)
        sys.exit(2)
