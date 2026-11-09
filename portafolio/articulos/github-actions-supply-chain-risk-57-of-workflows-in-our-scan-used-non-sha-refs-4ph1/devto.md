---
title: "GitHub Actions Supply-Chain Risk: 57% of Workflows in Our Scan Used Non-SHA Refs"
published: false
description: "The 64.9% figure describes rule occurrences—not workflow prevalence. Here is what our scan of 279..."
tags: a, i, s, e
canonical_url: "https://alexisromtz-lab.github.io/la-auditora/portafolio/articulos/en/github-actions-supply-chain-risk-57-of-workflows-in-our-scan-used-non-sha-refs-4ph1/"
---

*The 64.9% figure describes rule occurrences—not workflow prevalence. Here is what our scan of 279 GitHub Actions workflow files actually measured.*

## The denominator changes the headline

In a snapshot captured on October 31, 2026, we scanned 279 workflow files across nine open-source repositories. The rule `GATE_RC_5_REF_MUTABLE` flags each `uses:` reference that is not pinned to a full commit SHA.

At least one such reference appeared in 159 of the 279 workflows: **57.0%**. The finding appeared in seven of the nine repositories.

So where does 64.9% come from? The scan recorded 607 non-SHA-pinned `uses:` occurrences out of 936 total rule occurrences across seven rule categories. That is **64.9% of the occurrences**, not 64.9% of workflows. One workflow can contain multiple references and findings; those are different units.

| Repository | Workflow files scanned | Non-SHA-pinned `uses:` occurrences |
|---|---:|---:|
| [activepieces/activepieces](https://github.com/activepieces/activepieces) | 38 | 149 |
| [calcom/cal.com](https://github.com/calcom/cal.com) | 50 | 89 |
| [documenso/documenso](https://github.com/documenso/documenso) | 14 | 29 |
| [formbricks/formbricks](https://github.com/formbricks/formbricks) | 34 | 0 |
| [hoppscotch/hoppscotch](https://github.com/hoppscotch/hoppscotch) | 4 | 84 |
| [medusajs/medusa](https://github.com/medusajs/medusa) | 50 | 162 |
| [nocodb/nocodb](https://github.com/nocodb/nocodb) | 11 | 22 |
| [openstatusHQ/openstatus](https://github.com/openstatusHQ/openstatus) | 20 | 72 |
| [supabase/supabase](https://github.com/supabase/supabase) | 58 | 0 |
| **Total** | **279** | **607** |

## Why a non-SHA reference matters

A workflow can refer to an action by a version tag or branch, such as `owner/action@v4` or `owner/action@main`. Those names are convenient, but they do not themselves identify an immutable commit. If a reference is moved—or its upstream repository is compromised—later workflow runs may retrieve different code without a change to the workflow file.

GitHub recommends pinning actions to a full commit SHA and verifying that the SHA comes from the action’s upstream repository. A SHA pin makes the selected commit explicit; it does **not** prove that the commit is safe. Updates still need review.

## What this scan does not prove

This result is an exposure signal, not evidence of a compromise. We did not measure whether individual tags were protected or immutable, whether any reference had actually moved, or what code executed at runtime. Nor is this nine-repository scan a representative estimate of all GitHub Actions workflows.

A tenth candidate, `twentyhq/twenty`, could not be verified because its checkout was truncated. It was excluded from the denominator—not counted as clean.

## A practical next step

Review every `uses:` reference, replace mutable names with verified full commit SHAs where appropriate, and make updates through a deliberate review process. Keep counts of affected workflow files separate from counts of individual references.

For GitHub’s recommendations, see the [secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use). For commit-pinned, evidence-backed repository audits, explore [La Auditora](https://alexisromtz-lab.github.io/la-auditora/en/). [git-preflight-gate](https://github.com/alexisromtz-lab/git-preflight-gate) addresses a different concern—integrity checks before AI agents write to a repository; it is not an Actions workflow scanner. Its GitHub Marketplace listing is [CI Authority Gate](https://github.com/marketplace/actions/ci-authority-gate).

---

The RC5-only evidence package (finding-level data, workflow manifest, census, method, and SHA-256 checksums) is available in the [public release](https://github.com/alexisromtz-lab/platino-data-room/releases/tag/supply-chain-20261031-rc5-v1). It supports the RC5 counts above; it does not reproduce the 936-occurrence denominator across all seven rule categories.
