from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configure Gemini API
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

# Initialize Gemini 2.5 model
model = genai.GenerativeModel('gemini-2.5-flash')

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'CyberSentinel API is running',
        'endpoints': {
            '/analyze': 'POST - Analyze URL',
            '/health': 'GET - Health check'
        }
    })

@app.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze_url():
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        url = data.get('url', '')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        print(f"Analyzing URL: {url}")  # Debug log
        
        # Create prompt for Gemini to classify the URL
        prompt = f"""Analyze this URL and classify it into EXACTLY ONE of these four categories:
- Benign
- Malware
- Defacement
- Phishing

URL to analyze: {url}

Respond with ONLY the category name (one word). No explanation, no summary, just the single word classification."""
        
        # Get prediction from Gemini
        response = model.generate_content(prompt)
        prediction = response.text.strip()
        
        print(f"Gemini response: {prediction}")  # Debug log
        
        # Validate and normalize the response
        valid_categories = ['Benign', 'Malware', 'Defacement', 'Phishing']
        normalized_prediction = None
        
        for category in valid_categories:
            if category.lower() in prediction.lower():
                normalized_prediction = category
                break
        
        # Default to Benign if no valid category found
        if not normalized_prediction:
            normalized_prediction = 'Benign'
        
        result = {
            'prediction': normalized_prediction,
            'url': url
        }
        
        print(f"Returning result: {result}")  # Debug log
        
        return jsonify(result), 200
    
    except Exception as e:
        print(f"Error: {str(e)}")  # Debug log
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'model': 'gemini-2.5-flash'})

if __name__ == '__main__':
    print("Starting Flask server on http://127.0.0.1:5000")
    print("Make sure GEMINI_API_KEY environment variable is set")
    app.run(debug=True, host='0.0.0.0', port=5000)