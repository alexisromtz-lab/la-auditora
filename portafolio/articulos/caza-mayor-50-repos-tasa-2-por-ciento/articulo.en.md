---
title: I swept 50 repositories: two real defects and a 2 % hit rate
lede: I measured 765 workflow files in 50 repos with more than 5 000 stars: 262 steps invoke a test runner and 11 cannot make the workflow fail. The defensible-defect rate is 2 %, and the most severe one sits in the deadest repository.
date: 2026-11-06
tags: devops, ci, github-actions, opensource
cola_slug: red_caza-mayor-50-repos-tasa-2-por-ciento
fuente: DEPARTAMENTOS/comercial/CAZA_MAYOR_20261106.md
lang: en
---

## 0 · Verdict in one line

Of **50** company repositories with CI (≥ 5 000 ★, AI/DevTools/Fintech), **1** today has a CI-signal defect
that I would sign with my name in their repo; the other two targets have a real defect but a different
condition, and here I say which is which instead of selling all three the same.

## 1 · The measurement — the denominator, before the conclusion

| what was measured | magnitude | how it was obtained |
|---|---:|---|
| cohort | **50** repos | 273 candidates from 12 `gh search repos` queries → filter of `awesome`/course/clone lists and > 900 MB |
| workflow files read | **765** | download of `.github/workflows/*` via the API, parsed with PyYAML |
| steps that invoke a test runner | **262** | runner regex (`pytest`, `ctest`, `go test`, `npm test`, `tox`, `make test`, `dotnet test`, `bazel test`, …) |
| steps whose failure **cannot propagate** to the workflow result | **11 · 4,2 %** | `continue-on-error` (step or job) or `\|\| true` / `\|\| exit 0`, **without** a local postcondition **and** without a `needs:` consumer |
| distinct repos with at least one | **5 · 10 %** | `livekit/agents`, `ggml-org/llama.cpp`, `PrefectHQ/prefect`, `raga-ai-hub/RagaAI-Catalyst`, `Arize-ai/phoenix` |
| of those 5, with an explicit declaration of intent | **3** | Prefect calls it `(advisory)` and comments on it (`api-compatibility-tests.yaml:19-21`); llama.cpp leaves the real gate in `e2e-tests`; Arize is a bot workflow (`claude-daily-deps-upgrade.yml`) |
| of the remaining 2, a **live** repo | **1** | `livekit/agents` publishes commits today (`2026-11-06`); `RagaAI-Catalyst` has no commit since `2025-05-16` |

**⇒ Defensible-target rate: 1/50 = 2 %.** Three live targets would require sweeping ~150 repos.

### 1.1 · Self-audit of the instrument (three corrections measured in this turn)

1. **The first classifier was blind to `needs:` gates.** v1 only looked at later steps
   *within the same job*. v2 added `needs:` consumers and `needs.X.result` guards → same
   result (10 vs 10). The number survived, but the argument was not proven until it was tested.
2. **The runner regex was short.** It did not see `make test`, `dotnet test`, `bazel test`, `phpunit`, `rspec`.
   Extended: 262 steps, **+1 repo** (`Arize-ai/phoenix`, bot workflow). The rate moved from 4/50 to 5/50
   and the defensible-target rate **did not** move.
3. **The crawl's «CI pain» ranking was contaminated and is discarded.** It counted runs from fork
   branches and `action_required` (a workflow that never actually executed) as failures. Measured in
   `openai/evals`: **11 of 15** recent runs are `action_required` — hence the `0.99` of the first
   pass. A repo with healthy CI can produce that figure. **The ranking is withdrawn**; it is used in no
   decision in this document.

## 2 · The three targets

| # | repo | ★ | measured pin | defect | locus | severity | live repo |
|---:|---|---:|---|---|---|---|---|
| 1 | `livekit/agents` | 15 107 | `055744e1505b` | the STT suite cannot fail (two layers) | `test-stt.yml:201` | **MEDIUM** | **yes** (commit today) |
| 2 | `raga-ai-hub/RagaAI-Catalyst` | 16 185 | `ab6789331089` | the whole pipeline is advisory + dead output | `ci.yml:12,41,93` | **HIGH** | **no** (last commit 2025-05-16) |
| 3 | `ggml-org/llama.cpp` | 133 519 | `4b77dee0524c` | unit/client tests advisory while E2E does gate | `ui.yml:55` · `build-sanitize.yml:40` | LOW | yes (commit today) |

