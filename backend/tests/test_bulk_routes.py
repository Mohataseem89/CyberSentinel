import io
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from models import Base, BulkScanItem, BulkScanJob, User
from routes.bulk import bulk_bp


class BulkRouteTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(engine)
        self.Session = sessionmaker(bind=engine)
        s = self.Session()
        self.user1 = User(username="u1", email="u1@test", password_hash="x")
        self.user2 = User(username="u2", email="u2@test", password_hash="x")
        s.add_all([self.user1, self.user2]); s.commit()
        self.u1, self.u2 = self.user1.id, self.user2.id
        s.close()
        app = Flask(__name__); app.config.update(JWT_SECRET_KEY="test-secret", TESTING=True)
        JWTManager(app); app.register_blueprint(bulk_bp, url_prefix="/api")
        self.app, self.client = app, app.test_client()
        with app.app_context():
            self.h1 = {"Authorization": f"Bearer {create_access_token(identity=str(self.u1))}"}
            self.h2 = {"Authorization": f"Bearer {create_access_token(identity=str(self.u2))}"}
        self.session_patch = patch("routes.bulk.Session", self.Session); self.session_patch.start(); self.addCleanup(self.session_patch.stop)

    def make_job(self, owner=None, count=250, status="COMPLETED"):
        s = self.Session(); job = BulkScanJob(public_id=f"job-{datetime.utcnow().timestamp()}", user_id=owner or self.u1, status=status, total_urls=count, processed=count if status=="COMPLETED" else 0, successful=count if status=="COMPLETED" else 0, expires_at=datetime.utcnow()+timedelta(hours=1))
        s.add(job); s.flush()
        for i in range(count):
            verdict = ["Safe", "Suspicious", "Dangerous", "Unknown"][i % 4]
            s.add(BulkScanItem(job_id=job.id,row_number=i+2,url_redacted=f"https://h{i}.example/…",status="COMPLETED" if status=="COMPLETED" else "QUEUED",final_verdict=verdict,threat_score=float(i%100)))
        s.commit(); public_id=job.public_id; s.close(); return public_id

    def test_owner_can_paginate_results(self):
        job = self.make_job()
        r = self.client.get(f"/api/bulk/jobs/{job}?page=2&per_page=100", headers=self.h1)
        data=r.get_json(); self.assertEqual(r.status_code,200); self.assertEqual(len(data["results"]),100); self.assertEqual(data["results"][0]["row"],102); self.assertEqual(data["pagination"]["total_pages"],3)

    def test_verdict_filter_is_server_side(self):
        job=self.make_job(count=40); r=self.client.get(f"/api/bulk/jobs/{job}?verdict=Dangerous&per_page=100",headers=self.h1); data=r.get_json()
        self.assertEqual(data["pagination"]["total_items"],10); self.assertTrue(all(x["verdict"]=="Dangerous" for x in data["results"]))

    def test_invalid_page_size_is_rejected(self):
        job=self.make_job(count=1); self.assertEqual(self.client.get(f"/api/bulk/jobs/{job}?per_page=201",headers=self.h1).status_code,400)

    def test_other_user_cannot_read_cancel_or_export(self):
        job=self.make_job(status="QUEUED",count=2)
        self.assertEqual(self.client.get(f"/api/bulk/jobs/{job}",headers=self.h2).status_code,404)
        self.assertEqual(self.client.post(f"/api/bulk/jobs/{job}/cancel",headers=self.h2).status_code,404)
        self.assertEqual(self.client.get(f"/api/bulk/jobs/{job}/results.csv",headers=self.h2).status_code,404)

    def test_running_cancel_moves_to_cancelling(self):
        job=self.make_job(status="RUNNING",count=2)
        r=self.client.post(f"/api/bulk/jobs/{job}/cancel",headers=self.h1)
        self.assertEqual(r.status_code,200);self.assertEqual(r.get_json()["job"]["status"],"CANCELLING")

    def test_queued_cancel_clears_normalized_urls(self):
        job=self.make_job(status="QUEUED",count=2); s=self.Session(); db=s.query(BulkScanJob).filter_by(public_id=job).first()
        for item in db.items: item.normalized_url="https://secret.example/path?token=x"
        s.commit(); s.close()
        r=self.client.post(f"/api/bulk/jobs/{job}/cancel",headers=self.h1); self.assertEqual(r.status_code,200); self.assertEqual(r.get_json()["job"]["status"],"CANCELLED")
        s=self.Session(); db=s.query(BulkScanJob).filter_by(public_id=job).first(); self.assertTrue(all(i.normalized_url is None for i in db.items)); s.close()

    @patch("routes.bulk.trigger_bulk_worker", return_value=True)
    def test_create_job_triggers_worker_after_commit(self, trigger):
        r=self.client.post("/api/bulk/jobs",headers=self.h1,data={"file":(io.BytesIO(b"url\nhttps://example.com\n"),"urls.csv")},content_type="multipart/form-data")
        self.assertEqual(r.status_code,202); trigger.assert_called_once()


if __name__ == "__main__": unittest.main()
