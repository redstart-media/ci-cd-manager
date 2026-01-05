# CI/CD Manager - Stage 2: Pipeline Provisioning & Real-Time Monitoring

**Status**: Stage 2 Requirements Document  
**Date**: January 5, 2026  
**Focus**: Dynamic pipeline orchestration, real-time monitoring, and bi-directional VPS-CCM integration

---

## Overview

Stage 2 transforms CCM from a **static secret management tool** into a **dynamic pipeline orchestration platform** with real-time monitoring capabilities. The key shift is making CCM the **authoritative system for CI/CD pipeline provisioning**, while establishing a communication protocol between VPS Manager and CCM.

### Core Principle
**CI/CD provisioning is a responsibility of the CCM.** VPS Manager scripts request pipeline establishment from CCM; CCM manages the full lifecycle of pipelines (creation, monitoring, teardown) without destroying underlying repositories.

---

## Architecture Components

### 1. Pipeline Management System

#### PipelineManager Class
**Purpose**: Manage CI/CD pipeline lifecycle (provision, monitor, teardown)

**Key Responsibilities**:
- **Pipeline Provisioning**: Create new CI/CD pipelines for repositories
- **Pipeline Teardown**: Remove pipelines without deleting repositories
- **Pipeline Registry**: Maintain persistent state of all pipelines
- **Workflow Integration**: Interface with GitHub Actions workflows
- **Status Tracking**: Monitor pipeline execution state

**Data Structure - Pipeline State**:
```json
{
  "pipeline_id": "unique-pipeline-identifier",
  "repository": "owner/repo-name",
  "workflow_file": ".github/workflows/deploy.yml",
  "status": "active|inactive|error",
  "created_at": "2026-01-05T10:30:00Z",
  "last_updated": "2026-01-05T11:45:00Z",
  "config": {
    "trigger_branches": ["production", "main"],
    "environment": "production|staging",
    "auto_deploy": true,
    "notifications_enabled": true
  },
  "metrics": {
    "last_run": "2026-01-05T11:45:00Z",
    "last_status": "success|failure|running",
    "run_count": 42,
    "success_rate": 95.2,
    "average_duration_seconds": 180
  },
  "vps_integration": {
    "requested_by": "vps-manager",
    "linked_domain": "topengineer.us",
    "linked_app": "app-name"
  }
}
```

