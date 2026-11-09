# Contributing

## Workflow

1. Start from an up-to-date `main` and create a topic branch; do not push directly to `main`.
2. Activate the hooks in this clone before pushing:

   ```sh
   ./setup.sh
   ```

   This sets the repository's hook path to `.githooks` only when no effective path exists; it preserves the global/local setting when it is already `.githooks` and stops rather than replacing a custom path. Confirm with `git config --get core.hooksPath` (`.githooks`).
3. Before opening a pull request, run the local contact check:

   ```sh
   bash tests/test_portafolio_contacto.sh
   ```

   It checks the Spanish and English home and portfolio pages for actual WhatsApp and GitHub Issues links, rejects `mailto:` links, and does not need network access.
4. Push the topic branch and open a pull request to `main`. Resolve review conversations before merging.
5. After merging and the Pages deployment completes, verify the published contact links:

   ```sh
   CHECK_PUBLISHED=1 bash tests/test_portafolio_contacto.sh
   ```

   This checks the deployed Spanish and English home and portfolio pages and requires network access.

## Current checks

`main` requires pull requests, resolved conversations, and the `validate_html` status check; it does not require approvals. The `Pull request checks` workflow runs two separate jobs for pull requests to `main`: required `validate_html` runs the monitor regression tests, the canary falsifiers, the local pages checks and the site canary; `smoke_test_live` checks published pages and is not required, so a Pages or network outage does not block a merge when deterministic checks pass.

Running `./setup.sh` and passing the local `pre-push` hook remain project requirements, but the hook is local and can be bypassed; GitHub enforces `validate_html` through branch protection. A green `validate_html` check certifies the monitor's deterministic regression tests, the canary and its falsifiers, and local contact checks — not live availability. The `Daily availability monitor` workflow runs at 08:00 UTC and can also be dispatched manually; it records HTTP status, response time, and WhatsApp-link presence in a per-run CSV artifact retained for 30 days. A failed live probe fails that run, but the CSV upload still runs.

## Admission gate for reports (003 onwards)

A report is an executable artifact, not an article. The three files are mandatory and live under
`portafolio/<slug>/`:

| file | what it is | what a reviewer checks without reading the prose |
|---|---|---|
| `reproduce.py` | deterministic, standard library only, no network | `python3 reproduce.py` from a clean clone returns the declared RC |
| `ficha.json` | machine-readable record | `sujeto`, `hallazgo`, `limite`, `estado`, `locus`, `reproduccion` present and non-empty |
| `index.html` | the narrative | declares the same limits as `ficha.json` and links back to the index |

The RC contract is fixed for every report: `0` every declared claim reproduces · `1` at least one
claim diverges, which is a finding and not a crash · `2` the measurement could not be taken
(missing object, unparsable input, network needed) and **never** collapses into `0`.

Three conditions are admission requirements. A report that fails any of them is not published:

1. **Self-contained by default.** `python3 reproduce.py`, with no arguments, no network and no
   sibling repository, must reach the declared RC. If the report has to execute a third-party file,
   it ships a pinned copy under `objeto/` beside that file's licence, and the default run uses it.
2. **A negative control behind the finding.** A claim that can only confirm is not reproducible:
   the script also reports what it fails to see once one input is perturbed, so a green verdict
   cannot come out of a script that always says green.
3. **The limits travel inside the artifact.** Whatever `ficha.json` declares as `limite` appears in
   `index.html`. A page stronger than its own record lies by omission.

Reports 001 and 002 predate this gate. 002 satisfies all three; 001 executes the real workflow and
therefore requires it as an argument, so its clean-clone run returns `2`. The asymmetry is declared
in [README.md](./README.md) and is not treated as a defect of 001.

The gate is measured, not only written: `python3 tools/canario.py` runs in the `validate_html` job
and checks, offline, that every local link resolves, that no published report is orphaned from a
landing page or from `sitemap.xml`, that each ficha declares its six fields, that `CITATION.cff` and
`.zenodo.json` stay readable with a DOI linked from the README, and that the `rc` each ficha declares
is the one its script returns. `tests/test_canario.py` proves the canary can ring: every check has a
mutation that turns it red.

## Articles: the markdown is the source, the page is a projection

An article is not a report and does not carry `reproduce.py`. It is a sourced text plus the page
that publishes it, under `portafolio/articulos/<slug>/`:

| file | what it is | who writes it |
|---|---|---|
| `articulo.md` | the only source: `title`, `lede`, `date` in a `---` header, then the body | a person |
| `index.html` | the page, generated from `articulo.md` | `tools/paginas_articulos.py` |

`tools/paginas_articulos.py --aplicar` writes every page and the index at
`portafolio/articulos/`; `--check` writes nothing and returns `1` when a page differs by a single
byte from its source. CI runs `--check`, so a hand-edited page or a source edited without
regenerating fails the required check instead of shipping a page that disagrees with its own source.

Two invariants come from being public on a static site:

