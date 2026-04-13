import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ADD THIS: attach JWT token automatically
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      throw new Error(error.response?.data?.error || 'Please login first.');
    }
    if (error.response?.status === 403) {
      throw new Error(error.response?.data?.error || 'Admin access required.');
    }
    if (error.response?.status === 429) {
      throw new Error('Rate limit exceeded. Please try again later.');
    }
    if (error.response?.status === 400) {
      throw new Error(error.response?.data?.error || 'Invalid request');
    }
    if (error.response?.status === 500) {
      throw new Error(error.response?.data?.error || 'Server error. Please try again later.');
    }
    return Promise.reject(error);
  }
);

export const analyzeURL = async (url) => {
  const response = await api.post('/api/analyze-url', { url });
  return response.data;
};

export async function submitFeedback(data) {
  const response = await api.post('/api/feedback', {
    url: data.url,
    category: data.category,
    actual_threat: data.actual_threat,
    our_prediction: data.our_prediction,
    description: data.description
  });
  return response.data;
}

export const getFeedbackStats = async () => {
  const response = await api.get('/api/feedback/stats');
  return response.data;
};

export const getAllFeedback = async (status = '') => {
  const url = status ? `/api/feedback?status=${status}` : '/api/feedback';
  const response = await api.get(url);
  return response.data;
};

export const approveFeedback = async (feedbackId) => {
  const response = await api.put(`/api/feedback/${feedbackId}/approve`);
  return response.data;
};

export const rejectFeedback = async (feedbackId) => {
  const response = await api.put(`/api/feedback/${feedbackId}/reject`);
  return response.data;
};

export const retrainModel = async () => {
  const response = await api.post('/api/admin/retrain-model');
  return response.data;
};

export const reloadModel = async () => {
  const response = await api.post('/api/admin/reload-model');
  return response.data;
};

// IMPORTANT: do NOT use window.open for protected route
export const exportApprovedFeedback = async () => {
  const response = await api.get('/api/feedback/export-approved', {
    responseType: 'blob'
  });

  const blob = new Blob([response.data], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');

  link.href = url;
  link.download = 'approved_feedback.csv';
  document.body.appendChild(link);
  link.click();
  link.remove();

  window.URL.revokeObjectURL(url);
};

export default api;