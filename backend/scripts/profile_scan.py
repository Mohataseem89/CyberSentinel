"""Offline latency smoke check; never submits a URL to a live provider."""
from time import perf_counter
from services.ml_predictor import predictor
url = 'https://example.test/path'
start = perf_counter(); result = predictor.predict(url); elapsed = (perf_counter() - start) * 1000
print({"ml_available": result["available"], "latency_ms": round(elapsed, 2), "budget_ms": 500})
if elapsed > 500: raise SystemExit('ML latency budget exceeded')
