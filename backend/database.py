from models import Session, User, Scan, Feedback
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import csv
import os

FEEDBACK_CSV_FILE = "feedback_training_data.csv"

# APPROVED_FEEDBACK_CSV = os.path.join(
#     os.path.dirname(os.path.abspath(__file__)),
#     "approved_feedback.csv"
# )

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(DATA_DIR, exist_ok=True)

APPROVED_FEEDBACK_CSV = os.path.join(DATA_DIR, "approved_feedback.csv")
FEEDBACK_TRAINING_CSV = os.path.join(DATA_DIR, "feedback_training_data.csv")

def create_user(username, email, password):
    """Create a new user"""
    session = Session()
    try:
        user = User(username=username, email=email)
        user.set_password(password)
        session.add(user)
        session.commit()
        return user.to_dict()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_user_by_username(username):
    """Get user by username"""
    session = Session()
    try:
        user = session.query(User).filter_by(username=username).first()
        return user
    finally:
        session.close()


def get_user_by_id(user_id):
    """Get user by ID"""
    session = Session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        return user
    finally:
        session.close()


def save_scan(scan_data):
    """Save a scan to database"""
    session = Session()
    try:
        scan = Scan(
            user_id=scan_data.get('user_id'),
            url=scan_data.get('url'),
            domain=scan_data.get('domain'),
            final_verdict=scan_data.get('verdict'),
            threat_score=float(scan_data.get('threat_score') or 0),
            ml_prediction=scan_data.get('ml_prediction'),
            vt_malicious=scan_data.get('virustotal_malicious', 0),
            vt_suspicious=scan_data.get('virustotal_suspicious', 0),
            vt_harmless=0,
        )
        session.add(scan)
        session.commit()
        return scan.to_dict()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_all_scans(limit=100, offset=0, user_id=None, filter_verdict=None):
    """Get all scans with pagination and filters"""
    session = Session()
    try:
        query = session.query(Scan).order_by(desc(Scan.created_at))

        if user_id:
            query = query.filter_by(user_id=user_id)

        if filter_verdict:
            query = query.filter_by(verdict=filter_verdict)

        total = query.count()
        scans = query.limit(limit).offset(offset).all()

        return {
            'scans': [scan.to_dict() for scan in scans],
            'total': total,
            'limit': limit,
            'offset': offset
        }
    finally:
        session.close()


def get_analytics_stats(user_id=None):
    """Get analytics statistics"""
    session = Session()
    try:
        query = session.query(Scan)

        if user_id:
            query = query.filter_by(user_id=user_id)

        total_scans = query.count()
        benign_scans = query.filter_by(verdict='Benign').count()
        suspicious_scans = query.filter(Scan.verdict.in_(['Suspicious', 'Potentially Risky'])).count()
        phishing_scans = query.filter_by(verdict='Phishing').count()

        avg_score = session.query(func.avg(Scan.threat_score)).filter(
            Scan.user_id == user_id if user_id else True
        ).scalar()

        today = datetime.utcnow().date()
        scans_today = query.filter(func.date(Scan.created_at) == today).count()

        blocked = query.filter(Scan.threat_score >= 70).count()

        return {
            'total_scans': total_scans,
            'benign_scans': benign_scans,
            'suspicious_scans': suspicious_scans,
            'phishing_scans': phishing_scans,
            'malicious_scans': phishing_scans,
            'avg_threat_score': round(avg_score, 2) if avg_score else 0,
            'scans_today': scans_today,
            'blocked_threats': blocked
        }
    finally:
        session.close()


def get_daily_scans(days=7, user_id=None):
    """Get daily scan statistics"""
    session = Session()
    try:
        start_date = datetime.utcnow() - timedelta(days=days)

        query = session.query(
            func.date(Scan.created_at).label('date'),
            Scan.verdict,
            func.count(Scan.id).label('count')
        ).filter(Scan.created_at >= start_date)

        if user_id:
            query = query.filter_by(user_id=user_id)

        query = query.group_by(func.date(Scan.created_at), Scan.verdict)

        results = query.all()

        daily_data = {}
        for result in results:
            date_str = result.date.strftime('%Y-%m-%d')
            if date_str not in daily_data:
                daily_data[date_str] = {
                    'date': date_str,
                    'benign': 0,
                    'suspicious': 0,
                    'phishing': 0,
                    'total': 0
                }

            if result.verdict == 'Benign':
                daily_data[date_str]['benign'] = result.count
            elif result.verdict in ['Suspicious', 'Potentially Risky']:
                daily_data[date_str]['suspicious'] += result.count
            elif result.verdict == 'Phishing':
                daily_data[date_str]['phishing'] = result.count

            daily_data[date_str]['total'] += result.count

        return list(daily_data.values())
    finally:
        session.close()


