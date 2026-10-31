#!/usr/bin/env python3
"""Record a daily availability sample for the la-auditora public site."""

# HUELLA-MONITOR-AUDITORA-20261031

import argparse
import csv
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

DEFAULT_URL = "https://alexisromtz-lab.github.io/la-auditora/"
WHATSAPP_HOST = "wa.me"
WHATSAPP_PATH = "/525649997759"
USER_AGENT = "la-auditora-availability-monitor/1.0"


@dataclass(frozen=True)
class Measurement:
    timestamp_utc: str
    url: str
    http_status: int | None
    response_time_ms: float
    whatsapp_present: bool
    error: str

    @property
    def healthy(self) -> bool:
        return self.http_status == 200 and self.whatsapp_present


class HrefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self.hrefs.extend(value for key, value in attrs if key == "href" and value)


def _has_approved_whatsapp_link(html: str) -> bool:
    parser = HrefParser()
    parser.feed(html)
    return any(
        (parts := urlsplit(href)).scheme == "https"
        and parts.hostname == WHATSAPP_HOST
        and parts.path == WHATSAPP_PATH
        for href in parser.hrefs
    )


def probe(url: str, timeout: float = 15.0) -> Measurement:
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    started = time.perf_counter()
    status: int | None = None
    body = ""
    error = ""
    request = Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urlopen(request, timeout=timeout) as response:
            status = response.status
            body = response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        status = exc.code
        body = exc.read().decode("utf-8", errors="replace")
        error = f"HTTP_{exc.code}"
    except (URLError, TimeoutError, OSError) as exc:
        error = type(exc).__name__

    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    whatsapp_present = _has_approved_whatsapp_link(body)
    if status == 200 and not whatsapp_present:
        error = "WHATSAPP_MISSING"

    return Measurement(
        timestamp_utc=timestamp,
        url=url,
        http_status=status,
        response_time_ms=elapsed_ms,
        whatsapp_present=whatsapp_present,
        error=error,
    )


def append_measurement(path: Path, measurement: Measurement) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=Measurement.__dataclass_fields__)
        if write_header:
            writer.writeheader()
        writer.writerow(asdict(measurement))


def run_monitor(url: str, output: Path, timeout: float = 15.0) -> Measurement:
    measurement = probe(url, timeout)
    append_measurement(output, measurement)
    return measurement


def _positive_timeout(value: str) -> float:
    timeout = float(value)
    if timeout <= 0:
        raise argparse.ArgumentTypeError("timeout debe ser mayor que cero")
    return timeout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL, help="URL pública a consultar")
    parser.add_argument("--timeout", type=_positive_timeout, default=15.0, help="timeout en segundos")
    parser.add_argument("--output", type=Path, default=Path("monitor_auditora.csv"), help="CSV de salida")
    args = parser.parse_args(argv)

    measurement = run_monitor(args.url, args.output, args.timeout)
    status = measurement.http_status if measurement.http_status is not None else "NO_HTTP"
    result = "OK" if measurement.healthy else "FAIL"
    print(
        f"{result}: HTTP={status} tiempo_ms={measurement.response_time_ms:.3f} "
        f"whatsapp={str(measurement.whatsapp_present).lower()} error={measurement.error or '-'}"
    )
    return 0 if measurement.healthy else 1


if __name__ == "__main__":
    sys.exit(main())
