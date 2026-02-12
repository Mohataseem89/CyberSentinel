import { useState } from 'react';
import { AlertTriangle, CheckCircle, Flag, Send, Info, Target, Shield, Eye, Bug, Zap } from 'lucide-react';
import toast from 'react-hot-toast';

import Button from '../UI/Button';
import Input from '../UI/Input';
import Card from '../UI/Card';
import { submitFeedback } from '../../services/api';
import { validateURL } from '../../utils/helpers';

export default function FeedbackForm() {
  const [formData, setFormData] = useState({
    url: '',
    actualThreat: '',
    ourPrediction: '',
    description: '',
    category: ''
  });
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const threatLevels = [
    { value: 'Benign', label: 'Benign/Safe', icon: CheckCircle, color: 'text-success-600', bg: 'bg-success-50' },
    { value: 'Defacement', label: 'Defacement', icon: Eye, color: 'text-warning-600', bg: 'bg-warning-50' },
    { value: 'Malware', label: 'Malware', icon: Bug, color: 'text-danger-600', bg: 'bg-danger-50' },
    { value: 'Phishing', label: 'Phishing', icon: Zap, color: 'text-purple-600', bg: 'bg-purple-50' }
  ];

  const categories = [
    { value: 'false_negative', label: 'False Negative', description: 'Our system marked it as safe, but it\'s actually malicious' },
    { value: 'false_positive', label: 'False Positive', description: 'Our system marked it as malicious, but it\'s actually safe' },
    { value: 'new_threat', label: 'New Threat', description: 'Recently discovered malicious website not in our database' },
    { value: 'improvement', label: 'General Improvement', description: 'Suggestions for better detection accuracy' }
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.url.trim()) {
      toast.error('Please enter a URL');
      return;
    }

    const validation = validateURL(formData.url);
    if (!validation.isValid) {
      toast.error(validation.error);
      return;
    }

    if (!formData.actualThreat) {
      toast.error('Please select the actual threat level');
      return;
    }

    if (!formData.category) {
      toast.error('Please select a feedback category');
      return;
    }

    setLoading(true);

    try {
      await submitFeedback({
        url: formData.url.trim(),
        actualThreat: formData.actualThreat,
        ourPrediction: formData.ourPrediction,
        description: formData.description.trim(),
        category: formData.category,
        submittedAt: new Date().toISOString()
      });

      toast.success('🎉 Thank you! Your feedback helps improve our detection system');
      setSubmitted(true);
      
      setTimeout(() => {
        setFormData({
          url: '',
          actualThreat: '',
          ourPrediction: '',
          description: '',
          category: ''
        });
        setSubmitted(false);
      }, 3000);

    } catch (error) {
      console.error('Feedback submission failed:', error);
      toast.error('Failed to submit feedback. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="max-w-md text-center p-8">
          <CheckCircle className="w-16 h-16 text-success-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Thank You!</h2>
          <p className="text-gray-600 mb-6">
            Your feedback has been submitted successfully. Our AI will learn from your input to provide better protection.
          </p>
          <div className="text-sm text-gray-500">
            Redirecting back to form...
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <div className="flex justify-center items-center mb-4">
              <Flag className="w-12 h-12 text-primary-600 mr-3" />
              <h1 className="text-4xl font-bold text-gray-900">Report & Improve</h1>
            </div>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Help us improve CyberSentinel by reporting misclassified URLs and discovering new threats
            </p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid lg:grid-cols-2 gap-8">
          
          {/* Main Form */}
          <div>
            <Card className="p-6">
              <div className="flex items-center mb-6">
                <Target className="w-6 h-6 text-primary-600 mr-3" />
                <h2 className="text-xl font-semibold text-gray-900">Submit URL Feedback</h2>
              </div>

              <form onSubmit={handleSubmit} className="space-y-6">
                {/* URL Input */}
                <Input
                  label="Website URL"
                  placeholder="https://suspicious-website.com"
                  value={formData.url}
                  className=" w-full"
                  onChange={(e) => handleInputChange('url', e.target.value)}
                  required
                />

                {/* Feedback Category */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Feedback Category <span className="text-danger-500">*</span>
                  </label>
                  <div className="grid gap-3">
                    {categories.map((cat) => (
                      <div
                        key={cat.value}
                        onClick={() => handleInputChange('category', cat.value)}
                        className={`p-4 border rounded-lg cursor-pointer transition-all ${
                          formData.category === cat.value
                            ? 'border-primary-500 bg-primary-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <div className="font-medium text-gray-900 mb-1">{cat.label}</div>
                        <div className="text-sm text-gray-600">{cat.description}</div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Our Prediction */}
                {(formData.category === 'false_negative' || formData.category === 'false_positive') && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-3">
                      What did CyberSentinel predict?
                    </label>
                    <div className="grid grid-cols-2 gap-3">
                      {threatLevels.map((threat) => {
                        const Icon = threat.icon;
                        return (
                          <div
                            key={threat.value}
                            onClick={() => handleInputChange('ourPrediction', threat.value)}
                            className={`p-3 border rounded-lg cursor-pointer transition-all ${
                              formData.ourPrediction === threat.value
                                ? 'border-primary-500 bg-primary-50'
                                : 'border-gray-200 hover:border-gray-300'
                            }`}
                          >
                            <div className="flex items-center">
                              <Icon className={`w-4 h-4 mr-2 ${threat.color}`} />
                              <span className="text-sm font-medium">{threat.label}</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Actual Threat Level */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Actual Threat Level <span className="text-danger-500">*</span>
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    {threatLevels.map((threat) => {
                      const Icon = threat.icon;
                      return (
                        <div
                          key={threat.value}
                          onClick={() => handleInputChange('actualThreat', threat.value)}
                          className={`p-4 border rounded-lg cursor-pointer transition-all ${
                            formData.actualThreat === threat.value
                              ? 'border-primary-500 bg-primary-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <div className="flex items-center mb-2">
                            <Icon className={`w-5 h-5 mr-2 ${threat.color}`} />
                            <span className="font-medium">{threat.label}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Additional Details (Optional)
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    placeholder="Provide any additional context or evidence..."
                    className="input-primary min-h-24 w-full"
                    rows={3}
                  />
                </div>

                {/* Submit Button */}
                <Button
                  type="submit"
                  loading={loading}
                  disabled={!formData.url || !formData.actualThreat || !formData.category}
                  className="w-full bg-blue-700"
                >
                  <Send className="w-4 h-4 mr-2" />
                  {loading ? 'Submitting...' : 'Submit Feedback'}
                </Button>
              </form>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* How it Works */}
            <Card className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50">
              <h3 className="text-lg font-semibold text-blue-900 mb-4 flex items-center">
                <Info className="w-5 h-5 mr-2" />
                How It Works
              </h3>
              <div className="space-y-4">
                {[
                  'Submit URL with correct classification',
                  'Our team reviews and validates feedback',
                  'AI model learns and improves accuracy',
                  'Better protection for all users'
                ].map((step, index) => (
                  <div key={index} className="flex items-start">
                    <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold mr-3 mt-0.5 flex-shrink-0">
                      {index + 1}
                    </div>
                    <span className="text-sm text-blue-800">{step}</span>
                  </div>
                ))}
              </div>
            </Card>

            {/* Stats */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Shield className="w-5 h-5 mr-2" />
                Community Impact
              </h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center p-3 bg-success-50 rounded-lg">
                  <span className="text-success-700 font-medium">Reports Submitted</span>
                  <span className="text-success-600 font-bold">2,847</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-primary-50 rounded-lg">
                  <span className="text-primary-700 font-medium">Model Improvements</span>
                  <span className="text-primary-600 font-bold">156</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                  <span className="text-purple-700 font-medium">Accuracy Boost</span>
                  <span className="text-purple-600 font-bold">+12.3%</span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
