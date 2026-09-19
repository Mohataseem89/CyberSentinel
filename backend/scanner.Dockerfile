FROM python:3.10-slim
RUN groupadd -r scanner && useradd -r -g scanner -d /nonexistent -s /usr/sbin/nologin scanner
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /quarantine && chown scanner:scanner /quarantine
USER scanner
ENV FILE_SCAN_QUARANTINE_DIR=/quarantine
CMD ["python","-m","workers.file_scan_worker"]
