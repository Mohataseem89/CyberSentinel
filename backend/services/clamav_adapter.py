"""Minimal clamd INSTREAM client. No shell commands or user-controlled scanner arguments."""
import socket, struct

class ClamAVError(RuntimeError):
    def __init__(self, code, message): self.code=code; self.message=message; super().__init__(message)

class ClamAVAdapter:
    def __init__(self, host='127.0.0.1', port=3310, timeout=30, max_bytes=10*1024*1024):
        self.host=host; self.port=int(port); self.timeout=float(timeout); self.max_bytes=int(max_bytes)
    def ping(self):
        try:
            with socket.create_connection((self.host,self.port), timeout=self.timeout) as s:
                s.sendall(b'zPING\0'); data=s.recv(64)
            return b'PONG' in data
        except OSError: return False
    def scan_file(self, path):
        sent=0
        try:
            with socket.create_connection((self.host,self.port), timeout=self.timeout) as s:
                s.settimeout(self.timeout); s.sendall(b'zINSTREAM\0')
                with open(path,'rb') as f:
                    while True:
                        chunk=f.read(65536)
                        if not chunk: break
                        sent+=len(chunk)
                        if sent>self.max_bytes: raise ClamAVError('file_too_large','File exceeds scanner stream limit.')
                        s.sendall(struct.pack('!I',len(chunk))); s.sendall(chunk)
                s.sendall(struct.pack('!I',0))
                response=b''
                while b'\0' not in response and len(response)<8192:
                    part=s.recv(4096)
                    if not part: break
                    response+=part
        except socket.timeout as e: raise ClamAVError('scanner_timeout','Malware scanner timed out.') from e
        except OSError as e: raise ClamAVError('scanner_unavailable','Malware scanner is unavailable.') from e
        line=response.decode('utf-8','replace').strip('\0\r\n')
        if line.endswith(' OK'): return {'status':'clean','signature':None}
        if line.endswith(' FOUND'):
            sig=line.rsplit(': ',1)[-1][:-6].strip() if ': ' in line else 'detected'
            return {'status':'malware_detected','signature':sig[:200]}
        if 'ERROR' in line: raise ClamAVError('scanner_error','Malware scanner could not complete the scan.')
        raise ClamAVError('scanner_error','Malware scanner returned an unrecognized response.')
