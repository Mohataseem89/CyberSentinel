// Background service worker for CyberSentinel Extension

console.log('CyberSentinel Background Service Worker Started');

// Configuration
// const API_BASE_URL = 'http://localhost:5000';
const API_BASE_URL = 'http://127.0.0.1:5000';
const CACHE_DURATION = 3600000; // 1 hour in milliseconds

// Danger thresholds
const THREAT_LEVELS = {
  SAFE: 30,           // 0-30: Safe
  SUSPICIOUS: 50,     // 31-50: Suspicious  
  DANGEROUS: 70,      // 51-70: Dangerous
  CRITICAL: 100       // 71-100: Critical (BLOCK!)
};

// Installation
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('CyberSentinel Extension Installed');
    
    chrome.tabs.create({
      url: 'http://localhost:5173'
    });
    
    // Initialize storage
    chrome.storage.local.set({
      recentScans: [],
      settings: {
        autoScan: true,              // AUTO-SCAN ENABLED BY DEFAULT
        showWarnings: true,          // SHOW WARNINGS
        blockDangerous: true,        // BLOCK CRITICAL THREATS
        blockThreshold: 70           // Block if threat > 70%
      }
    });
  }
  
  createContextMenu();
});

/**
 * Create right-click context menu
 */
function createContextMenu() {
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: 'checkWithCyberSentinel',
      title: 'Check with CyberSentinel',
      contexts: ['link', 'page']
    });
    
    chrome.contextMenus.create({
      id: 'checkLinkURL',
      title: 'Check this link',
      contexts: ['link']
    });
    
    chrome.contextMenus.create({
      id: 'checkCurrentPage',
      title: 'Check this page',
      contexts: ['page']
    });
  });
}

/**
 * Handle context menu clicks
 */
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  console.log('Context menu clicked:', info.menuItemId);
  
  let urlToCheck = null;
  
  if (info.menuItemId === 'checkLinkURL' && info.linkUrl) {
    urlToCheck = info.linkUrl;
  } else if (info.menuItemId === 'checkCurrentPage' && info.pageUrl) {
    urlToCheck = info.pageUrl;
  } else if (info.menuItemId === 'checkWithCyberSentinel') {
    urlToCheck = info.linkUrl || info.pageUrl;
  }
  
  if (urlToCheck) {
    await scanURL(urlToCheck, tab);
  }
});

/**
 * Scan URL
 */
async function scanURL(url, tab) {
  console.log('Scanning URL:', url);
  
  // Check cache first
  const cached = await getCachedResult(url);
  if (cached) {
    console.log('Using cached result');
    showResult(cached, url, tab);
    return cached;
  }
  
  try {
    // Call API
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    // Cache result
    cacheResult(url, result);
    
    // Show result
    showResult(result, url, tab);
    
    return result;
    
  } catch (error) {
    // console.error('Scan error:', error);
    return null;
  }
}

/**
 * Show scan result
 */
function showResult(result, url, tab) {
  const verdict = result.final_verdict || 'Unknown';
  const threatScore = result.threat_score || 0;

  let message = '';

  if (verdict === 'Benign') {
    message = `Safe - Threat Score: ${threatScore}%`;
  } else if (verdict === 'Suspicious' || verdict === 'Potentially Risky') {
    message = `${verdict} - Threat Score: ${threatScore}%`;
  } else {
    message = `DANGER: ${verdict} - Threat Score: ${threatScore}%`;
  }

  if (chrome.notifications) {
    chrome.notifications.create({
    type: 'basic',
    iconUrl: chrome.runtime.getURL('icons/icon48.png'),
    title: 'CyberSentinel',
    message: message
  });
  } else {
    console.warn('notifications API is not available.');
  }

  if (tab && tab.id) {
    updateBadge(tab.id, verdict, threatScore);
  }

  saveRecentScan(url, result);
}

/**
 * Update browser action badge
 */
function updateBadge(tabId, verdict, threatScore) {
  let badgeText = '';
  let badgeColor = '#10b981'; // Green
  
  if (verdict === 'Benign') {
    badgeText = '✓';
    badgeColor = '#10b981';
  } else if (verdict === 'Suspicious' || verdict === 'Potentially Risky') {
    badgeText = '!';
    badgeColor = '#f59e0b';
  } else if (verdict === 'Phishing' || verdict === 'Malicious') {
    badgeText = '✕';
    badgeColor = '#ef4444';
  }
  
  chrome.action.setBadgeText({ text: badgeText, tabId: tabId });
  chrome.action.setBadgeBackgroundColor({ color: badgeColor, tabId: tabId });
}

