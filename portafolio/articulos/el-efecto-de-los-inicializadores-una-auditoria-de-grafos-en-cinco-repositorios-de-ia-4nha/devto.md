---
title: "The initializer effect: a graph audit of five AI repositories"
published: false
description: "Ablación de expansión de __init__.py en cinco snapshots Python; sensibilidad de SCC en grafos estáticos, no una puntuación de riesgo."
tags: p, y, t, h
canonical_url: "https://alexisromtz-lab.github.io/la-auditora/portafolio/articulos/en/el-efecto-de-los-inicializadores-una-auditoria-de-grafos-en-cinco-repositorios-de-ia-4nha/"
---

# The initializer effect: a graph audit of five AI repositories

**Date the analysis was published:** 28 October 2026. This is a descriptive measurement of five Python packages selected on purpose. It is not a ranking of the five biggest startups, and it is not a statistically representative sample.

## Introduction

Platino Labs published a reproducible import-graph analysis of five projects in the AI ecosystem. The [Data Room v2](https://github.com/alexisromtz-lab/la-auditora/releases/tag/arch-index-20261028-v2) contains the calculator, the five public `graph-input/1` projections and the sensitivity results. The [Release v1](https://github.com/alexisromtz-lab/la-auditora/releases/tag/arch-index-20261028-v1) keeps the methodology and the base results, including the commits evaluated.

The question is bounded: **how much does the static import graph change when only the expansion into ancestor `__init__.py` files is omitted?** We do not measure vulnerabilities, overall quality, business risk or run-time behaviour.

## Main finding: LangChain changes under ablation

In the `langchain` snapshot, the base graph contains **2 cyclic strongly connected components (SCC)**; the largest one holds 19 modules. When you keep the resolved direct destinations and omit only the ancestor expansion of `__init__.py`, the projected graph contains **0 cyclic SCC**.

This proves that the result of the static graph is sensitive to that edge-construction rule. It **does not prove** that the cycles disappear at run time, that packaging is the root cause, or that a performance defect exists. The ablation identifies a question for a later dynamic audit; it does not answer it.

LlamaIndex shows another shape: **4 cyclic SCC** persist in both graphs, although the largest one goes from **334 to 239 modules** inside a universe of 480 modules. The largest cycle shrinks, but it does not disappear. Nor is that, by itself, a measure of risk or technical debt.

## What the ablation removes, exactly

The obvious objection — "maybe the collapse from 2 to 0 is an artefact of the edge-construction rule" — can be measured instead of argued. On the same projection, the ablation removes **66 edges** across **25 of the 40 modules**.

And the cycles do not live in the initializer layer: the largest SCC has **19 modules, of which 17 are real modules** (`agents/factory.py` and sixteen `agents/middleware/*.py`) and only 2 are `__init__.py`. The second SCC has 3 modules: `mcp/adapter.py`, `mcp/tools.py` and `mcp/__init__.py`.

That the removed edge is real is not a convention of the calculator. In Python, importing a descendant executes the `__init__.py` of its ancestors: when you import `langchain.agents.middleware.pii`, the trace of `python -X importtime` shows `langchain`, `langchain.agents` and `langchain.agents.middleware` executed. That is exactly the `child → ancestor __init__` edge that the ablation suppresses. In an environment without `langchain-core` the import never completes, and that does not change the datum: the three ancestors already ran before the failure.

**Consequence, and it corrects the easy reading of the headline:** the **ablated** graph is the one that drifts away from Python's behaviour, not the base graph. The 0 describes what would happen if the `__init__.py` files were not executed when importing a descendant; it does not describe `langchain`. The conclusion of the previous section — that the measurement describes a property of the static graph and not a defect — still stands, but "2" is the faithful reading and "0" is the hypothetical one.

Membership of each SCC is recomputed with the `strongly_connected_components` function of the published calculator, applied to the projection whose SHA-256 is quoted above: the datum does not depend on a private instrument.

## Results per snapshot

| Repository / package | Commit measured | Base SCC | LOC | SCC / 10,000 LOC | SCC without initializer expansion | Largest SCC size: base → ablation |
|---|---|---:|---:|---:|---:|---:|
| [vLLM](https://github.com/vllm-project/vllm) · `vllm` | `7e3e3f6ab652550fdefecd8e9823394fd8e51950` | 23 | 959,216 | 0.240 | 8 | 1,648 → 1,394 |
| [LangChain](https://github.com/langchain-ai/langchain) · `langchain` | `facf2788ae1f60c62f2397d15698237c405a5f05` | 2 | 13,352 | 1.498 | 0 | 19 → 0 |
| [Transformers](https://github.com/huggingface/transformers) · `transformers` | `95bafdcccfffe17ec383999fc39273867b11385e` | 8 | 996,643 | 0.080 | 6 | 176 → 169 |
| [BentoML](https://github.com/bentoml/BentoML) · `bentoml` | `0aa1aea52b63b82100ff93675eff25f6428fb841` | 5 | 38,508 | 1.298 | 4 | 78 → 42 |
| [LlamaIndex](https://github.com/run-llama/llama_index) · `llama_index` | `619d74664e8404612038bc15a1a40c686037277c` | 4 | 61,322 | 0.652 | 4 | 334 → 239 |

> **What is verified and what is not, in these five rows.** The numbers are computed over the `graph-input/1` projections of Release v2. The `langchain` projection used here has SHA-256 `5733904a58211822291827c58f5104b013626acc6ef186aad4c569d77d71ff17`, identical to the published asset. The `--graph-sensitivity` mode **does not re-hash the source files** and declares `source_bytes_verified: false`: what is verified is the integrity of the distribution (the hash of the projection), **not** the correctness of the extraction. For the path with verification against the sources, use Release v1 and its commits.

LOC counts physical lines with Python tokens and excludes comments and blank lines. Density is `cyclic SCC / LOC × 10,000`; it serves to describe these snapshots, **not** as a quality score or as a probability of failure. The sample was selected on purpose and does not allow inferring prevalence across the whole industry.

## Reproducible methodology

The calculator builds a directed graph of Python modules and obtains its SCC with Tarjan's algorithm. An SCC counts as cyclic if it contains more than one module or a self-loop. `type_checking` imports are excluded; the other types included in the projection are kept.

To reproduce the ablation, download the assets of [Release v2](https://github.com/alexisromtz-lab/la-auditora/releases/tag/arch-index-20261028-v2) and run, with Python 3.10 or later:

```bash
python3 calculate_arch_index.py public_graph_bentoml_0aa1aea5.json --graph-sensitivity > graph_sensitivity_bentoml.json
python3 calculate_arch_index.py public_graph_langchain_facf2788.json --graph-sensitivity > graph_sensitivity_langchain.json
python3 calculate_arch_index.py public_graph_llamaindex_619d7466.json --graph-sensitivity > graph_sensitivity_llama_index.json
python3 calculate_arch_index.py public_graph_transformers_95bafdcc.json --graph-sensitivity > graph_sensitivity_transformers.json
python3 calculate_arch_index.py public_graph_vllm_7e3e3f6a.json --graph-sensitivity > graph_sensitivity_vllm.json
```

Every result includes the SHA-256 of the bytes of its input projection. The projections omit code snippets and local roots; **the `--graph-sensitivity` mode does not re-hash the source files** and declares `source_bytes_verified: false`, as warned next to the results table. To reproduce the base results with verification against the sources, follow the instructions and the full commits of Release v1.

## Why it matters — and what it does not claim

Cycles and the size of their components describe a topological property of the computed static graph. They can orient a review of boundaries between modules and later tests, but these data do not measure load times, import failures, testing complexity, vulnerabilities or technical debt. To claim any of those things you need specific instruments, windows and controls.

## CTA

Do you lead engineering and want to understand the dependency structure of your own system? [See Platino Labs' work on GitHub](https://github.com/alexisromtz-lab/la-auditora) and request an evaluation bounded to your repository, commit and research question.

---

**Addendum · 2026-10-31.** A reader pointed out that the warning `source_bytes_verified: false` lived in the methodology section and not next to the numbers. It was moved to the table block, and a measurement of what the ablation removes was added (66 edges across 25 of 40 modules; 17 of the 19 modules of the largest SCC are real modules) so that the figure of 0 SCC is not read as a property of `langchain`. The CTA destination was also fixed: it pointed to a private repository and returned 404 to any anonymous reader.

## The run-time objection, answered with the interpreter

The warning above says that these numbers describe a static graph. The question that follows — and it is the
right one — is whether the cycle exists at run time or only in the graph. It was measured with `python -X importtime` on the
published projection:

```text
import time:      2414 |       2414 |       langchain
import time:     24984 |      55275 |       langchain.agents.factory
import time:      4025 |      61714 |     langchain.agents
import time:      36 |      61749 |   langchain.agents.middleware
import time:       47 |      61795 | langchain.agents.middleware.pii
```

The indentation is the causal chain: importing the child executes its three ancestors. (The import does not complete in an
environment without `langchain-core`; the ancestors ran before the `ModuleNotFoundError`, and that is exactly
the point: an import that fails is still evidence of the edges that precede the failure.)

With that, the consequence inverts the easy reading of the headline. The **ablated** graph is the one that drifts from the
interpreter: the `0` describes what would happen if the `__init__.py` files were not executed when importing a descendant, and the
`2` is the faithful reading of `langchain` at that commit. The ablation does not erase the cycles because they are in the
initializers — 17 of the 19 modules of the largest SCC are real modules — it erases them by removing the 66 expansion
edges that Python does execute.

The objection produced the measurement, and the measurement moved the conclusion. That is the best use a comment can
have.

<!-- HUELLA-ARTICULO-INDICE-ARQUITECTURA-20261028 -->

<!-- HUELLA-ARTICULO-RESPUESTA-EJECUCION-20261031 -->
