from prometheus.config import Config
from prometheus.init.workflow import InitWorkflow

print("Testing Config.make_github_url:")
config = Config()
result = config.make_github_url("KTTicketing")
print("  make_github_url('KTTicketing') =", result)

print("\nTesting InitWorkflow with repo names:")
workflow = InitWorkflow(
    app_name="KTTicketing",
    app_remote="KTTicketing",
    app_instructions_remote="KTTicketing-instructions",
)
print("  workflow.app_remote =", workflow.app_remote)
print("  workflow.app_instructions_remote =", workflow.app_instructions_remote)
