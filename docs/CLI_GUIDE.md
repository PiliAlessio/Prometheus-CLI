# Prometheus CLI Guide

## Overview

This guide documents the Phase 2 CLI workflow for the simplified **two-repo model**:

- the **Prometheus repository** owns shared assets in `core/`
- each **app repository** contains app-specific files plus a `prometheus-core` submodule

The CLI is intended to make that structure easy to create, update, and publish.

## Architecture Assumptions

After initialization, an app repository should look like this:

```text
my-app/
├── instructions/
├── config/
├── .github/
├── .prometheus.yml
└── prometheus-core/
```

`prometheus-core/` is the checked-out submodule that points to `Prometheus/core`.

## Command Summary

| Command | Purpose |
|---|---|
| `prometheus init --app-name <name>` | Create a new app repo structure with the shared core submodule |
| `prometheus --push` | Push coordinated changes for the app repo and shared core |
| `prometheus update` | Pull latest app changes and sync the `prometheus-core` submodule |

## Initialization

### Create a New App Repository

```bash
prometheus init --app-name billing-api
```

Expected structure:

```text
billing-api/
├── instructions/
├── config/
├── .github/
├── .prometheus.yml
└── prometheus-core/
```

### What `init` Should Set Up

The initialization flow should create:

- `instructions/` for app-specific operating instructions
- `config/` for app-owned configuration
- `.github/` for app-specific automation
- `.prometheus.yml` for app metadata
- `prometheus-core/` as a git submodule pointing to `Prometheus/core`

### Typical `init` Workflow

1. create the target application directory
2. create the app-owned folders and configuration file
3. add `prometheus-core` as a submodule
4. prepare the repo for the first commit

### Practical Example

```bash
prometheus init --app-name customer-portal
cd customer-portal
git status
```

At that point you should see a clean app scaffold plus the tracked submodule.

### Using the `--app-name` Parameter

The `--app-name` parameter (formerly `--project-name` in older versions) specifies the name of your application repository. This name:

- becomes the directory name for the new app repo
- is recorded in `.prometheus.yml` for metadata
- helps identify your app in shared documentation and logs
- should be lowercase, hyphen-separated (e.g., `customer-portal`, `billing-api`)

Example with custom app name:

```bash
prometheus init --app-name my-microservice
```

Result:

```text
my-microservice/
├── .prometheus.yml
│   # contains: app_name: my-microservice
├── instructions/
├── config/
├── .github/
└── prometheus-core/
```

## Push Workflow

### Publish App and Core Changes

```bash
prometheus --push
```

Use this command when:

- only the app repo changed
- only `prometheus-core` changed
- both the app repo and shared core changed together

### Expected Behavior

The push flow should:

1. detect whether `prometheus-core` contains shared changes
2. publish shared changes to the Prometheus repository when needed
3. update the app repo's submodule pointer
4. push app repo changes

### Example: App-Only Change

```bash
# edit config/production.yml
prometheus --push
```

Result: the app repo is pushed; the core side should be a no-op.

### Example: Shared-Core Change

```bash
# edit prometheus-core/documentation/...
prometheus --push
```

Result:
- the Prometheus repository receives the shared change
- the app repo records the new `prometheus-core` revision

### Example: Coordinated Change

```bash
# edit prometheus-core/documentation/...
# edit instructions/rollout.md
prometheus --push
```

Result: both repositories are updated in the correct order.

### Push Command Examples

#### Push with Modified App Files

```bash
# Scenario: you've updated app-specific configuration and instructions
$ ls config/
app.yml
$ ls instructions/
setup.md

# Push only app changes (core is clean)
$ prometheus --push
✓ Pushing app repo changes...
✓ core submodule has no changes (skipped)
✓ App pushed to origin/main
```

#### Push with Modified Core Submodule

```bash
# Scenario: you've updated shared documentation in prometheus-core
$ ls prometheus-core/documentation/
shared-guide.md

# Push both core and app submodule reference
$ prometheus --push
✓ Pushing prometheus-core changes to shared repository...
✓ Updating app repo with new submodule pointer...
✓ Core pushed to Prometheus/core main
✓ App pushed with updated submodule reference
```

#### Push with Coordinated Changes

```bash
# Scenario: both app and core have changes
$ prometheus --push
✓ Pushing prometheus-core changes first...
✓ Core pushed to Prometheus/core main
✓ Updating app repo submodule pointer...
✓ Pushing app repo changes...
✓ App pushed to origin/main
✓ All changes synchronized
```

#### Push with No Changes

```bash
# Scenario: nothing has been modified
$ prometheus --push
→ No changes detected
→ App repo is already in sync with origin/main
→ prometheus-core is already in sync
✓ Nothing to push
```

### Push Error Handling

#### Uncommitted Changes

