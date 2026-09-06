import socket
import unittest
from unittest.mock import patch

from services.content_analyzer import ContentAnalyzer
from workers.safe_metadata_worker import UnsafeResolutionError, resolve_public_addresses


class SafeAnalysisTests(unittest.TestCase):
    def test_content_analysis_is_explicitly_disabled_and_network_free(self):
        result = ContentAnalyzer.analyze_content("https://example.com")

        self.assertFalse(result["available"])
        self.assertIsNone(result["score"])
        self.assertEqual(result["details"]["status"], "not_performed")

    @patch("workers.safe_metadata_worker.socket.getaddrinfo")
    def test_worker_rejects_any_non_public_dns_answer(self, getaddrinfo):
        getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0)),
        ]

        with self.assertRaises(UnsafeResolutionError):
            resolve_public_addresses("mixed.example")

    @patch("workers.safe_metadata_worker.socket.getaddrinfo")
    def test_worker_accepts_only_public_dns_answers(self, getaddrinfo):
        getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 0)),
            (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("2001:4860:4860::8888", 0, 0, 0)),
        ]

        self.assertEqual(resolve_public_addresses("public.example"), ("2001:4860:4860::8888", "8.8.8.8"))
