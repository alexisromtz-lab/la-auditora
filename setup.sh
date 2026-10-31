#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
HOOK="$ROOT/.githooks/pre-push"

if ! git -C "$ROOT" rev-parse --show-toplevel >/dev/null 2>&1; then
  printf 'ERROR: %s no pertenece a un repositorio Git.\n' "$ROOT" >&2
  exit 1
fi

if [[ ! -f "$HOOK" || ! -x "$HOOK" ]]; then
  printf 'ERROR: falta el hook ejecutable %s.\n' "$HOOK" >&2
  exit 1
fi

current="$(git -C "$ROOT" config --get core.hooksPath || true)"
case "$current" in
  "") git -C "$ROOT" config --local core.hooksPath .githooks ;;
  .githooks) : ;;
  *)
    printf 'ERROR: core.hooksPath ya está configurado como %s; revísalo antes de cambiarlo.\n' "$current" >&2
    exit 1
    ;;
esac

printf 'Hooks activados para este clon: %s\n' "$(git -C "$ROOT" config --get core.hooksPath)"

# SETUP-MARKER-20261031
