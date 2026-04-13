from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_jwt_extended import JWTManager, verify_jwt_in_request, get_jwt_identity, get_jwt
import os
import csv
import io
from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv
from database import save_scan, save_feedback, update_feedback_status, get_all_feedback, append_approved_feedback_to_csv
from analytics import analytics_bp
import subprocess
import sys
from services.ml_predictor import predictor
from flask_jwt_extended.exceptions import JWTExtendedException
from routes.auth import auth_bp

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
# app = Flask(__name__)

print(">>> LOADED UPDATED app.py <<<")
print(">>> FILE PATH:", __file__)

CORS(app)

CORS(app, resources={r"/api/*": {"origins": "*"}})

# Load config
from config import Config
app.config.from_object(Config)

CORS(
    app,
    resources={r"/*": {"origins": ["http://localhost:5173"]}},
    supports_credentials=True
)

# Initialize JWT
jwt = JWTManager(app)

@jwt.unauthorized_loader
def unauthorized_callback(reason):
    print("JWT unauthorized:", reason)
    return jsonify({"error": reason}), 401

@jwt.invalid_token_loader
def invalid_token_callback(reason):
    print("JWT invalid:", reason)
    return jsonify({"error": reason}), 422

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    print("JWT expired")
    return jsonify({"error": "Token has expired"}), 401

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    print("JWT revoked")
    return jsonify({"error": "Token has been revoked"}), 401

@jwt.needs_fresh_token_loader
def fresh_token_callback(jwt_header, jwt_payload):
    print("JWT fresh token required")
    return jsonify({"error": "Fresh token required"}), 401

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
# app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
app.register_blueprint(analytics_bp)

# Import services
from services.url_analyzer import HybridURLAnalyzer
from services.qr_service import QRCodeScanner
# from clamav_service import scan_file
from database import save_scan


def admin_required():
    verify_jwt_in_request()
    claims = get_jwt()
    role = claims.get("role")

    if role != "admin":
        return jsonify({"error": "Admin access required"}), 403

    return None
# BASIC ROUTES
@app.route('/')
def home():
    return jsonify({
        "message": "CyberSentinel Backend Running",
        "version": "2.0.0",
        "features": ["URL Analysis", "Email Scanning", "QR Code", "Document Scan", "Authentication", "Analytics"]
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "analyzer": "Hybrid ML + VirusTotal + Content"})

# URL ANALYSIS

