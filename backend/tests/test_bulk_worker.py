import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from models import Base, BulkScanItem, BulkScanJob, User
from workers import bulk_worker


class BulkWorkerTests(unittest.TestCase):
    def setUp(self):
        engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool);Base.metadata.create_all(engine);self.Session=sessionmaker(bind=engine)
        s=self.Session();u=User(username="worker",email="worker@test",password_hash="x");s.add(u);s.commit();self.uid=u.id;s.close()
        self.sp=patch("workers.bulk_worker.Session",self.Session);self.sp.start();self.addCleanup(self.sp.stop)

    def job(self,count=1,status="RUNNING"):
        s=self.Session();j=BulkScanJob(public_id=f"j-{datetime.utcnow().timestamp()}",user_id=self.uid,status=status,total_urls=count,expires_at=datetime.utcnow()+timedelta(hours=1),started_at=datetime.utcnow());s.add(j);s.flush()
        for i in range(count):s.add(BulkScanItem(job_id=j.id,row_number=i+2,normalized_url=f"https://h{i}.example",url_redacted=f"https://h{i}.example/…",status="QUEUED"))
        s.commit();jid=j.id;s.close();return jid

    @patch("workers.bulk_worker.HybridURLAnalyzer")
    def test_success_completes_and_removes_normalized_url(self, cls):
        cls.return_value.analyze.return_value={"final_verdict":"Safe","threat_score":3};jid=self.job();bulk_worker.process(jid)
        s=self.Session();j=s.get(BulkScanJob,jid);self.assertEqual(j.status,"COMPLETED");self.assertEqual(j.successful,1);self.assertIsNone(j.items[0].normalized_url);s.close()

    @patch("workers.bulk_worker.time.sleep",return_value=None)
    @patch("workers.bulk_worker.HybridURLAnalyzer")
    def test_transient_failure_retries(self, cls, _sleep):
        cls.return_value.analyze.side_effect=[RuntimeError("temporary"),{"final_verdict":"Safe","threat_score":4}];jid=self.job();bulk_worker.process(jid)
        s=self.Session();j=s.get(BulkScanJob,jid);self.assertEqual(j.status,"COMPLETED");self.assertEqual(j.items[0].attempts,1);self.assertEqual(j.successful,1);s.close()

    @patch("workers.bulk_worker.time.sleep",return_value=None)
    @patch("workers.bulk_worker.HybridURLAnalyzer")
    def test_permanent_failure_causes_partial_completion(self, cls, _sleep):
        cls.return_value.analyze.side_effect=[{"final_verdict":"Safe","threat_score":1},RuntimeError("bad"),RuntimeError("bad"),RuntimeError("bad")];jid=self.job(count=2);bulk_worker.process(jid)
        s=self.Session();j=s.get(BulkScanJob,jid);self.assertEqual(j.status,"PARTIALLY_COMPLETED");self.assertEqual(j.successful,1);self.assertEqual(j.failed,1);self.assertEqual(j.processed,2);s.close()

    @patch("workers.bulk_worker.HybridURLAnalyzer")
    def test_cancelling_job_clears_pending_urls(self, cls):
        jid=self.job(count=2,status="CANCELLING");bulk_worker.process(jid);cls.assert_not_called()
        s=self.Session();j=s.get(BulkScanJob,jid);self.assertEqual(j.status,"CANCELLED");self.assertTrue(all(i.normalized_url is None for i in j.items));s.close()

    def test_recover_stale_requeues_running_item(self):
        jid=self.job();s=self.Session();j=s.get(BulkScanJob,jid);j.started_at=datetime.utcnow()-timedelta(seconds=bulk_worker.STALE+1);j.items[0].status="RUNNING";s.commit();s.close();bulk_worker.recover_stale()
        s=self.Session();j=s.get(BulkScanJob,jid);self.assertEqual(j.status,"QUEUED");self.assertEqual(j.items[0].status,"QUEUED");s.close()


if __name__ == "__main__": unittest.main()
