import { useState, useEffect } from 'react';
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Download,
  Calendar,
  Globe,
  BarChart3,
  RefreshCw
} from 'lucide-react';
import {
  PieChart,
  Pie,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';
import axios from 'axios';
import toast from 'react-hot-toast';

// const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';
const API_BASE_URL = 'http://localhost:5000';
export default function Dashboard() {
  const [stats, setStats] = useState({
    total_scans: 0,
    benign_scans: 0,
    suspicious_scans: 0,
    phishing_scans: 0,
    avg_threat_score: 0,
    scans_today: 0,
    blocked_threats: 0
  });

  const [scanHistory, setScanHistory] = useState([]);
  const [topThreats, setTopThreats] = useState([]);
  const [dailyScans, setDailyScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [refreshing, setRefreshing] = useState(false);

  const normalizeStats = (data = {}) => ({
    total_scans: Number(data.total_scans ?? data.totalScans ?? 0),
    benign_scans: Number(data.benign_scans ?? data.benignScans ?? 0),
    suspicious_scans: Number(data.suspicious_scans ?? data.suspiciousScans ?? 0),
    phishing_scans: Number(data.phishing_scans ?? data.phishingScans ?? 0),
    avg_threat_score: Number(data.avg_threat_score ?? data.avgThreatScore ?? 0),
    scans_today: Number(data.scans_today ?? data.scansToday ?? 0),
    blocked_threats: Number(data.blocked_threats ?? data.blockedThreats ?? 0)
  });

  const loadDashboardData = async (showLoader = true) => {
    if (showLoader) setLoading(true);

    try {
      const statsRes = await axios.get(`${API_BASE_URL}/api/analytics/stats`);
      console.log('statsRes.data =', statsRes.data);
      setStats(normalizeStats(statsRes.data));
    } catch (error) {
      console.error('Stats API failed:', error);
    }

    try {
      const historyRes = await axios.get(`${API_BASE_URL}/api/analytics/history?limit=50`);
      console.log('historyRes.data =', historyRes.data);
      setScanHistory(Array.isArray(historyRes.data?.scans) ? historyRes.data.scans : []);
    } catch (error) {
      console.error('History API failed:', error);
    }

    try {
      const dailyRes = await axios.get(`${API_BASE_URL}/api/analytics/daily?days=7`);
      console.log('dailyRes.data =', dailyRes.data);
      setDailyScans(Array.isArray(dailyRes.data?.daily_scans) ? dailyRes.data.daily_scans : []);
    } catch (error) {
      console.error('Daily API failed:', error);
    }

    try {
      const threatsRes = await axios.get(`${API_BASE_URL}/api/analytics/top-threats?limit=10`);
      console.log('threatsRes.data =', threatsRes.data);
      setTopThreats(Array.isArray(threatsRes.data?.threats) ? threatsRes.data.threats : []);
    } catch (error) {
      console.error('Top threats API failed:', error);
    }

    if (showLoader) setLoading(false);
  };

  useEffect(() => {
    loadDashboardData(true);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      loadDashboardData(false);
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const refreshData = async () => {
    setRefreshing(true);
    await loadDashboardData(false);
    setRefreshing(false);
    toast.success('Dashboard refreshed!');
  };

  const pieData = [
    { name: 'Benign', value: stats.benign_scans, color: '#10b981' },
    { name: 'Suspicious', value: stats.suspicious_scans, color: '#f59e0b' },
    { name: 'Phishing', value: stats.phishing_scans, color: '#ef4444' }
  ].filter((item) => item.value > 0);

  const filteredHistory =
    filter === 'all'
      ? scanHistory
      : scanHistory.filter((s) => {
          if (filter === 'benign') return s.verdict === 'Benign';
          if (filter === 'suspicious') return s.verdict === 'Suspicious' || s.verdict === 'Potentially Risky';
          if (filter === 'phishing') return s.verdict === 'Phishing';
          return true;
        });

  const exportToCSV = () => {
    const headers = ['URL', 'Domain', 'Verdict', 'Threat Score', 'Timestamp'];
    const csvData = filteredHistory.map((scan) => [
      scan.url,
      scan.domain,
      scan.verdict,
      scan.threat_score,
      new Date(scan.created_at).toLocaleString()
    ]);

    const csv = [headers, ...csvData].map((row) => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cybersentinel-scans-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    toast.success('CSV exported successfully!');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Shield className="w-16 h-16 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-10">
      <div className="max-w-7xl mx-auto px-6">
        <div className="mb-10 bg-gradient-to-r from-blue-50 to-white p-6 rounded-xl border border-gray-100">          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">Analytics Dashboard</h1>
              <p className="text-gray-600">Real-time scan statistics and threat analysis</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={refreshData}
                disabled={refreshing}
                className="flex items-center gap-2 bg-white border border-gray-300 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-5 h-5 transition-transform ${refreshing ? 'animate-spin' : ''}`} />
                Refresh
              </button>
              <button
                onClick={exportToCSV}
                className="flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Download className="w-5 h-5" />
                Export CSV
              </button>
            </div>
          </div>
        </div>

        {/* TEMP DEBUG - remove later */}
        {/* <div className="bg-white rounded-xl shadow p-4 mb-6 text-sm">
          <div><strong>DEBUG stats:</strong> {JSON.stringify(stats)}</div>
          <div><strong>DEBUG API_BASE_URL:</strong> {API_BASE_URL}</div>
          <div><strong>DEBUG history count:</strong> {scanHistory.length}</div>
          <div><strong>DEBUG daily count:</strong> {dailyScans.length}</div>
          <div><strong>DEBUG threats count:</strong> {topThreats.length}</div>
        </div> */}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="bg-blue-100 p-3 rounded-lg">
                <BarChart3 className="w-6 h-6 text-blue-600" />
              </div>
              <span className="text-sm text-gray-500">Total</span>
            </div>
            <h3 className="text-3xl font-bold text-gray-900 mb-1">{stats.total_scans}</h3>
            <p className="text-sm text-gray-600">Total Scans</p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="bg-green-100 p-3 rounded-lg">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
              <span className="text-sm text-gray-500">
                {stats.total_scans > 0 ? ((stats.benign_scans / stats.total_scans) * 100).toFixed(1) : 0}%
              </span>
            </div>
            <h3 className="text-3xl font-bold text-green-600 mb-1">{stats.benign_scans}</h3>
            <p className="text-sm text-gray-600">Benign Sites</p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="bg-orange-100 p-3 rounded-lg">
                <AlertTriangle className="w-6 h-6 text-orange-600" />
              </div>
              <span className="text-sm text-gray-500">
                {stats.total_scans > 0 ? ((stats.suspicious_scans / stats.total_scans) * 100).toFixed(1) : 0}%
              </span>
            </div>
            <h3 className="text-3xl font-bold text-orange-600 mb-1">{stats.suspicious_scans}</h3>
            <p className="text-sm text-gray-600">Suspicious Sites</p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="bg-red-100 p-3 rounded-lg">
                <XCircle className="w-6 h-6 text-red-600" />
              </div>
              <span className="text-sm text-gray-500">
                {stats.total_scans > 0 ? ((stats.phishing_scans / stats.total_scans) * 100).toFixed(1) : 0}%
              </span>
            </div>
            <h3 className="text-3xl font-bold text-red-600 mb-1">{stats.phishing_scans}</h3>
            <p className="text-sm text-gray-600">Phishing Sites</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Threat Distribution</h2>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={100}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={index} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-gray-400">
                <p>No scan data yet. Start scanning URLs!</p>
              </div>
            )}
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Daily Scan Trends (Last 7 Days)</h2>
            {dailyScans.some((item) => item.total > 0) ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={dailyScans}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="benign" stroke="#10b981" strokeWidth={2} />
                  <Line type="monotone" dataKey="suspicious" stroke="#f59e0b" strokeWidth={2} />
                  <Line type="monotone" dataKey="phishing" stroke="#ef4444" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-gray-400">
                <p>No daily trend data available yet</p>
              </div>
            )}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
              <Calendar className="w-6 h-6 text-blue-600" />
              Scan History ({filteredHistory.length})
            </h2>
          </div>

          {filteredHistory.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">URL</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Verdict</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Threat Score</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredHistory.slice(0, 20).map((scan) => (
                    <tr key={scan.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4">{scan.url}</td>
                      <td className="py-3 px-4">{scan.verdict}</td>
                      <td className="py-3 px-4">{scan.threat_score}</td>
                      <td className="py-3 px-4">{new Date(scan.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12">
              <Shield className="w-16 h-16 text-gray-200 mx-auto mb-4" />
              <p className="text-gray-400 text-sm">No scans found.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}