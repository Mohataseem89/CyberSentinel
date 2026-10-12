import logging
import os
import time

import requests


log = logging.getLogger(__name__)

TRIGGER_URL = os.getenv("BULK_TRIGGER_URL", "").strip()
TRIGGER_SECRET = os.getenv("BULK_TRIGGER_SECRET", "").strip()

MAX_ATTEMPTS = int(os.getenv("BULK_TRIGGER_MAX_ATTEMPTS", "3"))
TIMEOUT_SECONDS = float(os.getenv("BULK_TRIGGER_TIMEOUT_SECONDS", "15"))


class BulkTriggerError(RuntimeError):
    pass


def trigger_bulk_worker():
    if not TRIGGER_URL or not TRIGGER_SECRET:
        raise BulkTriggerError("Bulk worker trigger is not configured.")

    last_error = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.post(
                TRIGGER_URL,
                headers={
                    "X-Trigger-Secret": TRIGGER_SECRET,
                },
                timeout=TIMEOUT_SECONDS,
            )

            if response.status_code == 202:
                return True

            # Authentication/configuration errors will not become successful
            # simply by retrying.
            if response.status_code in {400, 401, 403, 404, 405}:
                raise BulkTriggerError(
                    f"Bulk worker trigger returned HTTP "
                    f"{response.status_code}."
                )

            last_error = BulkTriggerError(
                f"Bulk worker trigger returned HTTP "
                f"{response.status_code}."
            )

        except requests.Timeout as exc:
            last_error = BulkTriggerError(
                "Bulk worker trigger timed out."
            )
            log.warning(
                "Bulk worker trigger timeout attempt=%s/%s",
                attempt,
                MAX_ATTEMPTS,
            )

        except requests.RequestException as exc:
            last_error = BulkTriggerError(
                "Bulk worker trigger request failed."
            )
            log.warning(
                "Bulk worker trigger request failed "
                "attempt=%s/%s error=%s",
                attempt,
                MAX_ATTEMPTS,
                type(exc).__name__,
            )

        if attempt < MAX_ATTEMPTS:
            time.sleep(min(2 ** (attempt - 1), 4))

    raise last_error or BulkTriggerError(
        "Bulk worker trigger failed."
    )