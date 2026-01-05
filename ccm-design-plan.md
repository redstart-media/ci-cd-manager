# CI/CD Manager Design Plan

## Project Overview

The **CI/CD Manager** (`ci-cd-manager.py`) is a robust tool for managing continuous integration and continuous deployment pipelines across GitHub repositories and VPS infrastructure. It extends the philosophy and architecture of VPS Manager to handle GitHub secrets management, CI/CD workflow orchestration, and deployment pipeline configuration.

## Design Principles

1. **Modular Architecture**: Separate concerns into distinct manager classes
2. **Environment-Based Configuration**: Use environment variables for sensitive data
3. **SSH + API Integration**: Combine local SSH (GitHub) with remote SSH (VPS) and REST API (GitHub)
4. **Rich CLI Interface**: Leverage Rich library for interactive, beautiful terminal UI
5. **Project-Centric**: Operations revolve around GitHub repositories with project-specific configurations
6. **Extensibility**: Designed to support future CI/CD providers and platforms

---

## Core Components

### 1. **GitHubSecretsManager** Class

**Purpose**: Manage GitHub Actions secrets across repositories via GitHub API

**Key Responsibilities**:
- Authenticate to GitHub API using token (`$GHT` environment variable)
- List secrets in a repository
- Get encrypted secret values from source repository
- Create/update secrets in destination repository
- Validate secret encryption compatibility
- Batch secret replication between repositories

**Key Methods**:
```
- __init__(token: str)
- verify_credentials() -> bool
- list_secrets(owner: str, repo: str) -> List[Dict]
- get_secret(owner: str, repo: str, secret_name: str) -> Optional[str]
- create_secret(owner: str, repo: str, secret_name: str, secret_value: str) -> bool
- update_secret(owner: str, repo: str, secret_name: str, secret_value: str) -> bool
- delete_secret(owner: str, repo: str, secret_name: str) -> bool
- replicate_secrets(source_repo: str, dest_repo: str, secret_names: List[str], transform_values: Dict = None) -> bool
- verify_secret_replication(source_repo: str, dest_repo: str, secret_names: List[str]) -> bool
```

**Configuration**:
- GitHub API Token: `$GHT` (read from environment)
- Base URL: `https://api.github.com`
- API Version: GitHub REST API v3

**API Endpoints Used**:
- `GET /repos/{owner}/{repo}/actions/secrets` - List secrets
- `GET /repos/{owner}/{repo}/actions/secrets/{secret_name}` - Get secret details
- `PUT /repos/{owner}/{repo}/actions/secrets/{secret_name}` - Create/update secret
- `DELETE /repos/{owner}/{repo}/actions/secrets/{secret_name}` - Delete secret

---

### 2. **CICDPipelineManager** Class

**Purpose**: Manage CI/CD pipeline definitions and configurations on VPS

**Key Responsibilities**:
- SSH connection to VPS (inherit patterns from VPSManager)
- Manage GitHub Actions workflow files
- Deploy and update workflow definitions
- Validate workflow YAML syntax
- Monitor workflow execution status
- Manage CI/CD environment configuration on VPS

**Key Methods**:
```
- __init__(host: str, username: str, port: int, github_manager: GitHubSecretsManager)
- connect() -> bool
- disconnect()
- execute(command: str, use_sudo: bool = False) -> Tuple[str, str, int]
- deploy_workflow(owner: str, repo: str, workflow_content: str, workflow_name: str) -> bool
- validate_workflow(workflow_content: str) -> bool
- get_workflow_status(owner: str, repo: str, workflow_name: str) -> Dict
- list_deployments(owner: str, repo: str) -> List[Dict]
- get_deployment_logs(owner: str, repo: str, deployment_id: str) -> str
- setup_deployment_environment(app_name: str, app_path: str, env_vars: Dict) -> bool
- get_vps_deployment_status(app_name: str) -> Dict
```

---

### 3. **ProjectConfiguration** Class

**Purpose**: Manage project-specific CI/CD configurations

**Key Responsibilities**:
- Load project configuration from local JSON/YAML files
- Manage multiple projects with different deployment targets
- Store project-specific secret mappings
- Define deployment environments (staging, production)
- Manage application paths and deployment scripts

