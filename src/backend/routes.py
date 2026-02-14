from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
from clamav_service import scan_file

upload_routes = Blueprint('upload_routes', __name__)


# @upload_routes.route('/scan-file', methods=['POST'])
# def scan_uploaded_file():
#     print("---- DEBUG START ----")
#     print("Content-Type:", request.content_type)
#     print("Headers:", request.headers)
#     print("Files:", request.files)
#     print("Form:", request.form)
#     print("---- DEBUG END ----")

#     # Ensure request is multipart
#     if not request.content_type or "multipart/form-data" not in request.content_type:
#         return jsonify({"error": "Request must be multipart/form-data"}), 400

#     if 'file' not in request.files:
#         return jsonify({"error": "No file uploaded"}), 400

#     file = request.files['file']

#     if file.filename == '':
#         return jsonify({"error": "Empty filename"}), 400

#     # Secure filename (VERY IMPORTANT)
#     filename = secure_filename(file.filename)

#     upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")

#     if not os.path.exists(upload_folder):
#         os.makedirs(upload_folder)

#     file_path = os.path.join(upload_folder, filename)
#     file.save(file_path)

#     #  Scan with ClamAV
#     try:
#         scan_result = scan_file(file_path)

#         return jsonify({
#             "filename": filename,
#             "scan_result": scan_result
#         }), 200

#     except Exception as e:
#         print("Scan error:", str(e))
#         return jsonify({
#             "error": "ClamAV scan failed",
#             "details": str(e)
#         }), 500



@upload_routes.route('/scan-file', methods=['POST'])
def scan_uploaded_file():
    if "multipart/form-data" not in request.content_type:
        return jsonify({"error": "Request must be multipart/form-data"}), 400

    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    scan_result = scan_file(file_path)

    return jsonify({
        "filename": file.filename,
        "scan_result": scan_result
    })