**The highest-severity target is in the deadest repo.** n=2 does not allow asserting a correlation: it is
published as an observation, not as a law.

## 3 · Target 1 — `livekit/agents` (the only one I sign)

### The defect, verbatim in `test-stt.yml@055744e1505b:201`

```yaml
- name: Run STT tests
  run: |
    uv run pytest -n 3 -v --stt --tb=long --junitxml=test-results.xml 2>&1 | tee test-output.txt || true
```

Two independent layers erase the result:

1. `|| true` turns any non-zero exit into 0.
2. Even if `|| true` is removed, the pipeline ends in `tee`, and in the default bash (no `pipefail`) the
   step status is `tee`'s, which is 0 as long as it can write the file. **Deleting `|| true` outright
   does not restore the gate** — this is what separates a superficial reading from a measurement.

### Why it is probably not what you meant

The later steps are already written to run no matter what (`Generate test summary` and
`Post results to PR` carry `if: always()`), and `pytest --junitxml` writes the XML on failure too. The
`|| true` **is not needed for the report to exist**: `always()` already bought that. The only thing it
buys is that a red STT suite is indistinguishable from a green one in the checks list.

### The contrast that makes the report credible

The same repository already implements the correct pattern in `ci.yml:34-43`: `continue-on-error: true` on
`ruff` **plus** a `Report ruff errors` step with `if: steps.ruff-check.outcome == 'failure' || …` that does
`exit 1`. That is: the house knows how to close a gate. `test-stt.yml` is an inconsistency, not a philosophy.

### Issue text — ready to paste

> **Título:** `ci: Test STT reports green on a failing suite —` || true`plus a`tee` pipeline erase the exit code`
>
> **Body:**
>
> ## What
>
> `.github/workflows/test-stt.yml:201` cannot fail:
>
> ```yaml
> - name: Run STT tests
>   run: |
>     uv run pytest -n 3 -v --stt --tb=long --junitxml=test-results.xml 2>&1 | tee test-output.txt || true
> ```
>
> Two independent layers erase the result:
>
> 1. `|| true` turns any non-zero exit into 0.
> 2. Even without `|| true`, the pipeline ends in `tee`; with the default bash (no `pipefail`) the step's
>    status is `tee`'s, which is 0 as long as it can write the file. So deleting `|| true` alone does
>    **not** restore the gate.
>
> Measured at `livekit/agents@055744e1505b1489976d06ca029b3001bc91ea55`.
>
> ## Why it is probably not what you meant
>
> The steps after it already run regardless of the test outcome (`Generate test summary` and
> `Post results to PR` both carry `if: always()`), and `pytest --junitxml` writes the XML on failure too.
> The `|| true` is not needed for the report to exist — `always()` already buys that. What it buys is
> that a red STT suite looks exactly like a green one in the checks list.
>
> ## Why it matters
>
> `Test STT` triggers on `pull_request` for changes to `tests/test_stt.py` and to its own workflow — the
> PRs most likely to break STT. The PR comment lists per-provider results, but nothing in the merge UI
> does. If this workflow is advisory by design, its name and a comment should say so; if it is a gate,
> it does not gate.
>
> ## Reproduction
>
> ```bash
> git clone --depth 1 https://github.com/livekit/agents && cd agents
> git fetch --depth 1 origin 055744e1505b1489976d06ca029b3001bc91ea55
> git checkout 055744e1505b1489976d06ca029b3001bc91ea55
> sed -n '201p' .github/workflows/test-stt.yml
>
> bash -c 'false | tee out.txt || true';            echo "exit=$?"   # 0  <- || true
> bash -c 'false | tee out.txt';                    echo "exit=$?"   # 0  <- tee, no pipefail
> bash -c 'set -o pipefail; false | tee out.txt';   echo "exit=$?"   # 1  <- lo que falta
> ```
>
> ## Proposal, cheapest first
>
> 1. **Keep the report, restore the signal:** drop `|| true` and run the step with `set -o pipefail`
>    (job-level `defaults.run.shell: bash -eo pipefail {0}`, or `set -o pipefail` inside the `run`).
>    `tee` still writes the log; the step now exits with pytest's status.
> 2. **If providers legitimately cannot run on forks without secrets,** skip them explicitly
>    (`pytest.mark.skipif(not os.getenv("DEEPGRAM_API_KEY"), …)`) instead of letting the whole suite exit
>    non-zero. A skip is honest; `|| true` is not.
> 3. **If the workflow is advisory by contract,** rename it (`Test STT (advisory)`) and leave a one-line
>    comment at line 201 saying so, so the next reader does not "fix" it in the wrong direction.
>
> Happy to send (1) as a PR if that is the direction — I did not want to change CI semantics in a repo
> where the reporting steps clearly have intent.

