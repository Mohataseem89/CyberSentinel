"""Versioned, deterministic lexical features for URL classification."""

from __future__ import annotations

from collections import Counter
import ipaddress
import math
from urllib.parse import urlsplit

FEATURE_SCHEMA_VERSION = 1
FEATURE_NAMES = (
    "url_length", "domain_length", "path_length", "num_dots", "num_hyphens",
    "num_underscores", "num_slashes", "num_question", "num_equals", "num_at",
    "num_ampersand", "num_digits", "has_ip", "is_https", "num_subdomains",
    "has_suspicious_words", "has_double_slash", "is_shortened", "entropy",
    "digit_ratio", "has_port",
)
SUSPICIOUS_KEYWORDS = frozenset({"login", "verify", "account", "secure", "update", "confirm", "banking", "paypal", "ebay", "signin"})
SHORTENER_HOSTS = frozenset({"bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly"})


class URLFeatureExtractor:
    """Extract exactly ``FEATURE_NAMES`` for every supplied URL-like string."""

    feature_names = FEATURE_NAMES
    schema_version = FEATURE_SCHEMA_VERSION

    @classmethod
    def extract_features(cls, url: object) -> dict[str, float | int]:
        value = "" if url is None else str(url).strip()
        parsed = cls._parse(value)
        hostname = (parsed.hostname or "").lower().rstrip(".")
        path = parsed.path or "/"
        try:
            port = parsed.port
        except ValueError:
            port = None

        digit_count = sum(character.isdigit() for character in value)
        features: dict[str, float | int] = {
            "url_length": len(value), "domain_length": len(hostname), "path_length": len(path),
            "num_dots": value.count("."), "num_hyphens": value.count("-"),
            "num_underscores": value.count("_"), "num_slashes": value.count("/"),
            "num_question": value.count("?"), "num_equals": value.count("="),
            "num_at": value.count("@"), "num_ampersand": value.count("&"),
            "num_digits": digit_count, "has_ip": int(cls._is_ip_literal(hostname)),
            "is_https": int(parsed.scheme.lower() == "https"),
            "num_subdomains": max(0, len(hostname.split(".")) - 2) if hostname else 0,
            "has_suspicious_words": int(any(keyword in value.lower() for keyword in SUSPICIOUS_KEYWORDS)),
            "has_double_slash": int("//" in path), "is_shortened": int(hostname in SHORTENER_HOSTS),
            "entropy": cls._calculate_entropy(value), "digit_ratio": digit_count / max(len(value), 1),
            "has_port": int(port is not None),
        }
        if tuple(features) != FEATURE_NAMES:
            raise RuntimeError("Feature schema does not match FEATURE_NAMES.")
        return features

    @staticmethod
    def _parse(value: str):
        try:
            return urlsplit(value if "://" in value else f"https://{value}")
        except ValueError:
            # Historic datasets contain malformed URL strings. Preserve the
            # lexical features while keeping hostname/path-derived values safe.
            return urlsplit("https://")

    @staticmethod
    def _is_ip_literal(hostname: str) -> bool:
        try:
            ipaddress.ip_address(hostname)
            return True
        except ValueError:
            return False

    @staticmethod
    def _calculate_entropy(value: str) -> float:
        if not value:
            return 0.0
        counts = Counter(value)
        length = len(value)
        return -sum((count / length) * math.log2(count / length) for count in counts.values())
