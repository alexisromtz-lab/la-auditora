---
title: Context economics — the 99.2 %
lede: 99.2 % of an agent's cost is input, not output. Measured across two generations of the same panel: the total moves 28.19 % between runs, the ratio moves 0.06 points. That is why what is sold is a ratio and not a receipt.
date: 2026-11-06
tags: ai, llm, productivity, opensource
cola_slug: red_economia-de-contexto-99-2
fuente: DEPARTAMENTOS/comercial/ARTICULO_ECONOMIA_CONTEXTO.md
lang: en
---

**Rule for this document:** no figure is written by hand. Each one carries the command or the `archivo:línea` that produces it, and any figure without a declared denominator is not published.

---

## 1 · The thesis in one sentence

**The cost of an agent is not in what the model writes; it is in what the call drags along.** Measured over
28 971 real calls across 5 days: `output` is **0.89 %** of consumption. **99.11 %** is `input`
(`REPORTE_TOKENS.md:130`).

Hence the uncomfortable corollary: optimising the model, the prompt or the temperature moves less than 1 % of
the bill. **The remaining 99 % is decided by how many times the history is resent.**

## 2 · The business number: cost per verified task

Not cost per call — cost per **task**, which is the unit in which it is billed and in which the decision is made.

| metric (median per task) | value | n |
|---|---:|---:|
| total consumption of the task (`input` + `output`) | **18 024 682.50** tok | 10 |
| of that, model `output` | **141 574.50** tok | 10 |
| model calls that had to be chained | 217.50 | 10 |
| tokens resent **per** call (carry-over) | 80 032.00 | 10 |

locus: `REPORTE_TOKENS.md:185-188 @ blob 1c09a667 (213 l)` — correct for the generation that §2 freezes; in the live generation the table lives at `:188-197 @ blob bc67c4c5` (see §8.1).

**A task costs 18.02 M tokens. Of those, 141.6 k —0.79 %— is what the model produced.** The rest is the same
story told again two hundred and seventeen times.

Carry-over = `1 − 141 574.50 / 18 024 682.50` = **99.215 %**.

> It is not 95 %. It is 99.2 %. The difference matters: 95 % still allows the fantasy that the remaining 5 %
> —«the real work»— is where the lever is. 99.2 % says there is no such 5 %.

## 3 · How it is reproduced (this is the part that gets billed)

The report is not an opinion with tables. It is a deterministic instrument over evidence from the machine's own
disk:

```bash
git cat-file blob bb7190b0 > /tmp/ttr.json           # el crudo de atribución, congelado por blob
.venv/bin/python tools/reporte_tokens.py --ttr /tmp/ttr.json --md-out /tmp/panel.md   # RC 150 = nominal
```

The verification run of 30-Oct-2026 reproduces `18 024 682.50` and `141 574.50` **exactly**, from blob
`bb7190b0` and not from a lost temporary file. A third-party reader can do the same without asking us for
anything.

**Why this is the commercial part and not the technical one:** any vendor can say «we optimise your context».
What almost nobody can do is hand over the command with which the client checks the figure on their own
machine.

## 4 · The percentage trap: three denominators, three truths

Here is the finding that turns the article into something that does not exist in the agents literature: **the
same saving measures three different figures depending on what it is divided against**, and almost all published
material does not declare the denominator.

Measured case: cutting the profile's tool-schema block from 73 to 22 tools.

| what it is divided against | figure | honest reading |
|---|---:|---|
| the schema block of the profile that features it | **57.9 %** | «I cut the block by 58 %» |
| the `input` of that same profile | **15.4 %** | «I saved 15 % of the input» |
| the `input` of the **whole** corpus | **8.73 %** | «I saved 8.7 % of the spend» |

All three are true. Only the third is «of the total», and it is the smallest. A vendor that publishes the first
as if it were the third is selling a number with a swapped subject — and that error is indistinguishable from a
lie in the contract, even when there is no intent.

The real weighted tax of the schema block is **730 356 952 / 2 472 640 471 = 29.54 %** of the input
(`REPORTE_TOKENS.md:142-160`, sum over calls). Almost a third of the money goes into declaring tools.

## 5 · And pruning is not linear: the tax depends on the set, not on the count

The market intuition —«fewer tools, less cost»— is **false**, and the same panel refutes it:

| tools exposed | `tool_tokens` per call | n |
|---:|---:|---:|
| 98 | 26 109.00 | 343 |
| 97 | **25 818.00** | 933 |
| 94 | **32 768.00** | 1 |
| 22 | 9 464.00 | 416 |
| 21 | **9 173.88** | 205 |

locus: `REPORTE_TOKENS.md:147-160`.

