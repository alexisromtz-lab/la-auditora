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

`main` requires pull requests, resolved conversations, and the `Portfolio contact regression` status check; it does not require approvals. The `Pull request checks` workflow runs `bash ./setup.sh` and `bash tests/test_portafolio_contacto.sh` for pull requests to `main`. The regression checks local pages only; published-page verification is separate because the PR content is not live yet.

Running `./setup.sh` and passing the local `pre-push` hook remain project requirements, but the hook is local and can be bypassed; GitHub enforces the regression separately through the status check. A green check certifies only the local contact checks.

## If the contact check fails

- Keep the exact `FAIL:` message and run `bash tests/test_portafolio_contacto.sh` to reproduce a local failure.
- For a published-page failure, confirm the Pages deployment completed, then run `CHECK_PUBLISHED=1 bash tests/test_portafolio_contacto.sh` again.
- Do not change the approved WhatsApp or GitHub Issues destinations without maintainer confirmation.

<!-- CONTRIB-CI-STATE-20261031 -->
<!-- HUELLA-CONTRIBUTING-CI-ENFORCED-20261031 -->
<!-- HUELLA-CONTRIB-CTA-POLICY-20261031 -->
<!-- HUELLA-CONTRIB-ALL-CTA-PAGES-20261031 -->
