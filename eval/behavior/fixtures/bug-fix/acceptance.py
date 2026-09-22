import runpy
import sys
from pathlib import Path

root = Path(sys.argv[1])
module = runpy.run_path(str(root / 'src/stats.py'))
mean = module['mean']
assert mean([1, 2, 3]) == 2
assert mean(iter([2, 4])) == 3
assert mean([-5, 3]) == -1
for values in ([], iter([])):
    try:
        mean(values)
    except ValueError:
        pass
    else:
        raise AssertionError('empty input must raise ValueError')
