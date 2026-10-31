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

`main` requires pull requests, resolved conversations, and the `validate_html` status check; it does not require approvals. The `Pull request checks` workflow runs two separate jobs for pull requests to `main`: `validate_html` checks the local pages and is required for merging; `smoke_test_live` checks the published pages and is not required, so a Pages or network outage does not block a merge when the deterministic check passes.

Running `./setup.sh` and passing the local `pre-push` hook remain project requirements, but the hook is local and can be bypassed; GitHub enforces `validate_html` through branch protection. A green `validate_html` check certifies only the local contact checks, not live availability.

## If the contact check fails

- Keep the exact `FAIL:` message and run `bash tests/test_portafolio_contacto.sh` to reproduce a local failure.
- For a failed `smoke_test_live`, confirm the Pages deployment completed, then run `CHECK_PUBLISHED=1 bash tests/test_portafolio_contacto.sh` again; this check is informational and does not block merges.
- Do not change the approved WhatsApp or GitHub Issues destinations without maintainer confirmation.

<!-- CONTRIB-CI-STATE-20261031 -->
<!-- HUELLA-CONTRIBUTING-CI-ENFORCED-20261031 -->
<!-- HUELLA-CONTRIB-CTA-POLICY-20261031 -->
<!-- HUELLA-CONTRIB-ALL-CTA-PAGES-20261031 -->
<!-- HUELLA-CONTRIB-CI-SYNC-20261031 -->
