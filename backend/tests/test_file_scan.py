import os, tempfile, unittest
from unittest.mock import patch
from services.file_scan import safe_original_name, stream_upload
from services.html_static_analyzer import analyze_html_bytes
from services.clamav_adapter import ClamAVAdapter, ClamAVError
from services.file_analysis import analyze_file

class Upload:
    def __init__(self,data):
        import io; self.stream=io.BytesIO(data)

class FileScanTests(unittest.TestCase):
    def test_filename_path_traversal_is_removed(self): self.assertNotIn('..',safe_original_name('../../evil.html'))
    def test_empty_upload_rejected_and_cleaned(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,'empty_file'): stream_upload(Upload(b''),d,100)
            self.assertEqual(os.listdir(d),[])
    def test_oversized_upload_rejected_and_cleaned(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,'file_too_large'): stream_upload(Upload(b'12345'),d,4)
            self.assertEqual(os.listdir(d),[])
    def test_html_scripts_are_static_indicators(self):
        r=analyze_html_bytes(b'<html><script>alert(1)</script><iframe src="https://example.com"></iframe></html>')
        codes={x['code'] for x in r['indicators']}; self.assertIn('scripts_present',codes); self.assertIn('embedded_content',codes)
    def test_html_dangerous_scheme_and_redirect(self):
        r=analyze_html_bytes(b'<meta http-equiv="refresh" content="0"><a href="javascript:alert(1)">x</a>')
        codes={x['code'] for x in r['indicators']}; self.assertIn('meta_redirect',codes); self.assertIn('dangerous_uri_scheme',codes)
    @patch('socket.create_connection', side_effect=OSError('down'))
    def test_clamav_unavailable_is_not_clean(self,_):
        with self.assertRaises(ClamAVError) as cm: ClamAVAdapter().scan_file(__file__)
        self.assertEqual(cm.exception.code,'scanner_unavailable')

    @patch('services.file_analysis.ClamAVAdapter.ping', return_value=True)
    @patch('services.file_analysis.ClamAVAdapter.scan_file', return_value={'status':'clean','signature':None})
    def test_clean_text_completes_without_claiming_guaranteed_safety(self,_,__):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'hello world'); name=f.name
        try:
            result=analyze_file(name,'text','0'*64)
            self.assertEqual(result['status'],'COMPLETED')
            self.assertEqual(result['verdict'],'CLEAN_CHECKS_COMPLETED')
        finally: os.remove(name)

    @patch('services.file_analysis.check_file_hash_reputation', return_value={'available':True,'evidence_available':False})
    @patch('services.file_analysis.ClamAVAdapter.ping', return_value=False)
    def test_scanner_unavailable_never_becomes_clean(self,_,__):
        result=analyze_file(__file__,'text','0'*64)
        self.assertEqual(result['verdict'],'UNABLE_TO_COMPLETE')
        self.assertEqual(result['error_code'],'malware_evidence_unavailable')

class ClamAVIntegrationTests(unittest.TestCase):
    @unittest.skipUnless(os.getenv('CLAMAV_INTEGRATION_TEST')=='1','set CLAMAV_INTEGRATION_TEST=1 with local clamd')
    def test_eicar_standard_test_fixture_is_detected(self):
        # Standard harmless EICAR antivirus test string, never executable malware.
        eicar=(b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-' + b'STANDARD-ANTIVIRUS-TEST-FILE!$H+H*')
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(eicar); name=f.name
        try:
            result=ClamAVAdapter(os.getenv('CLAMAV_HOST','127.0.0.1'),int(os.getenv('CLAMAV_PORT','3310'))).scan_file(name)
            self.assertEqual(result['status'],'malware_detected')
        finally: os.remove(name)

if __name__=='__main__': unittest.main()
