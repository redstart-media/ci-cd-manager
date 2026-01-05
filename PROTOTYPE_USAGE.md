# CI/CD Manager - Prototype Usage Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install paramiko rich requests pyyaml
```

### 2. Set Environment Variables
```bash
export GHT="your_github_token_here"
export VPS_HOST="23.29.114.83"
export VPS_USER="beinejd"
export VPS_PORT="2223"
export CCM_CONFIG="$HOME/.ccm/projects.json"
export CCM_DRY_RUN="false"  # Set to "true" for dry-run mode
```

### 3. Run the Manager
```bash
./ci-cd-manager.py
```

This will open an interactive menu.

---

## Features in This Prototype

### 1. Secrets Management
- **List secrets**: View all secrets in a repository
- **Create/Update secrets**: Add or modify GitHub Actions secrets
- **Delete secrets**: Remove secrets from a repository
- **Replicate secrets**: Copy secrets from source to destination repository with optional transformations

### 2. Projects Management
- **List projects**: View all configured projects
- **Create project**: Add a new project with GitHub and VPS configuration
- **View project**: Display project details
- **Delete project**: Remove a project configuration

### 3. Secret Replication
- Replicate secrets from one repository to another
- Apply project-specific transformations
- Support for bulk operations across repositories

### 4. VPS Management
- **Check VPS status**: View CPU, memory, disk usage, and NGINX status
- **Setup deployment environment**: Create necessary directories on VPS
- **Execute commands**: Run arbitrary commands on the VPS

### 5. Validation & Diagnostics
- **Validate setup**: Check GitHub API and VPS connectivity
- **Check connectivity**: Test connection to all services
- **Connection diagnostics**: Verify all integrations are working

---

## Configuration File Format

Configuration is stored in `~/.ccm/projects.json` (or `$CCM_CONFIG`):

```json
{
  "projects": {
    "project-name": {
      "github": {
        "owner": "github-owner",
        "repo": "repository-name"
      },
      "vps": {
        "app_name": "app-name",
        "app_path": "/path/to/app",
        "port": 3000
      },
      "secrets": {
        "VPS_HOST": "your-vps-ip",
        "VPS_USER": "ssh-username",
        "VPS_SSH_KEY": "VPS_SSH_KEY",
        "VPS_PORT": "2223",
        "VPS_APP_PATH": "/path/to/app"
      },
      "environments": {
        "production": {
          "branch": "main",
          "vps_host": "your-vps-ip",
          "deployment_script": "deploy.sh"
        }
      }
    }
  }
}
```

See `projects-example.json` for a complete example.

---

## Key Components

### GitHubSecretsManager
Handles all GitHub API interactions for secrets management.

**Methods**:
- `verify_credentials()`: Check if token is valid
- `list_secrets(owner, repo)`: List all secrets in a repo
- `create_secret(owner, repo, secret_name, secret_value)`: Create/update a secret
- `delete_secret(owner, repo, secret_name)`: Delete a secret

### ProjectConfiguration
Manages local project configuration.

**Methods**:
- `list_projects()`: Get all project names
- `get_project(project_name)`: Get project config
- `create_project(...)`: Add new project
- `delete_project(project_name)`: Remove project
- `get_secrets_mapping(project_name)`: Get secret mappings

### SecretReplicator
Handles intelligent secret replication between repositories.

**Methods**:
- `replicate_secrets(...)`: Copy secrets between repos
- `_apply_transformation(...)`: Transform secret values

### CICDPipelineManager
Manages VPS operations via SSH.

**Methods**:
- `connect()`: Establish SSH connection
- `execute(command, use_sudo)`: Run command on VPS
- `setup_deployment_environment(...)`: Setup app directories
- `get_vps_status()`: Get system metrics

### RepositoryManager
Interact with GitHub repositories.

**Methods**:
- `list_repositories(owner)`: List owner's repos
- `get_repository(owner, repo)`: Get repo details
- `list_branches(owner, repo)`: List repo branches

---

## Typical Workflows

### Workflow 1: Create New Project
1. Run `./ci-cd-manager.py`
2. Choose "Manage Projects" → "Create project"
3. Enter project details (GitHub owner/repo, VPS app path, etc.)

### Workflow 2: Replicate Secrets Between Repos
1. Run `./ci-cd-manager.py`
2. Choose "Replicate Secrets"
3. Enter source repository (redstart-media/topengineer.us)
4. Enter destination repository (redstart-media/new-repo)
5. Select project for transformations (optional)
6. Manager will replicate all secrets with transformations applied

### Workflow 3: Setup VPS for New Project
1. Run `./ci-cd-manager.py`
2. Choose "VPS Management" → "Setup deployment environment"
3. Enter app name and path
4. Manager will create directories and set permissions

### Workflow 4: Validate Everything Works
1. Run `./ci-cd-manager.py`
2. Choose "Validate Setup"
3. Manager checks GitHub API, VPS SSH, and project configuration
4. Review results to identify any issues

---

## Dry-Run Mode

To preview operations without making changes, set environment variable:
```bash
export CCM_DRY_RUN="true"
./ci-cd-manager.py
```

All operations will show what would happen without executing them.

---

## Logging

Logs are stored in `~/.ccm/logs/`:
- Each operation creates a log file
- Useful for auditing and debugging
- Contains timestamps and operation details

---

## API Integration Points

### GitHub API
- **Base URL**: `https://api.github.com`
- **Authentication**: Bearer token (from `$GHT`)
- **Endpoints Used**:
  - `GET /repos/{owner}/{repo}/actions/secrets` - List secrets
  - `PUT /repos/{owner}/{repo}/actions/secrets/{secret_name}` - Create/update
  - `DELETE /repos/{owner}/{repo}/actions/secrets/{secret_name}` - Delete
  - `GET /users/{owner}/repos` - List repositories
  - `GET /repos/{owner}/{repo}` - Get repo details