**Key Methods**:
```
- __init__(config_file: str = "projects.json")
- load_project(project_name: str) -> Dict
- list_projects() -> List[str]
- get_secrets_mapping(project_name: str) -> Dict
- get_deployment_config(project_name: str, environment: str) -> Dict
- validate_project_config(project_config: Dict) -> bool
- create_project(project_name: str, config: Dict) -> bool
- update_project(project_name: str, config: Dict) -> bool
- delete_project(project_name: str) -> bool
```

**Configuration Structure**:
```json
{
  "projects": {
    "project-name": {
      "github": {
        "owner": "redstart-media",
        "repo": "project-repo"
      },
      "vps": {
        "app_name": "project-app",
        "app_path": "/home/deployer/apps/project-app",
        "port": 3000
      },
      "secrets": {
        "VPS_HOST": "VPS_HOST",
        "VPS_USER": "VPS_USER",
        "VPS_SSH_KEY": "VPS_SSH_KEY",
        "VPS_PORT": "VPS_PORT",
        "VPS_APP_PATH": "/home/deployer/apps/project-app",
        "PROJECT_SPECIFIC_SECRET": "custom_value"
      },
      "environments": {
        "production": {
          "branch": "main",
          "vps_host": "23.29.114.83",
          "deployment_script": "deploy.sh"
        },
        "staging": {
          "branch": "develop",
          "vps_host": "staging.example.com",
          "deployment_script": "deploy-staging.sh"
        }
      }
    }
  }
}
```

---

### 4. **RepositoryManager** Class

**Purpose**: Manage repository operations and sync with GitHub

**Key Responsibilities**:
- List repositories for an organization
- Get repository details and metadata
- Clone repositories locally for inspection
- Get branch information
- Get workflow runs and their status
- Manage repository collaborators

**Key Methods**:
```
- __init__(token: str)
- list_repositories(owner: str, per_page: int = 100) -> List[Dict]
- get_repository(owner: str, repo: str) -> Dict
- list_branches(owner: str, repo: str) -> List[Dict]
- get_latest_release(owner: str, repo: str) -> Optional[Dict]
- list_workflow_runs(owner: str, repo: str, workflow_name: str = None) -> List[Dict]
- get_workflow_run_details(owner: str, repo: str, run_id: int) -> Dict
- get_workflow_run_logs(owner: str, repo: str, run_id: int) -> str
- trigger_workflow(owner: str, repo: str, workflow_file: str, inputs: Dict = None) -> bool
```

---

### 5. **SecretReplicator** Class

**Purpose**: Handle intelligent secret replication with transformations

**Key Responsibilities**:
- Replicate secrets from source to destination repositories
- Apply project-specific transformations to secret values
- Handle secret value encryption/decryption
- Validate secrets after replication
- Support bulk operations
- Track replication history

**Key Methods**:
```
- __init__(github_manager: GitHubSecretsManager)
- replicate_with_transform(source_repo: str, dest_repo: str, secret_mappings: Dict, transforms: Dict = None) -> bool
- apply_transformation(secret_name: str, secret_value: str, transform_config: Dict) -> str
- bulk_replicate(source_repo: str, dest_repos: List[str], secret_names: List[str]) -> Dict[str, bool]
- verify_replication(source_repo: str, dest_repo: str, secret_names: List[str]) -> Dict[str, bool]
- rollback_replication(source_repo: str, dest_repo: str, secret_names: List[str]) -> bool
```

**Supported Transformations**:
- `path_replacement`: Replace paths based on project config
- `prefix_override`: Override secret with project-specific prefix
- `computed`: Calculate secret value based on project config
- `environment_mapping`: Map environment-specific values

---

## Workflows & Use Cases

### Use Case 1: Initialize New Repository with Secrets

1. User creates new GitHub repository
2. User adds repository to project configuration
3. CI/CD Manager replicates core secrets from template repository
4. Manager applies project-specific transformations (app path, port, etc.)
5. Manager verifies secrets are properly encrypted in destination repo

**Command Flow**:
```
ccm init-repo [project-name] [destination-repo]
```

### Use Case 2: Bulk Secret Replication

