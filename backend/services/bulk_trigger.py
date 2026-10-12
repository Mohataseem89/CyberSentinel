import logging
import os

import requests


log = logging.getLogger(__name__)

TRIGGER_URL = os.getenv("BULK_TRIGGER_URL", "").strip()
TRIGGER_SECRET = os.getenv("BULK_TRIGGER_SECRET", "").strip()


def trigger_bulk_worker():
    if not TRIGGER_URL or not TRIGGER_SECRET:
        raise RuntimeError("Bulk worker trigger is not configured.")

    response = requests.post(
        TRIGGER_URL,
        headers={
            "X-Trigger-Secret": TRIGGER_SECRET,
        },
        timeout=15,
    )

    if response.status_code != 202:
        raise RuntimeError(
            f"Bulk worker trigger returned HTTP {response.status_code}."
        )

    return True