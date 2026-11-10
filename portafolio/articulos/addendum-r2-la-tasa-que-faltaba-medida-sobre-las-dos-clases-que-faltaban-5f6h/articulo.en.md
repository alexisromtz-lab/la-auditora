---
title: Addendum R2 — the missing rate, measured over the two missing classes
lede: Addendum R2 — la tasa que faltaba, medida sobre las dos clases que faltaban    Este artículo...
date: 2026-10-31
tags: security, github, devops, opensource
fuente: https://dev.to/alexisromtz7/addendum-r2-la-tasa-que-faltaba-medida-sobre-las-dos-clases-que-faltaban-5f6h
lang: en
solo_en: si
---

# Addendum R2 — the rate that was missing, measured over the two classes that were missing

> **This article replaces the previous one as a reading** —"Addendum: I corrected my own instrument and the number went
> from 807 to 612": `https://dev.to/alexisromtz7/addendum-corregi-mi-propio-instrumento-y-el-numero-bajo-de-807-a-612-5172`—
> whose body was published **without the Markdown it was written in**: the platform stored the text and discarded the syntax.
> The content is the same; the form is not. It is republished so that what was measured can be read. **The original is still alive and
> unedited**, as a record of what the publishing environment did to it (§9).

**This document does not rewrite the previous one.** The addendum published with `RC 2` and `RC 4`
(`ADDENDUM_ARTICULO_20261030.md`, blob `723dda49`, alive on Dev.to) remains **intact byte for byte**, because a public
act is not corrected by editing: it is corrected by addendum. What follows replaces **only** its section "The rate that was
missing", and only in the part it left open.

Fingerprint of this revision: `HUELLA-ADDENDUM-R2-TPR-RC1-RC5-20261030`. It is declared as code text and not as an
HTML comment for the reason measured in §9.

---

## 1. What was left open, said with the figure next to it

The previous addendum closed the rate of `RC 2` and `RC 4`: **33 cases, 100 % formal, 15.2 % substantive**. And it declared its
own residue on the same page: `RC 1` (60) and `RC 5` (308) still had **no rate**.

That means **368 of the 612 published observations — 60.1 % of the numerator — had no verdict**. A
client asking "what is your false-positive rate?" received an answer that held for 33 cases and was
presented as if it held for 612. That was the weakness, and it was not hidden: it was written down.

**It is no longer open.**

---

## 2. The measurement

Same discipline as last time, and in the same order: **first the prediction, then the reading.**

A pre-registration was written (`preregistro_tpr_rc1_rc5_20261030.json`, 129 lines, blob `05eaead8`) with the substantive
classes, the declared bias and five falsifiers, **before opening a single `run:` or a single `uses:`**. Then the
**163** workflow files of the batch were re-downloaded by `blob SHA` from the GitHub API and their
`sha256` verified against the manifest: **163/163 identical, 0 failures**. The engine reproduced the exact split:
`RC 1` 60 · `RC 2` 30 · `RC 4` 3 · `RC 5` 308.

| class | reading | result |
|---|---|---|
| **`RC 5` REF_MUTABLE** | does the cited `uses:` exist in the raw text and is its ref really floating? | **308/308**, 0 false positives |
| **`RC 1` AUTORIDAD_CONTAMINADA** | does the job have write access and execute code on the same cited line? | **60/60**, 0 false positives |
| **Negative control `RC 5`** | of 1321 `uses:`, **1013** are pinned to 40-character SHAs: how many does the engine flag? | **0 of 1013** |
| **Negative control `RC 1`** | **164** jobs execute third-party code **without** a write scope: how many does it flag? | **0 of 164** |

The two negative controls are the part that matters. An engine that flagged everything would have given 1321 instead of 308, and
174 instead of 60. It does not: **it discriminates in both directions of the conjunction**.

---

## 3. The substantive rate: this is where the number shrinks

Formal 100 % is not the figure that can be sold, and the previous addendum already said so for `RC 2`. For `RC 1` and `RC 5`
the effect is larger, because these two classes **are measured per occurrence and not per risk**.

### `RC 5` — 308 occurrences are not 308 risks: they are **31**

The `RC 5` sweep does not deduplicate. The same action repeated across twenty jobs yields twenty findings. In the 163
files there are **1321** `uses:` values, of which **308** are floating… and those 308 are only **31 distinct
references**. Publishing 308 without saying so would be inflating the numerator through the back door.

