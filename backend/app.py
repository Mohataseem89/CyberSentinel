from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os

# OPTIONAL content analysis
from dom_utils import try_fetch_dom_summary

app = Flask(__name__)
CORS(app)

# Gemini config
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "model": "gemini-2.5-flash"})


@app.route("/analyze", methods=["POST", "OPTIONS"])
def analyze():
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json()
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "URL is required"}), 400

    print(f"[+] Analyzing URL: {url}")

    # 🔹 Try content-based analysis (NON-BLOCKING)
    dom_summary = try_fetch_dom_summary(url)

    prompt = f"""
You are a cybersecurity phishing detection system.

Classify the following website into EXACTLY ONE category:
- Benign
- Malware
- Defacement
- Phishing

Analyze using:
1. URL structure and keywords
2. Brand impersonation signals
3. Website intent
4. Page content summary (if available)

URL: {url}

Page Content Summary:
{dom_summary if dom_summary else "Content not reachable or unavailable"}

Respond with ONLY ONE word from the categories.
"""

    try:
        response = model.generate_content(prompt)
        prediction = response.text.strip()

        valid = ["Benign", "Malware", "Defacement", "Phishing"]
        for v in valid:
            if v.lower() in prediction.lower():
                return jsonify({
                    "prediction": v,
                    "url": url,
                    "analysis": "URL + Content based"
                }), 200

        # fallback if Gemini response is unexpected
        return jsonify({
            "prediction": "Benign",
            "url": url,
            "analysis": "Fallback"
        }), 200

    except Exception as e:
        print(f"⚠️ Gemini error fallback: {e}")

        # 🔒 SECURITY-FIRST FALLBACK
        return jsonify({
            "prediction": "Phishing",
            "url": url,
            "analysis": "Error fallback"
        }), 200


if __name__ == "__main__":
    print("🚀 CyberSentinel Backend running on http://127.0.0.1:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
