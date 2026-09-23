import runpy
import shlex
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

# Parse examples as arguments against the evaluator's protected source copy.
# Never execute a documented command or trust a candidate-supplied parser.
protected = Path(sys.argv[2])
make_parser = runpy.run_path(str(protected / 'src/cli.py'))['parser']
markdown = (root / 'docs/usage.md').read_text(encoding='utf-8')
fenced = re.findall(r'```[^\n]*\n(.*?)```', markdown, re.DOTALL)
outside_fences = re.sub(r'```.*?```', '', markdown, flags=re.DOTALL)
snippets = fenced + re.findall(r'`([^`\n]+)`', outside_fences)
examples = []
for snippet in snippets:
    for line in snippet.splitlines():
        line = line.strip().removeprefix('$ ')
        if not re.match(r'(?:python(?:3)?|py)(?:\.exe)?\s', line):
            continue
        arguments = shlex.split(line)
        script_index = 2 if arguments[0] in ('py', 'py.exe') and arguments[1] == '-3' else 1
        if len(arguments) <= script_index or arguments[script_index] not in ('src/cli.py', './src/cli.py'):
            continue
        example = arguments[script_index + 1:]
        try:
            make_parser().parse_args(example)
        except SystemExit as exc:
            raise AssertionError('Documented CLI example must parse successfully.') from exc
        examples.append(example)
assert any(any(argument == '--limit' or argument.startswith('--limit=') for argument in example) for example in examples), 'Document a runnable example using --limit.'
