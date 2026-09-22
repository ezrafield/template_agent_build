import runpy
import sys
from pathlib import Path

root = Path(sys.argv[1])
import re
text = (root / 'docs/usage.md').read_text(encoding='utf-8').lower()
assert 'offline' in text and '--limit' in text and '--count' not in text
assert re.search(r'default[^.\n]*25|25[^.\n]*default', text)
assert re.search(r'1\s*(?:to|[-–])\s*100', text) and 'inclusive' in text
assert re.search(r'default[^.\n]*json|json[^.\n]*default', text)
assert not re.search(r'default[^.\n]*10|0\s*-\s*50|default[^.\n]*text', text)
