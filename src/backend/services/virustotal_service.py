import requests
import os
import logging

logger = logging.getLogger(__name__)

VIRUSTOTAL_API_KEY = os.environ.get('VIRUSTOTAL_API_KEY', '578cce9028f4b8d628f643b14bd4c0f6ccc75ec06fe6ac006b723a8ebc8d75f6')

def check_url_reputation(url):
    """
    Check URL reputation using VirusTotal API
    Returns: dict with reputation score and details
    """
    # if not VIRUSTOTAL_API_KEY or VIRUSTOTAL_API_KEY == '578cce9028f4b8d628f643b14bd4c0f6ccc75ec06fe6ac006b723a8ebc8d75f6':
    if not VIRUSTOTAL_API_KEY:
        logger.warning("VirusTotal API key not configured")
        return {
            "score": 50,  # Neutral score
            "positives": 0,
            "total": 0,
            "message": "VirusTotal not configured"
        }
    
    try:
        # VirusTotal URL scanning endpoint
        headers = {
            "x-apikey": VIRUSTOTAL_API_KEY
        }
        
        # Submit URL for scanning
        scan_url = "https://www.virustotal.com/api/v3/urls"
        
        import base64
        url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
        
        # Check if URL already scanned
        check_url = f"https://www.virustotal.com/api/v3/urls/{url_id}"
        
        response = requests.get(check_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            stats = data['data']['attributes']['last_analysis_stats']
            
            malicious = stats.get('malicious', 0)
            suspicious = stats.get('suspicious', 0)
            harmless = stats.get('harmless', 0)
            undetected = stats.get('undetected', 0)
            
            total = malicious + suspicious + harmless + undetected
            positives = malicious + suspicious
            
            # Calculate reputation score (0-100, lower is better)
            if total > 0:
                reputation_score = (positives / total) * 100
            else:
                reputation_score = 50
            
            return {
                "score": reputation_score,
                "positives": positives,
                "total": total,
                "malicious": malicious,
                "suspicious": suspicious,
                "harmless": harmless,
                "message": f"{positives}/{total} vendors flagged this URL"
            }
        
        else:
            # URL not in database, submit for scanning
            logger.info("URL not in VirusTotal database")
            return {
                "score": 50,
                "positives": 0,
                "total": 0,
                "message": "URL not previously scanned"
            }
    
    except Exception as e:
        logger.error(f"VirusTotal error: {str(e)}")
        return {
            "score": 50,
            "positives": 0,
            "total": 0,
            "message": "VirusTotal check failed"
        }