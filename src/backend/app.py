from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from routes import upload_routes
from clamav_service import scan_file
from services.url_analyzer import HybridURLAnalyzer
from services.qr_service import QRCodeScanner
# import os

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
    


# QR CODE SCANNER ENDPOINTS

@app.route("/api/qr/scan", methods=["POST"])
def scan_qr_code():
    """
    Scan QR code from uploaded image
    Returns extracted data and analyzes if it's a URL
    """
    try:
        if "image" not in request.files:
            return jsonify({"error": "No image file uploaded"}), 400
        
        image = request.files["image"]
        
        if image.filename == "":
            return jsonify({"error": "Empty filename"}), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
        file_ext = image.filename.rsplit('.', 1)[1].lower() if '.' in image.filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({
                "error": "Invalid file type. Allowed: PNG, JPG, JPEG, GIF, BMP, WEBP"
            }), 400
        
        # Save uploaded image temporarily
        upload_folder = app.config.get("UPLOAD_FOLDER", "uploads")
        os.makedirs(upload_folder, exist_ok=True)
        
        image_path = os.path.join(upload_folder, f"qr_{image.filename}")
        image.save(image_path)
        
        print(f"[+] Scanning QR code from: {image.filename}")
        
        # Decode QR code
        scanner = QRCodeScanner()
        result = scanner.decode_qr_code(image_path)
        
        # Delete temporary file
        try:
            os.remove(image_path)
        except:
            pass
        
        if result["status"] == "error":
            return jsonify(result), 400
        
        # If it's a URL, analyze it automatically
        analysis_result = None
        if result["is_url"]:
            url = result["data"]
            
            try:
                print(f"[+] Auto-analyzing URL from QR: {url}")
                analyzer = HybridURLAnalyzer()
                analysis_result = analyzer.analyze(url)
                
                # Save to database
                save_url_scan(
                    url=url,
                    verdict=analysis_result.get('final_verdict'),
                    threat_score=analysis_result.get('threat_score'),
                    ml_prediction=analysis_result.get('breakdown', {}).get('ml'),
                    virustotal_result=analysis_result.get('breakdown', {}).get('virustotal'),
                    content_analysis=analysis_result.get('breakdown', {}).get('content')
                )
            except Exception as e:
                print(f" Auto-analysis failed: {e}")
        
        return jsonify({
            "success": True,
            "qr_data": result["data"],
            "data_type": result["type"],
            "is_url": result["is_url"],
            "qr_count": result.get("qr_count", 1),
            "url_analysis": analysis_result
        }), 200
        
    except Exception as e:
        print(f" QR scan error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Failed to scan QR code",
            "details": str(e)
        }), 500

@app.route("/api/qr/analyze-url", methods=["POST"])
def analyze_qr_url():
    """
    Analyze URL extracted from QR code
    """
    try:
        data = request.get_json()
        url = data.get("url", "").strip()
        
        if not url:
            return jsonify({"error": "URL is required"}), 400
        
        print(f"[+] Analyzing QR URL: {url}")
        
        analyzer = HybridURLAnalyzer()
        result = analyzer.analyze(url)
        
        # Save to database
        save_url_scan(
            url=url,
            verdict=result.get('final_verdict'),
            threat_score=result.get('threat_score'),
            ml_prediction=result.get('breakdown', {}).get('ml'),
            virustotal_result=result.get('breakdown', {}).get('virustotal'),
            content_analysis=result.get('breakdown', {}).get('content')
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f" QR URL analysis error: {e}")
        return jsonify({
            "error": str(e),
            "final_verdict": "Error",
            "threat_score": 0
        }), 500

if __name__ == "__main__":
    print("CyberSentinel Backend - Hybrid ML Analysis System")
    print("ML Model + VirusTotal + Content Analysis")
    app.run(debug=True, host="0.0.0.0", port=5000)