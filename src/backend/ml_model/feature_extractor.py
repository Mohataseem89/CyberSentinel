import re
from urllib.parse import urlparse
import tld
import socket

class URLFeatureExtractor:
    """Extract features from URLs for ML model"""
    
    @staticmethod
    def extract_features(url):
        """
        Extract 20+ features from a URL
        Returns: dictionary of features
        """
        features = {}
        
        try:
            # Validate URL is a string
            if not isinstance(url, str):
                url = str(url) if url is not None else ""
            
            # Skip empty or invalid URLs
            if not url or url == 'nan' or len(url) < 5:
                # Return default features
                return {f'feature_{i}': 0 for i in range(21)}
            
            parsed = urlparse(url)
            domain = parsed.netloc
            path = parsed.path
            
            # 1 URL Length
            features['url_length'] = len(url)
            
            # 2 Domain Length
            features['domain_length'] = len(domain)
            
            # 3 Path Length
            features['path_length'] = len(path)
            
            # 4 number of dots
            features['num_dots'] = url.count('.')
            
            # 5 number of hyphens
            features['num_hyphens'] = url.count('-')
            
            # 6 number of underscores
            features['num_underscores'] = url.count('_')
            
            # 7 number of slashes
            features['num_slashes'] = url.count('/')
            
            # 8 number of question marks
            features['num_question'] = url.count('?')
            
            # 9 number of equals
            features['num_equals'] = url.count('=')
            
            # 10 number of @ symbols
            features['num_at'] = url.count('@')
            
            # 11 number of ampersands
            features['num_ampersand'] = url.count('&')
            
            # 12 number of digits
            features['num_digits'] = sum(c.isdigit() for c in url)
            
            # 13 has IP address (instead of domain name)
            features['has_ip'] = 1 if re.search(r'\d+\.\d+\.\d+\.\d+', domain) else 0
            
            # 14 uses HTTPS
            features['is_https'] = 1 if parsed.scheme == 'https' else 0
            
            # 15 number of subdomains
            features['num_subdomains'] = len(domain.split('.')) - 2 if domain else 0
            
            # 16 has suspicious keywords
            suspicious_keywords = ['login', 'verify', 'account', 'secure', 'update', 
                                   'confirm', 'banking', 'paypal', 'ebay', 'signin']
            features['has_suspicious_words'] = 1 if any(kw in url.lower() for kw in suspicious_keywords) else 0
            
            # 17 has double slashes in path
            features['has_double_slash'] = 1 if '//' in path else 0
            
            # 18 uses URL shortener
            shorteners = ['bit.ly', 'tinyurl', 'goo.gl', 't.co', 'ow.ly']
            features['is_shortened'] = 1 if any(short in domain for short in shorteners) else 0
            
            # 19 entropy of URL (randomness)
            features['entropy'] = URLFeatureExtractor._calculate_entropy(url)
            
            # 20 ratio of digits to total length
            features['digit_ratio'] = features['num_digits'] / max(len(url), 1)
            
            # 21 has port number
            features['has_port'] = 1 if parsed.port else 0
            
        except Exception as e:
            print(f"Error extracting features: {e}")
            # Return default features if error
            features = {f'feature_{i}': 0 for i in range(21)}
        
        return features
    
    @staticmethod
    def _calculate_entropy(string):
        """Calculate Shannon entropy of a string"""
        import math
        from collections import Counter
        
        if not string:
            return 0
        
        counts = Counter(string)
        length = len(string)
        
        entropy = -sum((count/length) * math.log2(count/length) 
                      for count in counts.values())
        
        return entropy