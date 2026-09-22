import runpy
import sys
from pathlib import Path

root = Path(sys.argv[1])
import ast
source = (root / 'src/pricing.py').read_text(encoding='utf-8')
module = runpy.run_path(str(root / 'src/pricing.py'))
assert callable(module['discount_cents'])
for cents in (-101, -1, 0, 1, 99, 101, 12345):
    for percent in (0, 1, 15, 50, 100):
        expected = cents - cents * percent // 100
        assert module['invoice_total'](cents, percent) == expected
        assert module['discount_cents'](cents, percent) == expected
        for months in (0, 1, 3):
            assert module['subscription_total'](cents, percent, months) == expected * months
functions = {node.name: node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)}
for name in ('invoice_total', 'subscription_total'):
    assert any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'discount_cents' for node in ast.walk(functions[name]))
