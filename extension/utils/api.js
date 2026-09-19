const API_BASE_URL = 'http://127.0.0.1:5000'; // Replace with the exact HTTPS production API origin before store submission.
const SENSITIVE_QUERY_KEYS = /^(token|access_token|auth|authorization|code|password|passwd|secret|api_?key|session|sid|jwt|email)$/i;

function sanitizeUrlForScan(input) {
  const parsed = new URL(input);
  if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error('Only http:// and https:// URLs can be checked.');
  parsed.username = '';
  parsed.password = '';
  parsed.hash = '';
  for (const [key] of parsed.searchParams) {
    if (SENSITIVE_QUERY_KEYS.test(key)) parsed.searchParams.set(key, '[redacted]');
  }
  return parsed.toString();
}

function validateResult(data) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error('CyberSentinel returned an invalid response.');
  const verdicts = new Set(['Safe', 'Suspicious', 'Dangerous', 'Unknown']);
  const verdict = verdicts.has(data.final_verdict) ? data.final_verdict : 'Unknown';
  const score = Number.isFinite(data.threat_score) ? Math.max(0, Math.min(100, data.threat_score)) : null;
  const indicators = Array.isArray(data.indicators) ? data.indicators.filter(v => typeof v === 'string').slice(0, 8) : [];
  return { final_verdict: verdict, threat_score: score, indicators, limitations: Array.isArray(data.limitations) ? data.limitations.filter(v => typeof v === 'string').slice(0, 4) : [] };
}

async function analyzeURL(input) {
  const url = sanitizeUrlForScan(input);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({url}), signal: controller.signal
    });
    const body = await response.json().catch(() => ({}));
    if (response.status === 429) throw new Error('RATE_LIMIT');
    if (response.status === 503) throw new Error('UNAVAILABLE');
    if (!response.ok) throw new Error(body.error || 'SCAN_FAILED');
    return { url, result: validateResult(body) };
  } finally { clearTimeout(timer); }
}

window.CyberSentinelAPI = { analyzeURL, sanitizeUrlForScan, validateResult };
