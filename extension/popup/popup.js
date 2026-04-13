// DOM Elements
const currentUrlElement = document.getElementById('currentUrl');
const statusIndicator = document.getElementById('statusIndicator');
const statusText = document.getElementById('statusText');
const scanCurrentBtn = document.getElementById('scanCurrentBtn');
const quickUrlInput = document.getElementById('quickUrlInput');
const quickScanBtn = document.getElementById('quickScanBtn');
const resultsSection = document.getElementById('resultsSection');
const resultIcon = document.getElementById('resultIcon');
const resultVerdict = document.getElementById('resultVerdict');
const resultScore = document.getElementById('resultScore');
const resultDetails = document.getElementById('resultDetails');
const recentList = document.getElementById('recentList');
const settingsBtn = document.getElementById('settingsBtn');
const dashboardBtn = document.getElementById('dashboardBtn');

// State
let currentTab = null;
let recentScans = [];

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  console.log('CyberSentinel Extension Loaded');
  
  // Get current tab
  await getCurrentTab();
  
  // Load recent scans
  loadRecentScans();
  
  // Check current page status (from storage)
  checkCurrentPageStatus();
  
  // Setup event listeners
  setupEventListeners();
  
  // Check backend connection
  checkBackendConnection();
});

/**
 * Get current active tab
 */
async function getCurrentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  currentTab = tab;
  
  if (tab && tab.url) {
    currentUrlElement.textContent = tab.url;
  } else {
    currentUrlElement.textContent = 'Unable to get current URL';
  }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
  scanCurrentBtn.addEventListener('click', scanCurrentPage);
  quickScanBtn.addEventListener('click', scanQuickURL);
  quickUrlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      scanQuickURL();
    }
  });
  settingsBtn.addEventListener('click', openSettings);
  dashboardBtn.addEventListener('click', openDashboard);
}

/**
 * Check backend connection
 */
async function checkBackendConnection() {
  try {
    const isConnected = await window.CyberSentinelAPI.ping();
    if (!isConnected) {
      showNotification('Backend not reachable. Make sure Flask server is running on localhost:5000', 'warning');
    }
  } catch (error) {
    console.error('Backend connection check failed:', error);
  }
}

/**
 * Scan current page
 */
async function scanCurrentPage() {
  if (!currentTab || !currentTab.url) {
    showNotification('No URL to scan', 'warning');
    return;
  }

  // Ignore chrome:// and extension pages
  if (currentTab.url.startsWith('chrome://') || 
      currentTab.url.startsWith('edge://') ||
      currentTab.url.startsWith('chrome-extension://')) {
    showNotification('Cannot scan browser internal pages', 'warning');
    return;
  }

  await scanURL(currentTab.url);
}

/**
 * Scan URL from quick input
 */
async function scanQuickURL() {
  const url = quickUrlInput.value.trim();
  
  if (!url) {
    showNotification('Please enter a URL', 'warning');
    return;
  }

  // Basic URL validation
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    showNotification('URL must start with http:// or https://', 'warning');
    return;
  }

  await scanURL(url);
}

/**
 * Main scan function
 */
