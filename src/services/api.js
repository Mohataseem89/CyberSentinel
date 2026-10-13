import axios from 'axios';

// const API_BASE_URL = 'http://localhost:5000';
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.DEV ? 'http://localhost:5000' : '');

if (!API_BASE_URL && import.meta.env.PROD) {
  throw new Error('VITE_API_BASE_URL is required for production builds.');
}

/*
 * Do NOT set a global Content-Type here.
 *
 * Axios will automatically use:
 * - application/json for normal JavaScript objects
 * - multipart/form-data with the correct boundary for FormData
 *
 * Setting application/json globally breaks file uploads because Flask
 * cannot populate request.form / request.files correctly.
 */
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180000,
});

// Attach JWT token automatically
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
      throw new Error(
        error.response?.data?.error || 'Please login first.'
      );
    }

    if (error.response?.status === 403) {
      throw new Error(
        error.response?.data?.error || 'Admin access required.'
      );
    }

    if (error.response?.status === 429) {
      throw new Error(
        error.response?.data?.error ||
          'Rate limit exceeded. Please try again later.'
      );
    }

    if (error.response?.status === 400) {
      throw new Error(
        error.response?.data?.error || 'Invalid request'
      );
    }

    if (error.response?.status === 413) {
      throw new Error(
        error.response?.data?.error || 'Uploaded file is too large.'
      );
    }

    if (error.response?.status === 415) {
      throw new Error(
        error.response?.data?.error ||
          'Unsupported or mismatched file type.'
      );
    }

    if (error.response?.status === 503) {
      throw new Error(
        error.response?.data?.error ||
          'Service temporarily unavailable.'
      );
    }

    if (error.response?.status === 500) {
      throw new Error(
        error.response?.data?.error ||
          'Server error. Please try again later.'
      );
    }

    return Promise.reject(error);
  }
);


// -----------------------------------------------------------------------------
// URL ANALYSIS
// -----------------------------------------------------------------------------

export const analyzeURL = async (url) => {
  const token = localStorage.getItem('access_token');

  const response = await api.post(
    '/analyze',
    { url },
    {
      headers: token
        ? { 'X-Retain-Scan': 'true' }
        : {},
    }
  );

  return response.data;
};


// -----------------------------------------------------------------------------
// FEEDBACK
// -----------------------------------------------------------------------------

export async function submitFeedback(data) {
  const response = await api.post('/api/feedback', {
    url: data.url,
    category: data.category,
    actual_threat: data.actual_threat,
    our_prediction: data.our_prediction,
    description: data.description.slice(0, 1000),
  });

  return response.data;
}

export const getFeedbackStats = async () => {
  const response = await api.get('/api/feedback/stats');
  return response.data;
};

export const getAllFeedback = async (status = '') => {
  const url = status
    ? `/api/feedback?status=${encodeURIComponent(status)}`
    : '/api/feedback';

  const response = await api.get(url);

  return response.data;
};

export const approveFeedback = async (feedbackId) => {
  const response = await api.put(
    `/api/feedback/${encodeURIComponent(feedbackId)}/approve`
  );

  return response.data;
};

export const rejectFeedback = async (feedbackId) => {
  const response = await api.put(
    `/api/feedback/${encodeURIComponent(feedbackId)}/reject`
  );

  return response.data;
};


// -----------------------------------------------------------------------------
// ADMIN / MODEL
// -----------------------------------------------------------------------------

export const retrainModel = async () => {
  const response = await api.post('/api/admin/retrain-model');
  return response.data;
};

export const reloadModel = async () => {
  const response = await api.post('/api/admin/reload-model');
  return response.data;
};


// -----------------------------------------------------------------------------
// FEEDBACK EXPORT
// -----------------------------------------------------------------------------

