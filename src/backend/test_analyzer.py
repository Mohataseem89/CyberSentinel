from services.url_analyzer import HybridURLAnalyzer

def test_analyzer():
    print(" Testing CyberSentinel URL Analyzer\n")
    
    test_urls = [
        "https://google.com",
        "http://facebook-login-verification-alert.com",
        "https://github.com",
        "http://verify-paypal-account.tk"
    ]
    
    analyzer = HybridURLAnalyzer()
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Testing: {url}")
        print('='*60)
        
        result = analyzer.analyze(url)
        
        print(f"Verdict: {result['final_verdict']}")
        print(f"Threat Score: {result['threat_score']:.1f}%")
        print(f"Confidence: {result['confidence']}")
        print(f"\nBreakdown:")
        print(f"  - ML Score: {result['breakdown']['ml']['score']:.1f}%")
        print(f"  - VirusTotal Score: {result['breakdown']['virustotal']['score']:.1f}%")
        print(f"  - Content Score: {result['breakdown']['content']['score']:.1f}%")
        
        if result['indicators']:
            print(f"\nIndicators:")
            for ind in result['indicators'][:3]:
                print(f"  • {ind}")

if __name__ == "__main__":
    test_analyzer()