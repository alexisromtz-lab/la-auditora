---
title: "Addendum: the number was 807, then 612 — and why I published both"
published: false
description: "Sobre: El hackeo de $6.3B no fue un bug de código (Dev.to, id 4949662, publicado 30-Oct-2026..."
tags: security, devops, opensource, github
canonical_url: "https://alexisromtz-lab.github.io/la-auditora/portafolio/articulos/en/addendum-corregi-mi-propio-instrumento-y-el-numero-bajo-de-807-a-612-5172/"
---

**About:** "[The $6.3B hack was not a code bug](https://dev.to/alexisromtz7/el-hackeo-de-63b-no-fue-un-bug-de-codigo-4gah)" (Dev.to, id `4949662`, published 30-Oct-2026 21:58:55Z).
**Fingerprint:** `HUELLA-ADDENDUM-CORRECCION-MOTOR-20261030`

The article states that **807 of the observations across ten repositories are not 807 vulnerabilities**, and names **228**
of them as coming from **two codes of the instrument itself that detect the mechanism, not the defect**. That paragraph was
honest and still is. What was missing was the next step: **if the code detects the mechanism and not the defect, the
code was wrong.** I fixed it. This addendum publishes the exact figure, because silently correcting an already published
number is the same class of fraud as inflating it.

---

## What was wrong (two domain defects, not two thresholds)

**1. `GATE_RC_4_SECRETO_EXPUESTO` measured usage, not leakage.** It flagged `${{ secrets.* }}` in `env:` — global or job level —
and in `with:`. Those are **the two sanctioned mechanisms** for handing a secret to a step without letting it into the body of the
script: flagging them as a finding was marking the correct way to use it as a leak. **Domain corrected:** `RC 4` measures the
interpolation **inside `run:`**, the only case where the value enters a shell line and can end up in a log.

**2. `GATE_RC_2_SUMIDERO_IMPUDO` treated the absence of `download-artifact` as if it were the sink.** A job with
`id-token: write` that materialises no tree, invokes no dynamic tool and restores no cache **executes nothing**: the
invariant held vacuously and the finding was the shape of a job that consumes nothing. **Domain corrected:** `RC 2`
measures the presence of the tree or of its dependencies (checkout, `npx`/`pipx`, or `actions/cache` **instead of** the
artifact — the cache is not authenticated against the build of the same run, and that is a broken chain of custody).

---

## The exact number

| | before | after |
|---|---:|---:|
| Gate observations | 596 | **401** |
| `SC1_*` (permission surface) | 211 | **211** |
| **Total** | **807** | **612** |
| `RC 4` (secret exposed) | 152 | **3** |
| `RC 2` (impure sink) | 76 | **30** |
| `RC 1` (contaminated authority) | 60 | **60** |
| `RC 5` (movable ref) | 308 | **308** |

**Removed: 195 observations** (149 from `RC 4`, 46 from `RC 2`). **Not 228: 228 was the size of the class, 195 its
contribution** — the rest of the class was already falling out through other conjunctions. The codes that hold the thesis up (`RC 1`,
`RC 5`, `SC1_ROOT_WRITE_INHERITED`) **did not move**: the correction removed noise, not criteria.

The delta is not estimated: the **163 workflows** of the batch were loaded once, anchored by `blob_sha` + `sha256`,
and were run **against the previous engine and the corrected one in the same run**.

---

## And the headline shrinks while the thesis gets stronger

- **807 observations, 115 with the conjunction** → **14.2 %**.
- **612 observations, 115 with the conjunction** → **18.8 %**.

The proportion of what the article defends **went up 4.6 points** because noise was removed from the denominator. **The falsifier
did not move:** 10 out of 10 repositories still have at least one authority conjunction, and the three readings of the falsifier
(A 10/10, B 6/10, C 4/10) remain identical. What changed is the instrument; the thesis still stands on the same code
as before the correction.

---

## The method, so that it can be repeated or taken apart

1. **Pre-registered prediction before touching the engine** — the independent census of the surface predicted `RC 4` = 4
   and `RC 2` = 30. Measured: `RC 4` = **3** (the census counted job rows; `RC 4` emits one finding per job, and a job in
   `withastro/astro` had two steps with a secret), `RC 2` = **30**. The prediction missed by one and the miss is
   published in the record, not deleted.
2. **Reproduction of the 807 as a control** over the same bytes before correcting: 596 + 211 = 807, exact. An engine
   that does not reproduce its own published figure cannot measure its correction.
3. **The test bench was part of the defect.** The positive case of `RC 4` asserted `RC 4` on `env:` — that is, the bench
   *endorsed* the defect. It was rewritten, and **three negative controls that make the old behaviour fail** were added:
   sanctioned `env:` → 0 findings, sanctioned `with:` → 0, job without a tree, dynamic tool or cache → 0. `--self-test`:
   **8 → 11 cases**, `RC 0`.
4. **Residue declared, not hidden:** a job with `env:` carrying secrets that executes third-party code only falls under
   `RC 1` if it also declares write scopes; outside that case the combination stays **OUT OF MEASUREMENT**. The
   narrowing is accepted in exchange for removing 195 observations that were not a defect.

---

## The rate that was missing

The TPR of `RC 2` and `RC 4` is already measured, and measured on the current engine. It is not a sample: it is a **census** of the
whole class, because the residual population was 33 findings and sampling 20 of 30 would have saved nothing.

