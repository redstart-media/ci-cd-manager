# CCM API Integration Guide

**Stage 2: VPS Manager ↔ CCM Communication Protocol**

---

## Overview

This guide documents how VPS Manager integrates with CCM to provision and manage CI/CD pipelines. The integration follows a request-response pattern with token-based authentication.

---

## API Endpoints

### 1. Provision Pipeline

**Endpoint**: `POST /api/pipelines/provision`

**Purpose**: VPS Manager requests CCM to provision a new CI/CD pipeline for a repository.

**Authentication**: `CCM-Token` header

**Request Format**:
```json
POST /api/pipelines/provision HTTP/1.1
Host: ccm-server:5000
CCM-Token: ccm_token_here
Content-Type: application/json

{
  "repo": "owner/repository-name",
  "workflow_file": ".github/workflows/deploy.yml",
  "config": {
    "trigger_branches": ["production", "main"],
    "environment": "production",
    "auto_deploy": true,
    "notifications_enabled": true
  },
  "linked_domain": "example.com",
  "linked_app": "my-app"
}
```

**Response** (Success - 201):
```json
{
  "success": true,
  "pipeline_id": "pipe_abc123def456xyz",
  "status": "active",
  "created_at": "2026-01-05T10:30:00Z",
  "repository": "owner/repository-name"
}
```

**Response** (Error - 400):
```json
{
  "success": false,
  "error": "Missing required fields: repo, workflow_file"
}
```

**Curl Example**:
```bash
curl -X POST http://localhost:5000/api/pipelines/provision \
  -H "CCM-Token: ccm_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "repo": "myorg/myrepo",
    "workflow_file": ".github/workflows/deploy.yml",
    "linked_domain": "example.com",
    "linked_app": "example-app"
  }'
```

---

### 2. Get Pipeline Stats

**Endpoint**: `GET /api/pipelines/<pipeline_id>/stats`

**Purpose**: Get real-time pipeline statistics and health metrics.

**Authentication**: `CCM-Token` header

**Response** (200):
```json
{
  "success": true,
  "stats": {
    "pipeline_id": "pipe_abc123def456xyz",
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
}
```

**Curl Example**:
```bash
curl -X GET http://localhost:5000/api/pipelines/pipe_abc123def456xyz/stats \
  -H "CCM-Token: ccm_token_here"
```

---

### 3. List Pipelines

**Endpoint**: `GET /api/pipelines`

**Purpose**: List all provisioned pipelines.

**Authentication**: `CCM-Token` header

**Response** (200):
```json
{
  "success": true,
  "pipelines": [
    {
      "pipeline_id": "pipe_abc123def456xyz",
      "repository": "owner/repo-one",
      "status": "active",
      "created_at": "2026-01-05T10:30:00Z",
      "vps_integration": {
        "linked_domain": "example.com",
        "linked_app": "example-app"
      }
    },
    {
      "pipeline_id": "pipe_def456ghi789xyz",
      "repository": "owner/repo-two",
      "status": "active",
      "created_at": "2026-01-04T14:15:00Z",
      "vps_integration": {
        "linked_domain": "example2.com",
        "linked_app": "example2-app"
      }
    }
  ],
  "count": 2
}
```

**Curl Example**:
```bash
curl -X GET http://localhost:5000/api/pipelines \
  -H "CCM-Token: ccm_token_here"
```

---

### 4. Teardown Pipeline

**Endpoint**: `DELETE /api/pipelines/<pipeline_id>`

**Purpose**: Deactivate a pipeline without destroying the repository.

**Authentication**: `CCM-Token` header

**Query Parameters**:
- `preserve_repo` (bool, default=true): Whether to preserve the repository

**Request**:
```bash
DELETE /api/pipelines/pipe_abc123def456xyz?preserve_repo=true HTTP/1.1
Host: ccm-server:5000
CCM-Token: ccm_token_here
```

**Response** (200):
```json
{
  "success": true,
  "pipeline_id": "pipe_abc123def456xyz",
  "message": "Pipeline deactivated, repository preserved"
}
```

**Curl Example**:
```bash
curl -X DELETE http://localhost:5000/api/pipelines/pipe_abc123def456xyz \
  -H "CCM-Token: ccm_token_here"
```

---

## VPS Manager Integration Flow

### Scenario 1: Deploying a New Application

