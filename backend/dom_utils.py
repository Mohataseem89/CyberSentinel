import requests
from bs4 import BeautifulSoup

def try_fetch_dom_summary(url: str, timeout: int = 5) -> str | None:
    """
    Attempts to fetch and summarize page content.
    NON-BLOCKING: returns None if unreachable.
    """

    try:
        if not url.startswith("http"):
            url = "http://" + url

        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "CyberSentinel/1.0"}
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract visible text (lightweight summary)
        texts = soup.stripped_strings
        summary = " ".join(list(texts)[:200])  # limit tokens

        return summary

    except Exception as e:
        print(f"[DOM] Skipped content analysis: {e}")
        return None
