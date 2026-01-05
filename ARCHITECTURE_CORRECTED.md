# CI/CD Manager - Corrected Architecture

## The Problem

The original pipeline discovery was fundamentally wrong:
- It tried to find workflows **on the VPS filesystem** (looking for `.github/workflows/deploy.yml`)
- Workflows are version-controlled on GitHub, not on the VPS
- The VPS is just where code gets **deployed** (executed)
- The source of truth is **always GitHub**

## The Solution

The corrected architecture properly separates **two environments**:

### Local Environment (`$GHT` Available)
**Purpose**: Direct access to GitHub via API

**Responsibilities**:
1. Query GitHub for repositories you own
2. Find repositories with CI/CD workflows
3. Identify deploy-related workflows (deploy, release, cd, production, etc.)
4. Store pipeline metadata

**Key Component**: `GitHubRepositoryDiscovery`
```python
discovery = GitHubRepositoryDiscovery(GHT)  # Uses local $GHT token
repos = discovery.find_deploy_workflows()
```

### Remote VPS Environment (`$GHT` NOT Available)
**Purpose**: See what's actually deployed

**Responsibilities**:
1. List NGINX domains
2. Find deployed applications in `/home/deployer/apps/`
3. Check git remotes (to link back to GitHub)
4. Check PM2 processes and status
5. Report infrastructure state

**Key Component**: `ServerDiscovery`
```python
discovery = ServerDiscovery(VPS_HOST, VPS_USER, VPS_PORT)
apps = discovery.discover_deployed_apps()  # No $GHT needed - just SSH
domains = discovery.discover_domains()
```

### The Match

The pipeline discovery **bridges both environments**:

```
GitHub Repositories (via $GHT)
         ↓
    Find deploy workflows
         ↓
    Get repo info
         ↓
Match with VPS ← VPS Deployments (via SSH)
     ↓
Register Pipeline
```

**Key Component**: `PipelineManager.discover_and_register_pipelines()`

```python
# Step 1: Find deploy-enabled repos on GitHub (uses local $GHT)
deploy_repos = github_discovery.find_deploy_workflows()

# Step 2: Check what's deployed on VPS (uses SSH, no token needed)
vps_apps = vps_discovery.discover_deployed_apps()
vps_domains = vps_discovery.discover_domains()

# Step 3: Match them together
for gh_repo in deploy_repos:
    if any(app_name in gh_repo['repo'] for app_name in vps_apps):
        register_pipeline(gh_repo, linked_to=app_name)
```

## Pipeline Registration

A pipeline is registered when:
1. A repository on GitHub has a deploy workflow
2. That repository is found (matching by repo name to VPS app)
3. The correlation is stored in the pipeline registry

**Data Structure**:
```json
{
  "pipeline_id": "ccm-abc123",
  "repository": "owner/repo-name",
  "workflow_file": ".github/workflows/deploy.yml",
  "workflow_name": "Deploy to Production",
  "status": "active",
  "github_config": {
    "owner": "owner",
    "repo": "repo-name",
    "workflow_id": 123456,
    "html_url": "https://github.com/owner/repo-name"
  },
  "vps_integration": {
    "linked_domains": ["example.com"],
    "linked_apps": ["example.com"],
    "discovery_timestamp": "2026-01-05T10:00:00"
  }
}
```

## Discovery Flow

### Current State

Running discovery will:

1. **Use local environment with $GHT**:
   - Query your GitHub account for all repositories
   - Check each repository for GitHub Actions workflows
   - Filter for deploy-related workflows (deploy, release, cd, production, etc.)
   
2. **Use remote VPS (SSH)**:
   - Connect to VPS
   - List NGINX enabled domains
   - Check `/home/deployer/apps/` for deployed applications
   - Extract git remote URLs from deployed apps
   
3. **Match & Register**:
   - Try to match GitHub repos to VPS deployments by name
   - Register matched pairs as pipelines
   - Store in local registry

### Current Test Results

```
✓ Found 100 repositories on GitHub
✓ Scanned all repositories for workflows
✗ Found 0 repositories with "deploy", "release", "cd", or "production" workflows

  ℹ️  This is EXPECTED if you haven't set up CI/CD workflows yet
```