```
VPS Manager                          CCM                    GitHub
    │                                │                         │
    ├─ User deploys new app
    │
    ├─ Setup app directory
    │
    ├─ Configure domain (NGINX)
    │
    ├─ POST /api/pipelines/provision
    │  ├─ repo: "user/my-app"
    │  ├─ workflow: ".github/workflows/deploy.yml"
    │  ├─ domain: "myapp.com"
    │  └─ app: "my-app"
    │                                │
    │                                ├─ Validate repo access ──→│
    │                                │                          │
    │                                │←─ Repo valid ────────────┤
    │                                │
    │                                ├─ Generate pipeline ID
    │                                ├─ Save to registry
    │                                └─ Start monitoring
    │                                │
    │←─ pipeline_id: "pipe_xyz..."──┤
    │
    └─ Store pipeline_id with app metadata
       Pipeline now monitored in real-time
```

### Scenario 2: Removing an Application

```
VPS Manager                          CCM                    GitHub
    │                                │                         │
    ├─ User removes app
    │
    ├─ Stop services
    │
    ├─ DELETE /api/pipelines/<id>
    │  └─ preserve_repo=true
    │                                │
    │                                ├─ Find pipeline
    │                                ├─ Mark as "inactive"
    │                                ├─ Cancel active runs ────→│
    │                                │                          │
    │                                │←─ Runs cancelled─────────┤
    │                                │
    │                                └─ Update registry
    │                                │
    │←─ success: true ───────────────┤
    │
    └─ Complete app removal
       Repo preserved on GitHub
       Can be re-provisioned later
```

### Scenario 3: Checking Application Health

```
VPS Manager                          CCM                    GitHub
    │                                │                         │
    ├─ Monitor application health
    │
    ├─ GET /api/pipelines/<id>/stats
    │                                │
    │                                ├─ Fetch recent runs ────→│
    │                                │                          │
    │                                │←─ Workflow data──────────┤
    │                                │
    │                                ├─ Calculate health score
    │                                └─ Compile metrics
    │                                │
    │←─ stats (health, duration, success_rate)
    │
    └─ Display in monitoring dashboard
       Alert if health score drops
```

---

## Python Integration Example

### Simple VPS Manager Integration

```python
import requests
import json
from typing import Optional, Dict

class CCMClient:
    """Simple Python client for CCM API"""
    
    def __init__(self, ccm_host: str, ccm_token: str):
        self.base_url = f"http://{ccm_host}:5000/api"
        self.token = ccm_token
        self.headers = {
            "CCM-Token": ccm_token,
            "Content-Type": "application/json"
        }
    
    def provision_pipeline(self, repo: str, workflow_file: str,
                          domain: Optional[str] = None,
                          app_name: Optional[str] = None) -> Optional[str]:
        """Provision a new pipeline"""
        try:
            response = requests.post(
                f"{self.base_url}/pipelines/provision",
                headers=self.headers,
                json={
                    "repo": repo,
                    "workflow_file": workflow_file,
                    "linked_domain": domain,
                    "linked_app": app_name,
                    "config": {
                        "trigger_branches": ["production"],
                        "environment": "production",
                        "auto_deploy": True
                    }
                },
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                if data.get('success'):
                    return data.get('pipeline_id')
            
            return None
        except Exception as e:
            print(f"Error provisioning pipeline: {e}")
            return None
    
    def teardown_pipeline(self, pipeline_id: str) -> bool:
        """Teardown a pipeline"""
        try:
            response = requests.delete(
                f"{self.base_url}/pipelines/{pipeline_id}",
                headers=self.headers,
                params={"preserve_repo": "true"},
                timeout=10
            )
            
            return response.status_code == 200 and response.json().get('success')
        except Exception as e:
            print(f"Error tearing down pipeline: {e}")
            return False
    
    def get_pipeline_stats(self, pipeline_id: str) -> Optional[Dict]:
        """Get pipeline statistics"""
        try:
            response = requests.get(
                f"{self.base_url}/pipelines/{pipeline_id}/stats",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data.get('stats')
            
            return None
        except Exception as e:
            print(f"Error getting pipeline stats: {e}")
            return None
    
    def list_pipelines(self) -> Optional[list]:
        """List all pipelines"""
        try:
            response = requests.get(
                f"{self.base_url}/pipelines",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data.get('pipelines', [])
            
            return None
        except Exception as e:
            print(f"Error listing pipelines: {e}")
            return None


if __name__ == "__main__":
    ccm = CCMClient("localhost", "ccm_token_here")
    
    pipeline_id = ccm.provision_pipeline(
        repo="myuser/myapp",
        workflow_file=".github/workflows/deploy.yml",
        domain="myapp.com",
        app_name="myapp"
    )
    
    if pipeline_id:
        print(f"Pipeline provisioned: {pipeline_id}")
        
        stats = ccm.get_pipeline_stats(pipeline_id)
        if stats:
            print(f"Health score: {stats['health_score']}")
            print(f"Success rate: {stats['metrics_24h']['success_rate']:.1f}%")
```

