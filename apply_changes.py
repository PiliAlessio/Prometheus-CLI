import pathlib

# Read the current file
file_path = pathlib.Path('tools/cli/src/prometheus/init/workflow.py')
content = file_path.read_text()

# Replace the __init__ method body
old_init_body = """        self.app_name = app_name
        self.app_remote = app_remote
        self.app_instructions_remote = app_instructions_remote
        self.core_remote = core_remote or DEFAULT_CORE_REPO_URL"""

new_init_body = """        self.config = Config()
        self.app_name = app_name
        # Convert repo names to full URLs if needed
        self.app_remote = (
            self.config.make_github_url(app_remote) if app_remote else None
        )
        self.app_instructions_remote = (
            self.config.make_github_url(app_instructions_remote)
            if app_instructions_remote
            else None
        )
        self.core_remote = core_remote or DEFAULT_CORE_REPO_URL"""

if old_init_body in content:
    print("✓ Found old init body")
    new_content = content.replace(old_init_body, new_init_body)
    
    # Verify the change was made
    if new_init_body in new_content:
        print("✓ Replacement successful")
        file_path.write_text(new_content)
        print("✓ File written")
    else:
        print("✗ Replacement failed")
else:
    print("✗ Old init body not found")
    print("\nSearching for 'self.app_name = app_name' pattern...")
    if 'self.app_name = app_name' in content:
        print("✓ Found pattern")
    else:
        print("✗ Pattern not found")
