# `prometheus --push` and `prometheus update`

This guide covers the two Phase 2 day-to-day commands:

- `prometheus --push`
- `prometheus update`

Use them from inside an **app repository** that contains `.prometheus.yml`.

## Workflow Summary

```text
Start work  -> prometheus update
Make commits -> git commit ...
Publish     -> prometheus --push
```

## `prometheus --push`

### When to use it

Use `prometheus --push` after you have already committed your work and want to publish:

- app-only commits
- shared commits made inside `prometheus-core`
- both, if each repo has its own commit ready

### What it does

Current CLI behavior:

1. verifies you are inside an app repo
2. checks the app repo for uncommitted files
3. checks whether the app repo is ahead of origin
4. pushes the app repo if it is clean and ahead
5. repeats the same checks for `prometheus-core`
6. prints a push summary

Important:

- it **does not create commits**
- it **does not update the submodule pointer for you**
- it skips any repo that is dirty or has nothing to push

### Basic example

```bash
prometheus --push
```

Example output:

```text
Push summary:
  app repo: pushed
    Branch: main
  prometheus-core submodule: pushed
    Branch: main
[OK] Push workflow completed.
```

### Example: app-only push

```bash
git add instructions\release-notes.md
git commit -m "Document rollout checklist"
prometheus --push
```

Example output:

```text
Push summary:
  app repo: pushed
    Branch: main
  prometheus-core submodule: skipped (no commits to push)
    Branch: main
[OK] Push workflow completed.
```

### Example: shared-core push

```bash
cd prometheus-core
git add core\documentation\shared-policy.md
git commit -m "Clarify shared policy"
cd ..
git add prometheus-core
git commit -m "Update prometheus-core pointer"
prometheus --push
```

Example output:

```text
Push summary:
  app repo: pushed
    Branch: main
  prometheus-core submodule: pushed
    Branch: main
[OK] Push workflow completed.
```

### Example: blocked by uncommitted changes

```bash
prometheus --push
```

Example output:

```text
Push summary:
  app repo: skipped (has uncommitted changes)
    Branch: main
    Modified files: README.md
  prometheus-core submodule: skipped (no commits to push)
    Branch: main
[OK] Push workflow completed.
```

### Troubleshooting `--push`

#### `app repo: skipped (has uncommitted changes)`

Commit or stash first:

```bash
git status
git add .
git commit -m "Your message"
```

#### `skipped (no commits to push)`

You probably committed nothing in that repo, or your branch is not ahead of origin:

```bash
git status
git log --oneline origin/main..HEAD
```

#### Shared change is pushed, but app still points to old core

You forgot the app repo pointer commit:

```bash
git add prometheus-core
git commit -m "Update prometheus-core pointer"
prometheus --push
```

#### `--push` fails outside an app repo

Run it from a repository that contains `.prometheus.yml`.

## `prometheus update`

### When to use it

Use `prometheus update`:

- at the start of the day
- after a teammate merges changes
- after switching branches
- before starting work on top of an existing app repo

### What it does

Current CLI behavior:

1. verifies you are inside an app repo
2. captures the current app revision
3. captures the current `prometheus-core` revision if present
4. runs `git pull --ff-only`
5. runs `git submodule update --remote`
6. prints the before/after revisions

### Basic example

```bash
prometheus update
```

Example output:

```text
Updated app repo: C:\Users\you\.prometheus\billing-api
  App revision: before-app -> after-app
  Core revision: before-core -> after-core
[OK] Update completed successfully.
```

### Example: verify the submodule after update

```bash
prometheus update
git submodule status
```

Example output:

```text
 6c7d8e9f0abc1234567890def1234567890abcd prometheus-core (heads/main)
```

### Manual equivalent

`prometheus update` currently maps to this rough Git flow:

```bash
git pull --ff-only
git submodule update --remote
```

If the submodule was never initialized or the remote URL changed, you may also need:

```bash
git submodule sync --recursive
git submodule update --init --recursive
```

### Troubleshooting `update`

#### `The update workflow only works inside an app repository.`

Move into an app repo root or any child folder under it.

#### `git pull --ff-only` fails

You likely have local commits or divergent history:

```bash
git status
git pull --rebase
```

If your team does not use rebase, resolve the divergence with your normal Git policy first, then rerun `prometheus update`.

#### `prometheus-core` did not appear

Initialize it manually:

```bash
git submodule update --init --recursive
```

#### The core revision changed unexpectedly

Inspect what changed:

```bash
git submodule status
cd prometheus-core
git log --oneline -5
```

## Typical Day of Work

### Morning sync

```bash
prometheus update
```

### Make app changes

```bash
git add config\app.yml instructions\handoff.md
git commit -m "Update app config and handoff notes"
```

### Make a shared change if needed

```bash
cd prometheus-core
git add core\documentation\team-patterns.md
git commit -m "Refine team patterns"
cd ..
git add prometheus-core
git commit -m "Update prometheus-core pointer"
```

### Publish everything

```bash
prometheus --push
```

### End-of-day mental model

```text
App repo commit history       -> app-specific changes + submodule pointer
Prometheus repo commit history -> shared core changes
```

## Before/After Diagram

### Before `prometheus update`

```text
Local app repo      -> older app commit
Local submodule     -> older core commit
Remote app repo     -> newer app commit
Remote Prometheus   -> newer core commit
```

### After `prometheus update`

```text
Local app repo      -> pulled forward
Local submodule     -> refreshed to tracked remote state
```

## Related Documents

- [TWO_REPO_WORKFLOW.md](./TWO_REPO_WORKFLOW.md)
- [APP_INITIALIZATION.md](./APP_INITIALIZATION.md)
- [CLI_GUIDE.md](./CLI_GUIDE.md)
- [GIT_FLOW.md](./GIT_FLOW.md)