async function scanURL(url) {
  // Show loading state
  scanCurrentBtn.disabled = true;
  quickScanBtn.disabled = true;
  scanCurrentBtn.innerHTML = `
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" class="spin">
      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" opacity="0.25"/>
      <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" stroke-width="4"/>
    </svg>
    Scanning...
  `;
  
  statusText.textContent = 'Analyzing...';
  statusIndicator.className = 'status-indicator';
  
  try {
    console.log('Scanning URL:', url);
    
    // Call API
    const result = await window.CyberSentinelAPI.analyzeURL(url);
    
    console.log('Scan result:', result);
    
    // Display results
    displayResults(result, url);
    
    // Save to recent scans
    saveRecentScan(url, result);
    
    // Update current page status if it matches
    if (currentTab && currentTab.url === url) {
      updateCurrentPageStatus(result);
    }
    
    // Show notification
    const verdict = result.final_verdict || 'Unknown';
    showNotification(`Scan complete: ${verdict}`, getNotificationType(verdict));
    
  } catch (error) {
    console.error('Scan error:', error);
    showNotification('Scan failed. Make sure backend is running.', 'danger');
    
    // Show error in results
    resultsSection.style.display = 'block';
    resultIcon.className = 'result-icon danger';
    resultIcon.textContent = '❌';
    resultVerdict.textContent = 'Scan Failed';
    resultScore.textContent = 'Backend not reachable';
    resultDetails.textContent = 'Make sure Flask server is running on http://localhost:5000';
  } finally {
    // Reset loading state
    scanCurrentBtn.disabled = false;
    quickScanBtn.disabled = false;
    scanCurrentBtn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
        <path d="M12 2L4 6V11C4 16.55 7.84 21.74 12 23C16.16 21.74 20 16.55 20 11V6L12 2Z" fill="currentColor"/>
      </svg>
      Scan This Page
    `;
  }
}

/**
 * Display scan results
 */
function displayResults(result, url) {
  resultsSection.style.display = 'block';
  
  const verdict = result.final_verdict || 'Unknown';
  const threatScore = result.threat_score || 0;
  
  // Set icon and colors based on verdict
  if (verdict === 'Benign') {
    resultIcon.className = 'result-icon safe';
    resultIcon.textContent = '✓';
  } else if (verdict === 'Suspicious' || verdict === 'Potentially Risky') {
    resultIcon.className = 'result-icon warning';
    resultIcon.textContent = '⚠';
  } else {
    resultIcon.className = 'result-icon danger';
    resultIcon.textContent = '✕';
  }
  
  resultVerdict.textContent = verdict;
  resultScore.textContent = `Threat Score: ${threatScore}%`;
  
  // Build details
  let details = '';
  
  if (result.ml_prediction) {
    details += `ML Prediction: ${result.ml_prediction.prediction} (${(result.ml_prediction.confidence * 100).toFixed(1)}%)\n`;
  }
  
  if (result.virustotal_analysis) {
    const vt = result.virustotal_analysis;
    details += `VirusTotal: ${vt.malicious || 0} malicious, ${vt.suspicious || 0} suspicious\n`;
  }
  
  if (result.content_analysis) {
    const ca = result.content_analysis;
    if (ca.has_ssl) details += '✓ SSL Certificate\n';
    if (ca.has_forms) details += '⚠ Contains forms\n';
    if (ca.suspicious_keywords) details += '⚠ Suspicious keywords detected\n';
  }
  
  resultDetails.textContent = details || 'No additional details available.';
}

/**
 * Update current page status
 */
function updateCurrentPageStatus(result) {
  const verdict = result.final_verdict || 'Unknown';
  
  statusText.textContent = verdict;
  
  if (verdict === 'Benign') {
    statusIndicator.className = 'status-indicator safe';
  } else if (verdict === 'Suspicious' || verdict === 'Potentially Risky') {
    statusIndicator.className = 'status-indicator warning';
  } else {
    statusIndicator.className = 'status-indicator danger';
  }
  
  // Save to storage
  chrome.storage.local.set({
    [`status_${currentTab.url}`]: result
  });
}

/**
 * Check current page status from storage
 */
async function checkCurrentPageStatus() {
  if (!currentTab || !currentTab.url) return;
  
  // Ignore chrome:// pages
  if (currentTab.url.startsWith('chrome://') || 
      currentTab.url.startsWith('edge://')) {
    statusText.textContent = 'Browser Page';
    return;
  }
  
  const key = `status_${currentTab.url}`;
  const result = await chrome.storage.local.get(key);
  
  if (result[key]) {
    updateCurrentPageStatus(result[key]);
  } else {
    statusText.textContent = 'Not scanned yet';
  }
}

/**
 * Save to recent scans
 */
function saveRecentScan(url, result) {
  const scan = {
    url: url,
    verdict: result.final_verdict || 'Unknown',
    threatScore: result.threat_score || 0,
    timestamp: new Date().toISOString()
  };
  
  // Get existing scans
  chrome.storage.local.get('recentScans', (data) => {
    let scans = data.recentScans || [];
    
    // Remove duplicates
    scans = scans.filter(s => s.url !== url);
    
    // Add new scan to beginning
    scans.unshift(scan);
    
    // Keep only last 10
    scans = scans.slice(0, 10);
    
    // Save
    chrome.storage.local.set({ recentScans: scans }, () => {
      loadRecentScans();
    });
  });
}

/**
 * Load recent scans
 */
function loadRecentScans() {
  chrome.storage.local.get('recentScans', (data) => {
    const scans = data.recentScans || [];
    
    if (scans.length === 0) {
      recentList.innerHTML = '<p class="empty-state">No recent scans</p>';
      return;
    }
    
    recentList.innerHTML = '';
    
    scans.forEach(scan => {
      const item = document.createElement('div');
      item.className = 'recent-item';
      
      const urlSpan = document.createElement('span');
      urlSpan.className = 'recent-item-url';
      urlSpan.textContent = scan.url;
      urlSpan.title = scan.url;
      
      const badge = document.createElement('span');
      badge.className = 'recent-item-badge';
      badge.textContent = scan.verdict;
      
      if (scan.verdict === 'Benign') {
        badge.classList.add('safe');
      } else if (scan.verdict === 'Suspicious' || scan.verdict === 'Potentially Risky') {
        badge.classList.add('warning');
      } else {
        badge.classList.add('danger');
      }
      
      item.appendChild(urlSpan);
      item.appendChild(badge);
      
      // Click to rescan
      item.addEventListener('click', () => {
        quickUrlInput.value = scan.url;
        scanQuickURL();
      });
      
      recentList.appendChild(item);
    });
  });
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
  // You can enhance this with a toast notification
  console.log(`[${type.toUpperCase()}]`, message);
  
  // Optional: Use Chrome notifications
  // chrome.notifications.create({
  //   type: 'basic',
  //   iconUrl: '../icons/icon48.png',
  //   title: 'CyberSentinel',
  //   message: message
  // });
}

/**
 * Get notification type based on verdict
 */
function getNotificationType(verdict) {
  if (verdict === 'Benign') return 'success';
  if (verdict === 'Suspicious' || verdict === 'Potentially Risky') return 'warning';
  return 'danger';
}

/**
 * Open settings
 */
function openSettings() {
  // Open settings page (we'll create this later)
  chrome.runtime.openOptionsPage();
}

/**
 * Open dashboard
 */
function openDashboard() {
  chrome.tabs.create({ url: 'http://localhost:5173' });
}

// Add CSS for spin animation
const style = document.createElement('style');
style.textContent = `
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  .spin {
    animation: spin 1s linear infinite;
  }
`;
document.head.appendChild(style);