## Next Steps

To actually discover pipelines, you need:

### Option 1: Create a Deploy Workflow
Create `.github/workflows/deploy.yml` in a GitHub repository:

```yaml
name: Deploy
on:
  push:
    branches:
      - main
      - production

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: echo "Deploying..."
```

### Option 2: Manually Register Pipelines
Use the CLI to manually register a pipeline and link it to your GitHub repo + VPS deployment

### Option 3: Match by Repository Name
The discovery algorithm matches by repo name pattern matching:
- GitHub repo `example.com` matches VPS app `example.com`
- GitHub repo `my-app` matches VPS app `my-app`

So naming your repos to match your VPS deployments helps!

## Architecture Diagram

```
LOCAL MACHINE (has $GHT)
├─ GitHubRepositoryDiscovery
│  └─ Queries GitHub API
│     └─ Finds repos with deploy workflows
│        └─ Returns: repo name, owner, workflow path
│
└─ PipelineManager
   ├─ Uses GitHub discovery results
   └─ Cross-references with VPS data
      └─ Registers matched pipelines

REMOTE VPS (SSH only, no $GHT)
├─ ServerDiscovery
│  └─ Connects via SSH
│     ├─ Lists NGINX domains
│     ├─ Scans /home/deployer/apps/
│     └─ Gets git remote URLs
│        └─ Returns: app paths, domains, repos
│
└─ PipelineManager receives results
   └─ Matches with GitHub data
      └─ Registers as pipelines
```

## Key Changes Made

1. **New Class**: `GitHubRepositoryDiscovery`
   - Queries GitHub API (requires `$GHT` token)
   - Finds repositories with deploy-related workflows
   - Uses local environment with direct API access

2. **Updated**: `discover_and_register_pipelines()`
   - Now takes **two discovery objects**: GitHub + VPS
   - Step 1: Find deploy workflows on GitHub (local)
   - Step 2: Find deployments on VPS (remote)
   - Step 3: Match and register (local)

3. **Updated**: `CICDManagerCLI`
   - Added `self.github_discovery` (initialized with local `$GHT`)
   - Passes both discovery objects to pipeline manager

4. **Removed**: VPS-side API checking
   - No longer tries to check GitHub from VPS
   - No longer looks for `.github/workflows/` on VPS filesystem

## Usage

```bash
# Run discovery from CLI
./run.zsh

# Select: 3 - CI/CD Pipelines
# Then: Option to discover pipelines
# The system will:
# 1. Use local $GHT to find your deploy workflows on GitHub
# 2. Connect to VPS to see what's deployed
# 3. Match them together
# 4. Register as pipelines
```

## Testing

To test the discovery process:

```bash
# Just GitHub discovery (what's on GitHub)
python3 << 'EOF'
from ci_cd_manager import GitHubRepositoryDiscovery
import os

discovery = GitHubRepositoryDiscovery(os.environ.get('GHT'))
repos = discovery.find_deploy_workflows()
print(f"Found {len(repos)} repos with deploy workflows")
EOF

# Just VPS discovery (what's deployed)
python3 << 'EOF'
from ci_cd_manager import ServerDiscovery
discovery = ServerDiscovery("23.29.114.83", "beinejd", 2223)
discovery.connect()
apps = discovery.discover_deployed_apps()
domains = discovery.discover_domains()
print(f"VPS Apps: {list(apps.keys())}")
print(f"VPS Domains: {domains}")
discovery.disconnect()
EOF
```

## Summary

The corrected architecture properly respects the separation between:
- **Source of Truth**: GitHub (has workflows, repo code)
- **Deployment Target**: VPS (runs deployed code)

Pipeline discovery now works correctly by:
1. Querying the source of truth (GitHub) with local credentials (`$GHT`)
2. Checking the deployment target (VPS) with SSH
3. Linking them together by name matching

This fixes the "no pipelines found" issue - it's not a bug, it means you simply don't have any workflows named deploy/release/cd/production yet!
