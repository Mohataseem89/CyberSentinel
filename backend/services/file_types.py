"""File type detection that never trusts browser-supplied metadata."""
from dataclasses import dataclass
from pathlib import Path

class FileTypeError(ValueError):
    def __init__(self, code, message):
        self.code=code; self.message=message; super().__init__(message)

@dataclass(frozen=True)
class DetectedFile:
    kind: str
    mime: str
    extension: str

SUPPORTED = {
    'text/html': ('html', '.html'),
    'text/plain': ('text', '.txt'),
    'application/pdf': ('pdf', '.pdf'),
    'image/png': ('png', '.png'),
    'image/jpeg': ('jpeg', '.jpg'),
    'image/gif': ('gif', '.gif'),
}
ARCHIVE_MIMES = {'application/zip','application/x-rar','application/x-rar-compressed','application/x-7z-compressed','application/gzip','application/x-tar'}
EXECUTABLE_MIMES = {'application/x-dosexec','application/x-executable','application/x-pie-executable','application/x-sharedlib'}

def detect_file(path: str, allowed_kinds: set[str]) -> DetectedFile:
    try:
        import magic
    except ImportError as e:
        raise FileTypeError('type_detector_unavailable','Server file-type detection is unavailable.') from e
    mime = magic.from_file(path, mime=True) or 'application/octet-stream'
    # libmagic may call small HTML documents text/plain; verify static markup without executing it.
    if mime == 'text/plain':
        sample=Path(path).read_bytes()[:8192].lstrip().lower()
        if sample.startswith(b'<!doctype html') or sample.startswith(b'<html') or b'<script' in sample or b'<body' in sample:
            mime='text/html'
    if mime in ARCHIVE_MIMES:
        raise FileTypeError('archives_disabled','Archive processing is disabled because safe extraction is not enabled.')
    if mime in EXECUTABLE_MIMES:
        raise FileTypeError('executable_rejected','Executable uploads are not accepted for analysis.')
    if mime not in SUPPORTED:
        raise FileTypeError('unsupported_file_type','This file type is not supported.')
    kind, ext=SUPPORTED[mime]
    if kind not in allowed_kinds:
        raise FileTypeError('unsupported_file_type','This file type is not enabled.')
    return DetectedFile(kind, mime, ext)
