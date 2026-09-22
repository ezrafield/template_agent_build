def ready(last_attempt_ms, now_ms, attempt):
    if attempt < 0:
        raise ValueError('attempt must be nonnegative')
    delay = (0, 250, 1000)[attempt] if attempt < 3 else 4000
    return now_ms - last_attempt_ms >= delay