**Key Methods**:
- `provision_pipeline(repo: str, workflow_file: str, config: Dict) -> Pipeline`
- `teardown_pipeline(pipeline_id: str, preserve_repo: bool = True) -> bool`
- `get_pipelines() -> List[Pipeline]` *(parallels VPS Manager's `get_sites()`)*
- `get_pipeline(pipeline_id: str) -> Optional[Pipeline]`
- `update_pipeline_status(pipeline_id: str) -> Pipeline`
- `get_pipeline_metrics(pipeline_id: str, time_range: str = "24h") -> Dict`

---

### 2. Real-Time Monitoring System

#### PipelineMonitor Class
**Purpose**: Real-time pipeline health and execution monitoring (parallels VPS Manager's `get_system_stats()`)

**Monitored Metrics**:

| Metric | Type | Source | Refresh Rate |
|--------|------|--------|--------------|
| **Pipeline Status** | Status | GitHub API | 10s |
| **Active Runs** | Count | GitHub Actions API | 10s |
| **Success Rate (24h)** | Percentage | GitHub Actions API | 60s |
| **Avg Run Duration** | Seconds | GitHub Actions API | 60s |
| **Last Run Time** | Timestamp | GitHub Actions API | 10s |
| **Last Run Status** | Status | GitHub Actions API | 10s |
| **Deployment Health** | Health Score | Aggregate | 30s |
| **Error Count (24h)** | Count | GitHub Actions API | 60s |
| **Queue Status** | Status | GitHub Actions API | 10s |

**Key Methods**:
- `get_pipeline_stats(pipeline_id: str) -> Dict` *(parallels VPS Manager's `get_system_stats()`)*
- `get_all_pipeline_stats() -> List[Dict]`
- `get_workflow_runs(pipeline_id: str, limit: int = 10) -> List[Dict]`
- `get_recent_failures(pipeline_id: str, hours: int = 24) -> List[Dict]`
- `calculate_health_score(pipeline_id: str) -> float` (0-100)

**Real-Time Dashboard Display** (Rich UI):
```
┌─────────────────────────────────────────────────────────────────┐
│                    CI/CD PIPELINE MONITOR                       │
├─────────────────────────────────────────────────────────────────┤
│ Pipeline          Status    Success  Duration  Last Run         │
├─────────────────────────────────────────────────────────────────┤
│ topengineer.us    ✓ Active   95.2%    3m 12s   5 min ago       │
│ portfolio         ✓ Active   88.5%    2m 45s   1 hour ago      │
│ api-service       ✗ Error    72.1%    5m 01s   Failed          │
│ docs              ✓ Active   100%     1m 15s   30 min ago      │
└─────────────────────────────────────────────────────────────────┘
```

---

### 3. API Integration System

#### PipelineAPI Class
**Purpose**: REST API endpoints for VPS Manager ↔ CCM communication

**Endpoint Design**:

```
POST /api/pipelines/provision
├─ Request: { repo, workflow_file, config, linked_domain, linked_app }
├─ Response: { pipeline_id, status, created_at }
└─ Called by: VPS Manager when deploying new application

GET /api/pipelines
├─ Response: List[Pipeline] with current status
└─ Called by: VPS Manager, CCM monitor UI

GET /api/pipelines/<pipeline_id>
├─ Response: Pipeline with full metrics
└─ Called by: VPS Manager, CCM monitor UI

GET /api/pipelines/<pipeline_id>/stats
├─ Response: Real-time stats (parallels /api/vps/stats)
└─ Called by: Real-time monitor, VPS Manager dashboard

GET /api/pipelines/<pipeline_id>/runs
├─ Query params: limit=10, branch=production
├─ Response: List of recent workflow runs
└─ Called by: Monitor UI, VPS Manager status checks

DELETE /api/pipelines/<pipeline_id>
├─ Query params: preserve_repo=true
├─ Response: { success, deleted_at }
└─ Called by: VPS Manager during application removal

POST /api/pipelines/<pipeline_id>/trigger
├─ Request: { branch, workflow_name }
├─ Response: { run_id, triggered_at }
└─ Called by: Manual deployment via monitor UI
```

**Request/Response Examples**:

*Provision Pipeline (VPS → CCM)*:
```json
POST /api/pipelines/provision
{
  "repo": "owner/topengineer-api",
  "workflow_file": ".github/workflows/deploy.yml",
  "config": {
    "trigger_branches": ["production"],
    "environment": "production",
    "auto_deploy": true,
    "notifications_enabled": true
  },
  "linked_domain": "topengineer.us",
  "linked_app": "topengineer-api"
}

Response:
{
  "pipeline_id": "pipe_abc123def456",
  "status": "active",
  "created_at": "2026-01-05T10:30:00Z",
  "repository": "owner/topengineer-api"
}
```

*Get Pipeline Stats (Monitor)*:
```json
GET /api/pipelines/pipe_abc123def456/stats

Response:
{
  "pipeline_id": "pipe_abc123def456",
  "status": "active",
  "last_run": {
    "timestamp": "2026-01-05T11:45:00Z",
    "status": "success",
    "duration_seconds": 192,
    "branch": "production"
  },
  "metrics_24h": {
    "run_count": 3,
    "success_count": 3,
    "success_rate": 100.0,
    "avg_duration_seconds": 187
  },
  "health_score": 95,
  "active_runs": 0,
  "queue_length": 0
}
```

---

### 4. Pipeline Provisioning Workflow

#### Scenario: VPS Manager Deploys New Application

```
1. VPS Manager creates app directory and configures domain
   ↓
2. VPS Manager makes POST /api/pipelines/provision request to CCM
   ├─ Includes: repo, workflow_file, domain, app_name
   ├─ CCM receives request
   └─ CCM validates:
      ├─ GitHub token has access to repo
      ├─ Workflow file exists in repo
      └─ Pipeline not already provisioned
   ↓
3. CCM creates Pipeline state object in registry
   ├─ Assigns unique pipeline_id
   ├─ Stores VPS linkage metadata
   └─ Records creation timestamp
   ↓
4. CCM enables GitHub Actions workflow (if disabled)
   └─ Uses GitHub API to enable workflow
   ↓
5. CCM responds with pipeline_id and status
   └─ VPS Manager stores pipeline_id in app metadata
   ↓
6. Pipeline is now monitored by CCM in real-time
   └─ Available in pipeline monitor dashboard
```

#### Scenario: VPS Manager Removes Application

```
1. VPS Manager receives app deletion request
   ↓
2. VPS Manager makes DELETE /api/pipelines/<pipeline_id> request
   ├─ Includes: preserve_repo=true
   └─ CCM receives request
   ↓
3. CCM validates deletion request
   ├─ Checks pipeline exists
   ├─ Verifies linked app/domain
   └─ Cancels any running workflows
   ↓
4. CCM removes pipeline state from registry
   ├─ Updates status to "inactive"
   ├─ Records deactivation timestamp
   └─ Does NOT delete repository or workflow files
   ↓
5. CCM responds with success
   └─ VPS Manager completes app removal
   ↓
6. Repository remains intact on GitHub
   └─ Can be re-linked to new pipeline later
```

---

### 5. Pipeline Registry & Persistence

#### Registry Structure
```
~/.ccm/pipelines.json
{
  "pipelines": {
    "pipe_abc123def456": { ...pipeline data... },
    "pipe_xyz789uvw123": { ...pipeline data... },
    ...
  },
  "registry_version": "2.0",
  "last_updated": "2026-01-05T11:45:00Z"
}
```

**Load/Save Operations**:
- Load registry on CCM startup
- Load specific pipeline on demand
- Cache pipeline list in memory with TTL (5 minutes)
- Save pipeline changes immediately
- Maintain backup of previous registry state

**Backup Strategy**:
```
~/.ccm/backups/
├── pipelines-2026-01-05-11-45-00.json
├── pipelines-2026-01-05-10-30-00.json
└── pipelines-2026-01-05-09-15-00.json
```

---

## Implementation Phases

### Phase 1: Core Pipeline Management (Week 1-2)
- [ ] Implement `PipelineManager` class with provision/teardown/status methods
- [ ] Create pipeline registry persistence layer
- [ ] Implement `PipelineAPI` class with basic REST endpoints
- [ ] Create pipeline data structure and validation
- [ ] Add pipeline state tracking

### Phase 2: Real-Time Monitoring (Week 2-3)
- [ ] Implement `PipelineMonitor` class with GitHub Actions integration
- [ ] Create real-time metrics collection system
- [ ] Build health score calculation algorithm
- [ ] Create Rich UI dashboard for pipeline monitoring
- [ ] Implement stats caching and refresh logic

### Phase 3: VPS-CCM Integration (Week 3)
- [ ] Design and document integration protocol
- [ ] Create integration examples/helpers
- [ ] Implement pipeline provisioning API endpoints
- [ ] Implement pipeline teardown API endpoints
- [ ] Test bi-directional communication

### Phase 4: Advanced Features (Week 4+)
- [ ] Pipeline triggering and manual deployment
- [ ] Workflow run history and logs integration
- [ ] Alert/notification system for pipeline failures
- [ ] Pipeline performance analytics
- [ ] Workflow configuration templates

---

## Key Design Decisions

### 1. Unique Pipeline IDs
- **Decision**: Use `pipe_<random-12-char-hex>` format
- **Rationale**: Decouples pipeline identity from repository names, allows repository renaming without breaking references
- **Example**: `pipe_abc123def456`

### 2. GitHub Actions Monitoring
- **Decision**: Use GitHub API for real-time workflow data, with 10-second refresh for status and 60-second for metrics
- **Rationale**: Provides authoritative source of truth, reduces strain on CCM system
- **Fallback**: Cache last known state if API unavailable

### 3. Non-Destructive Teardown
- **Decision**: `DELETE /api/pipelines/<id>` removes pipeline from CCM registry but preserves GitHub workflows and repository
- **Rationale**: Allows for quick re-linking, prevents accidental data loss, aligns with infrastructure-as-code principle
- **Example**: Application removed from VPS, but repository and workflow files remain intact on GitHub

### 4. VPS Linkage Metadata
- **Decision**: Store `linked_domain` and `linked_app` in pipeline state
- **Rationale**: Enables CCM to understand VPS context, supports cross-system monitoring and debugging
- **Example**: Monitor can display "topengineer.us" alongside pipeline status

### 5. Real-Time vs Polling
- **Decision**: Active polling from CCM to GitHub API (not webhooks)
- **Rationale**: Simpler architecture, no firewall holes needed, easier to test
- **Trade-off**: Slight delay in real-time updates (10-60 seconds)

---

## Data Flow Diagrams

### Setup Flow (VPS → CCM)
```
VPS Manager                 CCM                     GitHub API
    │                        │                           │
    ├──POST /provision─────→ │                           │
    │                        ├─validate repo────────────→│
    │                        │                           │
    │                        │←─repo exists─────────────┤
    │                        │                           │
    │                        ├─enable workflow──────────→│
    │                        │                           │
    │                        │←─workflow enabled────────┤
    │                        │                           │
    │←─{ pipeline_id }──────┤                           │
    │                        │                           │
    └─(store pipeline_id)    └─(monitor starts)         │
```

### Monitoring Flow (Real-Time)
```
Pipeline Monitor            CCM                     GitHub API
    │                        │                           │
    │<─request stats────────┤                           │
    │                        ├─get latest run──────────→│
    │                        │                           │
    │                        │←─run data────────────────┤
    │                        │                           │
    │                        ├─calculate health────────┤
    │                        │                           │
    │←─{ stats, health }────┤                           │
    │                        │                           │
    └─(display dashboard)   │                           │
```

### Teardown Flow (VPS → CCM)
```
VPS Manager                 CCM                     GitHub
    │                        │                        │
    ├──DELETE /pipeline_id─→ │                        │
    │                        ├─verify exists──────────→│
    │                        │                        │
    │                        │←─found──────────────────┤
    │                        │                        │
    │                        ├─cancel runs────────────→│
    │                        │                        │
    │                        │←─cancelled──────────────┤
    │                        │                        │
    │                        ├─remove from registry   │
    │                        │                        │
    │←─{ success: true }────┤                        │
    │                        │                        │
    └─(app removal complete) └─(pipeline inactive)    │
                                (repo preserved)
```

---

## Integration with Existing Components

### GitHubSecretsManager → PipelineManager
- **Current**: Handles secret replication across repos
- **Stage 2**: Works alongside PipelineManager for complete CI/CD automation
- **Integration**: Both use shared GitHub API client and token

### VPSManager → PipelineAPI
- **Current**: Manages VPS infrastructure, sites, services
- **Stage 2**: Communicates with CCM via REST API for pipeline provisioning
- **Integration**: VPS calls `POST /api/pipelines/provision` when creating apps
- **Example**: Deploy app to domain → VPS requests pipeline setup → CCM provisions → Pipeline monitoring begins

### ProjectConfiguration → PipelineRegistry
- **Current**: Stores project metadata (repos, secrets, etc.)
- **Stage 2**: Extended to store pipeline provisioning templates and defaults
- **Integration**: Pipeline provisioning can use project defaults for config

---

## API Security & Authentication

### Authentication Mechanism
- **Method**: Token-based authentication via `CCM-Token` header
- **Storage**: Generated during CCM initialization, stored in secure config
- **Sharing**: VPS Manager receives token during setup phase
- **Rotation**: Support token rotation without downtime

### Authorization Levels
```
- admin: Can provision, teardown, modify pipelines
- viewer: Can only view pipeline status and metrics
- api: Can provision/teardown (used by VPS Manager)
```

### Example Headers
```
curl -X POST http://ccm-host:8000/api/pipelines/provision \
  -H "CCM-Token: ccm_abc123def456xyz789" \
  -H "Content-Type: application/json" \
  -d '{...pipeline config...}'
```

---

## Monitoring Dashboard Features

### Metrics Displayed
- Pipeline status (active/inactive/error)
- Last workflow run status and duration
- 24-hour success rate with trend indicator
- Health score (0-100) with color coding
- Linked VPS domain and application
- Queue status and active run count
- Last run timestamp

### Interactive Features
- Drill-down into individual pipeline details
- View recent workflow runs (last 10)
- Manual workflow triggering
- Real-time refresh with configurable interval
- Filter pipelines by status, domain, or application
- Export pipeline status report

### Color Scheme & Indicators
```
✓ Active   = Green
✗ Error    = Red
⏸ Inactive = Gray
⟳ Running  = Blue
⚠ Warning  = Yellow
```

---

## Testing Strategy

### Unit Tests
- Pipeline provisioning logic
- Health score calculation
- Status translation from GitHub Actions
- Registry load/save operations

### Integration Tests
- GitHub API communication
- Full provision → monitor → teardown flow
- Concurrent pipeline operations
- API endpoint validation

### Manual Tests
- Provision pipeline via API
- Monitor dashboard display
- Teardown without data loss
- VPS Manager communication

---

## Success Criteria for Stage 2

✅ **Functional Requirements**:
- [ ] Can provision pipelines via API with config validation
- [ ] Can teardown pipelines without destroying repositories
- [ ] Real-time monitoring shows current pipeline status
- [ ] VPS Manager can communicate with CCM via REST API
- [ ] Pipeline registry persists across restarts

✅ **Performance Requirements**:
- [ ] Pipeline stats available within 5 seconds
- [ ] Dashboard updates every 10-30 seconds
- [ ] API endpoints respond in <1 second
- [ ] Registry handles 100+ pipelines efficiently

✅ **Reliability Requirements**:
- [ ] Graceful handling of GitHub API failures
- [ ] Pipeline state remains consistent across errors
- [ ] Automatic backup of registry state
- [ ] Clear logging of all provisioning/teardown operations

✅ **Documentation Requirements**:
- [ ] API endpoint documentation with examples
- [ ] Integration guide for VPS Manager
- [ ] Monitor dashboard user guide
- [ ] Troubleshooting guide for common issues

---

## Open Questions

1. **API Hosting**: Should CCM run as standalone daemon or within VPS Manager?
2. **Scaling**: How many pipelines before caching/optimization needed?
3. **Notifications**: What pipeline events should trigger alerts (failures, long runs, etc.)?
4. **Workflow Templates**: Should CCM provide default workflow templates for common patterns?
5. **Multi-VPS Support**: Should CCM support linking pipelines to multiple VPS instances?

---

## Next Steps

1. Review and validate this Stage 2 plan
2. Identify any missing requirements or clarifications needed
3. Begin Phase 1 implementation (Core Pipeline Management)
4. Create API specifications document
5. Setup CCM as REST service with authentication
