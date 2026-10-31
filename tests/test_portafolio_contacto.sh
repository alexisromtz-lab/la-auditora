#!/usr/bin/env bash
set -euo pipefail

# HUELLA-PORTAFOLIO-CONTACTO-TEST-20261031
# HUELLA-PORTAFOLIO-CONTACTO-MODES-20261031
# HUELLA-PORTAFOLIO-CONTACTO-HREF-20261031
readonly EXPECTED_EMAIL='alexis@tiendasplatino.com.mx'
readonly ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

check_contact() {
  local label="$1"
  local body="$2"
  grep -Fq "href=\"mailto:${EXPECTED_EMAIL}" <<< "$body" || fail "Contacto distinto en $label"
}

check_local() {
  for page in portafolio/index.html portafolio/en/index.html; do
    local file="$ROOT/$page"
    [[ -f "$file" ]] || fail "No existe $page"
    check_contact "$page" "$(<"$file")"
  done
  printf 'OK: contacto aprobado en las dos páginas locales.\n'
}

check_published() {
  for url in \
    'https://alexisromtz-lab.github.io/la-auditora/portafolio/' \
    'https://alexisromtz-lab.github.io/la-auditora/portafolio/en/'; do
    local response status body
    response="$(curl --fail --silent --show-error --location --max-time 20 --write-out $'\n%{http_code}' "$url")" \
      || fail "No se pudo consultar $url"
    status="${response##*$'\n'}"
    body="${response%$'\n'*}"
    [[ "$status" == '200' ]] || fail "HTTP $status en $url"
    check_contact "$url" "$body"
  done
  printf 'OK: contacto aprobado en las dos páginas publicadas (HTTP 200).\n'
}

if (( $# > 1 )); then
  fail 'Uso: bash tests/test_portafolio_contacto.sh [local|published]'
fi

case "${1:-local}" in
  local) check_local ;;
  published) check_published ;;
  *) fail 'Uso: bash tests/test_portafolio_contacto.sh [local|published]' ;;
esac
