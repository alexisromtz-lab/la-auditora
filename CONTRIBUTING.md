# Contributing

## Workflow

1. Start from an up-to-date `main` and create a topic branch; do not push directly to `main`.
2. Activate the hooks in this clone before pushing:

   ```sh
   ./setup.sh
   ```

   This changes only this clone's local Git configuration. Confirm with `git config --local --get core.hooksPath` (`.githooks`).
3. Before opening a pull request, run:

   ```sh
   bash tests/test_portafolio_contacto.sh
   ```

   It checks the local portfolio pages and the deployed pages, so it needs network access and a reachable GitHub Pages site.
4. Push the topic branch and open a pull request to `main`. Resolve review conversations before merging.
5. After merging a portfolio change, verify:
   `https://alexisromtz-lab.github.io/la-auditora/portafolio/`.

## Current checks

`main` requires pull requests and resolved conversations; it does not require an approval or a status check. This repository has an active GitHub Pages deployment workflow, but no CI workflow that tests pull requests. The billing block measured in the private `platino-labs` repository does not establish that Actions are disabled here.

Running `./setup.sh` and passing the local `pre-push` hook are project requirements, but the hook is local and can be bypassed; GitHub does not enforce it server-side. Do not treat a green pull request as proof that the contact regression ran.

## If the hook blocks a push

- Keep the exact `FAIL:` message and run `bash tests/test_portafolio_contacto.sh` to reproduce it.
- For a network or HTTP failure, check connectivity and the published Pages URL, then retry.
- For a local or published contact mismatch, do not change the expected email on your own; ask the maintainers to confirm the approved contact value.

<!-- CONTRIB-CI-STATE-20261031 -->
