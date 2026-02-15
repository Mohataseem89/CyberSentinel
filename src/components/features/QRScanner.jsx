import { useState, useRef } from 'react';
import { Camera, Upload, AlertTriangle, CheckCircle, XCircle, QrCode, Link, Shield, Zap } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

export default function QRScanner() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [qrResult, setQrResult] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file type
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/bmp', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      toast.error('Please upload a valid image file (PNG, JPG, GIF, BMP, WEBP)');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('File size must be less than 5MB');
      return;
    }

    setSelectedFile(file);
    setQrResult(null);

    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreview(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const handleScanQR = async () => {
    if (!selectedFile) {
      toast.error('Please select an image first');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('image', selectedFile);

    try {
      const response = await axios.post('http://localhost:5000/api/qr/scan', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setQrResult(response.data);

      if (response.data.is_url) {
        toast.success(' QR code scanned and URL analyzed!');
      } else {
        toast.success(' QR code scanned successfully!');
      }

    } catch (error) {
      console.error('QR scan error:', error);
      const errorMsg = error.response?.data?.error || error.response?.data?.message || 'Failed to scan QR code';
      toast.error(errorMsg);
      setQrResult({ error: errorMsg });
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPreview(null);
    setQrResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getVerdictColor = (verdict) => {
    switch (verdict) {
      case 'Benign':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'Potentially Risky':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'Suspicious':
        return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'Phishing':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getVerdictIcon = (verdict) => {
    switch (verdict) {
      case 'Benign':
        return <CheckCircle className="w-6 h-6 text-green-600" />;
      case 'Potentially Risky':
        return <AlertTriangle className="w-6 h-6 text-yellow-600" />;
      case 'Suspicious':
        return <AlertTriangle className="w-6 h-6 text-orange-600" />;
      case 'Phishing':
        return <XCircle className="w-6 h-6 text-red-600" />;
      default:
        return <Shield className="w-6 h-6 text-gray-600" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-10">
      <div className="max-w-6xl mx-auto px-6">
        
        {/* Header */}
        <div className="text-center mb-10">
          <div className="flex items-center justify-center gap-3 mb-4">
            <QrCode className="w-12 h-12 text-blue-600" />
            <h1 className="text-4xl font-bold text-gray-900">QR Code Scanner</h1>
          </div>
          <p className="text-gray-600 text-lg">
            Upload or scan QR codes to detect malicious URLs and phishing attempts
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          
          {/* Upload Section */}
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-semibold mb-6 flex items-center gap-2">
              <Upload className="w-6 h-6 text-blue-600" />
              Upload QR Code
            </h2>

            {/* File Input */}
            <div className="mb-6">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileSelect}
                className="hidden"
                id="qr-file-input"
              />
              <label
                htmlFor="qr-file-input"
                className="flex flex-col items-center justify-center w-full h-64 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-colors"
              >
                {preview ? (
                  <img src={preview} alt="QR Code Preview" className="max-h-60 max-w-full object-contain" />
                ) : (
                  <div className="text-center">
                    <Camera className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600 mb-2">Click to upload QR code image</p>
                    <p className="text-sm text-gray-400">PNG, JPG, GIF, BMP, WEBP (max 5MB)</p>
                  </div>
                )}
              </label>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button
                onClick={handleScanQR}
                disabled={!selectedFile || loading}
                className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-semibold flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Zap className="w-5 h-5 animate-spin" />
                    Scanning...
                  </>
                ) : (
                  <>
                    <QrCode className="w-5 h-5" />
                    Scan QR Code
                  </>
                )}
              </button>

              {(selectedFile || qrResult) && (
                <button
                  onClick={handleReset}
                  className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-semibold"
                >
                  Reset
                </button>
              )}
            </div>

            {selectedFile && (
              <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  📎 {selectedFile.name} ({(selectedFile.size / 1024).toFixed(2)} KB)
                </p>
              </div>
            )}
          </div>

          {/* Results Section */}
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-semibold mb-6 flex items-center gap-2">
              <Shield className="w-6 h-6 text-blue-600" />
              Scan Results
            </h2>

            {!qrResult ? (
              <div className="text-center py-16 text-gray-400">
                <QrCode className="w-24 h-24 mx-auto mb-4 opacity-50" />
                <p className="text-lg">Upload a QR code to see results</p>
              </div>
            ) : qrResult.error ? (
              <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-start gap-3">
                  <XCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-1" />
                  <div>
                    <h3 className="font-semibold text-red-800 mb-2">Scan Failed</h3>
                    <p className="text-red-700">{qrResult.error}</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                
                {/* QR Data */}
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-start gap-3 mb-3">
                    <QrCode className="w-5 h-5 text-gray-600 flex-shrink-0 mt-1" />
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-gray-900 mb-1">QR Code Data</h3>
                      <p className="text-sm text-gray-700 break-all">{qrResult.qr_data}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2 text-sm">
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
                      {qrResult.data_type}
                    </span>
                    {qrResult.is_url && (
                      <span className="px-2 py-1 bg-green-100 text-green-800 rounded flex items-center gap-1">
                        <Link className="w-3 h-3" />
                        URL Detected
                      </span>
                    )}
                  </div>
                </div>

                {/* URL Analysis Results */}
                {qrResult.is_url && qrResult.url_analysis && (
                  <div className={`p-6 rounded-lg border-2 ${getVerdictColor(qrResult.url_analysis.final_verdict)}`}>
                    <div className="flex items-start gap-4 mb-4">
                      {getVerdictIcon(qrResult.url_analysis.final_verdict)}
                      <div className="flex-1">
                        <h3 className="text-xl font-bold mb-2">
                          {qrResult.url_analysis.final_verdict}
                        </h3>
                        <p className="text-lg">
                          Threat Score: <strong>{qrResult.url_analysis.threat_score}%</strong>
                        </p>
                      </div>
                    </div>

                    {/* Threat Score Bar */}
                    <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
                      <div
                        className={`h-3 rounded-full ${
                          qrResult.url_analysis.threat_score >= 70 ? 'bg-red-500' :
                          qrResult.url_analysis.threat_score >= 50 ? 'bg-orange-500' :
                          qrResult.url_analysis.threat_score >= 30 ? 'bg-yellow-500' :
                          'bg-green-500'
                        }`}
                        style={{ width: `${qrResult.url_analysis.threat_score}%` }}
                      ></div>
                    </div>

                    {/* Recommendations */}
                    {qrResult.url_analysis.recommendations && qrResult.url_analysis.recommendations.length > 0 && (
                      <div className="mt-4">
                        <h4 className="font-semibold mb-2">Recommendations:</h4>
                        <ul className="space-y-1">
                          {qrResult.url_analysis.recommendations.map((rec, idx) => (
                            <li key={idx} className="text-sm flex items-start gap-2">
                              <span>•</span>
                              <span>{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {/* Non-URL Data */}
                {!qrResult.is_url && (
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-blue-800">
                       This QR code does not contain a URL. It contains {qrResult.data_type} data.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Info Section */}
        <div className="mt-12 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-8">
          <h3 className="text-2xl font-semibold text-blue-900 mb-6 text-center">
            How QR Code Scanning Works
          </h3>
          
          <div className="grid md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-3 text-2xl font-bold">
                1
              </div>
              <h4 className="font-semibold mb-2">Upload Image</h4>
              <p className="text-sm text-blue-800">
                Select a QR code image from your device
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-3 text-2xl font-bold">
                2
              </div>
              <h4 className="font-semibold mb-2">Decode QR</h4>
              <p className="text-sm text-blue-800">
                Advanced algorithms extract data from the QR code
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-3 text-2xl font-bold">
                3
              </div>
              <h4 className="font-semibold mb-2">Analyze URL</h4>
              <p className="text-sm text-blue-800">
                If URL detected, automatically analyze for threats
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-3 text-2xl font-bold">
                4
              </div>
              <h4 className="font-semibold mb-2">Get Results</h4>
              <p className="text-sm text-blue-800">
                View threat assessment and safety recommendations
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}