# Retry evidence

Followed docs/retries.md to docs/specs/retry-v2.md. Delays use milliseconds, not seconds: 0, 250, 1000, then capped at 4000. The inclusive boundary means ready at elapsed >= delay. Negative attempts raise ValueError.