```bash
$ git status
On branch main
Changes not staged for commit:
  modified: config/app.yml

$ prometheus --push
✗ Error: Cannot push with uncommitted changes
  Modified files:
    - config/app.yml
  
Action: Commit or stash changes, then retry
```

#### Connection Issues

```bash
$ prometheus --push
✗ Error: Push failed
  Reason: connection refused (unable to reach git server)

Action: Check network connectivity and retry
```

## Update Workflow

### Sync Local State

```bash
prometheus update
```

Run this:

- before starting work
- after teammates merge changes
- after switching branches

### Expected Behavior

The update flow should:

1. pull the latest app repository state
2. sync submodule metadata
3. update `prometheus-core` to the commit referenced by the app repo
4. leave the working tree aligned with the current app revision

### Example

```bash
prometheus update
git submodule status
```

Use the status output to confirm the app now points at the expected shared-core commit.

### Update Command Examples

#### Update with App Repository Changes

```bash
# Scenario: teammates merged changes to the app repo
$ prometheus update
✓ Pulling app repo changes...
  Updated from abc1234 to def5678
  config/app.yml | 2 +-
✓ Syncing prometheus-core submodule...
✓ Update complete
  App: abc1234 → def5678
  Core: updated to match new submodule pointer
```

#### Update with Core Submodule Updates

```bash
# Scenario: the app repo points to a new core version
$ prometheus update
✓ App repo is up to date
✓ Syncing prometheus-core to latest referenced version...
  Updated from core-old to core-new
✓ Core submodule is now synchronized
```

#### Update with No Changes

```bash
# Scenario: you're already fully up to date
$ prometheus update
→ App repo is already at latest
→ prometheus-core is already synchronized
✓ Nothing to update
```

### Update Error Handling

#### Merge Conflicts

```bash
$ prometheus update
✗ Error: Merge conflict during pull
  File: config/app.yml
  
Action: Resolve conflicts manually and retry
  git status
  # resolve conflicts in config/app.yml
  git add config/app.yml
  git commit -m "Resolve merge conflict"
  prometheus update
```

#### Detached HEAD State

```bash
$ prometheus update
✗ Error: Cannot update - submodule in detached HEAD state
  Submodule: prometheus-core

Action: Reset submodule to tracked branch:
  cd prometheus-core
  git checkout main
  cd ..
  prometheus update
```

## Suggested Day-to-Day Usage

### 1. Start from the latest state

```bash
prometheus update
```

### 2. Make changes

- edit app-specific files in the app repo
- edit shared content in `prometheus-core/` only when it should be reused

### 3. Publish changes

```bash
prometheus --push
```

## What Goes Where

| Location | Use |
|---|---|
| `prometheus-core/` | Shared standards, prompts, and reusable core docs |
| `instructions/` | App-specific instructions |
| `config/` | App-specific configuration |
| `.github/` | App-specific workflows |
| `.prometheus.yml` | App metadata and Prometheus settings |

## Troubleshooting

### `prometheus-core` is empty or missing

The submodule likely is not initialized. Re-sync the repo:

```bash
prometheus update
```

### Shared change was made, but teammates do not see it

The Prometheus-side change may not have been pushed yet. Run:

```bash
prometheus --push
```

### App repo references the wrong core revision

Update and verify the pointer:

```bash
prometheus update
git submodule status
```

### Push fails with "connection refused"

**Issue**: Unable to connect to git server (network or authentication problem)

**Solutions**:
1. Check your network connectivity: `ping github.com`
2. Verify SSH key is loaded: `ssh-add -l`
3. Test git access: `git ls-remote origin`
4. Try again when connection is restored

### Pull fails with uncommitted changes

**Issue**: `prometheus update` fails because working directory has pending changes

**Solutions**:
1. Commit your changes: `git add . && git commit -m "Your message"`
2. Stash changes: `git stash`
3. Then retry: `prometheus update`

### Submodule stuck in old state

**Issue**: `prometheus-core` doesn't reflect the latest app repo pointer

**Solutions**:
1. Manually update submodule: `git submodule update --remote`
2. Or use the update command: `prometheus update`
3. Verify status: `git submodule status`

### Merged changes not appearing after push

**Issue**: Changes were pushed but teammates don't see them

**Solutions**:
1. Verify both repositories were pushed:
   ```bash
   git log origin/main -1  # check app repo
   cd prometheus-core && git log origin/main -1  # check core
   ```
2. Teammates should run: `prometheus update`
3. If using CI/CD, check that workflows completed successfully

### Different teammates see different core versions

**Issue**: Each app repo has a different `prometheus-core` submodule pointer

**This is expected behavior**. Different app repos may intentionally pin different core versions. To sync to the latest core:

```bash
prometheus update
```

## Related Documents

- `core/documentation/HIERARCHY.md`
- `docs/SUBMODULE_GUIDE.md`
- `docs/GIT_FLOW.md`
