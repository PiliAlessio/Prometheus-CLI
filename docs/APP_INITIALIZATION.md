# App Initialization Guide

This guide shows how to create a new Phase 2 app repository, connect it to GitHub, and start working with the shared core.

## What `prometheus init` Creates

The current CLI command is:

```bash
prometheus init --app-name billing-api
```

Current implementation details:

- creates the repo under `~/.prometheus/<app-name>/`
- creates `.github/`, `config/`, and `instructions/`
- initializes a local Git repository
- adds `prometheus-core` as a Git submodule
- writes `.prometheus.yml`

## Before and After

### Before

```text
C:\Users\you\.prometheus\
└── (no billing-api folder yet)
```

### After

```text
C:\Users\you\.prometheus\
└── billing-api\
    ├── .github\
    ├── config\
    ├── instructions\
    ├── .prometheus.yml
    └── prometheus-core\
```

## Step-by-Step: Create a New App Repo

### 1. Run the init command

```bash
prometheus init --app-name billing-api
```

Example output:

```text
Initializing Prometheus app repo: billing-api
  App path: C:\Users\you\.prometheus\billing-api
  Core source: https://github.com/AlessioPili-KT/Prometheus.git
  Core version: 6c7d8e9
  Config: C:\Users\you\.prometheus\billing-api\.prometheus.yml
[OK] App repository initialized successfully!
```

### 2. Move into the new repo

```bash
cd %USERPROFILE%\.prometheus\billing-api
```

### 3. Inspect the generated structure

```bash
git status
git submodule status
```

You should see:

- a normal Git repository at the app root
- `prometheus-core` tracked as a submodule

## Structure of the Generated App Repo

### `.github\`

Use for app-specific GitHub Actions and automation.

### `config\`

Use for app-owned configuration.

### `instructions\`

Use for app-specific operating guidance and workflow notes.

### `.prometheus.yml`

This file is created from the CLI config object and currently stores:

```yaml
app_name: billing-api
remote_url: null
core_version: 6c7d8e9
languages: []
```

Notes:

- `remote_url` is not set automatically
- `core_version` records the checked-out submodule revision at init time

### `prometheus-core\`

This is the shared core checkout managed as a Git submodule.

## How to Connect the New Repo to GitHub

`prometheus init` creates the local repository, but it does **not** create or connect the GitHub remote for you.

### Option A: Create the repo with GitHub CLI

```bash
gh repo create <org>/billing-api --private --source . --remote origin
```

That command:

- creates the remote GitHub repository
- adds `origin`

### Option B: Add the remote manually

```bash
git remote add origin https://github.com/<org>/billing-api.git
git branch -M main
```

## First Push to Remote

If you have not pushed the repo yet, do the first push manually:

```bash
git add .
git commit -m "Initialize billing-api"
git push -u origin main
```

Example output:

```text
branch 'main' set up to track 'origin/main'.
```

## How to Sync with the Latest Core

### Normal daily sync

```bash
prometheus update
```

Example output:

```text
Updated app repo: C:\Users\you\.prometheus\billing-api
  App revision: 83d21aa -> 83d21aa
  Core revision: 6c7d8e9 -> 7ab45de
[OK] Update completed successfully.
```

### Intentional core upgrade

If you want the app repo to record a newer shared revision:

```bash
cd prometheus-core
git fetch
git checkout main
git pull
cd ..
git add prometheus-core
git commit -m "Update prometheus-core"
git push
```

## Recommended First-Day Flow

```bash
prometheus init --app-name billing-api
cd %USERPROFILE%\.prometheus\billing-api
git remote add origin https://github.com/<org>/billing-api.git
git branch -M main
git add .
git commit -m "Initialize billing-api"
git push -u origin main
prometheus update
```

## Troubleshooting

### `Missing option '--app-name'`

Use:

```bash
prometheus init --app-name billing-api
```

### Target directory already exists

The init workflow refuses to write into a non-empty target folder. Choose a new app name or clean the existing folder first.

### `prometheus-core` was not created correctly

Check that Git can access the Prometheus repository URL:

```bash
git ls-remote https://github.com/AlessioPili-KT/Prometheus.git
```

Then rerun init in a fresh target folder.

### GitHub remote is missing

Add it manually:

```bash
git remote add origin https://github.com/<org>/<app>.git
```

### First push fails

Verify:

```bash
git remote -v
git branch
git status
```

Then confirm you committed the initial scaffold before pushing.

## Related Documents

- [TWO_REPO_WORKFLOW.md](./TWO_REPO_WORKFLOW.md)
- [PUSH_UPDATE_COMMANDS.md](./PUSH_UPDATE_COMMANDS.md)
- [SUBMODULE_GUIDE.md](./SUBMODULE_GUIDE.md)
