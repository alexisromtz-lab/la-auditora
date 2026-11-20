---
title: Nearly half the code in 22 projects depends on a cycle, and the usual metric rewards the worst offender
lede: Across 33,688 modules in 22 projects, 28.1% sit inside a cycle and 48.3% are exposed to one. The two numbers do not rank the same: Spearman correlation between them is +0.041.
date: 2026-11-20
tags: architecture, python, graphs, opensource
lang: en
---

## The second number

When people talk about architectural debt in Python they publish one number: how many cycles there are. I measured two things across 22 projects instead of one — how many modules sit **inside** a cycle and how many, without being in one, **depend** on one.

| what was measured | magnitude | how it was obtained |
|---|---:|---|
| projects | **22** | hand-picked commits, each projection pinned to the commit its row declares |
| modules read | **33,688** | sum of `scc.modules` across the 22 public projections |
| modules inside a cycle | **9,466 · 28.1%** | they belong to a strongly connected component of size > 1 |
| exposed modules | **16,256 · 48.3%** | not in a cycle, but they reach one through the import graph |

The second number is the one that decides whether a change inside the cycle wakes you up at three in the morning.

"Exposed" has a mechanical, checkable definition: a module that belongs to no cyclic component but reaches one by following the import graph. That is, it imports — directly or transitively — something that sits inside a cycle.

## Cycle counts do not rank anything

I ordered the 22 projects by number of cyclic components and then reordered them by exposure. The Spearman correlation between the two orders is **+0.041** over 22 rows: essentially zero. A cycle count says nothing about how much code hangs off a cycle.

Four projects have exactly **one** cyclic component, and their sizes range from 33 to 801 modules:

| project | cyclic components | modules in the largest |
|---|---:|---:|
| apache/superset | 1 | 801 |
| gradio-app/gradio | 1 | 147 |
| pydantic/pydantic | 1 | 64 |
| stripe/stripe-python | 1 | 33 |

The same number for four projects, with a factor of 24 between the first and the last. Another pair: apache/airflow and pytest-dev/pytest have two cyclic components each, and they add up to 367 trapped modules versus 4 — airflow's largest encloses 363 modules and pytest's encloses 2.

## What produces the exposure

Working hypothesis: the culprit is not "having cycles", it is the package `__init__` sitting inside one. In 6 of the 10 rows where the package root could be resolved, the root is inside the largest component. The other 12 projects stay **unmeasured** on this point: the `paquete` field of their projection carries the literal `repo`, which is not a module. That is not a false, it is an absence of data, and an absence is not read as a zero.

The extreme case is huggingface/transformers: 3,139 modules, eight cyclic components, the largest with 176 modules, and 91.9% of the package exposed — 2,886 modules out of 3,139. The mechanism lives in the graph: `transformers` is the node with the most in-edges, 3,103 of those 3,139 modules import it, and that node sits inside the 176-module cycle. When the `__init__` falls inside a small cycle, every module in the package ends up depending on it.

## The metric rewards the worst offender

pytorch/pytorch has the largest cycle of the 22: **1,660 modules**, 65.7% of the package's 2,527, and 1,710 inside cycles overall (67.7%). Its exposure is 493 modules, 19.5%.

vllm-project/vllm: 1,648 in the largest component out of 3,003 modules (54.9%), 1,801 inside (60.0%), and only 704 exposed (23.4%).

In both cases exposure is low for the worst possible reason: the cycle swallowed the package and nobody was left outside to be exposed.

stripe/stripe-python is the mirror image: 1,651 modules, a single 33-module cycle (2.0%), and 1,368 exposed (82.9% of 1,651). Ordered by exposure, transformers tops the list and pytorch drops to the lower half. Ordered by how much of the package is trapped in a single component, the ranking flips.

Neither number is "the right one". The error is publishing only one and calling it architectural maturity.

## Blind spot — what this piece does not claim

It does not claim that a cycle causes a failure. I measured static import topology on 22 commits; I ran nothing and did not cross the graphs with incidents. A previous, published measurement of the same corpus found 2 ruptures in 1,449 modules: cycles tell you where to look, not what will break.

It does not claim that exposure implies execution risk. An exposed module may import the root package once at startup and never touch it again.

It does not claim that the 12 projects without a resolved root are free of a cyclic `__init__`: they are unmeasured, which is why the raw data marks them as such instead of counting them as zero.

It does not claim that 22 projects are a sample. They are 22 hand-picked commits with big names, not a draw; the rate holds for those 22 and for nobody else until it is repeated on another batch.

It does not claim that the instrument is portable for the reader: it computes with `tools/calculate_arch_index.py`. What anyone can verify without it is the arithmetic, by downloading the 22 public projections and summing the `scc.*` fields, which is exactly what I did here.

## Reproduce

```
.venv/bin/python tools/calculate_arch_index.py ingesta_ast_v2_mlflow_mlflow_cd1597e989e8.json --repo mlflow/mlflow
```

The 22 projections live in the `arch-index-20261029-batch2` release of the data room; the raw data behind this measurement is a 433-line JSON with `sha256:ff0c2459a62c8276`.

## Single CTA

Before accepting any architecture report — this one included — ask for both numbers: how many modules are inside a cycle and how many depend on one. If it only brings the first, it brings the one that can be discounted.

- The 22 projections: [https://github.com/alexisromtz-lab/platino-data-room/releases/tag/arch-index-20261029-batch2](https://github.com/alexisromtz-lab/platino-data-room/releases/tag/arch-index-20261029-batch2)
- The instrument: [https://alexisromtz-lab.github.io/auditor-toolkit/](https://alexisromtz-lab.github.io/auditor-toolkit/)
- The same piece on dev.to: [https://dev.to/alexisromtz7/casi-la-mitad-del-codigo-de-22-proyectos-depende-de-un-ciclo-y-el-indicador-habitual-premia-al-que-3ecn](https://dev.to/alexisromtz7/casi-la-mitad-del-codigo-de-22-proyectos-depende-de-un-ciclo-y-el-indicador-habitual-premia-al-que-3ecn)
