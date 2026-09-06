import unittest

from schemas.scan import ScanRequest, ScanVerdict
from services.url_normalizer import URLValidationError


class ScanSchemaTests(unittest.TestCase):
    def test_accepts_only_a_url_field(self):
        request = ScanRequest.from_json({"url": "example.com"})

        self.assertEqual(request.url.url, "https://example.com/")

    def test_rejects_non_object_and_unexpected_fields(self):
        self.assert_error([], "invalid_json")
        self.assert_error({"url": "example.com", "force": True}, "unexpected_fields")

    def test_public_verdict_vocabulary_is_stable(self):
        self.assertEqual(
            {verdict.value for verdict in ScanVerdict},
            {"safe", "suspicious", "dangerous", "unknown"},
        )

    def assert_error(self, payload, code):
        with self.assertRaises(URLValidationError) as raised:
            ScanRequest.from_json(payload)
        self.assertEqual(raised.exception.code, code)


if __name__ == "__main__":
    unittest.main()
