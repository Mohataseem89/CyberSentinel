import unittest
from unittest.mock import Mock, patch
import requests
import services.bulk_trigger as trigger


class BulkTriggerTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.multiple(trigger, TRIGGER_URL="https://trigger.test/trigger", TRIGGER_SECRET="secret", MAX_ATTEMPTS=3, TIMEOUT_SECONDS=1)
        self.env.start()
        self.addCleanup(self.env.stop)

    @patch("services.bulk_trigger.time.sleep", return_value=None)
    @patch("services.bulk_trigger.requests.post")
    def test_successful_trigger(self, post, _sleep):
        post.return_value = Mock(status_code=202)
        self.assertTrue(trigger.trigger_bulk_worker())
        self.assertEqual(post.call_count, 1)

    @patch("services.bulk_trigger.time.sleep", return_value=None)
    @patch("services.bulk_trigger.requests.post")
    def test_401_is_not_retried(self, post, _sleep):
        post.return_value = Mock(status_code=401)
        with self.assertRaises(trigger.BulkTriggerError):
            trigger.trigger_bulk_worker()
        self.assertEqual(post.call_count, 1)

    @patch("services.bulk_trigger.time.sleep", return_value=None)
    @patch("services.bulk_trigger.requests.post")
    def test_500_is_retried_then_succeeds(self, post, _sleep):
        post.side_effect = [Mock(status_code=500), Mock(status_code=500), Mock(status_code=202)]
        self.assertTrue(trigger.trigger_bulk_worker())
        self.assertEqual(post.call_count, 3)

    @patch("services.bulk_trigger.time.sleep", return_value=None)
    @patch("services.bulk_trigger.requests.post")
    def test_500_exhausts_retries(self, post, _sleep):
        post.return_value = Mock(status_code=500)
        with self.assertRaisesRegex(trigger.BulkTriggerError, "HTTP 500"):
            trigger.trigger_bulk_worker()
        self.assertEqual(post.call_count, 3)

    @patch("services.bulk_trigger.time.sleep", return_value=None)
    @patch("services.bulk_trigger.requests.post")
    def test_timeout_is_retried_then_fails(self, post, _sleep):
        post.side_effect = requests.Timeout("timeout")
        with self.assertRaisesRegex(trigger.BulkTriggerError, "timed out"):
            trigger.trigger_bulk_worker()
        self.assertEqual(post.call_count, 3)

    def test_missing_configuration_fails_closed(self):
        with patch.multiple(trigger, TRIGGER_URL="", TRIGGER_SECRET=""):
            with self.assertRaisesRegex(trigger.BulkTriggerError, "not configured"):
                trigger.trigger_bulk_worker()


if __name__ == "__main__":
    unittest.main()
