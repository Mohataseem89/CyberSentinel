import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Navigate, Route, Routes } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Navigation from './components/UI/Navigation';
import Footer from './components/UI/Footer';
import SEO from './components/SEO';
import FeedbackForm from './components/features/FeedbackForm';
import QRScanner from './components/features/QRScanner';
import Dashboard from './components/features/Dashboard';
import AdminFeedback from './components/features/AdminFeedback';
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import LearnPage from './pages/LearnPage';
import PrivacyPage from './pages/PrivacyPage';
import LimitationsPage from './pages/LimitationsPage';
import NotFoundPage from './pages/NotFoundPage';
import './App.css';

const ScannerPage = lazy(() => import('./pages/ScannerPage'));

function PrivateMeta({ children, title }) {
  return <><SEO title={title} path={window.location.pathname} noindex />{children}</>;
}

function AdminRoute({ children }) {
  const userData = localStorage.getItem('user');
  const token = localStorage.getItem('access_token');

  if (!token || !userData) return <Navigate to="/login" replace />;

  try {
    const user = JSON.parse(userData);
    if (user.role !== 'admin') return <Navigate to="/" replace />;
  } catch {
    return <Navigate to="/" replace />;
  }

  return children;
}

function App() {
  return (
    <Router>
      <div className="App min-h-screen bg-slate-50 text-slate-950">
        <Navigation />
        <Routes>
          <Route path="/" element={<Suspense fallback={<main className="p-8">Loading scanner…</main>}><ScannerPage /></Suspense>} />
          <Route path="/learn" element={<LearnPage />} />
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route path="/limitations" element={<LimitationsPage />} />

          <Route path="/login" element={<PrivateMeta title="Login — CyberSentinel"><Login /></PrivateMeta>} />
          <Route path="/register" element={<PrivateMeta title="Register — CyberSentinel"><Register /></PrivateMeta>} />
          <Route path="/analyze" element={<Navigate to="/" replace />} />
          <Route path="/reporturl" element={<PrivateMeta title="Report a URL — CyberSentinel"><FeedbackForm /></PrivateMeta>} />
          <Route path="/feedback" element={<Navigate to="/reporturl" replace />} />
          <Route path="/qrcode" element={<PrivateMeta title="QR Scanner — CyberSentinel"><QRScanner /></PrivateMeta>} />
          <Route path="/dashboard" element={<PrivateMeta title="Dashboard — CyberSentinel"><Dashboard /></PrivateMeta>} />
          <Route path="/history" element={<Navigate to="/dashboard" replace />} />
          <Route path="/results/*" element={<NotFoundPage />} />
          <Route path="/admin/feedback" element={<PrivateMeta title="Admin Feedback — CyberSentinel"><AdminRoute><AdminFeedback /></AdminRoute></PrivateMeta>} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
        <Footer />
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: { background: '#363636', color: '#fff' },
            success: { duration: 4000, style: { background: '#059669', color: '#fff' } },
            error: { duration: 5000, style: { background: '#dc2626', color: '#fff' } },
          }}
        />
      </div>
    </Router>
  );
}

export default App;
