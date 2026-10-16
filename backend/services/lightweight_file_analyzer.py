"""Lightweight, non-executing static analysis for supported uploads.

This module intentionally does not replace an antivirus engine.

It identifies structural and content indicators without executing,
rendering, extracting, fetching, or uploading user content.

Individual strings are weighted conservatively to reduce false positives.
"""

import math
import re


MAX_ANALYSIS_BYTES = 2 * 1024 * 1024

URL_RE = re.compile(
    rb"https?://[^\s<>\"']+",
    re.IGNORECASE,
)

SUSPICIOUS_TEXT_PATTERNS = (
    (
        rb"\bpowershell(?:\.exe)?\b",
        "powershell_reference",
        "medium",
    ),
    (
        rb"\bcmd(?:\.exe)?\s+/c\b",
        "command_shell_reference",
        "medium",
    ),
    (
        rb"\bwscript(?:\.exe)?\b|\bcscript(?:\.exe)?\b",
        "script_host_reference",
        "medium",
    ),
    (
        rb"\bmshta(?:\.exe)?\b",
        "mshta_reference",
        "medium",
    ),
    (
        rb"\brundll32(?:\.exe)?\b",
        "rundll32_reference",
        "medium",
    ),
    (
        rb"\bcertutil(?:\.exe)?\b",
        "certutil_reference",
        "low",
    ),
)

DOWNLOAD_OR_EXECUTION_PATTERNS = (
    rb"\binvoke-webrequest\b",
    rb"\binvoke-expression\b",
    rb"\biex\b",
    rb"\bdownloadstring\b",
    rb"\bdownloadfile\b",
    rb"\bstart-process\b",
    rb"\bfrombase64string\b",
    rb"\b-bypass\b",
    rb"\bencodedcommand\b",
)

PDF_PATTERNS = (
    (rb"/JavaScript\b", "pdf_javascript", "high"),
    (rb"/JS\b", "pdf_javascript_action", "high"),
    (rb"/Launch\b", "pdf_launch_action", "high"),
    (rb"/EmbeddedFile\b", "pdf_embedded_file", "high"),
    (rb"/OpenAction\b", "pdf_open_action", "medium"),
    (rb"/AA\b", "pdf_additional_action", "medium"),
    (rb"/URI\b", "pdf_external_uri", "low"),
    (rb"/AcroForm\b", "pdf_form", "low"),
)

IMAGE_SIGNATURES = {
    "png": (b"\x89PNG\r\n\x1a\n",),
    "jpeg": (b"\xff\xd8\xff",),
    "gif": (
        b"GIF87a",
        b"GIF89a",
    ),
}


def _indicator(code, severity, **extra):
    value = {
        "code": code,
        "severity": severity,
    }

    value.update(extra)

    return value


def _read_sample(path):
    with open(path, "rb") as handle:
        return handle.read(MAX_ANALYSIS_BYTES + 1)


def _entropy(data):
    if not data:
        return 0.0

    counts = [0] * 256

    for byte in data:
        counts[byte] += 1

    length = len(data)
    result = 0.0

    for count in counts:
        if not count:
            continue

        probability = count / length
        result -= probability * math.log2(probability)

    return result


def _deduplicate(indicators):
    seen = set()
    result = []

    for indicator in indicators:
        key = (
            indicator.get("code"),
            indicator.get("severity"),
        )

        if key in seen:
            continue

        seen.add(key)
        result.append(indicator)

    return result


def _analyze_text(raw):
    indicators = []
    execution_indicator_count = 0

    for pattern, code, severity in SUSPICIOUS_TEXT_PATTERNS:
        if re.search(pattern, raw, re.IGNORECASE):
            indicators.append(
                _indicator(
                    code,
                    severity,
                )
            )

            if severity == "medium":
                execution_indicator_count += 1

    behavior_matches = 0

    for pattern in DOWNLOAD_OR_EXECUTION_PATTERNS:
        if re.search(pattern, raw, re.IGNORECASE):
            behavior_matches += 1

    if behavior_matches:
        indicators.append(
            _indicator(
                "execution_or_download_behavior",
                (
                    "high"
                    if behavior_matches >= 2
                    else "medium"
                ),
                count=behavior_matches,
            )
        )

    if (
        execution_indicator_count >= 1
        and behavior_matches >= 1
    ):
        indicators.append(
            _indicator(
                "combined_execution_pattern",
                "high",
            )
        )

    urls = URL_RE.findall(raw)

    if len(urls) >= 10:
        indicators.append(
            _indicator(
                "many_embedded_urls",
                "medium",
                count=len(urls),
            )
        )

    return indicators


def _analyze_pdf(raw):
    indicators = []

    if not raw.startswith(b"%PDF-"):
        indicators.append(
            _indicator(
                "pdf_header_mismatch",
                "high",
            )
        )

    for pattern, code, severity in PDF_PATTERNS:
        count = len(
            re.findall(
                pattern,
                raw,
                re.IGNORECASE,
            )
        )

        if count:
            indicators.append(
                _indicator(
                    code,
                    severity,
                    count=count,
                )
            )

    # Also look for suspicious command/download references in textual
    # portions of the bounded PDF sample. Nothing is executed.
    indicators.extend(
        _analyze_text(raw)
    )

    return indicators


def _analyze_image(raw, kind):
    indicators = []

    expected_signatures = IMAGE_SIGNATURES.get(kind)

    if (
        expected_signatures
        and not any(
            raw.startswith(signature)
            for signature in expected_signatures
        )
    ):
        indicators.append(
            _indicator(
                "image_signature_mismatch",
                "high",
            )
        )

    # A PE/DOS marker after the image header can indicate appended or
    # embedded executable-like content. It is only an indicator and does
    # not prove that the image is malicious.
    if b"MZ" in raw[16:]:
        indicators.append(
            _indicator(
                "embedded_executable_marker",
                "medium",
            )
        )

    return indicators


def analyze_lightweight_file(path, kind):
    """Return bounded static indicators without executing the upload."""

    raw = _read_sample(path)
    indicators = []

    if kind == "pdf":
        indicators.extend(
            _analyze_pdf(raw)
        )

    elif kind == "text":
        indicators.extend(
            _analyze_text(raw)
        )

    elif kind in {"png", "jpeg", "gif"}:
        indicators.extend(
            _analyze_image(
                raw,
                kind,
            )
        )

    # Entropy is weak contextual evidence only. It must never independently
    # classify a file as malware.
    if raw and kind in {"text", "html"}:
        entropy_sample = raw[
            : min(
                len(raw),
                262144,
            )
        ]

        entropy = _entropy(
            entropy_sample
        )

        if entropy >= 7.95:
            indicators.append(
                _indicator(
                    "unusually_high_entropy",
                    "low",
                    entropy=round(
                        entropy,
                        2,
                    ),
                )
            )

    return _deduplicate(
        indicators
    )


def highest_indicator_severity(indicators):
    ranking = {
        "low": 1,
        "medium": 2,
        "high": 3,
    }

    highest = None
    highest_rank = 0

    for indicator in indicators:
        severity = indicator.get(
            "severity"
        )

        rank = ranking.get(
            severity,
            0,
        )

        if rank > highest_rank:
            highest = severity
            highest_rank = rank

    return highest