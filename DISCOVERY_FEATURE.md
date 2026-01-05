# CCM Discovery Feature: Auto-Detect Deployed Pipelines

**Date**: January 5, 2026  
**Feature**: Automatic discovery and registration of CI/CD pipelines from VPS  
**Status**: ✅ Implemented

---

## Overview

The **ServerDiscovery** feature enables CCM to scan the VPS server and automatically detect which applications have CI/CD pipelines deployed. This solves the critical problem of **pipeline registry synchronization** - ensuring CCM knows about all actual pipelines running on the VPS, not just manually registered ones.

### Problem It Solves

**Before**: CCM only knew about pipelines explicitly registered via the CLI. If a pipeline was deployed via other means (direct VPS provisioning, automation scripts), CCM wouldn't know about it.

**After**: CCM can scan the VPS and auto-discover all deployed applications with GitHub repos and CI/CD workflows, automatically registering them in the pipeline registry.

---

## Architecture

### ServerDiscovery Class (Lines 382-549)

**Purpose**: Connect to VPS and query actual deployment state

**Key Capabilities**:

#### 1. Discover Domains
```python
def discover_domains(self) -> List[str]
```
- Lists all NGINX-enabled domains at `/etc/nginx/sites-enabled/`
- Returns: `['topengineer.us', 'portfolio.com', ...]`

**How it works**: SSH command `ls -1 /etc/nginx/sites-enabled/`

#### 2. Discover Deployed Apps
```python
def discover_deployed_apps(self) -> Dict[str, Dict]
```
- Scans `/home/deployer/apps/` directory
- For each app directory:
  - Checks if it has `.git` directory (is a GitHub repo)
  - Checks for `.github/workflows/` directory
  - Parses `.git/config` to extract GitHub repository URL
  - Checks PM2 status

**Returns**:
```json
{
  "topengineer.us": {
    "domain": "topengineer.us",
    "path": "/home/deployer/apps/topengineer.us",
    "has_github_repo": true,
    "has_workflow": true,
    "workflow_file": ".github/workflows/deploy.yml",
    "github_repo": "myuser/topengineer-api",
    "pm2_running": true
  }
}
```

**SSH Commands Used**:
- `ls -1 /home/deployer/apps` - List app directories
- `test -d {path}/.git && echo yes || echo no` - Check for Git repo
- `ls -1 {path}/.github/workflows` - List workflow files
- `cat {path}/.git/config` - Extract GitHub remote URL
- `sudo -u deployer pm2 show {app}` - Check PM2 status

#### 3. Get Domain Details
```python
def get_domain_details(domain: str) -> Optional[Dict]
```
- Detailed information about a specific domain
- Checks NGINX configuration
- Verifies GitHub repo and workflow files
- Gets PM2 status

**Returns**:
```json
{
  "domain": "topengineer.us",
  "nginx_enabled": true,
  "github_repo": "myuser/topengineer-api",
  "has_deploy_workflow": true,
  "workflow_file": ".github/workflows/deploy.yml",
  "pm2_status": "online"
}
```

---

## Pipeline Discovery & Auto-Registration

### PipelineManager.discover_and_register_pipelines()

**Location**: Lines 733-802

**Purpose**: Convert discovered apps into registered pipelines

**Process**:

```
1. Use ServerDiscovery to get all deployed apps
   ↓
2. For each app:
   ├─ Check if it has GitHub repo and workflow
   ├─ Check if already registered (by linked_app)
   ├─ If new, create pipeline entry:
   │  ├─ Generate unique pipeline_id
   │  ├─ Store GitHub repo and workflow path
   │  ├─ Mark as "discovered" (auto-registered)
   │  ├─ Link to VPS domain/app
   │  └─ Set PM2 running status
   └─ Save to registry with backup
   ↓
3. Return count and list of new pipeline IDs
```

**Auto-Generated Pipeline Data**:
```json
{
  "pipeline_id": "pipe_abc123def456",
  "repository": "myuser/topengineer-api",
  "workflow_file": ".github/workflows/deploy.yml",
  "status": "active",
  "created_at": "2026-01-05T10:30:00Z",
  "discovered": true,
  "vps_integration": {
    "requested_by": "server-discovery",
    "linked_domain": "topengineer.us",
    "linked_app": "topengineer.us",
    "pm2_running": true,
    "discovery_timestamp": "2026-01-05T10:30:00Z"
  }
}
```

**Key Features**:
- ✅ Only registers pipelines with both GitHub repo AND workflow file
- ✅ Skips already-registered apps (avoids duplicates)
- ✅ Preserves discovery metadata
- ✅ Captures PM2 status at discovery time
- ✅ Maintains automatic backups

---

## CLI Integration

### Menu Option [5] Discover Pipelines

