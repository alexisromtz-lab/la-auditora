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
  python3 -c '
import sys
from html.parser import HTMLParser

label, whatsapp_base, issues_base = sys.argv[1:]

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.hrefs.extend(value for key, value in attrs if key == "href" and value is not None)

parser = LinkParser()
parser.feed(sys.stdin.read())

def matches_destination(href, base):
    return href == base or href.startswith(base + "?")

if not any(matches_destination(href, whatsapp_base) for href in parser.hrefs):
    print(f"FAIL: Falta enlace WhatsApp aprobado en {label}", file=sys.stderr)
    raise SystemExit(1)
if not any(matches_destination(href, issues_base) for href in parser.hrefs):
    print(f"FAIL: Falta enlace GitHub Issues aprobado en {label}", file=sys.stderr)
    raise SystemExit(1)
if any(href.lower().startswith("mailto:") for href in parser.hrefs):
    print(f"FAIL: Sigue publicado un enlace mailto en {label}", file=sys.stderr)
    raise SystemExit(1)
' "$label" "$WHATSAPP_URL" "$ISSUES_URL" <<< "$body" || return 1
}

check_finops_conversion() {
  local label="$1"
  local body="$2"
  python3 -c '
import sys
from html.parser import HTMLParser

label, template_href, pilot_href = sys.argv[1:]

class FinOpsParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.hrefs = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "section" and attributes.get("id") == "finops":
            self.active = True
        if self.active:
            if tag == "a" and attributes.get("href"):
                self.hrefs.append(attributes["href"])

    def handle_endtag(self, tag):
        if tag == "section" and self.active:
            self.active = False

    def handle_data(self, data):
        if self.active:
            self.text.append(data)

parser = FinOpsParser()
parser.feed(sys.stdin.read())
copy = " ".join(parser.text).casefold()
if template_href not in parser.hrefs:
    print(f"FAIL: Falta el enlace a la plantilla en {label}", file=sys.stderr)
    raise SystemExit(1)
if pilot_href not in parser.hrefs:
    print(f"FAIL: Falta la guía del piloto en {label}", file=sys.stderr)
    raise SystemExit(1)
if not all(term in copy for term in ("principalplatinoarn", "externalid", "rolearn")):
    print(f"FAIL: Falta explicar los parámetros IAM en {label}", file=sys.stderr)
    raise SystemExit(1)
if not any(phrase in copy for phrase in (
    "no es un enlace de despliegue de un clic",
    "not a ready-to-deploy one-click link",
)):
    print(f"FAIL: No se aclara que la plantilla no es un enlace listo para desplegar en {label}", file=sys.stderr)
    raise SystemExit(1)
if not any(phrase in copy for phrase in ("canal privado", "private channel")):
    print(f"FAIL: Falta el canal privado para compartir el RoleArn en {label}", file=sys.stderr)
    raise SystemExit(1)
' "$label" '/la-auditora/PLANTILLA_CFN_PLATINO_AUDIT_ROLE.yaml' 'https://github.com/alexisromtz-lab/la-auditora/blob/main/PILOTO_AWS.md' <<< "$body" || return 1
}

# HUELLA-TEST-FINOPS-CTA-20261031
# HUELLA-TEST-NEGATIVE-CONTROLS-20261031
comment_fixture='<!-- <a href="https://wa.me/525649997759?text=contact"><a href="https://github.com/alexisromtz-lab/git-preflight-gate/issues/new?title=request"> -->'
if check_contact 'comentarios HTML' "$comment_fixture" 2>/dev/null; then
  fail 'La validación acepta enlaces que solo aparecen en comentarios HTML'
fi
prefix_fixture='<a href="https://wa.me/525649997759.evil?text=contact"><a href="https://github.com/alexisromtz-lab/git-preflight-gate/issues/new.evil?title=request">'
if check_contact 'destinos con prefijo' "$prefix_fixture" 2>/dev/null; then
  fail 'La validación acepta destinos que solo comparten un prefijo'
fi

# HUELLA-TEST-ALL-CTA-PAGES-20261031
for page in index.html en/index.html portafolio/index.html portafolio/en/index.html; do
  file="$ROOT/$page"
  [[ -f "$file" ]] || fail "No existe $page"
  body="$(<"$file")"
  check_contact "$page" "$body" || fail "Enlaces de contacto inválidos en $page"
  if [[ "$page" == 'index.html' || "$page" == 'en/index.html' ]]; then
    check_finops_conversion "$page" "$body" || fail "CTA FinOps inválido en $page"
  fi
done

# HUELLA-TEST-PUBLISHED-OPT-IN-20261031
case "${CHECK_PUBLISHED:-0}" in
  0) ;;
  1)
    for url in \
      'https://alexisromtz-lab.github.io/la-auditora/' \
      'https://alexisromtz-lab.github.io/la-auditora/en/' \
      'https://alexisromtz-lab.github.io/la-auditora/portafolio/' \
      'https://alexisromtz-lab.github.io/la-auditora/portafolio/en/'; do
      response="$(curl --fail --silent --show-error --location --max-time 20 --write-out $'\n%{http_code}' "$url")" \
        || fail "No se pudo consultar $url"
      status="${response##*$'\n'}"
      body="${response%$'\n'*}"
      [[ "$status" == '200' ]] || fail "HTTP $status en $url"
      check_contact "$url" "$body" || fail "Enlaces de contacto inválidos en $url"
      case "$url" in
        'https://alexisromtz-lab.github.io/la-auditora/'|'https://alexisromtz-lab.github.io/la-auditora/en/')
          check_finops_conversion "$url" "$body" || fail "CTA FinOps inválido en $url"
          ;;
      esac
    done
    curl --fail --silent --show-error --location --max-time 20 --output /dev/null \
      'https://alexisromtz-lab.github.io/la-auditora/PLANTILLA_CFN_PLATINO_AUDIT_ROLE.yaml' \
      || fail 'No se pudo descargar la plantilla CloudFormation publicada'
    ;;
  *) fail 'CHECK_PUBLISHED debe ser 0 o 1' ;;
esac

if [[ "${CHECK_PUBLISHED:-0}" == '1' ]]; then
  printf 'OK: contacto y CTA FinOps en páginas ES/EN; plantilla publicada disponible (HTTP 200); mailto ausente.\n'
else
  printf 'OK: contacto en páginas ES/EN y CTA FinOps con plantilla/guía; mailto ausente.\n'
fi
