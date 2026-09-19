import os, sys
from services.clamav_adapter import ClamAVAdapter

def main():
    ok=ClamAVAdapter(os.getenv("CLAMAV_HOST","127.0.0.1"),int(os.getenv("CLAMAV_PORT","3310")),float(os.getenv("CLAMAV_TIMEOUT_SECONDS","5"))).ping()
    print("ready" if ok else "not ready")
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
