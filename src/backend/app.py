from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from routes import upload_routes
from clamav_service import scan_file
from services.url_analyzer import HybridURLAnalyzer

app = Flask(__name__)
CORS(app)

# Ensure uploads folder exists
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.register_blueprint(upload_routes)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "analyzer": "Hybrid ML + VirusTotal + Content"})

@app.route('/')
def home():
    return "CyberSentinel Backend Running - Hybrid ML Analysis"


#Ffila scna claamav wala
@app.route("/api/scan", methods=["POST"])
def scan_uploaded_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(file_path)

    #  Scan using ClamAV
    scan_result = scan_file(file_path)

    # Delete file after scanning
    try:
        os.remove(file_path)
    except:
        pass

    # Format response to match frontend expectations
    if scan_result.get("status") == "infected":
        return jsonify({"infected": True, "details": scan_result.get("details")}), 200
    elif scan_result.get("status") == "clean":
        return jsonify({"infected": False, "message": "File is clean"}), 200
    else:
        return jsonify({"error": scan_result.get("message", "Scan failed")}), 500


#  URL ANALYSIS (NEW HYBRID APPROACH)

@app.route("/analyze", methods=["POST", "OPTIONS"])
def analyze():
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json()
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "URL is required"}), 400

    print(f"[+] Analyzing URL: {url}")

    try:
        # Use hybrid analyzer
        analyzer = HybridURLAnalyzer()
        result = analyzer.analyze(url)
        
        return jsonify(result), 200

    except Exception as e:
        print(f" Analysis error: {e}")
        return jsonify({
            "error": str(e),
            "final_verdict": "Error",
            "threat_score": 0
        }), 500

if __name__ == "__main__":
    print("CyberSentinel Backend - Hybrid ML Analysis System")
    print("ML Model + VirusTotal + Content Analysis")
    app.run(debug=True, host="0.0.0.0", port=5000)