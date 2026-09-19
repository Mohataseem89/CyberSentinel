"""Validation/state helpers for authenticated asynchronous bulk URL scans."""
import csv, io, re
from dataclasses import dataclass
from services.url_normalizer import normalize_url, URLValidationError

ALLOWED_STATES={'QUEUED','RUNNING','COMPLETED','PARTIALLY_COMPLETED','FAILED','CANCELLING','CANCELLED','EXPIRED'}
TRANSITIONS={'QUEUED':{'RUNNING','CANCELLING','CANCELLED','EXPIRED'},'RUNNING':{'COMPLETED','PARTIALLY_COMPLETED','FAILED','CANCELLING','EXPIRED'},'CANCELLING':{'CANCELLED','PARTIALLY_COMPLETED'},'COMPLETED':{'EXPIRED'},'PARTIALLY_COMPLETED':{'EXPIRED'},'FAILED':{'EXPIRED'},'CANCELLED':{'EXPIRED'},'EXPIRED':set()}
SENSITIVE=re.compile(r'^(token|access_token|auth|authorization|code|password|passwd|secret|api_?key|session|sid|jwt|email)$',re.I)

class BulkValidationError(ValueError):
    def __init__(self,message,code='invalid_csv'): super().__init__(message); self.message=message; self.code=code

def can_transition(current,target): return target in TRANSITIONS.get(current,set())
def csv_safe(value):
    text='' if value is None else str(value)
    return "'"+text if text[:1] in ('=','+','-','@','\t','\r') else text

def redact_for_display(url):
    from urllib.parse import urlsplit
    try: p=urlsplit(url); return f'{p.scheme}://{p.hostname or "unknown"}/…'
    except Exception: return '[invalid URL]'

def parse_csv_bytes(raw,max_rows):
    if raw.startswith(b'\xef\xbb\xbf'): raw=raw[3:]
    try: text=raw.decode('utf-8')
    except UnicodeDecodeError as e: raise BulkValidationError('CSV must be UTF-8 encoded.','invalid_encoding') from e
    try: reader=csv.DictReader(io.StringIO(text,newline=''))
    except csv.Error as e: raise BulkValidationError('Malformed CSV.','malformed_csv') from e
    if not reader.fieldnames or 'url' not in [h.strip().lower() for h in reader.fieldnames if h]: raise BulkValidationError('CSV must contain a url column.','missing_url_column')
    key=next(h for h in reader.fieldnames if h and h.strip().lower()=='url'); rows=[]; seen=set(); errors=[]
    try:
      for line,row in enumerate(reader,start=2):
        value=(row.get(key) or '').strip()
        if not value: continue
        if len(rows)>=max_rows: raise BulkValidationError(f'CSV exceeds the {max_rows} URL limit.','too_many_rows')
        try: normalized=normalize_url(value).url
        except URLValidationError as e: errors.append({'row':line,'error':e.message}); continue
        if normalized in seen: continue
        seen.add(normalized); rows.append({'row':line,'url':normalized,'display_url':redact_for_display(normalized)})
    except csv.Error as e: raise BulkValidationError('Malformed CSV record.','malformed_csv') from e
    if not rows: raise BulkValidationError('CSV contains no valid URLs.','no_valid_urls')
    return rows,errors
