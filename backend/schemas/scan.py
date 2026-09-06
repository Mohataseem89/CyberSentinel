"""Stable contracts for URL scan requests and verdict names."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from services.url_normalizer import NormalizedURL, URLValidationError, normalize_url


class ScanVerdict(str, Enum):
    """Public verdict vocabulary for future scan responses."""

    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    DANGEROUS = "dangerous"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ScanRequest:
    """A validated, canonical URL scan request."""

    url: NormalizedURL

    @classmethod
    def from_json(cls, payload: Any) -> "ScanRequest":
        if not isinstance(payload, Mapping):
            raise URLValidationError("invalid_json", "A JSON object with a URL is required.")

        if set(payload) - {"url"}:
            raise URLValidationError("unexpected_fields", "Only the 'url' field is accepted.")

        return cls(url=normalize_url(payload.get("url")))


@dataclass(frozen=True)
class ScanResult:
    """Public shape produced by the risk engine; scores can be unavailable."""

    url: str
    final_verdict: ScanVerdict
    threat_score: float | None
    confidence: str
    evidence: Sequence[Mapping[str, Any]]
    limitations: Sequence[str]
