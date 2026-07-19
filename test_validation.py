from prometheus.init.workflow import InitWorkflow
from unittest.mock import patch

# Test the exact condition
remote = '__CREATE_WITH_GH__KTTicketing-instructions'
print(f'Remote value: {repr(remote)}')
print(f'Starts with __CREATE_WITH_GH__: {remote.startswith("__CREATE_WITH_GH__")}')
print(f'NOT starts with check: {not remote.startswith("__CREATE_WITH_GH__")}')
print()

# Now test with actual workflow
with patch('prometheus.init.workflow.InitWorkflow._is_remote_accessible', return_value=True):
    workflow = InitWorkflow(
        app_name='KTTicketing',
        app_remote='https://github.com/PiliAlessio/Prometheus.git',
        app_instructions_remote=remote,
        core_remote='https://github.com/PiliAlessio/Prometheus.git'
    )

    try:
        workflow._validate_remotes()
        print('PASS: Validation correctly skipped __CREATE_WITH_GH__ token')
    except RuntimeError as e:
        print(f'FAIL: {e}')
