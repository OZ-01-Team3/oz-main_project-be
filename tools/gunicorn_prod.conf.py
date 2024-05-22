import logging
import sys

bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
loglevel = "info"
# accesslog = "-"
# errorlog = "-"


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

    # 로그 메시지 중복 방지
    server.log.error_log.propagate = False
    server.log.access_log.propagate = False
