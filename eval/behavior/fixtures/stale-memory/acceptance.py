import runpy
import sys
from pathlib import Path

root = Path(sys.argv[1])
expired = runpy.run_path(str(root / 'src/cache.py'))['expired']
assert expired(0, 10, 10) is True
assert expired(0, 9, 10) is False
assert expired(0, 0, 0) is True
assert expired(100, 0, -1) is True
text = (root / 'docs/memory-correction.md').read_text(encoding='utf-8').lower()
assert len(text) <= 2000 and 'docs/cache-contract.md' in text
assert 'cache-policy.md' in text and 'cache-policy-copy.md' in text
assert 'duplicate' in text and ('retir' in text or 'deduplic' in text)
assert '>=' in text or 'greater than or equal' in text or 'at the ttl boundary' in text
assert 'second' in text
