#!/usr/bin/env bash
set -euo pipefail

# HUELLA-PORTAFOLIO-CONTACTO-TEST-20261031
readonly EXPECTED_EMAIL='alexis@tiendasplatino.com.mx'
readonly ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

for page in portafolio/index.html portafolio/en/index.html; do
  file="$ROOT/$page"
  [[ -f "$file" ]] || fail "No existe $page"
  grep -Fq "href=\"mailto:${EXPECTED_EMAIL}" "$file" || fail "Contacto local distinto en $page"
done

for url in \
  'https://alexisromtz-lab.github.io/la-auditora/portafolio/' \
  'https://alexisromtz-lab.github.io/la-auditora/portafolio/en/'; do
  response="$(curl --fail --silent --show-error --location --max-time 20 --write-out $'\n%{http_code}' "$url")" \
    || fail "No se pudo consultar $url"
  status="${response##*$'\n'}"
  body="${response%$'\n'*}"
  [[ "$status" == '200' ]] || fail "HTTP $status en $url"
  grep -Fq "mailto:${EXPECTED_EMAIL}" <<< "$body" || fail "Contacto publicado distinto en $url"
done

printf 'OK: contacto aprobado en las dos páginas locales y publicadas (HTTP 200).\n'
