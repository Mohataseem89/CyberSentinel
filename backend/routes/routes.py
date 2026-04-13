from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
from clamav_service import scan_file

upload_routes = Blueprint('upload_routes', __name__)


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