@app.route("/analyze", methods=["POST"])
def analyze():
    """Analyze URL for phishing"""
    try:
        data = request.get_json()
        url = data.get("url", "").strip()

        if not url:
            return jsonify({"error": "URL is required"}), 400

        print(f"[+] Analyzing URL: {url}")

        user_id = None
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except Exception:
            pass

        analyzer = HybridURLAnalyzer()
        result = analyzer.analyze(url)

        try:
            domain = urlparse(url).netloc or url

            breakdown = result.get("breakdown", {})
            ml_data = breakdown.get("ml", {}) or {}
            vt_data = breakdown.get("virustotal", {}) or {}
            content_data = breakdown.get("content", {}) or {}

            scan_data = {
                "user_id": user_id,
                "url": url,
                "domain": domain,
                "verdict": result.get("final_verdict"),
                "threat_score": result.get("threat_score"),
                "ml_prediction": ml_data.get("prediction"),
                "ml_confidence": ml_data.get("confidence"),
                "virustotal_malicious": vt_data.get("malicious", 0),
                "virustotal_suspicious": vt_data.get("suspicious", 0),
                "has_ssl": content_data.get("details", {}).get("ssl", {}).get("has_https", False),
                "has_forms": content_data.get("details", {}).get("has_login_form", False),
                "suspicious_keywords": bool(content_data.get("indicators")),
                "scan_type": "url",
                "ip_address": request.remote_addr,
                "user_agent": request.headers.get("User-Agent", "")
            }

            save_scan(scan_data)
            print("Scan saved to database")

        except Exception as e:
            print(f"Failed to save scan: {e}")

        return jsonify(result), 200

    except Exception as e:
        print(f"Analysis error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

###feedback

##just to test
# def admin_required():
#     verify_jwt_in_request()
#     claims = get_jwt()
#     role = claims.get("role")

#     if role != "admin":
#         return jsonify({"error": "Admin access required"}), 403

#     return None

@app.errorhandler(JWTExtendedException)
def handle_jwt_errors(e):
    print(" JWT ERROR:", str(e))
    return jsonify({"error": str(e)}), 422



###feedback
@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400

        url = (data.get("url") or "").strip()
        category = (data.get("category") or "").strip()
        actual_threat = (data.get("actual_threat") or "").strip()
        our_prediction = (data.get("our_prediction") or "").strip()
        description = (data.get("description") or "").strip()

        if not url:
            return jsonify({"error": "URL is required"}), 400

        if not category:
            return jsonify({"error": "Category is required"}), 400

        user_id = None
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except Exception:
            pass

        feedback_data = {
            "user_id": user_id,
            "url": url,
            "category": category,
            "actual_threat": actual_threat,
            "our_prediction": our_prediction,
            "description": description
        }

        saved_feedback = save_feedback(feedback_data)

        print(f"[+] Feedback saved as pending: {url}")

        return jsonify({
            "message": "Feedback submitted successfully and marked as pending review",
            "feedback": saved_feedback
        }), 201

    except Exception as e:
        print(f" Feedback error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
@app.route("/api/feedback", methods=["GET"])
def get_feedback():
    admin_check = admin_required()
    if admin_check:
        return admin_check
    try:
        status = request.args.get("status")  # optional filter

        feedback_list = get_all_feedback(status)

        return jsonify({
            "count": len(feedback_list),
            "feedback": feedback_list
        }), 200

    except Exception as e:
        print(f" Error fetching feedback: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/feedback/<int:feedback_id>/approve", methods=["PUT"])
def approve_feedback(feedback_id):
    admin_check = admin_required()
    if admin_check:
        return admin_check
    try:
        updated_feedback = update_feedback_status(feedback_id, "approved")

        if not updated_feedback:
            return jsonify({"error": "Feedback not found"}), 404

        csv_result = append_approved_feedback_to_csv(updated_feedback)

        print(f"[+] Feedback approved: {updated_feedback.get('url')}")
        print(f"[+] Approved CSV status: {csv_result}")

        return jsonify({
            "message": "Feedback approved successfully",
            "feedback": updated_feedback,
            "csv": csv_result
        }), 200

    except Exception as e:
        print(f" Approve feedback error: {e}")
        return jsonify({"error": str(e)}), 500



@app.route("/api/feedback/<int:feedback_id>/reject", methods=["PUT"])
def reject_feedback(feedback_id):
    admin_check = admin_required()
    if admin_check:
        return admin_check
    try:
        updated = update_feedback_status(feedback_id, "rejected")

        if not updated:
            return jsonify({"error": "Feedback not found"}), 404

        return jsonify({
            "message": "Feedback rejected",
            "feedback": updated
        }), 200

    except Exception as e:
        print(f" Reject error: {e}")
        return jsonify({"error": str(e)}), 500
    

@app.route("/api/feedback/export-approved", methods=["GET"])
def export_approved_feedback():
    admin_check = admin_required()
    if admin_check:
        return admin_check
    try:
        approved_feedback = get_all_feedback(status="approved")

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "id",
            "url",
            "category",
            "actual_threat",
            "our_prediction",
            "description",
            "status",
            "created_at"
        ])

        for item in approved_feedback:
            writer.writerow([
                item.get("id"),
                item.get("url"),
                item.get("category"),
                item.get("actual_threat"),
                item.get("our_prediction"),
                item.get("description"),
                item.get("status"),
                item.get("created_at"),
            ])

        csv_data = output.getvalue()
        output.close()

        return Response(
            csv_data,
            mimetype="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=approved_feedback.csv"
            }
        )

    except Exception as e:
        print(f" Export approved feedback error: {e}")
        return jsonify({"error": str(e)}), 500    
    


@app.route("/api/feedback/stats", methods=["GET"])
def feedback_stats():
    admin_check = admin_required()
    if admin_check:
        return admin_check
    try:
        all_feedback = get_all_feedback()

        total = len(all_feedback)
        pending = len([f for f in all_feedback if f.get("status") == "pending"])
        approved = len([f for f in all_feedback if f.get("status") == "approved"])
        rejected = len([f for f in all_feedback if f.get("status") == "rejected"])

        return jsonify({
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected
        }), 200

    except Exception as e:
        print(f" Feedback stats error: {e}")
        return jsonify({"error": str(e)}), 500
    

##retrain part    
    
