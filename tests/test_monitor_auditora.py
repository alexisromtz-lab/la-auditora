# HUELLA-TEST-MONITOR-AUDITORA-20261031

import csv
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
import unittest

from tools.monitor_auditora import run_monitor


class MonitorHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/healthy":
            status = 200
            body = '<a href="https://wa.me/525649997759?text=contact">WhatsApp</a>'
        elif self.path == "/missing-link":
            status = 200
            body = "<p>Site is online</p>"
        else:
            status = 503
            body = "temporarily unavailable"
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: object) -> None:
        return


class MonitorAuditoraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), MonitorHandler)
        cls.server_thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join()

    def test_records_http_latency_and_whatsapp_link(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / "telemetry.csv"
            result = run_monitor(f"{self.base_url}/healthy", output)
            with output.open(newline="", encoding="utf-8") as csv_file:
                rows = list(csv.DictReader(csv_file))

        self.assertTrue(result.healthy)
        self.assertGreaterEqual(result.response_time_ms, 0)
        self.assertEqual(rows[0]["http_status"], "200")
        self.assertEqual(rows[0]["whatsapp_present"], "True")
        self.assertEqual(rows[0]["error"], "")

    def test_records_http_error_and_reports_unhealthy(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / "telemetry.csv"
            result = run_monitor(f"{self.base_url}/unavailable", output)
            with output.open(newline="", encoding="utf-8") as csv_file:
                rows = list(csv.DictReader(csv_file))

        self.assertEqual(result.http_status, 503)
        self.assertFalse(result.healthy)
        self.assertEqual(rows[0]["http_status"], "503")
        self.assertEqual(rows[0]["whatsapp_present"], "False")
        self.assertEqual(rows[0]["error"], "HTTP_503")

    def test_missing_whatsapp_link_is_unhealthy(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / "telemetry.csv"
            result = run_monitor(f"{self.base_url}/missing-link", output)

        self.assertEqual(result.http_status, 200)
        self.assertFalse(result.healthy)
        self.assertEqual(result.error, "WHATSAPP_MISSING")


if __name__ == "__main__":
    unittest.main()
