import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Navigation from './components/UI/Navigation';
import URLAnalyzer from './components/features/URLAnalyzer';
import FeedbackForm from './components/features/FeedbackForm';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Navigation />
        
        <Routes>
          <Route path="/" element={<URLAnalyzer />} />
          <Route path="/analyze" element={<URLAnalyzer />} />
          <Route path="/reporturl" element={<FeedbackForm />} />
          <Route path="/feedback" element={<Navigate to="/reporturl" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
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
