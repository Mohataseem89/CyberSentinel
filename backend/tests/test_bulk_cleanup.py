import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from models import Base, BulkScanItem, BulkScanJob, User
from workers.cleanup_bulk import cleanup


class BulkCleanupTests(unittest.TestCase):
    def setUp(self):
        engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool); Base.metadata.create_all(engine); self.Session=sessionmaker(bind=engine)
        s=self.Session(); u=User(username="cleanup",email="cleanup@test",password_hash="x"); s.add(u);s.commit();self.uid=u.id;s.close()

    def add_job(self, expires):
        s=self.Session(); j=BulkScanJob(public_id=str(expires.timestamp()),user_id=self.uid,status="COMPLETED",total_urls=1,processed=1,successful=1,expires_at=expires);s.add(j);s.flush();s.add(BulkScanItem(job_id=j.id,row_number=2,url_redacted="https://example.com/…",status="COMPLETED"));s.commit();jid=j.id;s.close();return jid

    def test_expired_job_and_results_are_hard_deleted(self):
        now=datetime.utcnow(); expired=self.add_job(now-timedelta(seconds=1)); live=self.add_job(now+timedelta(hours=1))
        with patch("workers.cleanup_bulk.Session",self.Session): self.assertEqual(cleanup(now=now),1)
        s=self.Session();self.assertIsNone(s.get(BulkScanJob,expired));self.assertIsNotNone(s.get(BulkScanJob,live));self.assertEqual(s.query(BulkScanItem).filter_by(job_id=expired).count(),0);s.close()


if __name__ == "__main__": unittest.main()
