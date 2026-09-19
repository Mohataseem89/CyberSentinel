import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { BarChart3, BookOpen, Upload, Flag, Menu, QrCode, Search, Shield, X } from 'lucide-react';

export default function Navigation() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const userData = localStorage.getItem('user');
  let currentUser = null;

  try { currentUser = userData ? JSON.parse(userData) : null; } catch { currentUser = null; }
  const isAdmin = currentUser?.role === 'admin';

  const navItems = [
    { path: '/', label: 'URL Analysis', icon: Search },
    { path: '/learn', label: 'Learn', icon: BookOpen },
    { path: '/reporturl', label: 'Report URL', icon: Flag },
    { path: '/qrcode', label: 'QR Scanner', icon: QrCode },
    { path: '/dashboard', label: 'Dashboard', icon: BarChart3 },
    ...(currentUser ? [{ path: '/bulk', label: 'Bulk Scan', icon: Upload }] : []),
    ...(isAdmin ? [{ path: '/admin/feedback', label: 'Admin Panel', icon: Shield }] : []),
  ];

  const handleNavigation = (path) => { navigate(path); setMobileMenuOpen(false); };
  const handleLogout = () => { localStorage.removeItem('access_token'); localStorage.removeItem('user'); navigate('/login'); setMobileMenuOpen(false); };
  const isActive = (path) => path === '/' ? location.pathname === '/' || location.pathname === '/analyze' : location.pathname === path;

  return (
    <nav className="sticky top-0 z-50 border-b border-gray-200 bg-white shadow-sm" aria-label="Primary">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <button onClick={() => handleNavigation('/')} className="flex items-center transition-opacity hover:opacity-80" aria-label="CyberSentinel home">
            <Shield className="mr-2 h-8 w-8 text-blue-700" aria-hidden="true" />
            <span className="text-xl font-bold text-gray-900">CyberSentinel</span>
          </button>
          <div className="hidden items-center space-x-1 md:flex">
            {navItems.map((item) => { const Icon = item.icon; return <button key={item.path} onClick={() => handleNavigation(item.path)} className={`flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-all ${isActive(item.path) ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'}`}><Icon className="mr-2 h-4 w-4" aria-hidden="true" />{item.label}</button>; })}
            {currentUser ? <button onClick={handleLogout} className="rounded-lg px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50">Logout</button> : <button onClick={() => handleNavigation('/login')} className="rounded-lg px-4 py-2 text-sm font-medium text-blue-700 hover:bg-blue-50">Login</button>}
          </div>
          <div className="md:hidden"><button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="rounded-lg p-2 text-gray-600 hover:bg-gray-50 hover:text-gray-900" aria-expanded={mobileMenuOpen} aria-controls="mobile-navigation" aria-label="Toggle navigation">{mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}</button></div>
        </div>
        {mobileMenuOpen && <div id="mobile-navigation" className="border-t border-gray-200 py-4 md:hidden"><div className="flex flex-col space-y-1">{navItems.map((item) => { const Icon = item.icon; return <button key={item.path} onClick={() => handleNavigation(item.path)} className={`flex items-center rounded-lg px-3 py-2 text-sm font-medium ${isActive(item.path) ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'}`}><Icon className="mr-2 h-4 w-4" />{item.label}</button>; })}{currentUser ? <button onClick={handleLogout} className="rounded-lg px-3 py-2 text-left text-sm font-medium text-red-700 hover:bg-red-50">Logout</button> : <button onClick={() => handleNavigation('/login')} className="rounded-lg px-3 py-2 text-left text-sm font-medium text-blue-700 hover:bg-blue-50">Login</button>}</div></div>}
      </div>
    </nav>
  );
}