Fewer tools (94) cost **26.9 % more** than more tools (97). And one tool fewer than 22 (that is, 21) costs
**3.07 % less**. The tax is set by the **content** of the block —which schemas, with which description and which
JSON schema—, not by its length in units.

Consequence for whoever is going to buy this: the right question is not «how far can we prune?» but
**«which set, measured, for which task?»**. A contract that promises a percentage per cardinality threshold is
promising something the corpus does not support.

## 6 · What this article does NOT claim (and why saying it makes it sellable)

1. **It does not claim cost per row.** The 99.2 % is the **median of a panel of 200 evaluated commits**, with 10
   attributed tasks. Attribution by link exists but is residual: `por_enlace = 1`, `por_ventana = 199`
   (`REPORTE_TOKENS.md:69`). **We cannot tell a client «your task costs X»**. We can tell them «the median task
   of this panel costs 18.02 M». It is a fleet dashboard, not a per-service receipt, and the receipt is
   the missing product.
2. **It does not claim monetary savings.** The runtime's `cost` field travels with `isByok: true`: a `0.0` there
   means «not billed to this account», not «free». Without rates there are no euros (`REPORTE_TOKENS.md` §8).
3. **It does not claim routing.** The comparison of models by cost is `NO_MEDIDO` for the same reason.

Publishing the limits does not weaken the article: **it is the only way the three figures that are claimed can
be credible.**

## 7 · Closing

The sector measures tokens the way one measures petrol: litres consumed. The difference between that and
economics is knowing **how many of those litres moved the car and how many burned at the traffic light**. In an
agent, the traffic light is the resent context, and in this measurement it is **99.2 of every 100 litres**.

Whoever does not measure the carry-over is not optimising an agent: they are choosing a smaller engine for a car
that does not move.

---

**Full reproducible evidence:** `REPORTE_TOKENS.md` · **Instrument:** `tools/reporte_tokens.py` (RC 150
nominal) · **Frozen raw data:** `crudos/reporte_ttr_20261030.json @ bb7190b0`.

## 8 · The figure has a date (and the ratio does not)

This article was written on one **generation** of the raw data, and it has to be said with a number because the
defect is the house speciality: the producer scans the host's `session-state`, which **grows while it is being
written**, so two runs of the same command on the same day do **not** give the same medians.

| generation | raw blob | `T_total` median | `T_completion` median | calls | carry-over |
|---|---|---:|---:|---:|---:|
| §2 of this article | `bb7190b0` | 18 024 682.50 | 141 574.50 | 217.50 | **99.215 %** |
| live, in the repo | `03e9072b` | 23 105 392.50 | 167 397.00 | 276.50 | **99.276 %** |
| jump between the two | — | **+28.19 %** | +18.24 % | +27.13 % | **+0.061 pp** |

**That jump row is the article's thesis measured against itself.** The absolute moves **28.19 %** depending on
when the command is run; the **ratio moves 0.061 percentage points**. This is exactly why the number being sold
is a proportion and not a total: **a proportion survives regeneration, a total does not.**
Both generations give **99.2 %** and **99.3 %** — and in no case the **95 %** that was circulating. One of the
four columns of §2, `tokens por llamada = 80 032.00`, is identical in both generations: the median of a ratio
stays put even when both its operands move.

Two consequences that are not hidden:

1. **`REPORTE_TOKENS.md:185-188` was overtaken by its own sidecar, and it has already been corrected there.** The
   sidecar of the raw data (`crudos/reporte_ttr_20261030.meta.json`) declared, in the same
   tree, that «la primera generación publicó `18024682.5 / 141574.5` y esta publica `23105392.5 / 167397.0`» and
   that «la cifra que vale es la del crudo con su blob». The report's §7 table published the first one: it was
   measured and corrected in `REPORTE_TOKENS.md` (**commit `45917cec`**), where today it lives at `:188-197 @ blob bc67c4c5` and
   publishes `23 105 392.50 / 167 397.00`. The locus of §2 was not miswritten: it was correct for the blob it cites
   —`1c09a667`, 213 lines— and the neighbouring commit `6d74da06` displaced it, moving the table to `189-192` before
   the correction left it at `190-193`. **This section does not rewrite §2**: §2 is left as it was written,
   with its frozen generation and its blob, so that the difference between the two is auditable instead of invisible.
   It is an **addendum, not a replacement** — now with the dated closing, not with the open debt.
2. **Whoever runs the command today will get a third figure.** The figure is not the product; **the command is**.
   That is why §3 hands over the command and the blob, not the table.

`HUELLA-ARTICULO-ECONOMIA-CONTEXTO-VIGENCIA-20261030
`HUELLA-ARTICULO-COLATERAL-M7-CERRADO-20261030``
