import unittest
from services.bulk_scan import BulkValidationError, parse_csv_bytes, csv_safe, can_transition
class BulkScanTests(unittest.TestCase):
 def test_valid_csv_deduplicates(self):
  rows,errors=parse_csv_bytes(b'url\nhttps://example.com\nhttps://example.com\n',10);self.assertEqual(len(rows),1);self.assertEqual(errors,[])
 def test_missing_url_column(self):
  with self.assertRaises(BulkValidationError):parse_csv_bytes(b'link\nhttps://example.com\n',10)
 def test_invalid_url_is_row_error(self):
  rows,errors=parse_csv_bytes(b'url\njavascript:alert(1)\nhttps://example.com\n',10);self.assertEqual(len(rows),1);self.assertEqual(len(errors),1)
 def test_row_quota(self):
  with self.assertRaises(BulkValidationError):parse_csv_bytes(b'url\nhttps://a.example\nhttps://b.example\n',1)
 def test_csv_formula_export_is_neutralized(self):self.assertEqual(csv_safe('=1+1'),"'=1+1")
 def test_state_machine_rejects_invalid_transition(self):self.assertFalse(can_transition('COMPLETED','RUNNING'));self.assertTrue(can_transition('RUNNING','CANCELLING'))
if __name__=='__main__':unittest.main()