## 4 · Target 2 — `RagaAI-Catalyst` (serious defect, sleeping repo)

`ci.yml@ab6789331089`, a single workflow for the whole repo:

- `:12` `code-quality` with `continue-on-error: true`, and its steps are `ruff format .` + `ruff check --fix .`:
  **it fixes and does not commit**, on a disposable checkout. The job can neither fail nor leave a trace.
- `:41` the `test` job also with `continue-on-error: true`.
- `:40` the only `needs:` is `test → code-quality`. **Nobody needs `test`** ⇒ the workflow's terminal state
  is advisory.
- `:49` declares `outputs.test_summary` from `steps.pytest.outputs.test_summary`, which is produced at `:94`.
  `grep -rn test_summary .github/` returns **only those two lines**: the output is declared and nobody reads it.
- `:93` `pytest tests/ -v --junitxml=test-results/junit.xml | tee test-output.txt` — without `pipefail` in
  any workflow of the repo (`grep -rn pipefail` = 0). Even if the `coe` is removed, the step stays green.

**Honest diagnosis of the why:** `tests/` includes integration tests that require ~20 secrets; on
forks they cannot pass. The correct answer is to separate markers (`-m "not integration"` for the gate,
integration advisory), not to turn the whole pipeline advisory.

**And the state of the repo:** last commit `2025-05-16`. An issue here **produces no conversation**; it produces
an audit artifact. It is delivered as such, without counting it as a pitch.

## 5 · Target 3 — `llama.cpp` (mild defect in a live repo)

`ui.yml:55` marks the whole `ui-checks` job advisory, which includes `Run Client tests` and `Run Unit tests`
(`ui.yml:100`, `:105`); `build-sanitize.yml:40` does the same with `ctest`. But `e2e-tests` in the same
file does **not** carry `continue-on-error`: there is a real gate for E2E, not for unit/client nor for sanitizers.

It is published as a **design question** («is it intentional that unit/client are advisory while E2E
gates?»), not as an accusation. In a repo with 133 519 ★ and 2 584 open issues, a low-severity issue
competes against noise.

## 6 · Negative controls — what is NOT a defect

| repo | locus | why it is not a defect |
|---|---|---|
| `PrefectHQ/prefect` | `api-compatibility-tests.yaml:19-21` | the job is called `Cloud API compatibility (advisory)` and carries the comment «Keep compatibility and harness failures advisory for contributors» |
| `LMCache/LMCache` | `cpu_device.yml:366` | the file **declares** that there is no `continue-on-error`; all the `\|\| true` are docker/`df` cleanup |
| `Arize-ai/phoenix` | `claude-daily-deps-upgrade.yml` | bot workflow over its own PRs |
| `vibrantlabsai/ragas` | `ci.yaml:126,129` | it only runs `tests/unit`; `tests/e2e` are **32 paths** in `HEAD` and no workflow invokes them (`grep -rn e2e` over its 8 workflows = 0) — **coverage gap, not fail-open**, and the repo has no commit since `2026-02-24`, so nothing is proposed |