Before opening a single job body, a pre-registered prediction was written, so that the result would not be post-hoc.
Then the **163** workflow files of the batch were re-downloaded and their `sha256` verified against the manifest:
163 identical, 0 failures. The corrected engine reproduced **401** exact gate findings over those bytes
(`RC 1` 60 · `RC 2` 30 · `RC 4` 3 · `RC 5` 308). The population is reproduced, not remembered.

| reading | question | result |
|---|---|---|
| **Formal** | does the shape the engine reports exist in the raw YAML? | **33/33**, 0 false positives |
| **Negative control** | the 46 `RC 2` the old engine emitted and the corrected one removed, do they read as *without shape*? | **46/46**, 0 red |
| **Substantive** | of those 33 shapes, how many are a broken chain of custody? | **5/33** (15.2 %) |

The negative control is the part that matters and the part almost nobody publishes: without it, a high TPR only proves that the reader
agrees with itself.

**The figure that cannot be published as "vulnerabilities" is 612.** Of the 30 residual `RC 2` findings, **20 emit
only the `actions/checkout` reason** — and `actions/checkout` next to `id-token: write` is the shape of *every* correct
OIDC workflow: the checkout is a requirement of the pattern, not its defect. The false positive did not disappear with the correction:
**it changed form**. Before, the engine read badly (228 spurious observations); now it reads well a shape that is not a defect.
Saying "612 vulnerabilities" would still be an error, and this addendum does not say it.

And **16 of the 33** (48 %) are a finding of another class, which the prediction itself had not foreseen: `NO_SUMIDERO`. The
job declares `id-token: write` and **no step consumes that authority**. It does not publish, does not sign, does not attest. The authority
is granted and not exercised. The taxonomy of the prediction did not have that class; it is declared as a gap in the prediction, not
as a finding forced into place.

**That class is not assigned a severity, and the reason is declared: its value is `NOT_MEASURED`.** We do not know whether it is worth `0` — the
authority granted to a job that does not use it is surface without an act, and surface is not a defect by itself — nor whether it is
**the strongest finding of the batch**: a short-lived OIDC token that nobody consumes is still a credential issued
against the registry, and least privilege is measured by what the credential *can* do, not by what the YAML *uses*. Both
readings are defensible on the same bytes and neither is measured. Writing a severity here would be inventing it;
writing `0` would be reading `not measured` as zero. It stays open and in plain sight, in the same document that does close the figures
it could close.

**Two defects of the reader were found and corrected before publishing any figure.** The first gave 45/46 on
the negative control, because a comment at the end of a job key (`test-dev: # TODO`) broke the anchor. The second
gave 30/33 in the formal census, because a comment at the end of a permission (`id-token: write # OIDC`) broke the test.
Both, had they been published, would have "proven" that the engine was wrong when the error belonged to whoever read it. They remain
written here because the path counts.

What is still unmeasured does not change shape, only size: `RC 1` (60), `RC 5` (308) and the `SC1` codes (211)
**still have no rate**. And the four blind spots of the instrument are still there: default permissions of `GITHUB_TOKEN`,
OIDC policies of the destination registry, native code not isolated at runtime, and reusable workflows hosted in foreign
repositories.

---

**Verifiable evidence.** The six artefacts are published in a public release, each with the blob this text declares:

- [`gate_workflows_ci.py`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/tpr-motor-corregido-20261030/gate_workflows_ci.py) — blob `bc5f83ca`, 711 l: the instrument of the measurement.
- [`preregistro_correccion_motor_20261030.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/tpr-motor-corregido-20261030/preregistro_correccion_motor_20261030.json) — blob `47dfc620`, 43 l.
- [`preregistro_tpr_motor_corregido_20261030.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/tpr-motor-corregido-20261030/preregistro_tpr_motor_corregido_20261030.json) — blob `7e66dac0`, 73 l: the prior prediction.
- [`censo_tpr_motor_corregido_20261030.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/tpr-motor-corregido-20261030/censo_tpr_motor_corregido_20261030.json) — blob `2308ecbc`, 507 l: the census, 33 findings, their class, their locus and their negative control.
- [`lote_autoridad_10_repos_20261030_post_correccion.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/tpr-motor-corregido-20261030/lote_autoridad_10_repos_20261030_post_correccion.json) — blob `a2b3b5c2`, 1361 l: the measurement after the correction.
- [`lote_autoridad_10_repos_20261030.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/tpr-motor-corregido-20261030/lote_autoridad_10_repos_20261030.json) — blob `1bef96a8`, 238 l: the previous measurement, **superseded, not deleted**.

Full release, with the table of blobs and sizes:
[tpr-motor-corregido-20261030](https://github.com/alexisromtz-lab/platino-data-room/releases/tag/tpr-motor-corregido-20261030).

The pair `1bef96a8` / `a2b3b5c2` is published side by side on purpose: a corrected instrument is demonstrated by showing the old
number next to the new one, not by replacing it.

**Addendum · 2026-10-31 — two defects of this very addendum.** The first: the evidence was cited by path in a
private repository, unreadable for anyone without access. A path without a URL is not evidence: it is a claim with an inaccessible
locus. Now every artefact is a link that answers 200 without a session, measured. The second: the marker that closed
the text was published **broken** — the leading `<!--` was lost on publishing — and the rest stayed in view as a line of
junk at the end of the page, verified in the served `body_html`. Both fingerprints remain here, written in a way that
no markdown sanitiser can mangle.

*Fingerprints: `HUELLA-TPR-MEDIDA-ADDENDUM-20261030` · `HUELLA-NO-SUMIDERO-MEDIDO-ADDENDUM-20261030`*

HUELLA-ADDENDUM-EVIDENCIA-VERIFICABLE-20261031
