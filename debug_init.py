from prometheus.config import Config
import inspect

# Check if InitWorkflow has the Config class instantiation
from prometheus.init.workflow import InitWorkflow

source = inspect.getsource(InitWorkflow.__init__)
print("Looking for 'self.config = Config()':")
if 'self.config = Config()' in source:
    print('✓ Found')
else:
    print('✗ NOT found')

print("\nLooking for 'make_github_url':")
if 'make_github_url' in source:
    print('✓ Found')
else:
    print('✗ NOT found')

# Print the first 2000 chars
print("\nFirst 2000 characters of __init__:")
print(source[:2000])