## 7 · The expensive finding: the channel is not empty, it is busy

`livekit/agents#8231` (2026-10-29, «unit tests pin Python 3.12 while the package advertises 3.14 support»)
is an outsider's issue, with loci and a proposal — exactly the format of this document. Measured chronology:

| when | what | signer |
|---|---|---|
| 2026-10-29 | `#8231` is opened | `kcncb`, `author_association: NONE` |
| 2026-10-29 13:17 | someone takes it and declares «Slai Agent Runtime assisted» | `huong8373tt-beep`, `NONE` |
| 2026-10-30 02:19 | the original author answers (13 h) — **outsider to outsider** | `kcncb` |
| 2026-10-30 03:10 | `#8252` is opened | `huong8373tt-beep` |
| 2026-11-05 22:45 | `#8252` **closed without merge, by its own author** | `huong8373tt-beep` |

Review recorded on `#8252`: `devin-ai-integration[bot]` and `kcncb`. **Zero maintainer review.**

⇒ The «I audit your CI and tell you about it» channel **has conversation and no conversion**, and whoever
answers is usually another outsider agent. n=1: it is published as an observation with its falsifier — if
across 5 issues of our own in live repos **not one** maintainer reply appears, the observation holds.

## 8 · The corrected strategy

**«The Sniper»** (find the hidden defect in 50 repos and shoot) measured **2 %** live targets.
Its real cost is not the scan: it is that 49 out of every 50 attempts produce nothing and the shot is spent
on a dead repo or on a defect the owner declared on purpose.

**«The Interlocutor»** inverts the load: you do not look for the defect, you enter where **the pain is already
written** and bring the measurement the author does not have. The client declares the pain; the instrument
is the only thing contributed. It applies to the same channel, with the same public signature and a much
lower cost per attempt.

One entry rule: **no comment without a measurement the issue author does not already have**. If the
comment can be written without running anything, it is not written.

Concrete measured queue (open issues, unanswered, about CI/tests):

| repo | issue | state | what would be contributed |
|---|---|---|---|
| `vibrantlabsai/ragas` | #2989 «CI: check-docs fails on every fork PR — pull_request_target»: `claude-docs-check.yml` falls at ~6 s **in the checkout step**, before analysing anything | open, **0 comments** | confirm the block against `actions/checkout` and deliver the minimal diff with trimmed permissions |
| `ggml-org/llama.cpp` | #30281 `test-backend-ops` should exit 1 when a backend is missing | open, 0 comments | confirm with a run and propose the `exit` |
| `PrefectHQ/prefect` | #16404 / #16310 / #15558 flaky tests | open since 2024 | measure the per-test flake rate before opining |

**Note:** `ragas#2989` describes September 2026 runs on a repo whose last commit is
`2026-02-24`. Before commenting you must check that the workflow still exists at that pin; if it does not,
the issue is about another object and commenting on it burns the signature.

## 9 · DMs

**LiveKit — David Zhao.** Verified: `davidzhao` · name «David Zhao» · company `@livekit` · X `davidzh`.
No other handle is used: `russdsa` returns **404** and is not invented.

> Hi David — I spent a day auditing CI signal across 50 company repos in the voice-AI / infra space, and
> one finding landed in `livekit/agents`. `.github/workflows/test-stt.yml:201` can't fail: `|| true` plus a
> `tee` pipeline (no `pipefail`) erase pytest's exit code, so a red STT suite and a green one look
> identical in the checks list. Your ruff steps at `ci.yml:34-43` already do the opposite — they gate via a
> `steps.*.outcome` postcondition — which is why it reads as an inconsistency rather than a philosophy.
> Three-line fix, happy to send it as an issue or a PR, whichever you prefer. I run Platino Labs: we
> audit CI for fail-open guards like this one. No pitch attached — the finding is yours either way.

**RagaAI — `NO_MEDIDO`.** There is no verified founder handle; a name is not fabricated. The §4 finding
is delivered as an artifact, not as a DM.

## 10 · Pointers

