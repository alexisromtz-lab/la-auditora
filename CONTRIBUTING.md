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

`main` requires pull requests, resolved conversations, and the `validate_html` status check; it does not require approvals. The `Pull request checks` workflow runs two separate jobs for pull requests to `main`: required `validate_html` runs the monitor regression tests and checks local pages; `smoke_test_live` checks published pages and is not required, so a Pages or network outage does not block a merge when deterministic checks pass.

Running `./setup.sh` and passing the local `pre-push` hook remain project requirements, but the hook is local and can be bypassed; GitHub enforces `validate_html` through branch protection. A green `validate_html` check certifies the monitor's deterministic regression tests and local contact checks, not live availability. The `Daily availability monitor` workflow runs at 08:00 UTC and can also be dispatched manually; it records HTTP status, response time, and WhatsApp-link presence in a per-run CSV artifact retained for 30 days. A failed live probe fails that run, but the CSV upload still runs.

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

## If the contact check fails

- Keep the exact `FAIL:` message and run `bash tests/test_portafolio_contacto.sh` to reproduce a local failure.
- For a failed `smoke_test_live`, confirm the Pages deployment completed, then run `CHECK_PUBLISHED=1 bash tests/test_portafolio_contacto.sh` again; this check is informational and does not block merges.
- Do not change the approved WhatsApp or GitHub Issues destinations without maintainer confirmation.

<!-- CONTRIB-CI-STATE-20261031 -->
<!-- HUELLA-CONTRIBUTING-CI-ENFORCED-20261031 -->
<!-- HUELLA-CONTRIB-CTA-POLICY-20261031 -->
<!-- HUELLA-CONTRIBUTING-MONITOR-20261031 -->
<!-- HUELLA-CONTRIB-ALL-CTA-PAGES-20261031 -->
<!-- HUELLA-CONTRIB-CI-SYNC-20261031 -->
