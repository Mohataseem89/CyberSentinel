"""Foundation for a future isolated, SSRF-safe metadata worker.

This module intentionally performs no HTTP requests. It provides the public-IP
resolution check that must run before *every* future redirect hop, but remote
metadata collection remains disabled until the transport is isolated and can
pin validated DNS answers to outbound connections.
"""

from __future__ import annotations

import ipaddress
import socket

from services.url_normalizer import NormalizedURL


class UnsafeResolutionError(ValueError):
    """Raised when DNS returns a private, reserved, or otherwise non-public IP."""


def resolve_public_addresses(hostname: str) -> tuple[str, ...]:
    """Resolve a hostname and reject every non-global address.

    This is deliberately fail-closed. It is not sufficient to make arbitrary
    HTTP fetching safe: a later isolated worker must also pin these verified
    addresses for the actual connection to prevent DNS rebinding.
    """

    try:
        records = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as error:
        raise UnsafeResolutionError("Hostname could not be resolved.") from error

    addresses = tuple(sorted({record[4][0] for record in records}))
    if not addresses:
        raise UnsafeResolutionError("Hostname did not resolve to an address.")

    for address in addresses:
        if not ipaddress.ip_address(address).is_global:
            raise UnsafeResolutionError("Hostname resolves to a non-public address.")
    return addresses


class SafeMetadataWorker:
    """Disabled-by-design remote metadata worker contract."""

    def inspect(self, url: NormalizedURL) -> dict:
        return {
            "available": False,
            "status": "disabled",
            "message": "Remote metadata checks are disabled until an isolated worker is implemented.",
            "hostname": url.hostname,
        }