| piece | what it is | path |
|---|---|---|
| census instrument | census of fail-open guards over a pinned cohort | ``tools/correr_censo.py`` |
| level-6 probe | the corpus audit engine | ``tools/sonda_nivel_6.py`` |
| pre-write gate | A2.1 | ``tools/gate_pre_escritura.sh`` |
| article recipe | how a finding becomes a public note | [`ARTICULO_DEVTO_AUDITORIA_LITELLM_46923_PUBLICO.md`](ARTICULO_DEVTO_AUDITORIA_LITELLM_46923_PUBLICO.md) |
| publication network | how a note becomes queued | [`PUBLICAR_EN_RED.md`](PUBLICAR_EN_RED.md) |
| measured channel | `Canal público` with no reach · `Canal empresa` with `Sent` = 0 | [`_PLAN.md`](_PLAN.md) §2 · ``_REGISTRO.md`` row 25 |

**Duplication note:** another lane of the tree has `tools/auditar_fail_open_universal.py` in flight
(34 896 B, 2026-11-06T00:49) and `tools/auditar_soft_fail_buildkite.py`. The classifier used here was
ad-hoc in `/tmp/caza/` **before** finding `tools/correr_censo.py` in
``INVENTARIO_INSTRUMENTOS.md``. The numbers in this document are
reconciled against `correr_censo.py --planificar` (pins of 29/50 repos, state `PARCIAL` due to HTTP 403);
the remaining pins were taken with `gh api repos/{n}/commits?per_page=1`.

## 11 · The shots, executed (2026-11-06)

The two public acts of this document went out. There is no third: `llama.cpp` and `RagaAI-Catalyst`
remained as an internal artifact and are not published (§6 and §9 say why).

### 11.1 · `vibrantlabsai/ragas#2989` — technical comment published

<https://github.com/vibrantlabsai/ragas/issues/2989#issuecomment-6679331106>

The issue was still **open, 0 comments, unedited since `2026-09-02T15:16:45Z`**: the comment is the
first one. The workflow was verified to exist at the cited pin before writing (§8 demanded it).

**What the author did not have —measured at `298b68274234c060deacab3cf5fb52aa3a20e885`— and was delivered to him:**

| measurement | value |
|---|---|
| workflows that declare `pull_request_target` | **3 of 8**, and **2** check out the fork's code: the issue names **1** |
| the second one, `claude-docs-apply.yml:21-22` | the most exposed: `permissions: contents: write` (`:12`), token `CLAUDE_CODE_PAT \|\| GITHUB_TOKEN` (`:24`) |
| why that second one is unreachable today | the `check-docs` red kills the checkout **before** the step that sets `needs-doc-update`, and that label is the only trigger of `apply-docs` |
| runs of `Claude Docs Apply` (`216244931`) in its entire history | **0** |
| `allow-unsafe-pr-checkout` in `actions/checkout` | absent in v4.1.7 · v4.2.0 · v4.2.1 · v4.2.2 · v4.3.0 · v4.3.1; **first appearance v4.4.0** (`action.yml:101`) |
| runs of `Claude Docs Check` (`216244933`) | **391**, all from forks: 142 success · 223 failure · 26 cancelled |
| last success | `2026-07-20T11:26:10Z` |
| current red streak | **162 consecutive failures, 0 successes** since `2026-07-20T16:54:58Z` |
| release of `actions/checkout` v4.4.0 | `2026-07-20T15:36:10Z` — **78 minutes before** the first failure of the streak |
| honesty limit | logs older than ~`2026-08-08` expired (`HTTP 410`) ⇒ the cause of the **first** failure is `NO_MEDIDO`; the cause of all readable ones is the checkout guard |

The comment sells nothing, does not link this repo and mentions no services: it signs with `@alexisromtz-lab` at
the foot and declares the pin. The lesson it leaves: **the issue described half the pattern**, and that half was not
visible without running the census on the pin — not without reading the issue.

### 11.2 · `livekit/agents` — Issue published

<https://github.com/livekit/agents/issues/8417>

