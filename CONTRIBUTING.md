# Contributing

## Workflow

1. Start from an up-to-date `main` and create a topic branch; do not push directly to `main`.
2. Activate the hooks in this clone before pushing:

   ```sh
   ./setup.sh
   ```

   The setup preserves an effective `.githooks` path, stops rather than replacing a custom path, or sets `.githooks` locally if no hook path is configured. Confirm the effective value with `git config --get core.hooksPath` (`.githooks`).
3. Before opening a pull request, run the deterministic local check:

   ```sh
   bash tests/test_portafolio_contacto.sh
   ```

   This checks both local portfolio pages and does not need network access.
4. Push the topic branch and open a pull request to `main`. Resolve review conversations before merging.
5. After a portfolio deployment, check the published pages separately:

   ```sh
   bash tests/test_portafolio_contacto.sh published
   ```

   This smoke test needs network access and a reachable GitHub Pages site.

## Current checks

`main` requires pull requests, resolved conversations, and the `validate_html` status check; it does not require approvals. The `Pull request checks` workflow runs two separate jobs for pull requests to `main`: `validate_html` checks local HTML and is required for merging; `smoke_test_live` checks the published pages and is not required, so a Pages or network outage does not block a merge when the deterministic check passes.

Running `./setup.sh` and passing the local `pre-push` hook remain project requirements, but the hook is local and can be bypassed; GitHub enforces `validate_html` through branch protection. A green `validate_html` check certifies only the local contact checks, not live availability.

## If a check fails

- For a local contact mismatch, run `bash tests/test_portafolio_contacto.sh` to reproduce it. Do not change the approved email without maintainer confirmation.
- For a failed `smoke_test_live`, check connectivity and the published Pages URLs, then retry; this check is informational and does not block merges.

<!-- CONTRIB-CI-STATE-20261031 -->
<!-- HUELLA-CONTRIBUTING-CI-ENFORCED-20261031 -->
<!-- HUELLA-CONTRIBUTING-CI-DECOUPLED-20261031 -->