def get_top_threats(limit=10, user_id=None):
    """Get most common malicious domains"""
    session = Session()
    try:
        query = session.query(
            Scan.domain,
            func.count(Scan.id).label('count')
        ).filter(Scan.verdict == 'Phishing')

        if user_id:
            query = query.filter_by(user_id=user_id)

        query = query.group_by(Scan.domain).order_by(desc('count')).limit(limit)

        results = query.all()

        return [{'domain': r.domain, 'count': r.count} for r in results]
    finally:
        session.close()


def map_feedback_to_training_label(category, actual_threat):
    """
    Convert feedback into training label.
    Returns:
        'good', 'bad', or None
    """
    actual_threat = (actual_threat or "").strip().lower()
    category = (category or "").strip().lower()

    malicious_labels = {"phishing", "malware", "defacement"}
    benign_labels = {"benign", "safe", "benign/safe"}

    if category in {"false_negative", "new_threat"}:
        if actual_threat in malicious_labels:
            return "bad"

    if category == "false_positive":
        if actual_threat in benign_labels:
            return "good"

    return None


def append_feedback_to_csv(feedback_dict):
    """
    Append approved-format feedback to a CSV file for future model retraining.
    """
    label = map_feedback_to_training_label(
        feedback_dict.get("category"),
        feedback_dict.get("actual_threat")
    )

    if not label:
        return {
            "saved_to_csv": False,
            "reason": "Feedback not suitable for direct training dataset"
        }

    file_exists = os.path.exists(FEEDBACK_CSV_FILE)

    row = {
        "url": feedback_dict.get("url", ""),
        "label": label,
        "source": "user_feedback",
        "category": feedback_dict.get("category", ""),
        "actual_threat": feedback_dict.get("actual_threat", ""),
        "our_prediction": feedback_dict.get("our_prediction", ""),
        "description": feedback_dict.get("description", ""),
        "created_at": datetime.utcnow().isoformat()
    }

    with open(FEEDBACK_CSV_FILE, mode="a", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "url",
            "label",
            "source",
            "category",
            "actual_threat",
            "our_prediction",
            "description",
            "created_at"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)

    return {
        "saved_to_csv": True,
        "csv_file": FEEDBACK_CSV_FILE,
        "label": label
    }



def save_feedback(feedback_data):
    """Save user feedback to DB only"""
    session = Session()
    try:
        feedback = Feedback(
            user_id=feedback_data.get('user_id'),
            url=feedback_data.get('url'),
            category=feedback_data.get('category'),
            actual_threat=feedback_data.get('actual_threat'),
            our_prediction=feedback_data.get('our_prediction'),
            description=feedback_data.get('description'),
            status="pending"
        )

        session.add(feedback)
        session.commit()
        session.refresh(feedback)

        return feedback.to_dict()

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_all_feedback(status=None):
    """Get all feedback (optionally filter by status)"""
    session = Session()
    try:
        query = session.query(Feedback)

        if status:
            query = query.filter_by(status=status)

        feedback_list = query.order_by(Feedback.created_at.desc()).all()

        return [f.to_dict() for f in feedback_list]

    finally:
        session.close()


def update_feedback_status(feedback_id, new_status):
    """Update feedback status and append to CSV only when approved"""
    session = Session()
    try:
        feedback = session.query(Feedback).filter_by(id=feedback_id).first()

        if not feedback:
            return None

        feedback.status = new_status
        session.commit()
        session.refresh(feedback)

        feedback_dict = feedback.to_dict()



        if new_status == "approved":
            try:
                csv_result = append_approved_feedback_to_csv(feedback_dict)
            except Exception as csv_error:
                print(f" Approved CSV append failed during approval: {csv_error}")
                csv_result = {
                    "saved_to_csv": False,
                    "reason": str(csv_error)
                }

            feedback_dict["csv_status"] = csv_result

        return feedback_dict

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def append_approved_feedback_to_csv(feedback: dict):
    """
    Append one approved feedback row to approved_feedback.csv
    """

    print(f"[+] Writing approved feedback to: {APPROVED_FEEDBACK_CSV}")
    os.makedirs(os.path.dirname(APPROVED_FEEDBACK_CSV), exist_ok=True)
    file_exists = os.path.exists(APPROVED_FEEDBACK_CSV)

    # prevent duplicate export of same feedback id
    existing_ids = set()
    if file_exists:
        with open(APPROVED_FEEDBACK_CSV, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                existing_ids.add(str(row.get("id")))

    if str(feedback.get("id")) in existing_ids:
        return {
            "saved_to_csv": False,
            "reason": "Feedback already exported",
            "csv_file": APPROVED_FEEDBACK_CSV
        }

    with open(APPROVED_FEEDBACK_CSV, mode="a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        if not file_exists:
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

        writer.writerow([
            feedback.get("id"),
            feedback.get("url"),
            feedback.get("category"),
            feedback.get("actual_threat"),
            feedback.get("our_prediction"),
            feedback.get("description"),
            feedback.get("status"),
            feedback.get("created_at")
        ])

    return {
        "saved_to_csv": True,
        "csv_file": APPROVED_FEEDBACK_CSV
    }