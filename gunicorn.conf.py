# Gunicorn — used in production (Oracle Cloud, etc.).
# Scraping can run a long time; keep this timeout above your worst-case /results POST.
import os

bind = os.environ.get("GUNICORN_BIND", "127.0.0.1:8000")
workers = int(os.environ.get("GUNICORN_WORKERS", "2"))
threads = int(os.environ.get("GUNICORN_THREADS", "4"))
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "300"))
graceful_timeout = 60
worker_class = "gthread"
accesslog = "-"
errorlog = "-"
capture_output = True