Title: `ci: Test STT cannot fail — || true and a tee pipeline erase the exit code`. Full body of §3.
Re-verified before firing: at `055744e1505b1489976d06ca029b3001bc91ea55`, `test-stt.yml:201` is

```
uv run pytest -n 3 -v --stt --tb=long --junitxml=test-results.xml 2>&1 | tee test-output.txt || true
```

No duplicate: `gh issue list -R livekit/agents --author @me --state all` returned **0** issues before the
filing. The report survives the channel's bots (§7) because it does not compete for attention: it contributes three lines of
`bash` the reader can run to see the `exit=0` with their own eyes.

### 11.3 · The census that made §11.1 possible

`tools/correr_censo.py` died at **29 pins of 50** because it had no authenticated mode: `token()` only read
`GITHUB_TOKEN`/`GH_TOKEN`, both absent, while `gh auth status` was green — 60 requests per hour
without credentials, 2 per repo = **30 repos per hour**, exactly the ceiling where it stopped. Fixed in
`6a56efa0` with `gh auth token` as a third source, published source and typed absence. Measured in the act,
same cohort: **`PARCIAL` 29/50 → `RESUELTA` 50/50** with `autenticacion.fuente = gh:auth-token`.
Without that fix, the §11.1 table would have stayed at half its rows.

---

---

## 12. What the world answered — interaction census (2026-11-06)

Measured with `gh api "search/issues?q=commenter:alexisromtz-lab"` (39 threads) by reading the comments of each thread, not counting notifications. Census window: up to `2026-11-06T18:15Z`.

### 12.1 The footprint, measured

| foreign repos | threads where we commented |
|---|---|
| `tenstorrent/tt-metal` | **14** |
| `vllm-project/vllm-omni` | **7** |
| `BerriAI/litellm` | 3 |
| `vllm-project/vllm` · `huggingface/transformers` · `huggingface/smolagents` · `astral-sh/uv` · `duetosymmetry/qnm` · `vibrantlabsai/ragas` | 1 each |
| **Total** | **30 foreign threads** (39 with our own 9) |

Of those 30, **13** received later human activity and **6** received a reply **addressed to our comment**, not neighbouring activity.

### 12.2 The humans who answered

| thread | who | what they said | verdict |
|---|---|---|---|
| `livekit/agents#8417` | `iamdgarcia` (CONTRIBUTOR, 6 PRs in the repo) | verified the finding, contributed 2 data points of their own and offered the PR | **conversion** |
| `vllm-project/vllm-omni#9086` | `hsliuustc0106` | `APPROVED`, 4 checks green | **approved, not merged** |
| `vllm-project/vllm-omni#9096` | `hsliuustc0106` | `APPROVED`, 4 checks green | **approved, not merged** |
| `vllm-project/vllm-omni#9129` | `Big2Wheel` | validation on real hardware: Ascend 910B3, image `96fa…` | **external validation** |
| `duetosymmetry/qnm#22` | `duetosymmetry` (maintainer) | «Alexis — I'll happily review a PR that you submit fixing the bug you found» | **invitation** → `qnm#45` |
| `BerriAI/litellm#47340` | `Mrun25` | «Thanks for digging into this, alexisromtz-lab. The TTL-plumbing analysis is a real adjacent gap» | **technical credit** |
| `vllm-project/vllm#62322` | `mosafariuk` | corrected our measurement with the published wheel | **correction accepted** |
| `BerriAI/litellm#46923` | `shaikn6` | «`_has_pre_deployment_request_rewriters` doesn't exist anywhere» | **ghost citation** |
| `tenstorrent/tt-metal#53639` | `kinginu` (PR author) | «ignore comments from @alexisromtz-lab… could you block @alexisromtz-lab from this repo» | **public damage** |

**11 distinct people** interacted: 6 in comments and 5 in reviews or hardware validation.

### 12.3 The interaction rate, against its baseline

| metric | value |
|---|---|
| foreign threads with a reply addressed to us | **6 / 30 = 20 %** |
| foreign threads with any later human activity | 13 / 30 = 43 % |
| big-game baseline (cold, genuine, live issue) | **1 / 50 = 2 %** |
| factor | **≈10×** |

