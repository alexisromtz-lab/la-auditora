---
title: "The $6.3B hack was not a code bug"
published: false
description: "Ten public repositories with a deployment workflow, measured with the exact commit of each one: 807 findings and 115 with a conjunction of authority. None of the ten returns a clean green, and the article says why that is not 807 vulnerabilities."
tags: security, devops, supplychain, opensource
canonical_url: "https://alexisromtz-lab.github.io/la-auditora/portafolio/articulos/en/el-hackeo-de-6-3b-no-fue-un-bug-de-codigo/"
---

**Where the figures come from:** my own measurement, reproducible. Every figure in this article has its commit; the
breakdown by code is further down, not in an appendix.

---

## What is confirmed, and what the press is still arguing about

Between October 29 and 30, eight outlets published the same fact: the largest theft in the history of
cryptocurrency, between **$6.3 and $6.4 billion**, with TRM Labs attributing it to North Korea. An Ethereum upgrade,
**EIP-7702**, appears in every piece: it lets an account delegate its signing capability to another contract. With
that delegation signed, hot wallets were drained.

So far, the headline. Now the part almost nobody is publishing:

- **Cryptonews, October 30:** «EIP-7702 didn't cause Binance hack, but may have amplified losses».
- **CCN, October 30:** «$3.66B Was Stolen Without It».
- **CryptoTicker, October 29:** «$2.8B Drained From Hot Wallet via EIP-7702».

Added up, those three pieces say something uncomfortable: **most of the money was lost without the upgrade
being involved**. If that holds, then EIP-7702 is not the cause. It is the amplifier.

And a fourth piece, from the same day, closes the circle from the other side: **The News International** headlines that
Binance «confirms advanced EIP-7702 exploits and compromised DevOps laptop». That is: that the vector came through a
**compromised engineer machine** is not this article's hypothesis — the exchange itself confirmed it. The fact is not
mine; the angle is.

All four headlines were verified on October 30, 2026 with publication date and outlet; none is quoted from
memory.

And if it is not the cause, the right question is not «what primitive failed?». It is: **who could sign?**

---

## The hole is the chain of authority, not the line of code

A code audit looks for the error in the program. The incident points elsewhere: an engineer's machine with
signing and deployment capability, and a delegation that turns one signature into permanent authority. None of that
lives in a badly written line. It lives in the **chain of authority**: which identity can publish, with which token,
from which artifact, and with how many factors.

That is not a hypothesis about cryptocurrency. It is the structure of any modern deployment. And it can be measured.

---

## We measured it in our own house first

We have an instrument that audits the authority surface of GitHub Actions: who has write permission and at the same
time executes code, who can publish through OIDC and at the same time builds the artifact, which actions come in by
movable tag, where secrets travel inline.

We ran it against our own repository, before running it against anyone else's.

**Result: 8 findings, `RC 1` (`FINDINGS`).** Six were from the same workflow. The three that matter:

1. That workflow declares `pages: write` + `id-token: write` **at the root**, not on the deployment job. Every job
   inherits it, including the one that compiles.
2. It comes in through **four floating tags** (`@v4`, `@v5`, `@v3`, `@v4`). A tag is a movable reference: whoever can
   move it executes code inside the perimeter that can publish.
3. The deploy job consumes the OIDC token without consuming an artifact built separately: **it builds and signs in the
   same context**.

None of the three pieces is dramatic on its own. **The conjunction is the finding**: a publishing token inherited
by every job, plus four entry doors that somebody else can move.

Run time: **1.2 seconds**. Zero tokens. Without installing anything in the audited repository.

---

## And then we fixed it, because a report with no fix is an invoice

This is where most audits end and where this article should start to differentiate itself.

**First move — fix.** Root permissions cut to `contents: read`. `pages: write` and `id-token: write` drop
to the `deploy` job, where they are exercised. The workflow splits into two jobs with `needs:`: one builds and uploads
the artifact, the other publishes, and **the one that publishes no longer has the repository code on its disk**. The
four floating refs become full SHAs. And a `download-artifact` appears that did not exist before: the gate had demanded
it from the start and we were right not to believe the first green — without that step, the whole artifact is a sink
for the instrument, because no step in the job declares it as an input.

**Second move — measure again.** 8 findings → **3**.

**Third move — the one almost nobody makes: do not delete the residue, declare it.**