| class | occurrences | distinct | what it is |
|---|---:|---:|---|
| **First party** (`actions/*`) | 239 | 17 | movable tag from GitHub over GitHub code. Documented pattern |
| **Third party, floating tag** | 42 | 5 | `pnpm/action-setup@v6`, `dtolnay/rust-toolchain@stable`, `oven-sh/setup-bun@v2`, `rust-lang/crates-io-auth-action@v1`, `vercel/next.js/.github/actions/pr-auto-label@canary` |
| **Floating reusable workflow** | 10 | 6 | a **whole** workflow from another repo executed with this repo's token |
| **Unsubstituted placeholder** | 17 | 3 | see §4 — a class the prediction did not have |
| **Docker image without digest** | **0** | 0 | I predicted 8; there is not a single one in the 10 repos |

**The real third-party surface: 52 occurrences and 11 distinct references** — **16.9 %** of the occurrences and
**35.5 %** of the distinct ones. The other 256 are split into 239 `actions/*`, which for a client is noise (control of the
ref belongs to GitHub, not to the attacker the client fears), and 17 placeholders that do not resolve and are counted as their own
class in §4, not as third party.

> **Correction with a chain (`HUELLA-ADDENDUM-R2-CORRECCION-PORCENTAJE-TERCEROS-20261030`).** The first version of this
> paragraph, written hours earlier and never published, said **22.4 %** and "the other 239". That percentage is correct for 69
> occurrences, not for 52: the sentence had added to the numerator the 17 from `R7`, which are `$/.github/…` paths of the client's own
> repository and therefore are not third-party code. **The table above never said 69; it said 42 + 10.**
> The number in the prose and the one in its own table were not measuring the same thing, and nothing compared them. The wrong
> literal is kept in view because an addendum that corrects figures cannot be edited in silence — that is the same rule that
> brought it into being. The correction travels with the census:
> `INVESTIGACION/evidencia/censo_tpr_rc1_rc5_20261030.json`, field `superficie_de_terceros.correccion_con_cadena`.

### `RC 1` — 60 findings, **10** uphold the name of the code

`RC 1` is called `AUTORIDAD_CONTAMINADA`. The conjunction it measures — write **and** execution in the same job — is
correct and yields 60/60 formal. But only a part of those 60 lines **exercise or hand over** the authority:

| class | n | what it is |
|---|---:|---|
| **A1 — remote write exercised** | 9 | `gh run cancel`, `gh pr comment`, `gh api --method POST`: the token is the instrument of that same line |
| **A2 — download to execution** | 1 | `curl https://rustwasm.github.io/…/init.sh -sSf \| sh` with `id-token: write`: code chosen at runtime, executed with the credential in the environment |
| **A3 — inherits third party** | 28 | `pnpm install`, `cargo build`, `npx -y firebase-tools@15.15.0`, `cargo binstall`, `gh` running with the token available |
| **A4 — local mutation** | 5 | `git config` without push: the authority is declared and not exercised |
| **A5 — code of the repo itself** | 11 | `pnpm run build`, `node scripts/…`: whoever sees the token is the owner of the repo |
| **A7 — lexeme without execution** | 6 | see §4 |

**Authority exercised or handed over: 10 of 60 (16.7 %).** That is the number the word "contaminated" can defend.

---

## 4. The two classes the prediction did not have

On two consecutive days, the same pattern: **the taxonomy falls short and the new class shows up in the same place
where the engine reads well.** Yesterday it was `NO_SUMIDERO` (16 of 33). Today there are two, and both are declared instead of being forced into place.

**R7 — unsubstituted placeholder: 17 occurrences, 3 literals, 3 repositories and 6 files.** The raw bytes
contain local references written with GitHub's template placeholder (`$/…`) that was never substituted:
`$/.github/actions/setup` **5 times, all in `sveltejs/svelte` `ci.yml`**; `$/.github/actions/issues-helper`
**11 times in `vitejs/vite`** —6 in `bot.yml`, 3 in `issue-labeled.yml`, 1 in `issue-close-require.yml`, 1 in
`lock-closed-issues.yml`—; and `$/.github/workflows/notify-resolved-issues.yml` **1 time in `nuxt/nuxt` `release.yml`**.
The bytes are genuine from the origin: the `git hash-object` of the **six** files matches one by one the `blob_sha`
declared by the manifest, so it is not an artefact of the download. **Its severity stays `NOT_MEASURED`**, for the same
reason as `NO_SUMIDERO`: `0` if one reads that a `uses` that does not resolve holds no custody, and "the strongest finding" if one
reads that the file declares an intention it does not execute and whoever audits it will believe it is pinned. Resolving it requires
knowing whether the repo generates that file or commits it as is, and the file does not say.

