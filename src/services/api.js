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


import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  'https://nnqgdzzoernnyqvtsivz.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5ucWdkenpvZXJubnlxdnRzaXZ6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEwNzA1MDcsImV4cCI6MjA4NjY0NjUwN30.9c-xoRT-YdCr0YOttBw6okXFpomO1hjsy8lMvXeayfo'
);

export async function submitFeedback(data) {
  const { error } = await supabase
    .from('feedback')
    .insert([data]);

  if (error) throw error;
}

export const getFeedbackStats = async () => {
  const response = await api.get('/api/feedback/stats');
  return response.data;
};

export default api;