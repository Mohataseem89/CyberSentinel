
import { useState, useEffect } from 'react';
import { Shield, AlertTriangle, CheckCircle, XCircle, TrendingUp, Activity } from 'lucide-react';
import axios from 'axios';

export default function URLAnalyzer() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [recentSearches, setRecentSearches] = useState([]);


  useEffect(() => {
  const stored = localStorage.getItem('recentUrls');
  if (stored) {
    setRecentSearches(JSON.parse(stored));
  }
}, []);



  const handleAnalyze = async () => {
    if (!url.trim()) {
      alert('Please enter a URL');
      return;
    }

    setLoading(true);

    setResult(null);

    try {
      const response = await axios.post('http://localhost:5000/analyze', { url });
      setResult(response.data);
      // Save to recent searches
      const updated = [url, ...recentSearches.filter(u => u !== url)].slice(0, 5);
      setRecentSearches(updated);
      localStorage.setItem('recentUrls', JSON.stringify(updated));

    } catch (error) {
      console.error('Analysis error:', error);
      setResult({
        final_verdict: 'Error',
        threat_score: 0,
        error: error.response?.data?.error || 'Failed to analyze URL. Check if backend is running.'
      });
    } finally {
      setLoading(false);
    }
  };

  const getVerdictColor = (verdict) => {
    switch (verdict) {
      case 'Benign':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'Potentially Risky':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'Suspicious':
        return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'Phishing':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getVerdictIcon = (verdict) => {
    switch (verdict) {
      case 'Benign':
        return <CheckCircle className="w-8 h-8 text-green-600" />;
      case 'Potentially Risky':
        return <AlertTriangle className="w-8 h-8 text-yellow-600" />;
      case 'Suspicious':
        return <AlertTriangle className="w-8 h-8 text-orange-600" />;
      case 'Phishing':
        return <XCircle className="w-8 h-8 text-red-600" />;
      default:
        return <Shield className="w-8 h-8 text-gray-600" />;
    }
  };

  const getThreatLevel = (score) => {
    if (score >= 70) return { label: 'Critical', color: 'bg-red-500' };
    if (score >= 50) return { label: 'High', color: 'bg-orange-500' };
    if (score >= 30) return { label: 'Medium', color: 'bg-yellow-500' };
    return { label: 'Low', color: 'bg-green-500' };
  };

  return (
    <div className="min-h-screen bg-gray-50 py-10">
      <div className="max-w-6xl mx-auto px-6">
        
        {/* Header */}
        <div className="text-center mb-10">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Shield className="w-12 h-12 text-blue-600" />
            <h1 className="text-4xl font-bold text-gray-900">URL Security Analyzer</h1>
          </div>
          <p className="text-gray-600 text-lg">
            Hybrid ML-powered phishing detection using Machine Learning, VirusTotal, and Content Analysis
          </p>
        </div>

        {/* Input Section */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
          <div className="flex gap-4">
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
              placeholder="Enter URL to analyze (e.g., https://example.com)"
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
            <button
              onClick={handleAnalyze}
              disabled={loading || !url.trim()}
              className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-semibold"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <Activity className="w-5 h-5 animate-spin" />
                  Analyzing...
                </span>
              ) : (
                'Analyze'
              )}
            </button>
          </div>

          {/* Quick Test Examples */}
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="text-sm text-gray-600">Quick test:</span>
            <button
              onClick={() => setUrl('https://google.com')}
              className="text-sm text-blue-600 hover:underline"
            >
              Benign (Google)
            </button>
            <span className="text-gray-400">|</span>
            <button
              onClick={() => setUrl('http://facebook-login-verification-alert.com')}
              className="text-sm text-red-600 hover:underline"
            >
              Phishing Test
            </button>
          </div>
        </div>


        {/* #recent serach section */}
{recentSearches.length > 0 && (
  <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
    <h3 className="text-lg font-semibold mb-4">Recent Scans</h3>

    <div className="flex flex-wrap gap-3">
      {recentSearches.map((item, index) => (
        <button
          key={index}
          onClick={() => {
            setUrl(item);
            handleAnalyze();
          }}
          className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm transition"
        >
          {item}
        </button>
      ))}
    </div>
  </div>
)}

















        {/* Results Section */}
        {result && (
          <div className="space-y-6">
            
            {/* Main Verdict Card */}
            <div className={`rounded-xl shadow-lg p-8 border-2 ${getVerdictColor(result.final_verdict)}`}>
              <div className="flex items-start gap-6">
                <div className="flex-shrink-0">
                  {getVerdictIcon(result.final_verdict)}
                </div>
                
                <div className="flex-1">
                  <h2 className="text-3xl font-bold mb-2">{result.final_verdict}</h2>
                  <p className="text-lg mb-4">
                    Threat Score: <strong>{result.threat_score}%</strong> 
                    <span className="ml-2 text-sm">
                      ({getThreatLevel(result.threat_score).label} Risk)
                    </span>
                  </p>
                  
                  {/* Threat Score Bar */}
                  <div className="w-full bg-gray-200 rounded-full h-4 mb-4">
                    <div
                      className={`h-4 rounded-full ${getThreatLevel(result.threat_score).color}`}
                      style={{ width: `${result.threat_score}%` }}
                    ></div>
                  </div>

                  {/* URL Display */}
                  <div className="bg-white bg-opacity-50 rounded-lg p-3 mb-4">
                    <p className="text-sm font-mono break-all">{result.url}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Analysis Breakdown */}
            <div className="grid md:grid-cols-3 gap-6">
              
              {/* ML Model Analysis */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex items-center gap-3 mb-4">
                  <TrendingUp className="w-6 h-6 text-purple-600" />
                  <h3 className="text-xl font-semibold">ML Model</h3>
                  <span className="ml-auto text-sm bg-purple-100 text-purple-800 px-3 py-1 rounded-full">
                    30% weight
                  </span>
                </div>
                
                {result.breakdown?.ml && (
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Prediction:</span>
                      <span className={`font-semibold ${
                        result.breakdown.ml.prediction === 'phishing' ? 'text-red-600' : 'text-green-600'
                      }`}>
                        {result.breakdown.ml.prediction}
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Confidence:</span>
                      <span className="font-semibold">
                        {(result.breakdown.ml.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Threat Score:</span>
                      <span className="font-semibold text-orange-600">
                        {result.breakdown.ml.score.toFixed(1)}%
                      </span>
                    </div>
                    
                    {/* Probability bars */}
                    {result.breakdown.ml.probabilities && (
                      <div className="mt-4 space-y-2">
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>Legitimate</span>
                            <span>{(result.breakdown.ml.probabilities.legitimate * 100).toFixed(1)}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-green-500 h-2 rounded-full"
                              style={{ width: `${result.breakdown.ml.probabilities.legitimate * 100}%` }}
                            ></div>
                          </div>
                        </div>
                        
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>Phishing</span>
                            <span>{(result.breakdown.ml.probabilities.phishing * 100).toFixed(1)}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-red-500 h-2 rounded-full"
                              style={{ width: `${result.breakdown.ml.probabilities.phishing * 100}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* VirusTotal Analysis */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Shield className="w-6 h-6 text-blue-600" />
                  <h3 className="text-xl font-semibold">VirusTotal</h3>
                  <span className="ml-auto text-sm bg-blue-100 text-blue-800 px-3 py-1 rounded-full">
                    30% weight
                  </span>
                </div>
                
                {result.breakdown?.virustotal && (
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Detections:</span>
                      <span className="font-semibold text-red-600">
                        {result.breakdown.virustotal.positives}/{result.breakdown.virustotal.total}
                      </span>
                    </div>
                    
                    {result.breakdown.virustotal.malicious > 0 && (
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Malicious:</span>
                        <span className="font-semibold text-red-600">
                          {result.breakdown.virustotal.malicious}
                        </span>
                      </div>
                    )}
                    
                    {result.breakdown.virustotal.suspicious > 0 && (
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Suspicious:</span>
                        <span className="font-semibold text-orange-600">
                          {result.breakdown.virustotal.suspicious}
                        </span>
                      </div>
                    )}
                    
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Threat Score:</span>
                      <span className="font-semibold text-orange-600">
                        {result.breakdown.virustotal.score.toFixed(1)}%
                      </span>
                    </div>
                    
                    <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                      <p className="text-sm text-blue-800">
                        {result.breakdown.virustotal.message}
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Content Analysis */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Activity className="w-6 h-6 text-green-600" />
                  <h3 className="text-xl font-semibold">Content Analysis</h3>
                  <span className="ml-auto text-sm bg-green-100 text-green-800 px-3 py-1 rounded-full">
                    40% weight
                  </span>
                </div>
                
                {result.breakdown?.content && (
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Indicators:</span>
                      <span className="font-semibold">
                        {result.breakdown.content.indicators.length}
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Threat Score:</span>
                      <span className="font-semibold text-orange-600">
                        {result.breakdown.content.score.toFixed(1)}%
                      </span>
                    </div>
                    
                    {/* SSL Status */}
                    {result.breakdown.content.details?.ssl && (
                      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-2">
                          {result.breakdown.content.details.ssl.has_https ? (
                            <>
                              <CheckCircle className="w-4 h-4 text-green-600" />
                              <span className="text-sm text-green-800">HTTPS Enabled</span>
                            </>
                          ) : (
                            <>
                              <XCircle className="w-4 h-4 text-red-600" />
                              <span className="text-sm text-red-800">No HTTPS</span>
                            </>
                          )}
                        </div>
                        <p className="text-xs text-gray-600 mt-1">
                          {result.breakdown.content.details.ssl.details}
                        </p>
                      </div>
                    )}
                    
                    {/* Login Form Detection */}
                    {result.breakdown.content.details?.has_login_form && (
                      <div className="p-3 bg-yellow-50 rounded-lg">
                        <p className="text-sm text-yellow-800">
                           Login form detected
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Indicators & Recommendations */}
            <div className="grid md:grid-cols-2 gap-6">
              
              {/* Security Indicators */}
              {result.indicators && result.indicators.length > 0 && (
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                    <AlertTriangle className="w-6 h-6 text-orange-600" />
                    Security Indicators
                  </h3>
                  <ul className="space-y-2">
                    {result.indicators.map((indicator, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm">
                        <span className="text-orange-600 mt-1">•</span>
                        <span className="text-gray-700">{indicator}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Recommendations */}
              {result.recommendations && result.recommendations.length > 0 && (
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                    <Shield className="w-6 h-6 text-blue-600" />
                    Recommendations
                  </h3>
                  <ul className="space-y-2">
                    {result.recommendations.map((rec, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm">
                        <span className="text-blue-600 mt-1">✓</span>
                        <span className="text-gray-700">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Technical Details (Collapsible) */}
            {/* <details className="bg-white rounded-xl shadow-lg p-6">
              <summary className="text-xl font-semibold cursor-pointer hover:text-blue-600">
                View Technical Details
              </summary>
              <pre className="mt-4 p-4 bg-gray-50 rounded-lg overflow-auto text-xs">
                {JSON.stringify(result, null, 2)}
              </pre>
            </details> */}
          </div>
        )}

        {/* Info Section */}
        {!result && !loading && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h3 className="text-2xl font-semibold mb-4">How It Works</h3>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <TrendingUp className="w-8 h-8 text-purple-600" />
                </div>
                <h4 className="font-semibold mb-2">Machine Learning</h4>
                <p className="text-sm text-gray-600">
                  Random Forest model trained on 50,000+ URLs with 20+ features
                </p>
              </div>
              
              <div className="text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Shield className="w-8 h-8 text-blue-600" />
                </div>
                <h4 className="font-semibold mb-2">VirusTotal API</h4>
                <p className="text-sm text-gray-600">
                  Cross-reference with 70+ security vendors and antivirus engines
                </p>
              </div>
              
              <div className="text-center">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Activity className="w-8 h-8 text-green-600" />
                </div>
                <h4 className="font-semibold mb-2">Content Analysis</h4>
                <p className="text-sm text-gray-600">
                  Deep inspection of webpage content, forms, SSL, and suspicious patterns
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}



const saveScanToHistory = (url, result) => {
  const scan = {
    id: Date.now(),
    url: url,
    domain: new URL(url).hostname,
    verdict: result.final_verdict,
    threatScore: result.threat_score,
    timestamp: new Date().toISOString(),
    mlPrediction: result.ml_prediction?.prediction || 'unknown',
    virusTotalDetections: result.virustotal_analysis?.malicious || 0
  };

  const history = JSON.parse(localStorage.getItem('scanHistory')) || [];
  history.unshift(scan);
  
  // Keep last 100 scans
  const trimmed = history.slice(0, 100);
  localStorage.setItem('scanHistory', JSON.stringify(trimmed));
};

// Call this after successful scan:
// saveScanToHistory(url, result);
