from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from database import delete_owned_scan, export_owned_scans, get_owned_scans

history_bp = Blueprint("history", __name__)

@history_bp.route("/history", methods=["GET"])
@jwt_required()
def history():
    return jsonify(get_owned_scans(int(get_jwt_identity()), min(int(request.args.get("limit", 25)), 100)))

@history_bp.route("/history/export", methods=["GET"])
@jwt_required()
def export_history():
    return jsonify({"scans": export_owned_scans(int(get_jwt_identity()))})

@history_bp.route("/history/<int:scan_id>", methods=["DELETE"])
@jwt_required()
def delete_history(scan_id):
    return ("", 204) if delete_owned_scan(int(get_jwt_identity()), scan_id) else (jsonify({"error":"Scan not found."}), 404)