1. User updates secrets in source repository
2. CI/CD Manager identifies all destination repositories for a project
3. Manager replicates secrets to all destinations with transformations
4. Manager verifies replication across all destinations
5. Manager logs replication history

**Command Flow**:
```
ccm replicate-secrets [source-repo] --project [project-name] --verify
```

### Use Case 3: Validate CI/CD Setup

1. Manager checks all required secrets exist in repository
2. Manager validates secrets are properly encrypted
3. Manager checks workflow files syntax
4. Manager verifies VPS deployment environment is ready
5. Manager runs test deployment workflow

**Command Flow**:
```
ccm validate [project-name] --environment [staging|production]
```

### Use Case 4: Manage Deployments

1. Manager monitors workflow runs on GitHub
2. Manager coordinates deployment steps on VPS
3. Manager tracks deployment status and logs
4. Manager handles rollback if deployment fails
5. Manager updates project status

**Command Flow**:
```
ccm deploy [project-name] --environment [staging|production]
ccm deploy-status [project-name]
ccm rollback [project-name]
```

---

## Environment Variables

**Required**:
- `GHT`: GitHub authentication token (personal access token or app token)
- `VPS_HOST`: VPS server IP address
- `VPS_USER`: VPS SSH username
- `VPS_PORT`: VPS SSH port

**Optional**:
- `GHT_ORG`: Default GitHub organization (default: from config)
- `CCM_CONFIG`: Path to projects configuration file (default: `projects.json`)
- `CCM_LOG_LEVEL`: Logging level (default: `INFO`)
- `CCM_DRY_RUN`: Enable dry-run mode (default: `false`)

---

## Configuration Files

### 1. **projects.json** (Local Configuration)
- Location: `~/.ccm/projects.json` or custom path via `$CCM_CONFIG`
- Purpose: Define all managed projects and their configurations
- Structure: Hierarchical project definitions with GitHub, VPS, and secrets mappings

### 2. **.github/workflows/** (Remote Configuration)
- Location: Repository `.github/workflows/` directory
- Purpose: CI/CD workflow definitions
- Content: YAML workflow files generated/managed by CI/CD Manager

### 3. **Workflow Execution Logs**
- Location: `~/.ccm/logs/` or cloud storage
- Purpose: Track all CI/CD operations for audit and debugging

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     CI/CD Manager CLI                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────┐  ┌────────────────────────────┐   │
│  │ ProjectConfiguration│  │ Rich Console Interface     │   │
│  │  Manager           │  │ (Interactive CLI)          │   │
│  └────────────────────┘  └────────────────────────────┘   │
│           │                          │                      │
├─────────────────────────────────────────────────────────────┤
│                   Core Managers Layer                       │
│                                                              │
│  ┌──────────────────┐ ┌──────────────────┐                │
│  │GitHubSecrets     │ │CICDPipeline      │                │
│  │Manager           │ │Manager           │                │
│  └──────────────────┘ └──────────────────┘                │
│           │                     │                           │
│  ┌──────────────────┐ ┌──────────────────┐                │
│  │RepositoryManager │ │SecretReplicator  │                │
│  └──────────────────┘ └──────────────────┘                │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                   Integration Layer                         │
│                                                              │
│  ┌────────────────────┐  ┌────────────────────────────┐   │
│  │ GitHub API         │  │ VPS SSH Connection         │   │
│  │ (REST v3)          │  │ (Paramiko)                 │   │
│  └────────────────────┘  └────────────────────────────┘   │
│           │                          │                      │
├─────────────────────────────────────────────────────────────┤
│                   External Systems                          │
│                                                              │
│  ┌────────────────────┐  ┌────────────────────────────┐   │
│  │ GitHub.com         │  │ VPS Server                 │   │
│  │ (Secrets, Workflows,   (CI/CD Deployments)        │   │
│  │  Repos, Workflows)     (Application Management)    │   │
│  └────────────────────┘  └────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Command Structure

### Secret Management
```
ccm secrets list [owner/repo]
ccm secrets show [owner/repo] [secret-name]
ccm secrets set [owner/repo] [secret-name] [value]
ccm secrets delete [owner/repo] [secret-name]
ccm secrets replicate [source-repo] [dest-repo] [--secret-names ...]
ccm secrets validate [project-name]
```

