"""Strict, side-effect-free validation and canonicalization for scan URLs."""

from __future__ import annotations

from dataclasses import dataclass
import ipaddress
from typing import Any
from urllib.parse import SplitResult, urlsplit, urlunsplit


MAX_URL_LENGTH = 2_048
ALLOWED_SCHEMES = frozenset({"http", "https"})


class URLValidationError(ValueError):
    """A client-safe validation error with a stable machine-readable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class NormalizedURL:
    url: str
    scheme: str
    hostname: str
    port: int | None


def normalize_url(value: Any) -> NormalizedURL:
    """Return one canonical public HTTP(S) URL without making a network request.

    A missing scheme is normalized to HTTPS. URL fragments are intentionally
    removed because they are client-side only and must not affect a scan.
    """

    if not isinstance(value, str):
        raise URLValidationError("invalid_url", "URL must be a string.")

    candidate = value.strip()
    if not candidate:
        raise URLValidationError("missing_url", "URL is required.")
    if len(candidate) > MAX_URL_LENGTH:
        raise URLValidationError("url_too_long", f"URL must be at most {MAX_URL_LENGTH} characters.")
    if any(char.isspace() or ord(char) < 32 for char in candidate):
        raise URLValidationError("invalid_url", "URL must not contain whitespace or control characters.")

    if "://" not in candidate:
        candidate = f"https://{candidate}"

    try:
        parsed = urlsplit(candidate)
    except ValueError as error:
        raise URLValidationError("invalid_url", "URL could not be parsed.") from error

    scheme = parsed.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise URLValidationError("unsupported_scheme", "Only HTTP and HTTPS URLs can be scanned.")
    if not parsed.netloc or not parsed.hostname:
        raise URLValidationError("invalid_host", "URL must include a public hostname.")
    if parsed.username is not None or parsed.password is not None:
        raise URLValidationError("credentials_not_allowed", "URLs with embedded credentials are not accepted.")

    try:
        hostname = parsed.hostname.encode("idna").decode("ascii").lower().rstrip(".")
    except UnicodeError as error:
        raise URLValidationError("invalid_host", "Hostname is not valid internationalized-domain input.") from error

    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise URLValidationError("private_host", "Localhost URLs cannot be scanned.")

    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        raise URLValidationError("ip_literal_not_allowed", "IP-address URLs cannot be scanned.")

    try:
        port = parsed.port
    except ValueError as error:
        raise URLValidationError("invalid_port", "URL contains an invalid port.") from error

    if port is not None and not 1 <= port <= 65_535:
        raise URLValidationError("invalid_port", "URL contains an invalid port.")

    netloc = hostname
    if port is not None and port not in {80 if scheme == "http" else 443}:
        netloc = f"{hostname}:{port}"

    path = parsed.path or "/"
    normalized = urlunsplit(SplitResult(scheme, netloc, path, parsed.query, ""))
    if len(normalized) > MAX_URL_LENGTH:
        raise URLValidationError("url_too_long", f"URL must be at most {MAX_URL_LENGTH} characters.")

    return NormalizedURL(url=normalized, scheme=scheme, hostname=hostname, port=port)
