import logging
from services.ml_predictor import predictor
from services.virustotal_service import check_url_reputation
from services.content_analyzer import ContentAnalyzer

logger = logging.getLogger(__name__)

class HybridURLAnalyzer:
    """
    Hybrid URL Analysis combining:
    - ML Model (30% weight)
    - VirusTotal Reputation (30% weight)
    - Content Analysis (40% weight)
    """
    
    WEIGHTS = {
        "ml": 0.30,
        "virustotal": 0.30,
        "content": 0.40
    }
    
    @staticmethod
    def analyze(url):
        """
        Perform comprehensive URL analysis
        Returns: dict with final verdict and detailed breakdown
        """
        logger.info(f" Analyzing URL: {url}")
        
        results = {
            "url": url,
            "final_verdict": "unknown",
            "threat_score": 0,
            "confidence": "low",
            "breakdown": {},
            "indicators": [],
            "recommendations": []
        }
        
        # 1. ML Model Analysis (30%)
        logger.info(" Running ML analysis...")
        ml_result = predictor.predict(url)
        results["breakdown"]["ml"] = ml_result
        ml_score = ml_result["score"]
        
        # 2. VirusTotal Reputation (30%)
        logger.info(" Checking VirusTotal reputation...")
        vt_result = check_url_reputation(url)
        results["breakdown"]["virustotal"] = vt_result
        vt_score = vt_result["score"]
        
        # 3. Content Analysis (40%)
        logger.info(" Analyzing webpage content...")
        content_result = ContentAnalyzer.analyze_content(url)
        results["breakdown"]["content"] = content_result
        content_score = content_result["score"]
        
        # Calculate weighted threat score
        threat_score = (
            ml_score * HybridURLAnalyzer.WEIGHTS["ml"] +
            vt_score * HybridURLAnalyzer.WEIGHTS["virustotal"] +
            content_score * HybridURLAnalyzer.WEIGHTS["content"]
        )
        
        results["threat_score"] = round(threat_score, 2)
        
        # Determine final verdict
        if threat_score >= 70:
            results["final_verdict"] = "Phishing"
            results["confidence"] = "high"
            results["recommendations"].append(" DO NOT enter any personal information")
            results["recommendations"].append(" Block this URL immediately")
            
        elif threat_score >= 50:
            results["final_verdict"] = "Suspicious"
            results["confidence"] = "medium"
            results["recommendations"].append(" Proceed with extreme caution")
            results["recommendations"].append(" Verify the sender/source")
            
        elif threat_score >= 30:
            results["final_verdict"] = "Potentially Risky"
            results["confidence"] = "low"
            results["recommendations"].append(" Be cautious")
            results["recommendations"].append(" Verify URL authenticity")
            
        else:
            results["final_verdict"] = "Benign"
            results["confidence"] = "high"
            results["recommendations"].append(" URL appears safe")
        
        # Collect all indicators
        results["indicators"].extend(content_result["indicators"])
        
        if ml_result["prediction"] == "phishing":
            results["indicators"].append(f"ML Model: {ml_result['confidence']:.1%} confidence phishing")
        
        if vt_result["positives"] > 0:
            results["indicators"].append(f"VirusTotal: {vt_result['positives']}/{vt_result['total']} vendors flagged")
        
        logger.info(f" Analysis complete: {results['final_verdict']} (Score: {threat_score:.1f})")
        
        return results