from flask import Blueprint, request, jsonify
import psycopg2
import psycopg2.extras
import os
from datetime import datetime, timedelta

analytics_bp = Blueprint("analytics_bp", __name__)

# DATABASE_URL = "postgresql://postgres:PG%40dmin89@localhost:5432/cybersentinel"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///cybersentinel.db")


def get_connection():
    return psycopg2.connect(DATABASE_URL)


@analytics_bp.route("/api/analytics/stats", methods=["GET"])
def get_analytics_stats():
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT
                COUNT(*) AS total_scans,
                COUNT(*) FILTER (WHERE final_verdict = 'Benign') AS benign_scans,
                COUNT(*) FILTER (
                    WHERE final_verdict IN ('Suspicious', 'Potentially Risky')
                ) AS suspicious_scans,
                COUNT(*) FILTER (WHERE final_verdict = 'Phishing') AS phishing_scans,
                COALESCE(AVG(threat_score), 0) AS avg_threat_score,
                COUNT(*) FILTER (WHERE DATE(created_at) = CURRENT_DATE) AS scans_today,
                COUNT(*) FILTER (WHERE threat_score >= 70) AS blocked_threats
            FROM scans
        """)

        stats = cur.fetchone()

        cur.close()
        conn.close()

        return jsonify({
            "total_scans": stats["total_scans"] or 0,
            "benign_scans": stats["benign_scans"] or 0,
            "suspicious_scans": stats["suspicious_scans"] or 0,
            "phishing_scans": stats["phishing_scans"] or 0,
            "avg_threat_score": float(stats["avg_threat_score"] or 0),
            "scans_today": stats["scans_today"] or 0,
            "blocked_threats": stats["blocked_threats"] or 0
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/api/analytics/history", methods=["GET"])
def get_scan_history():
    try:
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)
        filter_type = request.args.get("filter", "all")

        offset = (page - 1) * limit

        where_clause = ""
        params = []

        if filter_type == "benign":
            where_clause = "WHERE final_verdict = 'Benign'"
        elif filter_type == "suspicious":
            where_clause = "WHERE final_verdict IN ('Suspicious', 'Potentially Risky')"
        elif filter_type == "phishing":
            where_clause = "WHERE final_verdict = 'Phishing'"

        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        count_query = f"SELECT COUNT(*) AS total FROM scans {where_clause}"
        cur.execute(count_query, params)
        total = cur.fetchone()["total"]

        history_query = f"""
            SELECT
                id,
                user_id,
                url,
                domain,
                final_verdict AS verdict,
                threat_score,
                ml_prediction,
                vt_malicious,
                vt_suspicious,
                vt_harmless,
                created_at
            FROM scans
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        cur.execute(history_query, params + [limit, offset])
        scans = cur.fetchall()

        cur.close()
        conn.close()

        return jsonify({
            "scans": scans,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/api/analytics/daily", methods=["GET"])
def get_daily_scans():
    try:
        days = request.args.get("days", 7, type=int)
        start_date = datetime.now().date() - timedelta(days=days - 1)

        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT
                DATE(created_at) AS scan_date,
                final_verdict,
                COUNT(*) AS count
            FROM scans
            WHERE DATE(created_at) >= %s
            GROUP BY DATE(created_at), final_verdict
            ORDER BY scan_date ASC
        """, [start_date])

        rows = cur.fetchall()
        cur.close()
        conn.close()

        daily_map = {}
        for i in range(days):
            d = start_date + timedelta(days=i)
            key = d.strftime("%Y-%m-%d")
            daily_map[key] = {
                "date": key,
                "benign": 0,
                "suspicious": 0,
                "phishing": 0,
                "total": 0
            }

        for row in rows:
            day = row["scan_date"].strftime("%Y-%m-%d")
            verdict = row["final_verdict"]
            count = row["count"]

            if day not in daily_map:
                continue

            if verdict == "Benign":
                daily_map[day]["benign"] += count
            elif verdict in ("Suspicious", "Potentially Risky"):
                daily_map[day]["suspicious"] += count
            elif verdict == "Phishing":
                daily_map[day]["phishing"] += count

            daily_map[day]["total"] += count

        return jsonify({
            "daily_scans": list(daily_map.values())
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/api/analytics/top-threats", methods=["GET"])
def get_top_threats():
    try:
        limit = request.args.get("limit", 10, type=int)

        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT
                domain,
                COUNT(*) AS count
            FROM scans
            WHERE final_verdict = 'Phishing'
              AND domain IS NOT NULL
              AND domain <> ''
            GROUP BY domain
            ORDER BY count DESC
            LIMIT %s
        """, [limit])

        threats = cur.fetchall()

        cur.close()
        conn.close()

        return jsonify({"threats": threats}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500