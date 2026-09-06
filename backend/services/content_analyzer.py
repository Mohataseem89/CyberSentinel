

class ContentAnalyzer:
    """Return an explicit unavailable state until an isolated worker is ready."""

    @staticmethod
    def analyze_content(_url: str) -> dict:
        return {
            "score": None,
            "available": False,
            "indicators": [],
            "details": {
                "status": "not_performed",
                "reason": "Remote page-content analysis is disabled for SSRF protection.",
            },
        }