// IMPORTANT: do NOT use window.open for protected route
export const exportApprovedFeedback = async () => {
  const response = await api.get(
    '/api/feedback/export-approved',
    {
      responseType: 'blob',
    }
  );

  const blob = new Blob(
    [response.data],
    { type: 'text/csv' }
  );

  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');

  link.href = url;
  link.download = 'approved_feedback.csv';

  document.body.appendChild(link);
  link.click();
  link.remove();

  window.URL.revokeObjectURL(url);
};


// -----------------------------------------------------------------------------
// AUTH
// -----------------------------------------------------------------------------

export const loginUser = async (formData) => {
  const response = await api.post(
    '/api/auth/login',
    formData
  );

  return response.data;
};

export const registerUser = async (formData) => {
  const response = await api.post(
    '/api/auth/register',
    formData
  );

  return response.data;
};


// -----------------------------------------------------------------------------
// QR SCANNER
// -----------------------------------------------------------------------------

export const scanQRCode = async (formData) => {
  /*
   * Do NOT manually set Content-Type.
   *
   * The browser/Axios must generate:
   *
   * multipart/form-data; boundary=...
   */
  const response = await api.post(
    '/api/qr/scan',
    formData
  );

  return response.data;
};


// -----------------------------------------------------------------------------
// BULK SCANNING
// -----------------------------------------------------------------------------

export const createBulkJob = async (file) => {
  const form = new FormData();

  form.append('file', file);

  /*
   * Do NOT manually set multipart/form-data.
   * Axios/browser generates the multipart boundary.
   */
  const response = await api.post(
    '/api/bulk/jobs',
    form
  );

  return response.data;
};

export const listBulkJobs = async () => {
  const response = await api.get('/api/bulk/jobs');
  return response.data;
};

export const getBulkJob = async (
  id,
  { page = 1, perPage = 100, verdict = '' } = {}
) => {
  const params = {
    page,
    per_page: perPage,
  };

  if (verdict) {
    params.verdict = verdict;
  }

  const response = await api.get(
    `/api/bulk/jobs/${encodeURIComponent(id)}`,
    { params }
  );

  return response.data;
};

export const cancelBulkJob = async (id) => {
  const response = await api.post(
    `/api/bulk/jobs/${encodeURIComponent(id)}/cancel`
  );

  return response.data;
};

export const downloadBulkResults = async (id) => {
  const response = await api.get(
    `/api/bulk/jobs/${encodeURIComponent(id)}/results.csv`,
    {
      responseType: 'blob',
    }
  );

  const url = window.URL.createObjectURL(response.data);
  const link = document.createElement('a');

  link.href = url;
  link.download = `cybersentinel-${id}.csv`;

  document.body.appendChild(link);
  link.click();
  link.remove();

  window.URL.revokeObjectURL(url);
};


// -----------------------------------------------------------------------------
// FILE ANALYSIS
// -----------------------------------------------------------------------------

export const getFileScanCapabilities = async () => {
  const response = await api.get(
    '/api/file-scans/capabilities'
  );

  return response.data;
};

export const createFileScan = async (file, consent) => {
  const form = new FormData();

  form.append('file', file);
  form.append(
    'consent',
    consent ? 'true' : 'false'
  );

  /*
   * IMPORTANT:
   *
   * Do not provide Content-Type here.
   *
   * Axios/browser must generate something similar to:
   *
   * Content-Type:
   * multipart/form-data; boundary=----WebKitFormBoundary...
   *
   * Flask will then correctly populate:
   *
   * request.files["file"]
   * request.form["consent"]
   */
  const response = await api.post(
    '/api/file-scans',
    form
  );

  return response.data;
};

export const listFileScans = async () => {
  const response = await api.get(
    '/api/file-scans'
  );

  return response.data;
};

export const getFileScan = async (id) => {
  const response = await api.get(
    `/api/file-scans/${encodeURIComponent(id)}`
  );

  return response.data;
};


// -----------------------------------------------------------------------------
// AXIOS INSTANCE
// -----------------------------------------------------------------------------

export default api;