@app.route("/api/admin/retrain-model", methods=["POST"])
def retrain_model():
    admin_check = admin_required()
    if admin_check:
        return admin_check
    """
    Safely run:
    1. prepare_training_data.py
    2. train_model.py
    """
    try:
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        ml_dir = os.path.join(backend_dir, "ml")

        prepare_script = os.path.join(ml_dir, "prepare_training_data.py")
        train_script = os.path.join(ml_dir, "train_model.py")

        if not os.path.exists(prepare_script):
            return jsonify({"error": f"prepare_training_data.py not found at {prepare_script}"}), 500

        if not os.path.exists(train_script):
            return jsonify({"error": f"train_model.py not found at {train_script}"}), 500

        print("\n[ADMIN] Starting model retraining...")
        print(f"[ADMIN] ML directory: {ml_dir}")

        # Step 1: prepare dataset
        prepare_result = subprocess.run(
            [sys.executable, prepare_script],
            cwd=ml_dir,
            capture_output=True,
            text=True
        )

        if prepare_result.returncode != 0:
            print("[ADMIN] Dataset preparation failed")
            print(prepare_result.stderr)
            return jsonify({
                "success": False,
                "step": "prepare_training_data",
                "error": prepare_result.stderr or "Dataset preparation failed",
                "stdout": prepare_result.stdout
            }), 500

        # Step 2: train model
        train_result = subprocess.run(
            [sys.executable, train_script],
            cwd=ml_dir,
            capture_output=True,
            text=True
        )

        if train_result.returncode != 0:
            print("[ADMIN] Model training failed")
            print(train_result.stderr)
            return jsonify({
                "success": False,
                "step": "train_model",
                "error": train_result.stderr or "Model training failed",
                "stdout": train_result.stdout
            }), 500

        print("[ADMIN] Model retraining completed successfully")

        # NEW: reload model in memory
        reload_success = predictor.reload_model()

        return jsonify({
            "success": True,
            "message": "Model retrained successfully",
            "model_reloaded": reload_success,
            "prepare_output": prepare_result.stdout,
            "train_output": train_result.stdout
        }), 200


    except Exception as e:
        print(f"[ADMIN] Retrain error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    

@app.route("/api/admin/reload-model", methods=["POST"])
def reload_model():
    admin_check = admin_required()
    if admin_check:
        return admin_check
    success = predictor.reload_model()
    return jsonify({
        "success": success,
        "message": "Model reloaded" if success else "Reload failed"
    }), 200 if success else 500      



# QR CODE SCANNER
@app.route("/api/qr/scan", methods=["POST"])
def scan_qr():
    """Scan QR code from uploaded image"""
    try:
        if "image" not in request.files:
            return jsonify({"error": "No image file uploaded"}), 400
        
        image = request.files["image"]
        
        if image.filename == "":
            return jsonify({"error": "Empty filename"}), 400
        
        # Save image
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], f"qr_{image.filename}")
        image.save(image_path)
        
        print(f"[+] Scanning QR code from: {image.filename}")
        
        # Decode QR
        scanner = QRCodeScanner()
        result = scanner.decode_qr_code(image_path)
        
        # Delete file
        try:
            os.remove(image_path)
        except:
            pass
        
        if result["status"] == "error":
            return jsonify(result), 400
        
       # Auto-analyze URL if found
        analysis_result = None
        if result["is_url"]:
            url = result["data"]
            
            try:
                analyzer = HybridURLAnalyzer()
                analysis_result = analyzer.analyze(url)

                # Save QR scan to database
                save_scan({
                    'user_id': None,
                    'url': url,
                    'domain': urlparse(url).netloc,
                    'verdict': analysis_result.get('final_verdict'),
                    'threat_score': analysis_result.get('threat_score'),
                    'ml_prediction': analysis_result.get('ml_prediction', {}).get('prediction') if analysis_result.get('ml_prediction') else None,
                    'virustotal_malicious': analysis_result.get('virustotal_analysis', {}).get('malicious', 0) if analysis_result.get('virustotal_analysis') else 0,
                    'virustotal_suspicious': analysis_result.get('virustotal_analysis', {}).get('suspicious', 0) if analysis_result.get('virustotal_analysis') else 0,
                })
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
        print(f"QR scan error: {e}")
        return jsonify({"error": str(e)}), 500

# START SERVER
if __name__ == "__main__":
    print("\n" + "="*60)
    print(" CyberSentinel Backend - Hybrid ML Analysis System")
    print("="*60)
    print(" ML Model + VirusTotal + Content Analysis")
    print(" User Authentication Enabled")
    print(" Database Integration Active")
    print(" Running on http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(debug=True, host="0.0.0.0", port=5000)