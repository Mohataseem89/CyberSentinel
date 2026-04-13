// API configuration
const API_BASE_URL = 'http://localhost:5000';

// API helper functions
const API = {
  /**
   * Analyze URL for phishing
   */
  async analyzeURL(url) {
    try {
      // const response = await fetch(`${API_BASE_URL}/api/analyze-url`, {
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

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  /**
   * Get feedback statistics
   */
  async getFeedbackStats() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/feedback/stats`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  /**
   * Check if backend is reachable
   */
  async ping() {
    try {
      const response = await fetch(`${API_BASE_URL}/`, {
        method: 'GET',
        timeout: 5000
      });
      return response.ok;
    } catch (error) {
      return false;
    }
  }
};

// Make API available globally
if (typeof window !== 'undefined') {
  window.CyberSentinelAPI = API;
}