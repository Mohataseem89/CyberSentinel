// Content script - Runs on every page
// Injects warnings for dangerous URLs

console.log('CyberSentinel Content Script Loaded');

// Check if current page is flagged
(async function checkPage() {
  const currentURL = window.location.href;
  
  // Get cached result for current URL
  const cacheKey = `cache_${currentURL}`;
  
  chrome.storage.local.get(cacheKey, (data) => {
    if (data[cacheKey]) {
      const result = data[cacheKey].result;
      const verdict = result.final_verdict;
      
      // Show warning if dangerous
      if (verdict === 'Phishing' || verdict === 'Malicious') {
        showWarningOverlay(result);
      }
    }
  });
})();

/**
 * Show warning overlay
 */
function showWarningOverlay(result) {
  // Check if warning is already shown
  if (document.getElementById('cybersentinel-warning')) {
    return;
  }
  
  // Create overlay
  const overlay = document.createElement('div');
  overlay.id = 'cybersentinel-warning';
  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.95);
    z-index: 999999;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  `;
  
  const content = document.createElement('div');
  content.style.cssText = `
    background: white;
    padding: 40px;
    border-radius: 12px;
    max-width: 500px;
    text-align: center;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  `;
  
  const icon = document.createElement('div');
  icon.style.cssText = `
    font-size: 64px;
    margin-bottom: 20px;
  `;
  icon.textContent = '⚠️';
  
  const title = document.createElement('h1');
  title.style.cssText = `
    font-size: 28px;
    font-weight: 700;
    color: #dc2626;
    margin-bottom: 16px;
  `;
  title.textContent = 'Dangerous Website Detected!';
  
  const message = document.createElement('p');
  message.style.cssText = `
    font-size: 16px;
    color: #374151;
    line-height: 1.6;
    margin-bottom: 24px;
  `;
  const verdict = result.final_verdict || 'Unknown';
  const threatScore = result.threat_score || 0;
  message.textContent = `This website has been flagged as ${verdict} with a threat score of ${threatScore}%. Proceeding may put your personal information at risk.`;
  
  const buttonContainer = document.createElement('div');
  buttonContainer.style.cssText = `
    display: flex;
    gap: 12px;
    justify-content: center;
  `;
  
  const backButton = document.createElement('button');
  backButton.style.cssText = `
    background: #dc2626;
    color: white;
    border: none;
    padding: 12px 32px;
    font-size: 16px;
    font-weight: 600;
    border-radius: 8px;
    cursor: pointer;
  `;
  backButton.textContent = 'Go Back (Recommended)';
  backButton.onclick = () => {
    window.history.back();
  };
  
  const proceedButton = document.createElement('button');
  proceedButton.style.cssText = `
    background: #6b7280;
    color: white;
    border: none;
    padding: 12px 32px;
    font-size: 16px;
    font-weight: 600;
    border-radius: 8px;
    cursor: pointer;
  `;
  proceedButton.textContent = 'Proceed Anyway';
  proceedButton.onclick = () => {
    overlay.remove();
  };
  
  buttonContainer.appendChild(backButton);
  buttonContainer.appendChild(proceedButton);
  
  content.appendChild(icon);
  content.appendChild(title);
  content.appendChild(message);
  content.appendChild(buttonContainer);
  
  overlay.appendChild(content);
  document.body.appendChild(overlay);
}

// Listen for messages from background
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'showWarning') {
    showWarningOverlay(request.result);
    sendResponse({ success: true });
  }
});