### VPS SSH
- **Host**: From `$VPS_HOST`
- **Port**: From `$VPS_PORT`
- **Username**: From `$VPS_USER`
- **Auth**: SSH keys (passwordless SSH)

---

## Security Notes

1. **Token Management**:
   - GitHub token stored in `$GHT` environment variable
   - Never commit tokens to version control
   - Use personal access tokens with minimal required scopes

2. **Secrets Encryption**:
   - GitHub API encrypts secrets server-side
   - Secrets are never logged or displayed in plaintext
   - Use password input prompts when entering secrets

3. **SSH Key Security**:
   - Leverages existing passwordless SSH setup
   - Private keys remain on local machine
   - Use SSH agent for key management

4. **Dry-Run Mode**:
   - Preview all operations before execution
   - Identify issues without making changes
   - Useful for validation and testing

---

## Troubleshooting

### GitHub API Authentication Fails
- Check `$GHT` is set to valid token
- Verify token has required scopes (repo, workflow)
- Test with `curl -H "Authorization: token $GHT" https://api.github.com/user`

### VPS SSH Connection Fails
- Verify SSH is running: `ssh -p 2223 beinejd@23.29.114.83`
- Check SSH key is in `~/.ssh/` and has correct permissions
- Ensure VPS IP and port are correct in environment variables

### Projects Configuration Not Found
- Check `$CCM_CONFIG` path exists or create with CLI
- Ensure directory `~/.ccm/` has write permissions
- See `projects-example.json` for configuration format

### Secret Replication Fails
- Verify source and destination repositories exist
- Check GitHub token has repo access for both repos
- Ensure secret names follow GitHub naming conventions (alphanumeric, underscore)

---

## Next Steps

This prototype provides the foundation for:
1. **Advanced secret management** with encryption and rotation
2. **Workflow orchestration** across GitHub and VPS
3. **Deployment automation** with rollback support
4. **Multi-environment support** (staging, production, etc.)
5. **Monitoring and alerting** for failed deployments
6. **Audit trails** for compliance and security

See `ccm-design-plan.md` for the full architecture and future enhancements.
