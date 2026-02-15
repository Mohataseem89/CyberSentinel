import cv2
from pyzbar import pyzbar
from PIL import Image
import numpy as np
import logging

logger = logging.getLogger(__name__)

class QRCodeScanner:
    """QR Code scanning and URL extraction"""
    
    @staticmethod
    def decode_qr_code(image_path):
        """
        Decode QR code from image and extract URL
        Returns: dict with url, data_type, and status
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            
            if img is None:
                return {
                    "status": "error",
                    "message": "Failed to read image file"
                }
            
            # Decode QR codes
            decoded_objects = pyzbar.decode(img)
            
            if not decoded_objects:
                # Try with PIL as fallback
                pil_img = Image.open(image_path)
                img_array = np.array(pil_img)
                decoded_objects = pyzbar.decode(img_array)
            
            if not decoded_objects:
                return {
                    "status": "error",
                    "message": "No QR code detected in image"
                }
            
            # Extract data from first QR code
            qr_data = decoded_objects[0]
            decoded_data = qr_data.data.decode('utf-8')
            data_type = qr_data.type
            
            logger.info(f"QR Code decoded: {decoded_data}")
            
            # Check if it's a URL
            is_url = decoded_data.startswith(('http://', 'https://'))
            
            return {
                "status": "success",
                "data": decoded_data,
                "type": data_type,
                "is_url": is_url,
                "qr_count": len(decoded_objects)
            }
            
        except Exception as e:
            logger.error(f"QR decode error: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to decode QR code: {str(e)}"
            }
    
    @staticmethod
    def extract_url_from_data(data):
        """
        Extract URL from QR code data
        Handles various formats
        """
        # Direct URL
        if data.startswith(('http://', 'https://')):
            return data
        
        # WiFi QR code format: WIFI:T:WPA;S:SSID;P:password;;
        if data.startswith('WIFI:'):
            return None
        
        # VCard format
        if data.startswith('BEGIN:VCARD'):
            # Extract URL from vCard if present
            for line in data.split('\n'):
                if line.startswith('URL:'):
                    return line.replace('URL:', '').strip()
            return None
        
        # SMS/Tel formats
        if data.startswith(('tel:', 'sms:', 'mailto:')):
            return None
        
        # If it looks like a URL without protocol
        if '.' in data and ' ' not in data:
            return f"https://{data}"
        
        return None