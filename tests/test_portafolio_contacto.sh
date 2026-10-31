#!/usr/bin/env bash
set -euo pipefail

# HUELLA-PORTAFOLIO-CONTACTO-TEST-20261031
# HUELLA-PORTAFOLIO-CONTACTO-GITHUB-20261031
readonly WHATSAPP_URL='https://wa.me/525649997759'
readonly ISSUES_URL='https://github.com/alexisromtz-lab/git-preflight-gate/issues/new'
readonly ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

check_contact() {
  local label="$1"
  local body="$2"
  grep -Fq "$WHATSAPP_URL" <<< "$body" || fail "Falta WhatsApp aprobado en $label"
  grep -Fq "$ISSUES_URL" <<< "$body" || fail "Falta GitHub Issues aprobado en $label"
  ! grep -Fq 'mailto:' <<< "$body" || fail "Sigue publicado un enlace mailto en $label"
}

for page in portafolio/index.html portafolio/en/index.html; do
  file="$ROOT/$page"
  [[ -f "$file" ]] || fail "No existe $page"
  check_contact "$page" "$(<"$file")"
done

case "${CHECK_PUBLISHED:-0}" in
  0) ;;
  1)
    for url in \
      'https://alexisromtz-lab.github.io/la-auditora/portafolio/' \
      'https://alexisromtz-lab.github.io/la-auditora/portafolio/en/'; do
      response="$(curl --fail --silent --show-error --location --max-time 20 --write-out $'\n%{http_code}' "$url")" \
        || fail "No se pudo consultar $url"
      status="${response##*$'\n'}"
      body="${response%$'\n'*}"
      [[ "$status" == '200' ]] || fail "HTTP $status en $url"
      check_contact "$url" "$body"
    done
    ;;
  *) fail 'CHECK_PUBLISHED debe ser 0 o 1' ;;
esac

if [[ "${CHECK_PUBLISHED:-0}" == '1' ]]; then
  printf 'OK: enlaces aprobados en páginas locales y publicadas (HTTP 200); mailto ausente.\n'
else
  printf 'OK: enlaces aprobados en páginas locales ES/EN; mailto ausente.\n'
fi
