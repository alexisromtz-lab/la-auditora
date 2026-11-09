---
title: How I found 6 silent security gates in GnuTLS (and why CI green isn't always what it seems)
lede: There is a dangerous assumption in modern software engineering: "The pipeline is green, therefore the...
date: 2026-11-06
tags: d, e, v, o, p, s, ,,  , g, i, t, l, a, b, ,,  , s, e, c, u, r, i, t, y, ,,  , o, p, e, n, s, o, u, r, c, e
fuente: https://dev.to/alexisromtz7/how-i-found-6-silent-security-gates-in-gnutls-and-why-ci-green-isnt-always-what-it-seems-145d
lang: en
solo_en: si
---

There is a dangerous assumption in modern software engineering: **"The pipeline is green, therefore the code is safe."**

But what if the pipeline is lying to you? 

I recently ran a static analysis on the GitLab CI configuration of **GnuTLS**, a foundational cryptographic library that secures a massive portion of the internet's TLS traffic. 

I found **six test jobs that can fail without turning the pipeline red**. 

Out of 15 jobs in the file that execute a test runner, 6 of them (40%) are configured with `allow_failure: true`. This means that if a test fails, GitLab still reports the pipeline as passed. 

Here is the breakdown of what I found, why it matters, and how it can be fixed in one line.

### The 6 Silent Gates

| Job | `allow_failure` at | What it runs |
|---|---|---|
| `mingw64/test` | `.gitlab-ci.yml:127` | `mingw64-make -C tests check` under wine |
| `mingw32/test` | `.gitlab-ci.yml:127` | same, 32-bit |
| `fedora-threadsan/test` | `.gitlab-ci.yml:480` | ThreadSanitizer suite |
| `fedora-cross/aarch64-linux-gnu/test` | `.gitlab-ci.yml:614` | full suite under qemu |
| `fedora-cross/ppc64le-linux-gnu/test` | `.gitlab-ci.yml:632` | same (big-endian) |
| `fedora-cross/s390x-linux-gnu/test` | `.gitlab-ci.yml:650` | same (big-endian) |

For contrast, there are 9 other jobs in the same file (like `fedora/test` and `fedora-sanitizers/test`) that *do* hard-fail the pipeline. So the project clearly wants strict gates; these six are the exception.

### Why is this dangerous?

Two of these jobs (`mingw*` and `fedora-threadsan`) have a comment that says: 
> `# FIXME: the above step doesn't work on a rootless container`

The intention was to forgive *one specific step* (like a container setup). But in GitLab CI, `allow_failure: true` applies to the **entire job**. If a real data-race regression or a byte-order bug is introduced, the pipeline will stay green.

Even worse, the four `fedora-cross` jobs have *no comments at all*. They carry no stated reason. The `ppc64le` and `s390x` jobs are the only ones testing big-endian architectures. A failure there could silently reach `master`.

### The Surgical Fix

You don't need to remove the escape hatch entirely. If the runner is flaky (e.g., OOM or timeout), you can tell GitLab to forgive *only* infrastructure errors, while still failing the pipeline on actual assertion errors (exit code 2).

Instead of:
```yaml
allow_failure: true
