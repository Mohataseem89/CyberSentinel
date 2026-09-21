import logging

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class QRCodeScanner:
    """QR Code scanning and URL extraction."""

    @staticmethod
    def _get_pyzbar():
        """
        Load pyzbar only when QR decoding is requested.

        pyzbar depends on the native ZBar shared library. Some production
        environments do not provide ZBar, so importing pyzbar at module
        startup must not prevent the entire API from starting.
        """
        try:
            from pyzbar import pyzbar

            return pyzbar
        except (ImportError, OSError) as exc:
            logger.warning(
                "QR decoding is unavailable because the ZBar runtime "
                "could not be loaded."
            )
            return None

    @staticmethod
    def decode_qr_code(image_path):
        """
        Decode QR code from image and extract its payload.

        Returns a dictionary containing status and decoded QR information.
        QR decoding being unavailable must not crash the application.
        """
        pyzbar = QRCodeScanner._get_pyzbar()

        if pyzbar is None:
            return {
                "status": "unavailable",
                "message": (
                    "QR code decoding is temporarily unavailable on "
                    "this deployment."
                ),
            }

        try:
            # Read image with OpenCV first.
            img = cv2.imread(image_path)

            if img is None:
                return {
                    "status": "error",
                    "message": "Failed to read image file",
                }

            decoded_objects = pyzbar.decode(img)

            if not decoded_objects:
                # Try PIL representation as a fallback.
                with Image.open(image_path) as pil_img:
                    img_array = np.array(pil_img)
                    decoded_objects = pyzbar.decode(img_array)

            if not decoded_objects:
                return {
                    "status": "error",
                    "message": "No QR code detected in image",
                }

            qr_data = decoded_objects[0]

            try:
                decoded_data = qr_data.data.decode("utf-8")
            except UnicodeDecodeError:
                return {
                    "status": "error",
                    "message": "QR code contains unsupported text encoding",
                }

            data_type = qr_data.type

            # Never log the raw QR payload. It can contain URLs with
            # credentials, reset tokens, query parameters, or other
            # sensitive information.
            logger.info(
                "QR code decoded successfully (type=%s, count=%d)",
                data_type,
                len(decoded_objects),
            )

            decoded_data = decoded_data.strip().lstrip("\ufeff")

            normalized_url = QRCodeScanner.extract_url_from_data(decoded_data)

            return {
                "status": "success",
                "data": normalized_url or decoded_data,
                "type": data_type,
                "is_url": normalized_url is not None,
                "qr_count": len(decoded_objects),
            }

        except (OSError, ValueError) as exc:
            logger.warning(
                "QR decode failed due to image/runtime error: %s",
                type(exc).__name__,
            )
            return {
                "status": "error",
                "message": "Failed to decode QR code",
            }
        except Exception:
            logger.exception("Unexpected QR decode failure")
            return {
                "status": "error",
                "message": "Failed to decode QR code",
            }

    @staticmethod
    def extract_url_from_data(data):
        """
        Extract URL from QR code data.

        Handles direct URLs and selected common QR payload formats.
        """
        if not isinstance(data, str):
            return None

        data = data.strip()

        if not data:
            return None

        # Direct URL
        if data.startswith(("http://", "https://")):
            return data

        # WiFi QR code format: WIFI:T:WPA;S:SSID;P:password;;
        if data.startswith("WIFI:"):
            return None

        # vCard format
        if data.startswith("BEGIN:VCARD"):
            for line in data.splitlines():
                if line.startswith("URL:"):
                    return line.replace("URL:", "", 1).strip()
            return None

        # SMS/Tel/email formats
        if data.startswith(("tel:", "sms:", "mailto:")):
            return None

        # URL-like value without protocol
        if "." in data and " " not in data:
            return f"https://{data}"

        return None