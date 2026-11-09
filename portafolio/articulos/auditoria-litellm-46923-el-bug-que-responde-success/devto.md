---
title: "The bug that answers SUCCESS: a reproducible audit of litellm#46923"
published: false
description: "Six arms, an HTTP server that records the real payload and a negative control. How to audit a framework defect without mocks, why the candidate patch makes the synchronous path worse, and why the dangerous state is the one that looks like success."
tags: devops, git, productivity, opensource
canonical_url: "https://alexisromtz-lab.github.io/la-auditora/portafolio/articulos/en/auditoria-litellm-46923-el-bug-que-responde-success/"
---

A program that fails is easy to audit: it returns an error, you read it, you fix it.

The expensive problem is the opposite one. The program **finishes fine**, writes `SUCCESS` to the log, and along the way it skipped the guard that was supposed to protect you. No trace, no exception, nothing to look for. Just an enormous request that went out raw to the provider.

That is what we found in [`BerriAI/litellm`](https://github.com/BerriAI/litellm) `#46923`, and what this article tries to show is not the bug: it is **how it is measured**, so that the bug is not an opinion.

Everything that follows has a command, a commit and a witness.

---

## 1. The instrument trap (the one you had to find before believing anything)

The first rule of an audit is that the instrument is not the object. Here the instrument was lying for a one-line reason:

```
cd /tmp/litellm
/tmp/venv_lit103/bin/python -c "import litellm; print(litellm.__file__)"
  -> /private/tmp/litellm/litellm/__init__.py
```

Running from the clone root puts **the tree in `sys.path[0]`**. The package installed in the virtualenv **is never imported**. Any measurement with `PYTHONPATH=/tmp/litellm` measures the tree (`1.107.0` plus a local patch), not the version the report declares.

The label «probado en `1.103.0`» was not backed by the command.

The fix is not `PYTHONPATH` — it is taking the instrument out of the tree:

```
cd /tmp && /tmp/venv_lit103/bin/python -c "import litellm; print(litellm.__file__)"
  -> /private/tmp/venv_lit103/lib/python3.14/site-packages/litellm/__init__.py
VERSION_MEDIDA 1.103.0
```

An instrument that does not print **where** it imports from is not measuring: it is quoting.

---

## 2. Six arms, a server that is a witness

`REPRO_46923_V4.py` (181 lines) starts a local HTTP server that **records the payload it receives**. No mocks: the server is the witness. If the request went out raw, you see it in the body that arrived.

Declared parameters: `WINDOW = 1000`, prompt `"hello " * 3000` (≈ 6 000 raw tokens, 18 000 characters).

Arms: **A** `acompletion` with checks ON + hook · **B** `acompletion` with checks OFF + hook · **C** `acompletion` with checks ON and **no** hook (control) · **D** synchronous `completion` ON + hook · **E** synchronous OFF + hook · **F** synchronous OFF with no hook.

### `litellm==1.103.0` — site-packages, instrument out of the tree · `RC=0`

| arm | path | checks | result | hook executed | hits | payload |
|---|---|---|---|---|---|---|
| A | `acompletion` | ON | `RAISED ContextWindowExceededError` | NO | 0 | — |
| B | `acompletion` | OFF | `SUCCESS` | **YES** | 1 | `'short'` (5 chars) |
| C | `acompletion` | ON (no hook) | `RAISED ContextWindowExceededError` | NO | 0 | — |
| D | `completion` | ON | `RAISED ContextWindowExceededError` | NO | 0 | — |
| E | `completion` | OFF | `SUCCESS` | **NO** | 1 | **raw (18 000 chars)** |
| F | `completion` | OFF (no hook) | `SUCCESS` | NO | 1 | raw (18 000 chars) |

The four rows of the public report are backed by **A · B · D · E**.

And on a clean `HEAD` (`d7620c77a1eb`, version `1.107.0`, extracted with `git archive HEAD litellm`, 79 MiB): **identical arm by arm**. The defect is not a version problem.

---

## 3. The cause is not «compression that never arrives»: it is an unreachable hook

The easy reading is that the compression hook fails. It does not fail: **it does not exist on the synchronous path**.

```
grep "def pre_call_deployment_hook"  ->  0 ocurrencias
```

There is only `async def async_pre_call_deployment_hook` (`integrations/custom_logger.py:280`, called from `utils.py:1543` and `utils.py:2078`). **There is no synchronous sibling.** In `Router.completion` you cannot await a coroutine, so the hook never runs and the raw payload goes out to the provider.

A vocabulary detail that changes the diagnosis: it is not «compression that never arrives». It is **a structurally unreachable hook**.

---

## 4. The negative control that corrects the easy reading

Arm **C** is the one that gave the most information, and it is the one almost nobody runs: `acompletion` with checks ON and **no** registered hook.

Result: `RAISED ContextWindowExceededError`.

That is: **the check does work**. The defect is not «the check is never useful», it is «the check decides on the raw payload when a hook could have reduced it». Without arm C, the article would have said the opposite with the same confidence.

A test bench with no positive control only proves that the instrument can say *no*.

---

## 5. The retraction that does not reproduce

Here comes the uncomfortable part, and I include it because it is the method.

In the same thread I published a **retraction**: I claimed to have measured `main @ d7620c7`. When I measured it:

```
                                         HEAD limpio d7620c7      árbol /tmp/litellm
_has_pre_deployment_request_rewriters           0 ocurrencias            2 ocurrencias
litellm/router.py                                       16 171 líneas      16 200 líneas
git status --porcelain -- litellm/router.py               (limpio)              M
```

The function my retraction cited **does not exist in the commit it claimed to have measured**: it is the one the **candidate patch adds**. The line number I cited belonged to the patched tree (+29 lines), and the `WARNING router.py:13931` only shows up there.

The retraction was a measurement over the wrong tree. It was published, it was measured against the object, and the discrepancy was declared — the history was not edited.

---

## 6. The candidate patch fixes A and makes D worse

The patch that exists today in the thread: **47 lines · 2 331 B · SHA16 `210bdc4c91cfdddd`**, applies with `patch --dry-run -p1` → `RC 0` on a clean `HEAD`. It is not upstream: it is a local proposal.

Measured in the patched tree:

| arm | before | after |
|---|---|---|
| A | `RAISED` | **`SUCCESS`** + `WARNING router.py:13931` |
| D | `RAISED` | **`SUCCESS` with a raw payload of 18 000 chars** |

Its condition `_has_pre_deployment_request_rewriters()` **skips the local rejection without telling the paths apart**. On the synchronous path there is no hook that could run, so the only guard is lost and the over-window request goes out raw, **with no error and no compression**.

A patch that improves one arm and degrades another is not a half-done patch: it is a **behavior change** the original report did not declare.

---

## 7. The sibling defect: a `ttl` that is computed and never read

In `#47340` the pattern repeats in another shape. The rate limiter computes the counter expiry:

```
parallel_request_limiter_v3.py:1391-1397
  key=counter_key, increment_value=total_tokens, ttl=self.window_size
```

And the in-memory path throws it away:

```
in_memory_cache.py:255-264
  await self.async_increment(increment["key"], increment["increment_value"], **kwargs)
```

`increment["ttl"]` **is never read**. Identical in `HEAD` (`1.107.0`, l. 266-273). The default window is **60 s** (`LITELLM_RATE_LIMIT_WINDOW_SIZE`).

Meanwhile, the Redis branch **does** honor it: `redis.call('SET', …)` followed by `EXPIRE counter_key window_size` and `if ttl > 0 then EXPIRE counter_key ttl`.

Two doors, one and the same contract: **one honors it and the other throws it away without warning**. Whoever deploys with Redis does not see the bug; whoever deploys in memory does. The configuration decides whether the defect exists for you.

---

## 8. What this audit does **not** claim

- It does **not** reproduce the case from the original report (267 860 raw tokens against a 262 144 window). The instrument uses `WINDOW=1000` and a prompt of ≈ 6 000 tokens: it measures **the order**, not that magnitude.
- The figure «*sends 500 tokens raw*» on published row 4 **has no command backing it in this instrument**: here the synchronous arm sends **18 000 characters**. The discrepancy is declared, not adjudicated: they are two different instruments.
- The effective default of `default_ttl` in `1.83.10` **was not measured**: what was measured is `base_cache.py:23` (60) and the handler's default in `HEAD` (600).
- The patch is **not** merged and no PR was opened with it.

An audit with no limits section is advertising.

---

## 9. The pattern, which is the only thing that can be generalized

The three cases in this article are not three bugs: they are **one and the same law**.

| case | how it looks from outside | what actually happened |
|---|---|---|
| `sys.path[0]` | «probado en 1.103.0» | 1.107.0 + patch was measured |
| arm E | `SUCCESS`, 1 hit | raw payload to the provider |
| memory branch | counter created | no window expiry |

**The dangerous state is the one that looks like success.** And that is why the instrument that detects it cannot be an `assert` that does not fail: it has to be a guard that **denies the write before touching the file**.

That is exactly the shape of the gate we use to audit without dirtying anyone's tree. Before writing a line it demands a target tuple —absolute `TARGET` · `BLOB_PRE` · exclusive mark · previous lines— and returns a code that authorizes or blocks:

| RC | meaning |
|---:|---|
| `0` | correct pre-flight: the target accepts an edit over `BLOB_PRE` |
| `10` | the object does not exist (creation) |
| `11` | **the mark already lives in the target** ⇒ collision: the row is already written |
| `12` | the measured blob is not the contracted one ⇒ the tree moved |
| `13` | dirty git state ⇒ unadjudicated modifications |
| `14` | the target is not inside a git tree ⇒ the gate cannot verify identity |
| `15` | the line count does not match the contract |
| `20` | wrong usage (incomplete tuple, or a relative `TARGET`) |

`RC 14` exists for the same reason as this article: with no git tree, `git status` returns `128` with **empty output**, and a naive gate reads «empty» as «clean» and gives green. Here the impossibility is declared.

Every code comes out **with its cause printed**. A correct `RC` for the wrong reason is not a gate: it is a coincidence.

---

## 10. How you run it

The CI gate is a package, and the pre-write one is a script with no dependencies:

```bash
pip install git-preflight-gate        # gate de CI (trae PyYAML)
ci-authority-gate /path/to/your/repo  # RC 0 = pasa · RC > 0 = fail-closed, causa impresa
```

```bash
curl -fsSL https://raw.githubusercontent.com/alexisromtz-lab/git-preflight-gate/main/preflight-gate.sh -o preflight-gate.sh
bash preflight-gate.sh /ruta/absoluta/archivo.py <blob_pre> <marca_exclusiva> <lineas_pre>
```

The case bench ships included and is exercised with `bash tests/must_fail.sh`: **9 cases, 9/9**, each one checking the code **and** the cause — `20` (incomplete tuple), `20` (relative path), `10`, `11`, `12`, `15`, `13`, `14`, and the positive control `0`.

---

## Closing

The `#46923` bug is real, it is alive in `HEAD`, and no version fixes it. But the finding of the article is not the bug: it is that **six arms and a witness** turn «I think the hook does not run» into a table anyone can run again — and that **the negative control** is what kept me from publishing the opposite conclusion with the same confidence.

---

**Want to audit your repo?** Use `pip install git-preflight-gate` or reach me at [la-auditora](https://github.com/alexisromtz-lab/la-auditora).

If you would rather start without installing anything, leave `owner/repo` in the comments and I will publish in this same thread the first count: how clean your tree is for an agent that writes, and what codes the gate returns over your most churned paths. No cloning your code, no asking you for a key.