---

## Bash Integration Example

### Script for Provisioning Pipeline from VPS

```bash
#!/bin/bash

CCM_HOST="${CCM_HOST:-localhost:5000}"
CCM_TOKEN="${CCM_TOKEN:-ccm_token_here}"

REPO="$1"
DOMAIN="$2"
APP_NAME="$3"

if [ -z "$REPO" ] || [ -z "$DOMAIN" ]; then
    echo "Usage: $0 <repo> <domain> [app_name]"
    exit 1
fi

RESPONSE=$(curl -s -X POST "http://${CCM_HOST}/api/pipelines/provision" \
  -H "CCM-Token: ${CCM_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"repo\": \"${REPO}\",
    \"workflow_file\": \".github/workflows/deploy.yml\",
    \"linked_domain\": \"${DOMAIN}\",
    \"linked_app\": \"${APP_NAME}\"
  }")

PIPELINE_ID=$(echo "$RESPONSE" | jq -r '.pipeline_id')

if [ -n "$PIPELINE_ID" ] && [ "$PIPELINE_ID" != "null" ]; then
    echo "✓ Pipeline provisioned: $PIPELINE_ID"
    echo "  Domain: $DOMAIN"
    echo "  App: ${APP_NAME:-N/A}"
else
    echo "✗ Failed to provision pipeline"
    echo "$RESPONSE"
    exit 1
fi
```

---

## Setup Instructions

### 1. Configure CCM

Set environment variables:
```bash
export GHT="your_github_token"
export CCM_API_TOKEN="your_secure_ccm_token"
export VPS_HOST="your_vps_ip"
export VPS_USER="your_vps_user"
export VPS_PORT="your_vps_ssh_port"
```

### 2. Start CCM as Service

```bash
nohup python3 /path/to/ci-cd-manager.py > /var/log/ccm.log 2>&1 &
```

Or with systemd:
```ini
[Unit]
Description=CI/CD Manager
After=network.target

[Service]
Type=simple
User=deployer
ExecStart=/usr/bin/python3 /path/to/ci-cd-manager.py
Restart=on-failure
RestartSec=10
Environment="GHT=your_github_token"
Environment="CCM_API_TOKEN=your_secure_ccm_token"

[Install]
WantedBy=multi-user.target
```

### 3. From VPS Manager

```bash
source /path/to/setup_ccm_integration.sh
ccm_provision_pipeline "owner/repo" "example.com" "app-name"
```

---

## Error Handling

### Common Errors

**401 Unauthorized**:
```json
{
  "success": false,
  "error": "Invalid CCM-Token"
}
```
→ Check `CCM_API_TOKEN` environment variable

**404 Not Found**:
```json
{
  "success": false,
  "error": "Pipeline not found: pipe_invalid_id"
}
```
→ Verify pipeline ID exists in CCM registry

**400 Bad Request**:
```json
{
  "success": false,
  "error": "Missing required fields: repo, workflow_file"
}
```
→ Check request payload includes all required fields

### Retry Strategy

Implement exponential backoff:
```python
import time

def call_ccm_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                raise
```

---

## Security Considerations

### 1. Token Management
- Store `CCM_API_TOKEN` securely (e.g., in `.env` or secrets manager)
- Rotate tokens regularly
- Use different tokens for different environments (dev/staging/prod)

### 2. Network Security
- Run CCM on internal network (not exposed to internet)
- Use VPN or SSH tunnel for remote VPS connections
- Implement rate limiting on API endpoints
- Add IP whitelisting if possible

### 3. Data Protection
- All GitHub tokens are environment variables (never committed)
- Pipeline registry stored with restricted file permissions
- Audit logs for all provision/teardown operations

---

## Monitoring & Troubleshooting

### Check Pipeline Health

```bash
curl -H "CCM-Token: $CCM_API_TOKEN" \
  http://localhost:5000/api/pipelines/pipe_xyz/stats | jq '.stats'
```

### View Recent Errors

```bash
tail -f /home/user/.ccm/logs/*.log
```

### Registry Backup

```bash
cp ~/.ccm/pipelines.json ~/.ccm/backups/pipelines-backup.json
```

---

## Next Steps

1. Run CCM in CI/CD mode (background service)
2. Configure VPS Manager to call CCM API during deployment
3. Set up monitoring dashboard for real-time pipeline visibility
4. Implement alerts for pipeline failures
5. Create automation scripts for common workflows
