import requests
from bs4 import BeautifulSoup
import ssl
import socket
from urllib.parse import urlparse
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class ContentAnalyzer:
    """Analyze webpage content for phishing indicators"""
    
    @staticmethod
    def analyze_content(url, timeout=10):
        """
        Analyze webpage content for suspicious patterns
        Returns: dict with analysis results and score
        """
        analysis = {
            "score": 0,
            "indicators": [],
            "details": {}
        }
        
        try:
            # fetch webpage content
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            
            # Check SSL certificate
            ssl_score = ContentAnalyzer._check_ssl(url)
            analysis["details"]["ssl"] = ssl_score
            
            if ssl_score["has_issues"]:
                analysis["score"] += 30
                analysis["indicators"].append("SSL certificate issues")
            
            # to parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            #  login forms chk krne ke liye
            forms = soup.find_all('form')
            password_fields = soup.find_all('input', {'type': 'password'})
            
            if password_fields:
                analysis["details"]["has_login_form"] = True
                
                # known login page hai ki nhi
                parsed = urlparse(url)
                trusted_domains = [
                    'google.com', 'facebook.com', 'twitter.com', 'microsoft.com',
                    'amazon.com', 'paypal.com', 'apple.com', 'linkedin.com',
                    'instagram.com', 'github.com', 'stackoverflow.com'
                ]
                
                domain = parsed.netloc.lower()
                is_trusted = any(trusted in domain for trusted in trusted_domains)
                
                if not is_trusted and password_fields:
                    analysis["score"] += 25
                    analysis["indicators"].append("Login form on untrusted domain")
            
            # to Check for brand impersonation
            brand_keywords = {
                'paypal': ['paypal', 'payment', 'send money'],
                'bank': ['bank', 'banking', 'account'],
                'amazon': ['amazon', 'prime', 'aws'],
                'microsoft': ['microsoft', 'office', 'outlook'],
                'google': ['google', 'gmail', 'drive']
            }
            
            page_text = soup.get_text().lower()
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            for brand, keywords in brand_keywords.items():
                if any(kw in page_text for kw in keywords) and brand not in domain:
                    analysis["score"] += 20
                    analysis["indicators"].append(f"Possible {brand} impersonation")
                    break
            
            #  Check for suspicious JavaScript
            scripts = soup.find_all('script')
            suspicious_js_patterns = [
                'document.cookie', 'localStorage', 'sessionStorage',
                'btoa', 'atob', 'eval(', 'XMLHttpRequest'
            ]
            
            for script in scripts:
                script_text = script.string if script.string else ""
                if any(pattern in script_text for pattern in suspicious_js_patterns):
                    analysis["score"] += 10
                    analysis["indicators"].append("Suspicious JavaScript detected")
                    break
            
            # to Check for hidden iframes
            iframes = soup.find_all('iframe', style=lambda value: value and 'display:none' in value)
            if iframes:
                analysis["score"] += 15
                analysis["indicators"].append("Hidden iframes detected")
            
            # check for excessive redirects
            if len(response.history) > 2:
                analysis["score"] += 10
                analysis["indicators"].append(f"{len(response.history)} redirects detected")
            
            # check for suspicious form actions
            for form in forms:
                action = form.get('action', '')
                if action.startswith('http') and urlparse(action).netloc != parsed_url.netloc:
                    analysis["score"] += 20
                    analysis["indicators"].append("Form submits to different domain")
            
            # check page title for suspicious patterns
            title = soup.find('title')
            if title:
                title_text = title.get_text().lower()
                suspicious_title_words = ['verify', 'suspended', 'urgent', 'alert', 'confirm']
                if any(word in title_text for word in suspicious_title_words):
                    analysis["score"] += 10
                    analysis["indicators"].append("Suspicious page title")
            
            # check for fake security badges
            images = soup.find_all('img')
            for img in images:
                alt_text = img.get('alt', '').lower()
                if any(badge in alt_text for badge in ['secure', 'verified', 'ssl', 'trusted']):
                    analysis["score"] += 5
                    analysis["indicators"].append("Security badge detected (may be fake)")
            
            # normalize score to 0-100
            analysis["score"] = min(analysis["score"], 100)
            
            logger.info(f"Content analysis completed. Score: {analysis['score']}")
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout accessing {url}")
            analysis["score"] = 40
            analysis["indicators"].append("Website timeout (suspicious)")
            
        except requests.exceptions.SSLError:
            logger.warning(f"SSL error for {url}")
            analysis["score"] = 60
            analysis["indicators"].append("SSL certificate error")
            
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error for {url}")
            analysis["score"] = 50
            analysis["indicators"].append("Cannot connect to website")
            
        except Exception as e:
            logger.error(f"Content analysis error: {str(e)}")
            analysis["score"] = 50
            analysis["indicators"].append("Analysis error")
        
        return analysis
    
    @staticmethod
    def _check_ssl(url):
        """Check SSL certificate validity"""
        result = {
            "has_https": False,
            "has_issues": False,
            "details": ""
        }
        
        try:
            parsed = urlparse(url)
            
            if parsed.scheme != 'https':
                result["has_issues"] = True
                result["details"] = "Not using HTTPS"
                return result
            
            result["has_https"] = True
            
            # Check certificate
            hostname = parsed.netloc.split(':')[0]
            context = ssl.create_default_context()
            
            with socket.create_connection((hostname, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Certificate exists and is valid
                    result["details"] = "Valid SSL certificate"
            
        except ssl.SSLCertVerificationError:
            result["has_issues"] = True
            result["details"] = "Invalid SSL certificate"
            
        except Exception as e:
            logger.debug(f"SSL check error: {str(e)}")
            result["details"] = "Could not verify SSL"
        
        return result