- **A relative link is not published as a link.** The body of an article may cite internal corpus
  files; those destinations do not exist in this repository, so the generator renders them as
  `<code>` and never as an anchor. The canary fails on a link that points outside the published
  tree, which is the negative control of that rule.
- **A source missing `title`, `lede` or `date` stops the generator** with `1` and names the field.
  A public page without a description is not a lesser page, it is an incomplete one.

The RC contract of the generator: `0` pages current or written · `1` drift or an unreadable source ·
`2` nothing to measure (no `portafolio/articulos`, or no article) · `3` invalid arguments. `2` never
collapses into `0`.

The canary covers the family as well: every article must be declared in `sitemap.xml`, linked from
the articles index, and that index linked from each landing page. Nine mutations in
`tests/test_canario.py` and twenty in `tests/test_paginas_articulos.py` prove both can ring.

## Language: what is published travels in English, what is instructed stays in Spanish

A published copy is read by people who do not read Spanish; an instruction is read by whoever is
pasting it. Mixing the two languages in the same block is how a draft gets published as if it were
the article. So the rule is a boundary, not a preference:

- **Published text — the article bodies, the page copy, the network variants — is written in
  English.** `portafolio/articulos/<slug>/articulo.en.md` is its only source.
- **Instructions, commit messages, ledger rows and this file stay in Spanish.** They are read while
  working, not after publishing.

The English twin lives **beside** its Spanish source, never in place of it, and the generator
publishes it at the mirrored path `portafolio/articulos/en/<slug>/`:

| file | what it is | who writes it |
|---|---|---|
| `articulo.en.md` | the English source of the same article, header declaring `lang: en` | a person |
| `en/<slug>/index.html` | the English page, generated from `articulo.en.md` | `tools/paginas_articulos.py` |
| `en/index.html` | the English articles index | `tools/paginas_articulos.py` |

Three rules keep the twin from becoming a second truth:

- **The filename declares the language, and the header cannot contradict it.** A file named
  `articulo.en.md` whose header says `lang: es` stops the generator with `1`: that is the
  "the name claims more than the file does" pattern, caught before it ships.
- **An English twin without a Spanish source is an error, not an orphan.** The twin is a
  translation; a translation of nothing is a fork of the site.
- **A twin that exists must be reachable.** The canary requires the English index, its entries in
  `sitemap.xml`, a link from the Spanish page to its twin and a link back. Both pages declare
  `hreflang` (`es`, `en`, `x-default`) so a machine pairs them without reading them.

What a twin may **not** do is move a number. `tests/test_articulos_en.py` compares the multiset of
numeric tokens of the Spanish body against the English one, requires each fenced code block to be
byte-identical, and requires the density of Spanish markers to collapse against the Spanish source.
A translated figure is not a translation: it is a second measurement that nobody ran.

### The round trip to the network loses structure, and that is a measurable defect

`portafolio/articulos/<slug>/devto.md` is the dev.to projection: the English body, untouched, under
the header dev.to actually reads (`description`, `published`, `canonical_url`). `tools/devto.py`
writes it and `--check` in CI refuses a hand-edited copy.

The reason it exists is a publication that came out wrong: the body travelled wrapped in a
` ```text ` fence "so it could be copied", the outer fence closed at the first inner fence, and the
page was published with 1 code block instead of 8, 0 tables instead of 4 and 1 heading instead of
11 — the `##` had not survived the trip, so `3. The cause` arrived as an ordered list. Copying from
the **rendered** GitHub view produces the same damage without any fence: the markers are markup, and
copying a rendered page copies the text, not the markup.

So: **paste from the raw file, never from the rendered page**, and never wrap markdown in a fence to
make it copyable. `tests/test_devto.py` holds the four falsifiers that name this defect, including
the mechanism measured on the fence itself (a wrapped body yields two fenced regions instead of one,
and the second one is empty).


## If the contact check fails

- Keep the exact `FAIL:` message and run `bash tests/test_portafolio_contacto.sh` to reproduce a local failure.
- The test suite needs Python 3.10 or newer (`tools/monitor_auditora.py` annotates `int | None` at runtime); on 3.9 the monitor module fails to import and the red is of the interpreter, not of the site.
- For a failed `smoke_test_live`, confirm the Pages deployment completed, then run `CHECK_PUBLISHED=1 bash tests/test_portafolio_contacto.sh` again; this check is informational and does not block merges.
- Do not change the approved WhatsApp or GitHub Issues destinations without maintainer confirmation.

<!-- CONTRIB-CI-STATE-20261031 -->
<!-- HUELLA-CONTRIBUTING-CI-ENFORCED-20261031 -->
<!-- HUELLA-CONTRIB-CTA-POLICY-20261031 -->
<!-- HUELLA-CONTRIBUTING-MONITOR-20261031 -->
<!-- HUELLA-CONTRIB-ALL-CTA-PAGES-20261031 -->
<!-- HUELLA-CONTRIB-CI-SYNC-20261031 -->
