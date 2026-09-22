import runpy
import sys
from pathlib import Path

root = Path(sys.argv[1])
chunks = runpy.run_path(str(root / 'src/chunks.py'))['chunks']
assert list(chunks(iter(range(5)), 3)) == [[0, 1, 2], [3, 4]]
assert list(chunks([1, 2, 3])) == [[1, 2], [3]]
assert list(chunks([], 1)) == []
for size in (True, False, 0, -1, 1.2, '2'):
    try:
        list(chunks([1], size))
    except ValueError:
        pass
    else:
        raise AssertionError('invalid size accepted')
