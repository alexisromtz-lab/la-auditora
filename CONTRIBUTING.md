# Contributing

## Workflow

1. Start from an up-to-date `main` and create a topic branch; do not push directly to `main`.
2. Activate the hooks in this clone before pushing:

   ```sh
   ./setup.sh
   ```

   This changes only this clone's local Git configuration. Confirm with `git config --local --get core.hooksPath` (`.githooks`).
3. Before opening a pull request, run the local contact check:

   ```sh
   bash tests/test_portafolio_contacto.sh
   ```

   It checks both local language pages for the approved WhatsApp and GitHub Issues links and rejects `mailto:`. It does not need network access.
4. Push the topic branch and open a pull request to `main`. Resolve review conversations before merging.
5. After merging and the Pages deployment completes, verify the published contact links:

   ```sh
   CHECK_PUBLISHED=1 bash tests/test_portafolio_contacto.sh
   ```

   This checks both deployed language pages and requires network access.

## Current checks

`main` requires pull requests and resolved conversations; it does not require an approval or a status check. This repository has an active GitHub Pages deployment workflow, but no CI workflow that tests pull requests. The billing block measured in the private `platino-labs` repository does not establish that Actions are disabled here.

Running `./setup.sh` and passing the local `pre-push` hook are project requirements, but the hook is local and can be bypassed; GitHub does not enforce it server-side. Do not treat a green pull request as proof that the contact regression ran.

## If the contact check fails

- Keep the exact `FAIL:` message and run `bash tests/test_portafolio_contacto.sh` to reproduce a local failure.
- For a published-page failure, confirm the Pages deployment completed, then run `CHECK_PUBLISHED=1 bash tests/test_portafolio_contacto.sh` again.
- Do not change the approved WhatsApp or GitHub Issues destinations without maintainer confirmation.

<!-- CONTRIB-CI-STATE-20261031 -->
<!-- HUELLA-CONTRIB-CTA-POLICY-20261031 -->