The 3 that remain are not bugs. Two are the corpus `keepalive`: a job that needs `contents: write` because its
work **is** to run `git push --dry-run`. Taking the write away does not close a hole: it turns off the keepalive. The
third is the write grant for the `deploy` job, which now really is where it is used.

The obvious temptation is to silence the instrument. Add an exclusion list, a `# noqa`, a filter. That turns the audit
into theater: the next real finding comes in through the same door we just opened.

What we did instead was an **adjudication registry**: a file where each exception is written with its code, its
workflow, its job and **the record that authorizes it**. The instrument reads that registry and demands two things a
filter cannot give:

- **Zero orphans.** A row that no longer matches any finding is reported as an error. A registry that only
  grows is a graveyard of exceptions.
- **Adjudication does not delete the finding.** The finding stays in the JSON, with its severity, its `job` and its
  `motivo`. What changes is the verdict of the repository: from `FINDINGS` to `ADJUDICADO`.

**Result: `RC 0`, `ADJUDICADO`, zero orphans.** And when the instrument finds something again that is not in the
registry, it goes red again. *That* is what a `# noqa` cannot do.

This is the commercial point, and it is worth saying without decoration: **the deliverable is not a number of
findings. It is a number of findings that moves, and a residue with a name and a record.** Anyone can run a scanner
and hand you 29 violations. What almost nobody delivers is the proof that the 29 dropped to 3, why those 3 are still
there, and who signed each one.

---

## And in somebody else's project, 21 findings

On an active open source project (≈11 workflows), the same instrument returned **21 findings**: a release job
with `contents: write`, `pull-requests: write` and `id-token: write` that also runs the build in the same context, and
a bot token passed inline to a third-party action.

**And here comes the part almost no security vendor writes:** that job only fires on `push` to `main`,
inside an `if` that requires being the repository owner. **There is no untrusted input.** The finding is *structural,
not exploitable*. Publishing «secret exposed in a public repo» would have been technically true on the surface and
false in the risk.

That distinction —**structural ≠ exploitable**— is the difference between a report a CISO can use and one they have
to shut off.

And that foreign repo was not cloned. `--repo owner/name` resolves the name before the first call, reads the workflows
through a read-only API and publishes the exact commit it measured (`6c9ca431`). **Not one write to somebody else's
disk, not one extra token.** If measuring someone's house requires copying their code, it is not a measurement: it is
a move.

---

## Ten repositories, ten measurements, none silent

One case is not a sample. Ten public repositories, all with at least one workflow whose name publishes or deploys
something. The inclusion criterion is declared before measuring, not after: **a repository enters the batch if it has a
deployment or publishing workflow**.

| Repository | Measured commit | Findings | Conjunction of authority | Verdict |
|---|---|---:|---:|---|
| `withastro/starlight` | `6c9ca431` | 21 | 4 | `RC 1` |
| `withastro/astro` | `10dae2f3` | 51 | 19 | `RC 1` |
| `vercel/next.js` | `4fed142e` | 181 | 36 | `RC 1` |
| `nuxt/nuxt` | `363f3b87` | 59 | 12 | `RC 1` |
| `sveltejs/svelte` | `fe21fce0` | 12 | 2 | `RC 1` |
| `remix-run/remix` | `2eb9249c` | 170 | 9 | `RC 1` |
| `angular/angular` | `458303fe` | 26 | 4 | `RC 1` |
| `vuejs/core` | `24c9d0bf` | 11 | 6 | `RC 1` |
| `facebook/react` | `16453bcd` | 234 | 11 | `RC 1` |
| `vitejs/vite` | `90bc034a` | 42 | 12 | `RC 1` |
| **Total** | **10 commits** | **807** | **115** | **10 of 10** |

Two repositories from the original list were left out, and saying so is part of the method: `gatsbyjs/gatsby` has no
deployment or publishing workflow at all (one only, and it is not a deploy one) — it is declared `NO_APLICA` and
replaced by `vitejs/vite`. `astro-build/astro` does not exist: the correct organization is `withastro`, and
`withastro/astro` was measured.

