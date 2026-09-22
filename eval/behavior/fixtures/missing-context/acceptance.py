import runpy
import sys
from pathlib import Path

root = Path(sys.argv[1])
ready = runpy.run_path(str(root / 'src/scheduler.py'))['ready']
for attempt, delay in ((0, 0), (1, 250), (2, 1000), (3, 4000), (10, 4000)):
    assert ready(100, 100 + delay, attempt) is True
    assert ready(100, 99 + delay, attempt) is False
try:
    ready(0, 10000, -1)
except ValueError:
    pass
else:
    raise AssertionError('negative attempts accepted')
text = (root / 'docs/investigation.md').read_text(encoding='utf-8').lower()
assert 'docs/specs/retry-v2.md' in text and 'millisecond' in text
assert 'inclusive' in text or '>=' in text or 'at or after' in text
