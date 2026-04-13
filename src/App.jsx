import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Navigation from './components/UI/Navigation';
import URLAnalyzer from './components/features/URLAnalyzer';
import FeedbackForm from './components/features/FeedbackForm';
import './App.css';
import QRScanner from './components/features/QRScanner';
// import EmailScanner from './components/features/EmailScanner';
import Dashboard from './components/features/Dashboard';
import AdminFeedback from './components/features/AdminFeedback';
import Login from './components/auth/Login'
import Register from './components/auth/Register';



function AdminRoute({ children }) {
  const userData = localStorage.getItem('user');
  const token = localStorage.getItem('access_token');

  if (!token || !userData) {
    return <Navigate to="/login" replace />;
  }

  try {
    const user = JSON.parse(userData);
    if (user.role !== 'admin') {
      return <Navigate to="/" replace />;
    }
  } catch {
    return <Navigate to="/" replace />;
  }

  return children;
}


function App() {
  return (
    <Router>
      <div className="App">
        <Navigation />
        
        <Routes>
          <Route path="/" element={<URLAnalyzer />} />
          <Route path="/login" element={<Login />} />
          <Route path="/analyze" element={<URLAnalyzer />} />
          <Route path="/reporturl" element={<FeedbackForm />} />
          <Route path="/feedback" element={<Navigate to="/reporturl" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
          <Route path="/qrcode" element={<QRScanner />} />
          {/* <Route path="/emailscan" element={<EmailScanner />} /> */}
          <Route path="/dashboard" element={<Dashboard />} />
          {/* <Route path="/admin/feedback" element={<AdminFeedback />} /> */}
          <Route path="/admin/feedback" element={<AdminRoute><AdminFeedback /></AdminRoute>}/>
          <Route path="/register" element={<Register />} />



        </Routes>
        
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
            success: {
              duration: 4000,
              style: {
                background: '#059669',
                color: '#fff',
              },
            },
            error: {
              duration: 5000,
              style: {
                background: '#dc2626',
                color: '#fff',
              },
            },
          }}
        />
      </div>
    </Router>
  );
}

export default App;
