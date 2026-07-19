import pathlib

file_path = pathlib.Path('tools/cli/src/prometheus/init/workflow.py')
content = file_path.read_text()

print(f'File size: {len(content)} bytes')
print(f'Has self.config: {"self.config" in content}')
print(f'Has make_github_url: {"make_github_url" in content}')

# Show lines 57-75
lines = content.split('\n')
for i in range(56, min(75, len(lines))):
    print(f'{i+1:3d}: {lines[i]}')