**And here is the part a scanner vendor does not write: 807 are not 807 vulnerabilities.** They are 807
observations of the YAML surface. Of those, **115 are the conjunction this article defends** — write authority that
executes, authority inherited from the root, or missing root permissions. The other **692** split without decoration:
**308** movable refs (real hygiene), **153** scope reviews that contract SC-1 marks as `REVIEW`,
**3** root reads under review, and **228** from **two codes of the instrument itself that detect the mechanism, not the
defect**. `SECRETO_EXPUESTO` flags any `${{ secrets.* }}` in an `env:`, which is *the correct way* to pass a
secret to a step; and `SUMIDERO_IMPUDO` flags a job with `id-token: write` that runs `actions/checkout`, which is what
**every** publishing job has to do to have something to publish. Publishing the raw number would have been the
same sin we criticize three paragraphs above, with the sign flipped.

The full table, with the breakdown by code and the exact commit of each measurement, is the one above: ten rows, ten commits, none silent. The batch record keeps the ten SHAs and the criterion they were chosen with.

---

## What this instrument does NOT measure

Saying it is part of the contract, not a clause at the foot of the page:

- **Default permissions** of `GITHUB_TOKEN` at repository or organization level: invisible from the YAML.
- **OIDC policies of the destination** (npm, PyPI, AWS): the instrument sees that there is a door, not which lock it has.
- **Dependency modification at runtime** when non-isolated native code runs.
- **Reusable workflows (`workflow_call`) and composite actions hosted in foreign repositories.**
- **Runtime.** It measures the declared surface of the YAML; it does not certify what happens when it runs.

An instrument that does not declare its blindness is not an instrument: it is an opinion with a JSON format.

---

## The falsifier

This thesis dies in two ways, and both are measurable:

- If in **10 repositories with deployment workflows** the instrument does not find **a single** conjunction of inherited
  authority with movable doors, then there is no market: the problem does not exist outside our house.
- If it finds **10 of 10**, then the finding stops being a finding and becomes the norm — and the product is no
  longer the scan (which anyone runs in a second), but the **remediation** and the evidence that it was done.

Neither of the two is a defeat. Both force you to stop selling «audit» and start selling «this got
closed, and here is the proof».

**The falsifier has already been exercised, and the comfortable branch did not come out.** Ten repositories, ten
measurements: **10 of 10 have at least one conjunction of authority** (minimum 2, in `sveltejs/svelte`; maximum 36, in
`vercel/next.js`). There is not a single repository in the batch where the problem does not exist.

**And the measurement found a hole in the falsifier, not in the thesis.** The text said «conjunction of inherited
authority **with** movable doors», and that conjunction admits three readings. All three are published:

| Reading of the falsifier | Repositories that satisfy it |
|---|---:|
| **A** — at least one conjunction of authority (criterion declared in the evidence) | **10 of 10** |
| **B** — conjunction of authority **and** at least one `uses:` with a movable tag | **6 of 10** |
| **C** — write authority inherited **from the root** and movable tag | **4 of 10** |

**No reading gives zero.** The first branch of the falsifier —«if it does not find a single one, there is no market»—
is refuted under all three. But the second is not reached clean either: only reading **A** gets to 10 of 10. The
falsifier was written with two branches and a hole in the middle, and that hole was filled by the measurement, not by
rhetoric. The honest version of the falsifier is not binary: it is **a threshold** — «if fewer than half of the
repositories with deployment show the conjunction, the problem is not structural, and this falls». Measured: 4 of 10
under the strictest reading. **It does not fall, and barely.**

That resolves the thesis to the **second** branch under the declared reading, and it has to be said with the same
clarity used for our own finding: **the conjunction of authority is not a rarity; it is the norm of the ecosystem.** If
it is the norm, the scan is not a product — anyone runs it in a second, and ours is not billed for speed either.
**What is scarce is closure:** that the number goes down, that the residue has a name and a record, and that the next
scan can prove it did not go back up.

The branch that kills the thesis would have been the first. The second came out. **The product that survives this
measurement is the one already described in the 8 → 3 → 0 section, not the one described in the headline.**

---

## If you want to know where your single signing point is

You do not need to install anything or give us access to your code. A repository name is enough: the instrument reads
the declared surface of your workflows and returns, in seconds, how many jobs concentrate publishing authority and how
many of their inputs somebody else can move.

If the result is «there is no declared chain of authority», that is the finding: absence is published too.

---

*Do you want the measurement on your repository? Leave the name (`owner/repo`) in the comments of this article and I
will publish the count in the same thread: how many jobs concentrate publishing authority, and how many of their
inputs somebody else can move. Without cloning your code, without asking you for a key, without installing anything on
your machine.*