> **Correction with a chain (`HUELLA-ADDENDUM-R2-R7-POR-ARCHIVO-20261030`).** The previous version of this paragraph, written
> hours earlier and never published, named `facebook/react` as one of the repositories with placeholders. Measured over
> the 163 workflows already verified by `sha256`: `facebook/react` has **26 workflows and zero occurrences**, and the 17
> are in `svelte` (5), `vite` (11) and `nuxt` (1). The count never changed — 17 occurrences, 3 literals — the attribution
> did. It is the third case of the same defect in the day: **a structured field that is correct next to a sentence that is not
> derived from it**, just like the 22.4 % in §5. The correction travels with the census, field
> `clase_no_prevista.correccion_con_cadena`.

**A7 — the lexeme matches while nothing is executed: 6 of 60.** An `echo "  - NPM name: …"` matches the `npm` pattern.
A `yq '.allowBuilds[]=false' -i pnpm-workspace.yaml` matches because the **name of the file** says `pnpm`. It is not a
defect of the engine — its declared domain is lexical per line — but it is noise for a client, and that is why it is counted
separately and published: **it is how a false positive survives the correction of the engine.**

---

## 5. Four defects of the reader, found before publishing

The lesson from last time was applied with a will: **the reader is wrong too, and when it is wrong it declares
the correct instrument guilty.** An independent desk reader, without the engine's parser, found four:

1. `permissions: {}` read as `{'{}': 'write'}` → `RC 1` inflated from 60 to **121** (61 false reds).
2. The job `uses:` counted twice → `RC 5` inflated from 308 to **319** (11 false reds).
3. Quoted permission values (`contents: 'read'`) keeping the quotes → a real job fell out: **59 of 60**.
4. `run:` folded over several lines read only on the first → a cited line appeared truncated.

**All four were the reader's. The engine did not change a single line: its formal output holds 368/368.**

---

## 6. Prediction against measurement, without dressing it up

| prediction (pre-registered) | measured | verdict |
|---|---|---|
| `RC 5`: 308 TP, 0 FP, ±4 | 308 / 0 | met |
| `RC 1`: 60 TP, 0 FP, ±6 | 60 / 0 | met |
| **31 to 60** distinct literals, point estimate 45 | **31** | met **at the edge**, by one literal |
| `RC 5` split: 240 / 55 / 8 / 3 / 2 / 0 | 239 / 42 / **0** / 10 / 0 / **17** | right direction, three deviations |
| Distinct third parties: 12 ± 6 | 11 | met |
| `A1`+`A2`: **9** ± 6 | **10** | met |

Three deviations that are published because they were measured: **the docker image without a digest does not exist** in the 10 repos (I predicted
8), **the floating reusable workflow is triple** what was predicted (3 → 10, and it is the strongest class of the
four), and **a class that was not in the taxonomy appeared** (R7, 17). Point estimate 45 against 31 is not a method failure:
it is the difference between **estimating how many occurrences there would be** and **counting how many distinct references there are**.

---

## 7. What still has no rate, and why it is said

**`SC1` — 211 observations, and they are not all the same thing.** They are not from the gate: they are the substitution and chain count
of the harness itself. This act measures **368 of 612 observations (60.1 %)** — but that denominator is not the one for
**findings**, and confusing them is the defect this addendum already committed once with another figure. Of the 244 without a census,
**156 are `REVIEW` by contract design** (`SC1_JOB_WRITE_SCOPE_REVIEW` 153 + `SC1_ROOT_READ_ALL_REVIEW` 3): they are
inventory, not findings, and there is no rate to assign them because they do not assert a vulnerability. **55 are a real
conjunction** (`SC1_ROOT_PERMISSIONS_MISSING` 36 + `SC1_ROOT_WRITE_INHERITED` 19). And **33 are the corrected class** (`RC 2` 30
+ `RC 4` 3), validated by domain review with a chain, not by census. Over the denominator a CTO would want
— the one for those that assert a vulnerability, **456** — the coverage is **368/456 = 80.7 %**, and what is left to census
is **55 cases, 9.0 % of the total**, not 211. What is published as 60.1 % is still correct as long as the denominator
is "observations"; it stops being so the moment the denominator is "findings".

