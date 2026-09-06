"""Quota-aware VirusTotal reputation adapter; it never submits URLs for scanning."""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import time
from collections import OrderedDict

import requests

logger = logging.getLogger(__name__)
_CACHE: OrderedDict[str, tuple[float, dict]] = OrderedDict()


def _cache_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def _cached(url: str):
    key = _cache_key(url)
    item = _CACHE.get(key)
    if not item:
        return None
    expires_at, value = item
    if expires_at <= time.monotonic():
        _CACHE.pop(key, None)
        return None
    _CACHE.move_to_end(key)
    return {**value, "cached": True}


def _store(url: str, result: dict) -> dict:
    ttl = max(1, int(os.environ.get("VT_CACHE_TTL_SECONDS", "900")))
    max_entries = max(1, int(os.environ.get("VT_CACHE_MAX_ENTRIES", "1000")))
    key = _cache_key(url)
    _CACHE[key] = (time.monotonic() + ttl, {**result, "cached": False})
    _CACHE.move_to_end(key)
    while len(_CACHE) > max_entries:
        _CACHE.popitem(last=False)
    return _CACHE[key][1]


def _unavailable(message: str, reason: str) -> dict:
    return {"score": None, "positives": 0, "total": 0, "malicious": 0, "suspicious": 0,
            "available": False, "evidence_available": False, "cached": False,
            "message": message, "unavailable_reason": reason}


def check_url_reputation(url: str) -> dict:
    """Look up an existing report only, with bounded requests and no URL logging."""
    cached = _cached(url)
    if cached:
        return cached
    api_key = os.environ.get("VIRUSTOTAL_API_KEY")
    if not api_key:
        return _unavailable("VirusTotal is not configured.", "not_configured")
    try:
        url_id = base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").strip("=")
        response = requests.get(f"https://www.virustotal.com/api/v3/urls/{url_id}", headers={"x-apikey": api_key}, timeout=(2, 8), allow_redirects=False)
        if response.status_code == 200:
            stats = response.json()["data"]["attributes"]["last_analysis_stats"]
            malicious, suspicious = int(stats.get("malicious", 0)), int(stats.get("suspicious", 0))
            harmless, undetected = int(stats.get("harmless", 0)), int(stats.get("undetected", 0))
            total, positives = malicious + suspicious + harmless + undetected, malicious + suspicious
            if total <= 0:
                return _store(url, {"score": None, "positives": 0, "total": 0, "malicious": 0, "suspicious": 0, "available": True, "evidence_available": False, "message": "VirusTotal returned no vendor evidence."})
            return _store(url, {"score": round((positives / total) * 100, 2), "positives": positives, "total": total, "malicious": malicious, "suspicious": suspicious, "available": True, "evidence_available": True, "message": f"{positives}/{total} vendors flagged this URL."})
        if response.status_code == 404:
            return _store(url, {"score": None, "positives": 0, "total": 0, "malicious": 0, "suspicious": 0, "available": True, "evidence_available": False, "message": "VirusTotal has no existing report for this URL."})
        if response.status_code == 429:
            logger.warning("VirusTotal quota exhausted")
            return _unavailable("VirusTotal quota is temporarily exhausted.", "quota_exhausted")
        logger.warning("VirusTotal lookup failed with status %s", response.status_code)
        return _unavailable("VirusTotal reputation is temporarily unavailable.", "provider_error")
    except (requests.RequestException, ValueError, KeyError, TypeError):
        logger.warning("VirusTotal lookup failed", exc_info=True)
        return _unavailable("VirusTotal reputation is temporarily unavailable.", "request_failed")