### Project Management
```
ccm project init [project-name] [owner/repo]
ccm project list
ccm project show [project-name]
ccm project config [project-name] [--set key=value ...]
ccm project delete [project-name]
```

### Repository Management
```
ccm repo list [owner]
ccm repo show [owner/repo]
ccm repo secrets-sync [owner/repo]
```

### Deployment Management
```
ccm deploy [project-name] [--environment staging|production]
ccm deploy-status [project-name]
ccm deploy-logs [project-name] [run-id]
ccm rollback [project-name]
```

### CI/CD Pipeline Management
```
ccm workflow list [project-name]
ccm workflow show [project-name] [workflow-name]
ccm workflow trigger [project-name] [workflow-name] [--input key=value ...]
ccm workflow logs [project-name] [workflow-name] [run-id]
```

### Validation & Diagnostics
```
ccm validate [project-name] [--environment staging|production]
ccm check-connectivity
ccm diagnose
```

---

## Error Handling & Validation

### GitHub API Error Handling
- Validate token authenticity before operations
- Handle rate limiting (respect X-RateLimit headers)
- Retry logic for transient failures
- Clear error messages for API errors (404, 401, 422, etc.)

### VPS Connection Error Handling
- Verify SSH connectivity before operations
- Handle connection timeouts gracefully
- Retry SSH commands with exponential backoff
- Detailed error reporting for deployment failures

### Configuration Validation
- Validate project configuration on load
- Check for required fields (GitHub repo, VPS app path, etc.)
- Validate secret names match GitHub Actions naming conventions
- Verify transformation logic before applying

### Pre-Operation Checks
- Verify GitHub token has necessary scopes
- Check VPS deployment environment is ready
- Validate all required secrets exist in source repo
- Check destination repos are writable

---

## Security Considerations

1. **Token Management**:
   - Only use environment variables (never hardcode tokens)
   - Support token rotation
   - Validate token scopes on startup

2. **Secret Encryption**:
   - GitHub API handles secret encryption
   - Never log secret values
   - Support masked output in logs

3. **SSH Key Management**:
   - Leverage existing passwordless SSH setup
   - Support SSH key from agent
   - Validate server fingerprints

4. **Audit Trail**:
   - Log all secret operations
   - Track who replicated which secrets
   - Maintain deployment history

5. **Dry-Run Mode**:
   - Preview operations before execution
   - Show what will change
   - Reversible operations

---

## Future Enhancements

1. **Multi-Provider Support**:
   - GitLab CI/CD integration
   - Bitbucket Pipelines integration
   - Jenkins integration

2. **Advanced Features**:
   - Secret rotation automation
   - Deployment approval workflows
   - Blue-green deployments
   - Canary deployments
   - A/B testing support

3. **Monitoring & Alerting**:
   - Workflow failure notifications
   - Deployment health monitoring
   - Performance metrics tracking
   - Slack/Discord integration

4. **Policy Management**:
   - Enforce secret naming conventions
   - Require approval for production deployments
   - Audit access to secrets
   - Secret expiration policies

---

## Technology Stack

- **Language**: Python 3.8+
- **SSH**: Paramiko (same as VPS Manager)
- **API**: Requests (same as VPS Manager)
- **CLI**: Rich (same as VPS Manager)
- **Config**: JSON/YAML (standard formats)
- **Logging**: Python logging module
- **Testing**: pytest

---

## Implementation Phases

### Phase 1: Core Infrastructure
1. Set up base manager classes
2. Implement GitHubSecretsManager
3. Implement ProjectConfiguration
4. Basic CLI framework

### Phase 2: GitHub Integration
1. Complete GitHub API methods
2. Implement secret replication
3. Add repository management
4. Workflow operations

### Phase 3: VPS Integration
1. Implement CICDPipelineManager
2. VPS SSH integration
3. Deployment operations
4. Log aggregation

### Phase 4: Advanced Features
1. SecretReplicator with transformations
2. Bulk operations
3. Validation & diagnostics
4. Error recovery

### Phase 5: Polish & Release
1. Comprehensive error handling
2. Full test coverage
3. Documentation
4. Release v1.0
