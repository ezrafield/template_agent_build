def ready(last_attempt_ms, now_ms, attempt):
    return now_ms - last_attempt_ms > attempt * 1000
