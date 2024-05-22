import logging
import logging.handlers
import os
import sys
from datetime import datetime

os.makedirs("logs/gunicorn", exist_ok=True)

bind = "127.0.0.1:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
accesslog = f"./logs/gunicorn/access_{datetime.now().strftime('%Y-%m-%d')}.log"
errorlog = f"./logs/gunicorn/error_{datetime.now().strftime('%Y-%m-%d')}.log"
loglevel = "info"


def post_fork(server, worker):
    log_formatter = logging.Formatter('%(asctime)s [%(process)d] [%(levelname)s] %(message)s')

    # 기존 핸들러 제거
    for handler in server.log.error_log.handlers:
        server.log.error_log.removeHandler(handler)
    for handler in server.log.access_log.handlers:
        server.log.access_log.removeHandler(handler)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    server.log.error_log.addHandler(console_handler)
    server.log.access_log.addHandler(console_handler)

    # error log 파일 핸들러
    error_file_handler = logging.handlers.WatchedFileHandler(errorlog)
    error_file_handler.setFormatter(log_formatter)
    server.log.error_log.addHandler(error_file_handler)

    # access log 파일 핸들러
    access_file_handler = logging.handlers.WatchedFileHandler(accesslog)
    access_file_handler.setFormatter(log_formatter)
    server.log.access_log.addHandler(access_file_handler)

    # 로그 메시지 중복 방지
    server.log.error_log.propagate = False
    server.log.access_log.propagate = False