**Location**: Lines 1563-1598

**Workflow**:

```
Main Menu [5] Discover Pipelines
    ↓
"Connect to VPS and scan for pipelines?"
    ↓
    YES:
        ├─ Connect via SSH
        ├─ Scan /home/deployer/apps/
        ├─ For each app, extract GitHub info
        ├─ Auto-register new pipelines
        ├─ Display newly registered pipelines
        └─ Show pipeline IDs and domains
    
    NO:
        └─ Return to main menu
```

**Sample Output**:

```
Discover CI/CD Pipelines from VPS

This will scan the VPS for deployed applications with GitHub repos and CI/CD workflows.

Connect to VPS and scan for pipelines? [y/N]: y
✓ Connected to VPS

[Scanning deployed applications...]

✓ Auto-registered: topengineer.us → pipe_abc123def456
  Repository: myuser/topengineer-api
  Workflow: .github/workflows/deploy.yml

✓ Discovered and registered 1 pipelines

Newly registered pipelines:
  • pipe_abc123def456 (topengineer.us)

To view all pipelines, select option [4] CI/CD Pipelines
```

---

## Use Cases

### Scenario 1: Initial Setup
**Situation**: VPS has been running for months with multiple applications deployed.  
**Challenge**: CCM registry is empty.

**Solution**:
```
[5] Discover Pipelines
→ Automatically finds all deployed apps with CI/CD
→ Populates CCM registry with existing pipelines
→ No manual registration needed
```

### Scenario 2: Manual VPS Deployment
**Situation**: DevOps deploys new app directly via VPS Manager, not through CCM API.  
**Challenge**: CCM doesn't know about the new deployment.

**Solution**:
```
[5] Discover Pipelines
→ Finds newly deployed app
→ Auto-registers it in CCM
→ Pipeline now visible in monitoring dashboard
```

### Scenario 3: Sync Lost Registrations
**Situation**: Pipeline registry file gets corrupted or lost.  
**Challenge**: CCM loses track of pipelines, but VPS still has them.

**Solution**:
```
[5] Discover Pipelines
→ Rebuilds registry from actual VPS state
→ Recovers all active pipelines
→ Timestamps show when recovery happened
```

### Scenario 4: Multi-Team Deployments
**Situation**: Multiple teams deploy apps to same VPS.  
**Challenge**: Each team manually registers pipelines - easy to miss.

**Solution**:
```
[5] Discover Pipelines (run periodically)
→ Automatically finds all new deployments
→ Ensures CCM registry stays synchronized
→ Can be automated in cron job
```

---

## Technical Details

### SSH Commands Reference

**List apps**:
```bash
ls -1 /home/deployer/apps
```

**Check for Git repo**:
```bash
test -d /home/deployer/apps/domain/.git && echo yes || echo no
```

**List workflows**:
```bash
ls -1 /home/deployer/apps/domain/.github/workflows 2>/dev/null
```

**Extract GitHub remote**:
```bash
cat /home/deployer/apps/domain/.git/config
# Parse: [remote "origin"]
#        url = git@github.com:user/repo.git
```

**Check PM2 status**:
```bash
sudo -u deployer /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2 show domain
```

### Error Handling

**Connection Failures**:
```
[red]✗ Failed to connect to VPS[/red]
→ Check VPS_HOST, VPS_USER, VPS_PORT env variables
→ Verify SSH key is configured
→ Test with: ssh user@host -p port
```

**Missing App Directory**:
```
→ App directory doesn't exist at /home/deployer/apps/domain
→ Check that app was properly provisioned
```

**No Git Repo**:
```
→ Application not a Git repository
→ Pipeline only registered if GitHub repo present
→ Run: git init && git add origin ... from app directory
```

**No Workflow**:
```
→ Application has no .github/workflows directory
→ Create workflow file before discovery
→ Pipeline only registers if workflow exists
```

### Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Connect to VPS | 1-2s | SSH connection setup |
| List apps | <1s | Directory listing |
| Check each app | 1-2s | Git config parsing, PM2 check |
| Register pipelines | <1s per app | Registry save with backup |
| **Total for 5 apps** | **~10-15s** | Depends on network latency |

---

## Discovery vs Manual Provisioning

### Manual Provisioning
```
CLI Menu [4] → [2] Provision Pipeline
├─ User enters: repo URL, workflow file
├─ User links: domain, app name
└─ Pipeline explicitly registered
```

**Advantages**:
- ✅ Explicit control over pipeline config
- ✅ Can customize trigger branches, environment
- ✅ Good for CI/CD pipelines planned in advance

**Disadvantages**:
- ✗ Manual process prone to mistakes
- ✗ Doesn't discover existing pipelines
- ✗ Registry can get out of sync with VPS