/**
 * Cache scan result
 */
async function cacheResult(url, result) {
  const cacheKey = `cache_${url}`;
  const cacheData = {
    result: result,
    timestamp: Date.now()
  };
  
  await chrome.storage.local.set({ [cacheKey]: cacheData });
}

/**
 * Get cached result
 */
async function getCachedResult(url) {
  const cacheKey = `cache_${url}`;
  const data = await chrome.storage.local.get(cacheKey);
  
  if (data[cacheKey]) {
    const cached = data[cacheKey];
    const age = Date.now() - cached.timestamp;
    
    if (age < CACHE_DURATION) {
      return cached.result;
    }
  }
  
  return null;
}

/**
 * Save to recent scans
 */
async function saveRecentScan(url, result) {
  const scan = {
    url: url,
    verdict: result.final_verdict || 'Unknown',
    threatScore: result.threat_score || 0,
    timestamp: new Date().toISOString()
  };
  
  const data = await chrome.storage.local.get('recentScans');
  let scans = data.recentScans || [];
  
  scans = scans.filter(s => s.url !== url);
  scans.unshift(scan);
  scans = scans.slice(0, 20);
  
  await chrome.storage.local.set({ recentScans: scans });
}

/**
 * 🚨 NEW: AUTO-SCAN ON PAGE LOAD
 */


if (chrome.webNavigation && chrome.webNavigation.onCommitted) {
  chrome.webNavigation.onCommitted.addListener(async (details) => {
    try {
      // Only for main frame
      if (details.frameId !== 0) return;

      const url = details.url;

      // Skip browser/internal pages
      if (
        !url ||
        url.startsWith('chrome://') ||
        url.startsWith('chrome-extension://') ||
        url.startsWith('edge://') ||
        url.startsWith('about:')
      ) {
        return;
      }

      // Read settings
      const data = await chrome.storage.local.get('settings');
      const settings = data.settings || {};

      if (settings.autoScan === false) {
        console.log('Auto-scan disabled');
        return;
      }

      console.log('[AUTO-SCAN] Scanning on page load:', url);

      // Get tab info from tabId
      let tab = null;
      try {
        tab = await chrome.tabs.get(details.tabId);
      } catch (err) {
        console.warn('Could not get tab details:', err);
      }

      const result = await scanURL(url, tab);

      if (!result) return;

      const verdict = result.final_verdict || 'Unknown';
      const threatScore = result.threat_score || 0;

      // Optional warning/block for dangerous sites
      if (settings.blockDangerous && threatScore >= (settings.blockThreshold || 70)) {
        chrome.tabs.update(details.tabId, {
          url: chrome.runtime.getURL('warning.html')
        });
      }
    } catch (error) {
      console.error('[AUTO-SCAN] Error:', error);
    }
  });
} else {
  console.warn('webNavigation API is not available. Check manifest permissions.');
}


/**
 * Handle messages from popup or content scripts
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Message received:', request);
  
  if (request.action === 'scanURL') {
    scanURL(request.url, sender.tab).then(() => {
      sendResponse({ success: true });
    }).catch((error) => {
      sendResponse({ success: false, error: error.message });
    });
    return true;
  }
  
  if (request.action === 'getSettings') {
    chrome.storage.local.get('settings', (data) => {
      sendResponse({ settings: data.settings || {} });
    });
    return true;
  }
  
  if (request.action === 'updateSettings') {
    chrome.storage.local.set({ settings: request.settings }, () => {
      sendResponse({ success: true });
    });
    return true;
  }
});

// Clear old cache periodically
setInterval(async () => {
  console.log('Cleaning old cache...');
  
  const allData = await chrome.storage.local.get(null);
  const now = Date.now();
  const keysToRemove = [];
  
  for (const key in allData) {
    if (key.startsWith('cache_')) {
      const cached = allData[key];
      const age = now - cached.timestamp;
      
      if (age > CACHE_DURATION) {
        keysToRemove.push(key);
      }
    }
  }
  
  if (keysToRemove.length > 0) {
    await chrome.storage.local.remove(keysToRemove);
    console.log(`Removed ${keysToRemove.length} expired cache entries`);
  }
}, 3600000);