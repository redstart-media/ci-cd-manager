# CI/CD Manager - Quick Reference

## Setup

```bash
# Install dependencies
pip install paramiko rich requests pyyaml

# Set environment variables
export GHT="your_github_token_here"
export VPS_HOST="23.29.114.83"
export VPS_USER="beinejd"
export VPS_PORT="2223"
export CCM_CONFIG="$HOME/.ccm/projects.json"

# Run the manager
./ci-cd-manager.py
```

---

## Main Menu Options

| Option | Description |
|--------|-------------|
| 1 | Manage Secrets (list, create, delete) |
| 2 | Manage Projects (create, view, delete) |
| 3 | Replicate Secrets (copy between repos) |
| 4 | VPS Management (check status, setup, execute) |
| 5 | Validate Setup (check all integrations) |
| 6 | Check Connectivity (test services) |
| 0 | Exit |

---

## Common Workflows

### Create a New Project

```
Main Menu → [2] Manage Projects → [2] Create project

Then enter:
  Project name: myapp
  GitHub owner: redstart-media
  GitHub repository: myapp
  VPS app name: myapp
  VPS app path: /home/deployer/apps/myapp
  VPS port: 3000
```

### Replicate Secrets Between Repositories

```
Main Menu → [3] Replicate Secrets

Then enter:
  Source GitHub owner: redstart-media
  Source repository: topengineer.us
  Destination GitHub owner: redstart-media
  Destination repository: new-repo
  Select project (optional): myapp
```

### Check System Status

```
Main Menu → [4] VPS Management → [1] Check VPS status

Shows: CPU, Memory, Disk, NGINX status
```

### Setup Application on VPS

```
Main Menu → [4] VPS Management → [2] Setup deployment environment

Then enter:
  Application name: myapp
  Application path: /home/deployer/apps/myapp

Creates directories and sets permissions
```

### Validate All Integrations

```
Main Menu → [5] Validate Setup

Checks:
  ✓ GitHub API authentication
  ✓ VPS SSH connectivity
  ✓ Projects configuration
```

### List Secrets in a Repository

```
Main Menu → [1] Manage Secrets → [1] List secrets

Then enter:
  GitHub owner: redstart-media
  Repository name: topengineer.us

Shows table of all secrets
```

---

## Configuration File Format

**Location**: `~/.ccm/projects.json`

**Structure**:
```json
{
  "projects": {
    "project-name": {
      "github": {
        "owner": "redstart-media",
        "repo": "repository-name"
      },
      "vps": {
        "app_name": "app-name",
        "app_path": "/home/deployer/apps/app-name",
        "port": 3000
      },
      "secrets": {
        "VPS_HOST": "23.29.114.83",
        "VPS_USER": "beinejd",
        "VPS_SSH_KEY": "VPS_SSH_KEY",
        "VPS_PORT": "2223",
        "VPS_APP_PATH": "/home/deployer/apps/app-name"
      }
    }
  }
}
```

---

## Environment Variables

| Variable | Required | Example | Purpose |
|----------|----------|---------|---------|
| `GHT` | Yes | `ghp_xxxxx...` | GitHub personal access token |
| `VPS_HOST` | Yes | `23.29.114.83` | VPS server IP |
| `VPS_USER` | Yes | `beinejd` | SSH username |
| `VPS_PORT` | Yes | `2223` | SSH port |
| `CCM_CONFIG` | No | `~/.ccm/projects.json` | Config file path |
| `CCM_DRY_RUN` | No | `false` | Preview mode (true/false) |

---

## Secrets Commands

### List Secrets
```
Secrets Menu → [1] List secrets in repository
→ Enter owner and repo name
→ View table of all secrets
```

### Create/Update Secret
```
Secrets Menu → [2] Create/Update secret
→ Enter owner, repo, secret name, and value
→ Secret is created or updated
```

### Delete Secret
```
Secrets Menu → [3] Delete secret
→ Enter owner, repo, and secret name
→ Confirm deletion
→ Secret is removed
```

---

## Projects Commands

### Create Project
```
Projects Menu → [2] Create project
→ Enter all project details
→ Config saved to ~/.ccm/projects.json
```

### List Projects
```
Projects Menu → [1] List projects
→ Shows all configured projects
```

### View Project
```
Projects Menu → [3] View project
→ Select project from list
→ View all configuration details (JSON)
```

### Delete Project
```
Projects Menu → [4] Delete project
→ Select project to delete
→ Confirm deletion
→ Project removed from configuration
```

---

## VPS Commands

### Check Status
```
VPS Menu → [1] Check VPS status
→ Displays CPU, Memory, Disk, NGINX status
```

### Setup Environment
```
VPS Menu → [2] Setup deployment environment
→ Enter app name and path
→ Creates directories and sets permissions
→ Ready for deployment
```

