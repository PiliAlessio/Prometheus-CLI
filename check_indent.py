import pathlib

file_path = pathlib.Path('tools/cli/src/prometheus/init/workflow.py')
content = file_path.read_text()

# Show hex for lines 58-61
lines = content.split('\n')
for i in range(57, min(61, len(lines))):
    line = lines[i]
    print(f'Line {i+1}:')
    print(f'  Text: {repr(line)}')
    print(f'  Indent: {repr(line[:20])}')
    print()
