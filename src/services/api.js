import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for better error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 429) {
      throw new Error('Rate limit exceeded. Please try again later.');
    }
    if (error.response?.status === 400) {
      throw new Error(error.response.data?.error || 'Invalid request');
    }
    if (error.response?.status === 500) {
      throw new Error('Server error. Please try again later.');
    }
    return Promise.reject(error);
  }
);

export const analyzeURL = async (url) => {
  const response = await api.post('/api/analyze-url', { url });
  return response.data;
};

export const submitFeedback = async (feedbackData) => {
  const response = await api.post('/api/feedback', feedbackData);
  return response.data;
};

export const getFeedbackStats = async () => {
  const response = await api.get('/api/feedback/stats');
  return response.data;
};

export default api;