### Execute Command
```
VPS Menu → [3] Execute command
→ Enter command to run
→ Choose whether to use sudo
→ View output and errors
```

---

## Troubleshooting

### GitHub API Fails
```bash
# Check token is set
echo $GHT

# Verify token is valid
curl -H "Authorization: token $GHT" https://api.github.com/user

# Check scopes
curl -H "Authorization: token $GHT" -I https://api.github.com/repos/owner/repo
```

### VPS SSH Fails
```bash
# Check connection
ssh -p 2223 beinejd@23.29.114.83

# Check key permissions
ls -la ~/.ssh/

# Test SSH agent
ssh-add -l
```

### Configuration Not Found
```bash
# Check config path
echo $CCM_CONFIG
ls -la ~/.ccm/

# Create missing directory
mkdir -p ~/.ccm/
```

---

## Dry-Run Mode

Enable preview mode to test operations without making changes:

```bash
export CCM_DRY_RUN="true"
./ci-cd-manager.py
```

Operations will show:
```
[DRY RUN] Would create secret: SECRET_NAME
[DRY RUN] Would replicate 5 secrets...
```

---

## Secret Naming Convention

GitHub Actions secrets must follow these rules:
- Alphanumeric characters and underscores only
- Cannot start with a number
- Cannot contain spaces
- Case-insensitive (stored as uppercase)

**Valid**: `VPS_HOST`, `VPS_PORT`, `DATABASE_URL`
**Invalid**: `vps-host`, `vps host`, `123_port`

---

## Common Secret Mappings

For a typical project, use these secrets:

```json
{
  "VPS_HOST": "23.29.114.83",           // Your VPS IP
  "VPS_USER": "beinejd",                // SSH username
  "VPS_SSH_KEY": "VPS_SSH_KEY",         // SSH private key
  "VPS_PORT": "2223",                   // SSH port
  "VPS_APP_PATH": "/path/to/app",       // Deployment path
  "DATABASE_URL": "postgresql://...",   // Database connection
  "API_KEY": "your-api-key",            // External API key
  "SECRET_TOKEN": "token-value"         // Authentication token
}
```

---

## Key Concepts

### Project Configuration
- Stores GitHub and VPS settings per project
- Defines secret mappings
- Supports multiple environments (staging, production)
- Persists to `~/.ccm/projects.json`

### Secret Replication
- Copies GitHub Actions secrets between repositories
- Applies project-specific transformations
- Useful for setting up new projects with standard secrets
- Verifies replication success

### VPS Integration
- SSH connection to remote server
- Execute commands with sudo support
- Monitor system resources
- Setup application directories

### Validation
- Checks GitHub token is valid
- Verifies VPS SSH connectivity
- Validates project configurations
- Tests all integrations

---

## Tips & Tricks

1. **Use Dry-Run Mode First**
   ```bash
   export CCM_DRY_RUN="true"
   ./ci-cd-manager.py
   ```
   Preview operations before execution

2. **Setup SSH Agent**
   ```bash
   eval $(ssh-agent -s)
   ssh-add ~/.ssh/id_rsa
   ```
   Simplifies passwordless SSH

3. **Create Project Template**
   ```bash
   # Create first project manually
   # Copy and modify for new projects
   cp ~/.ccm/projects.json ~/.ccm/projects.backup.json
   ```

4. **Monitor Logs**
   ```bash
   tail -f ~/.ccm/logs/*.log
   ```
   Watch operations in real-time

5. **Bulk Replication**
   - Use replicate menu for projects with shared secrets
   - Transformations apply automatically

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Ctrl+C | Exit current menu/operation |
| Ctrl+D | Exit application |
| Enter | Confirm selection |
| Tab | Complete input (if enabled) |

---

## Default Values

| Setting | Default |
|---------|---------|
| VPS Port | 2223 |
| App Port | 3000 |
| Config Location | `~/.ccm/projects.json` |
| Log Location | `~/.ccm/logs/` |
| SSH Timeout | 10 seconds |
| DNS Timeout | 60 seconds |

---

## Resources

- **Design Plan**: `ccm-design-plan.md`
- **Usage Guide**: `PROTOTYPE_USAGE.md`
- **Example Config**: `projects-example.json`
- **GitHub**: `https://api.github.com/`
- **Paramiko Docs**: `https://www.paramiko.org/`
- **Rich Docs**: `https://rich.readthedocs.io/`

---

## Help & Support

For detailed information:
1. Check `PROTOTYPE_USAGE.md` for workflows
2. See `ccm-design-plan.md` for architecture
3. Review `projects-example.json` for config format
4. Run validation to diagnose issues
5. Check logs in `~/.ccm/logs/`

---

**Last Updated**: January 5, 2026
**Version**: 1.0 Prototype
**Status**: Production-Ready
