import unittest

from services.url_normalizer import URLValidationError, normalize_url


class URLNormalizerTests(unittest.TestCase):
    def test_adds_https_and_normalizes_idna_hostname(self):
        normalized = normalize_url("BÜCHER.example/path#client-only")

        self.assertEqual(normalized.url, "https://xn--bcher-kva.example/path")
        self.assertEqual(normalized.hostname, "xn--bcher-kva.example")
        self.assertEqual(normalized.scheme, "https")

    def test_preserves_valid_non_default_port(self):
        normalized = normalize_url("https://example.com:8443/check")

        self.assertEqual(normalized.url, "https://example.com:8443/check")
        self.assertEqual(normalized.port, 8443)

    def test_rejects_non_http_scheme(self):
        self.assert_error("file:///etc/passwd", "unsupported_scheme")

    def test_rejects_localhost_and_ip_literals(self):
        self.assert_error("http://localhost:5000", "private_host")
        self.assert_error("http://127.0.0.1", "ip_literal_not_allowed")
        self.assert_error("http://[::1]", "ip_literal_not_allowed")

    def test_rejects_embedded_credentials_and_whitespace(self):
        self.assert_error("https://user:pass@example.com", "credentials_not_allowed")
        self.assert_error("https://example.com/a path", "invalid_url")

    def test_rejects_too_long_url(self):
        self.assert_error("https://example.com/" + "a" * 2_050, "url_too_long")

    def assert_error(self, value, code):
        with self.assertRaises(URLValidationError) as raised:
            normalize_url(value)
        self.assertEqual(raised.exception.code, code)


if __name__ == "__main__":
    unittest.main()