### Auto Discovery
```
CLI Menu [5] → Discover Pipelines
├─ System scans VPS
├─ Finds all apps with GitHub + workflows
└─ Auto-registers with defaults
```

**Advantages**:
- ✅ Automatic, no manual steps
- ✅ Finds existing pipelines
- ✅ Keeps registry synchronized
- ✅ Fast and reliable

**Disadvantages**:
- ✗ Uses default config (can be customized later)
- ✗ Only finds apps with existing workflows
- ✗ Requires working SSH connection

### Best Practice

**Hybrid Approach**:
1. Run discovery when setting up CCM (populates existing pipelines)
2. Use manual provisioning for new pipelines
3. Run discovery periodically (weekly cron) to sync any missed deployments

---

## Automation: Discovery as a Service

### Cron Job for Periodic Discovery

```bash
#!/bin/bash
# /usr/local/bin/ccm-discover-pipelines

export GHT="your_github_token"
export CCM_API_TOKEN="your_ccm_token"
export VPS_HOST="23.29.114.83"
export VPS_USER="beinejd"
export VPS_PORT="2223"

python3 /path/to/ci-cd-manager.py <<EOF
5
y
EOF
```

**Crontab Entry**:
```bash
# Run discovery weekly (every Sunday at 2 AM)
0 2 * * 0 /usr/local/bin/ccm-discover-pipelines >> /var/log/ccm-discovery.log 2>&1
```

### API Discovery Endpoint (Future)

```python
@app.post('/api/discovery/scan')
def trigger_discovery():
    """Trigger VPS scan and auto-register pipelines"""
    discovery = ServerDiscovery(VPS_HOST, VPS_USER, VPS_PORT)
    if discovery.connect():
        count, ids = pipeline_manager.discover_and_register_pipelines(discovery)
        discovery.disconnect()
        return {"success": True, "discovered": count, "pipeline_ids": ids}
    return {"success": False, "error": "VPS connection failed"}
```

---

## Integration with Existing Components

### With PipelineManager
- Discovery creates pipeline entries
- Same format as manually provisioned pipelines
- All pipeline operations work identically

### With PipelineRegistry
- Discovered pipelines stored same way
- Automatic backups created
- Registry version unchanged (2.0)

### With PipelineMonitor
- Discovered pipelines monitored same as others
- Real-time stats collection works
- Health scores calculated correctly

### With VPS Manager
- Discovery queries same SSH connection
- Respects PM2 paths and NVM setup
- Complements VPS domain discovery

---

## Data Flow Diagram

```
CCM CLI
  ↓
[5] Discover Pipelines Menu
  ↓
ServerDiscovery.connect()
  ↓
SSH → VPS
  ├─ ls /home/deployer/apps
  ├─ for each app:
  │  ├─ test -d app/.git
  │  ├─ cat app/.git/config
  │  ├─ ls app/.github/workflows
  │  └─ pm2 show app
  └─ Return to CCM
  ↓
PipelineManager.discover_and_register_pipelines()
  ├─ Filter apps with GitHub + workflow
  ├─ Check for duplicates
  ├─ Generate pipeline_id
  ├─ Create pipeline_data
  └─ registry.add_pipeline()
  ↓
PipelineRegistry._save_registry()
  ├─ Create backup
  ├─ Write pipelines.json
  └─ Return success
  ↓
Display results
  ├─ Show newly registered pipelines
  ├─ Show pipeline IDs and domains
  └─ Offer to view full pipeline list
```

---

## Summary

**ServerDiscovery** adds critical **inventory synchronization** capability to CCM:

✅ **Automatic Detection** - Find actual pipelines on VPS  
✅ **Zero Manual Steps** - Just click and scan  
✅ **Duplicate Prevention** - Won't register same pipeline twice  
✅ **Data Preservation** - Backups created on every change  
✅ **Integration Ready** - Works with all existing CCM features  
✅ **Flexible** - Manual + discovery can coexist  

**Next Steps**:
1. Run discovery on initial setup
2. Use CLI to provision new pipelines
3. Run discovery periodically to stay in sync
4. Monitor all pipelines via dashboard
5. Use API for automation

---

## Commands Quick Reference

### Run Discovery from CLI
```
[5] Discover Pipelines
→ Connect to VPS and scan for pipelines? [y/N]: y
```

### View Discovered Pipelines
```
[4] CI/CD Pipelines
→ [1] List pipelines
```

### Get Stats for Discovered Pipeline
```
[4] CI/CD Pipelines
→ [3] View pipeline details
→ Select discovered pipeline
```

### Manual Sync Rebuild
```bash
python3 ci-cd-manager.py
[5] Discover Pipelines
→ (This rebuilds registry from VPS state)
```