The Interlocutor strategy holds up with the data: commenting where a human is already measuring yields
ten times more than opening a cold issue. What the data does **not** support is that every comment yields:
**1 in every 6 replies was hostility**, and **2 of 9 humans accused the account of citing objects that do not exist**. Both accusations are the same defect, and the defect is ours.

### 12.4 The damage, measured and dated

`tenstorrent/tt-metal#53639`, comments by `kinginu` of `2026-10-20T03:15:49Z` (1 325 car.) and of `2026-10-21T02:51:12Z` (244 car.):

> «Please ignore comments from @alexisromtz-lab. I dont have any connections with this bot.»
>
> «@jberkowitzTT could you block @alexisromtz-lab from this repo, or hide their comments as off topic? I have no connection with that bot, and it keeps stepping into the review conversation.»

**After that request we published two more comments** in the same thread: `2026-10-27T22:23:48Z` (6 077 car.) and `2026-10-27T22:51:14Z` (1 790 car.). A human asked us to leave the thread and we answered with 7 867 characters. That is not a content failure: it is a **listening** failure, and it is the only one on this list that a measurement cannot fix.

### 12.5 The two ghost citations

| thread | the citation that was made | what the human measured |
|---|---|---|
| `BerriAI/litellm#46923` | `_has_pre_deployment_request_rewriters`, `router.py:1062` | 0 repo-wide occurrences at `d7620c77a1`; `router.py:1062` is `_exact_base_model_max_input_tokens()` |
| `duetosymmetry/qnm#22` | `medicion_qnm_cf_tol.py` in the Zenodo record | «I can not find `medicion_qnm_cf_tol.py` at the Zenodo record you pointed to» |

Both were withdrawn — `litellm#46923@2026-10-20T13:55:38Z` withdraws the mechanism, and `qnm#45@2026-10-21T14:59:54Z` records the DOI erratum — but **they were withdrawn after a human found them**, not before publishing them. It is exactly the class the corpus already names (`MEDICIÓN CON BLOB`, `SIN_OBJETO` in `tools/verificar_cita_publicable.py`, A2.2): a cited object that does not exist at the destination.

### 12.6 The two loops that were closed today

1. **`livekit/agents#8417@2026-11-06T18:14:59Z`** (1 881 car.) — reply to `iamdgarcia`. It confirms their two points against `main@055744e1505b` (`pipefail` 0 occurrences in 271 lines; `:201` is the only `pytest` invocation through `tee`; the three following steps carry `if: always()`), corrects the minimal fix — **deleting `|| true` alone does nothing**, because without `pipefail` the pipe status is `tee`'s, which is `0` — and hands them the PR. Verified by read-back: 2 comments in the thread, the second one is ours.
2. **`vllm-project/vllm#62322@2026-11-06T18:15:00Z`** (1 475 car.) — **withdrawal** of half 1 of our comment of `2026-10-19`. Our harness installed a synthetic wheel **by file path**; `mosafariuk` resolves by name with `--extra-index-url`, which is the only branch where `uv` rejects a `Requires-Dist` with a URL. What we measured was our reconstruction of METADATA, not the artifact people install. The `triton @` of `requirements/cpu.txt:25-26` gated by `platform_machine == "x86_64"` explains the x86_64/aarch64 asymmetry with nothing else. Verified by read-back: 3 comments, the third one is ours.

### 12.7 Policy that comes out of this day

- **`tenstorrent/tt-metal`: zero writes.** A PR author asked that the account be blocked in that repo. The resolution is not a message — any new message is the conduct that motivated the request. The thread is left as it is and not revisited.
- **No foreign comment is published with a symbol, a path or a file that has not been read in the destination repo and at the declared commit.** Both ghost citations would have been stopped by the same probe that already runs on our commits (A2.2), which today has no authority over the mouth.
- **Open loops are closed or declared.** One remains declared: `BerriAI/litellm#47340`, `Mrun25`'s repro of `2026-10-20T04:25:18Z`, without our reply.