*Fingerprint of this revision: `HUELLA-ADDENDUM-R2-DENOMINADOR-20261030` (MEDICIÓN CON UNIDAD, applied to its own
statement: the 60.1 % was not wrong, it was measuring another population).*

**And three more residues, declared:** `RC 5` emits `job: '-'`, so it does not say *which* job consumes the action and the
per-job severity stays `NOT_MEASURED`; the engine's own residue still stands (`env:` with secrets + third-party execution
only falls under `RC 1` if there are write scopes); and the substantive reading is a desk reading, over the YAML, without
executing the workflows: it does not measure whether a third-party action is hostile today, it measures whether the ref is pinnable and whether the authority
is exercised.

---

## 8. The sentence that can be published

> **612 observations, of which 456 assert a vulnerability. Census: 368 — 80.7 % of the findings and
> 60.1 % of the observations.** Of the remaining 244: **156 are `REVIEW` inventory** by contract, **55 are a real
> conjunction without a census** and **33 are the corrected class**, validated by domain review.
> Formal TPR **368/368**. Negative control: **1013** pinned refs not flagged and **164** jobs without write not flagged.
> Substantive: **10 of 60** authority findings exercise or hand over the credential; **11 distinct references** of
> third parties across 308 floating-ref occurrences; **17** references that do not resolve — 5 in `sveltejs/svelte` `ci.yml`,
> 11 in **four** workflows of `vitejs/vite` (6 of them in `bot.yml`), 1 in `nuxt/nuxt` `release.yml` — with
> severity `NOT_MEASURED`.

There is no round number and there is not going to be one. What there is, is an instrument that was wrong 195 times, published it,
corrected itself, measured its own rate, found four defects **in its reader** and published those too, and left in plain sight what
it could not measure. That is what a CTO can audit. A "1000 vulnerabilities" is not.

---

## 9. Publishing note: the declared format and the executed format

The previous addendum was written in Markdown and published without it. Measured today against the public API (`GET
/api/articles/4950016`, HTTP 200, `published_at 2026-10-31T00:18:48Z`): the **stored** `body_markdown` contains
**0** `**`, **0** backticks, **0** `|` and **0** `##`. The loss is not in the render: it is in the source.
That is why the format is not recovered by switching modes in the editor — the body has to be rewritten.

And there is a detail that is a mechanism, not an accident: of the **two** HTML comments in the published body, the one that
opened a line lost its `<` (`!-- HUELLA-TPR-MEDIDA…`, visible as text) and the one that came inline behind the `-->`
survived intact (`<!-- HUELLA-NO-SUMIDERO-MEDIDO…`). **Falsifiable rule with `n=1` body: Dev.to removes the first `<`
of a line that starts with `<`; the following ones on the same line survive.** It is not "the start of the body", as
was declared in the first reading: the body starts with text, not with `<`. A single observation is not a rule: it is
published with its `n` and its falsifier.

Operational consequence, applied in this very document: **no fingerprint of this revision travels as an HTML
comment; they travel as code text**, in the header and in the footer. It is the same defect this document measures in the
others: a declared intention — the format, the fingerprint, the `permissions:` — that the execution environment does not execute.

Fingerprint of this section: `HUELLA-ADDENDUM-R2-NOTA-FORMATO-20261030`.

---

*Source of truth for the figures: `INVESTIGACION/evidencia/censo_tpr_rc1_rc5_20261030.json` (blob `a2a7aa26`,
after the two corrections with a chain of 30-Oct-2026) and
`INVESTIGACION/evidencia/preregistro_tpr_rc1_rc5_20261030.json` (blob `05eaead8`), both over the same 163
workflow files with identity verified by `sha256` and `git hash-object`.*

*Fingerprint of this revision: `HUELLA-ADDENDUM-R2-R7-LOCUS-20261030`.*

*Fingerprint of this revision: `HUELLA-ADDENDUM-R2-R7-POR-ARCHIVO-20261030` and `HUELLA-ADDENDUM-R2-DENOMINADOR-20261030`. The
six files with `R7` were verified one by one with `git hash-object` against the manifest; the denominator of 456
comes from `composicion` and from the `SC1` counts of the batch, not from the prose.*
