#!/usr/bin/env python3
"""
CI/CD Manager - GitHub Actions and VPS deployment pipeline manager
Manages GitHub secrets, CI/CD workflows, and deployment orchestration
"""

import os
import sys
import json
import time
import base64
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

try:
    import paramiko
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    from rich.text import Text
    import nacl.public
    import nacl.utils
    import nacl.encoding
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install paramiko rich requests PyNaCl")
    sys.exit(1)


# ============================================================================
# CONFIGURATION
# ============================================================================

GHT = os.environ.get('GHT', os.environ.get('GITHUB_TOKEN', ""))
VPS_HOST = os.environ.get('VPS_HOST', os.environ.get('VPS_SRV1_IP', "23.29.114.83"))
VPS_SSH_USERNAME = os.environ.get('VPS_USER', os.environ.get('VPS_SSH_USERNAME', "beinejd"))
VPS_SSH_PORT = int(os.environ.get('VPS_PORT', os.environ.get('VPS_SRV1_PORT', "2223")))
def _get_ssh_key_path():
    """Find SSH key, supporting multiple key types"""
    home = Path.home()
    possible_keys = [
        home / ".ssh" / "id_ed25519",
        home / ".ssh" / "id_rsa",
        home / ".ssh" / "id_ecdsa",
        home / ".ssh" / "id_dsa"
    ]
    for key_path in possible_keys:
        if key_path.exists():
            return str(key_path)
    return str(home / ".ssh" / "id_rsa")

VPS_SSH_KEY = os.environ.get('VPS_SSH_KEY', _get_ssh_key_path())
CCM_CONFIG_PATH = os.environ.get('CCM_CONFIG', str(Path.home() / ".ccm" / "projects.json"))
CCM_PIPELINES_PATH = os.environ.get('CCM_PIPELINES', str(Path.home() / ".ccm" / "pipelines.json"))
CCM_LOG_PATH = Path.home() / ".ccm" / "logs"
CCM_BACKUPS_PATH = Path.home() / ".ccm" / "backups"
DRY_RUN = os.environ.get('CCM_DRY_RUN', "false").lower() == "true"

# Ensure directories exist
CCM_LOG_PATH.mkdir(parents=True, exist_ok=True)
CCM_BACKUPS_PATH.mkdir(parents=True, exist_ok=True)

# Validate configuration
if not GHT:
    print("[red]Error: GitHub token not configured. Set GHT or GITHUB_TOKEN environment variable.[/red]")
    print("Configuration file: ~/.zshrc or ~/.bashrc")
    sys.exit(1)

# ============================================================================


class GitHubSecretsManager:
    """Manages GitHub Actions secrets via API"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        self.console = Console()
        
        if not token:
            self.console.print("[yellow]Warning: GitHub token not set (GHT environment variable)[/yellow]")
    
    def verify_credentials(self) -> bool:
        """Verify GitHub token is valid"""
        try:
            response = requests.get(
                f"{self.base_url}/user",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                self.console.print(f"[green]✓ Authenticated as: {user_data.get('login')}[/green]")
                return True
            else:
                self.console.print(f"[red]Authentication failed: {response.status_code}[/red]")
                return False
        except Exception as e:
            self.console.print(f"[red]Error verifying credentials: {e}[/red]")
            return False
    
    def list_secrets(self, owner: str, repo: str) -> List[Dict]:
        """List all secrets in a repository"""
        try:
            response = requests.get(
                f"{self.base_url}/repos/{owner}/{repo}/actions/secrets",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('secrets', [])
            else:
                self.console.print(f"[red]Failed to list secrets: {response.status_code}[/red]")
                return []
        except Exception as e:
            self.console.print(f"[red]Error listing secrets: {e}[/red]")
            return []
    
    def _get_repo_public_key(self, owner: str, repo: str) -> Optional[Tuple[str, str]]:
        """Get repository public key for secret encryption (returns key_id and key)"""
        try:
            response = requests.get(
                f"{self.base_url}/repos/{owner}/{repo}/actions/secrets/public-key",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('key_id'), data.get('key')
            return None
        except Exception as e:
            self.console.print(f"[red]Error getting public key: {e}[/red]")
            return None
    
    def _encrypt_secret(self, secret_value: str, public_key_str: str) -> str:
        """Encrypt secret value using repository public key"""
        try:
            public_key = nacl.public.PublicKey(public_key_str, encoder=nacl.encoding.Base64Encoder)
            encrypted = nacl.public.Box(nacl.public.PrivateKey.generate()).encrypt(
                secret_value.encode(), public_key
            )
            return base64.b64encode(encrypted.ciphertext).decode()
        except Exception as e:
            self.console.print(f"[red]Error encrypting secret: {e}[/red]")
            return ""
    
    def create_secret(self, owner: str, repo: str, secret_name: str, secret_value: str) -> bool:
        """Create or update a secret in a repository"""
        if DRY_RUN:
            self.console.print(f"[cyan][DRY RUN] Would create secret: {secret_name}[/cyan]")
            return True
        
        try:
            key_result = self._get_repo_public_key(owner, repo)
            if not key_result:
                self.console.print(f"[red]Failed to get public key for {owner}/{repo}[/red]")
                return False
            
            key_id, public_key = key_result
            encrypted_value = self._encrypt_secret(secret_value, public_key)
            
            if not encrypted_value:
                return False
            
            data = {
                "encrypted_value": encrypted_value,
                "key_id": key_id,
                "visibility": "all"
            }
            
            response = requests.put(
                f"{self.base_url}/repos/{owner}/{repo}/actions/secrets/{secret_name}",
                headers=self.headers,
                json=data,
                timeout=10
            )
            
            if response.status_code in [201, 204]:
                self.console.print(f"[green]✓ Created secret: {secret_name}[/green]")
                return True
            elif response.status_code == 422:
                self.console.print(f"[yellow]Secret {secret_name} already exists[/yellow]")
                return True
            else:
                self.console.print(f"[red]Failed to create secret: {response.status_code}[/red]")
                if response.text:
                    self.console.print(f"[red]{response.text}[/red]")
                return False
        except Exception as e:
            self.console.print(f"[red]Error creating secret: {e}[/red]")
            return False
    
    def delete_secret(self, owner: str, repo: str, secret_name: str) -> bool:
        """Delete a secret from a repository"""
        if DRY_RUN:
            self.console.print(f"[cyan][DRY RUN] Would delete secret: {secret_name}[/cyan]")
            return True
        
        try:
            response = requests.delete(
                f"{self.base_url}/repos/{owner}/{repo}/actions/secrets/{secret_name}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 204:
                self.console.print(f"[green]✓ Deleted secret: {secret_name}[/green]")
                return True
            else:
                self.console.print(f"[red]Failed to delete secret: {response.status_code}[/red]")
                return False
        except Exception as e:
            self.console.print(f"[red]Error deleting secret: {e}[/red]")
            return False


class RepositoryManager:
    """Manages GitHub repository operations"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.console = Console()
    
    def list_repositories(self, owner: str) -> List[Dict]:
        """List repositories for an owner"""
        try:
            response = requests.get(
                f"{self.base_url}/users/{owner}/repos",
                headers=self.headers,
                params={"per_page": 100},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            self.console.print(f"[red]Error listing repositories: {e}[/red]")
            return []
    
    def get_repository(self, owner: str, repo: str) -> Optional[Dict]:
        """Get repository details"""
        try:
            response = requests.get(
                f"{self.base_url}/repos/{owner}/{repo}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            self.console.print(f"[red]Error getting repository: {e}[/red]")
            return None
    
    def list_branches(self, owner: str, repo: str) -> List[Dict]:
        """List branches in a repository"""
        try:
            response = requests.get(
                f"{self.base_url}/repos/{owner}/{repo}/branches",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            self.console.print(f"[red]Error listing branches: {e}[/red]")
            return []


class SecretReplicator:
    """Handles intelligent secret replication with transformations"""
    
    def __init__(self, github_manager: GitHubSecretsManager):
        self.github = github_manager
        self.console = Console()
    
    def replicate_secrets(self, source_owner: str, source_repo: str, dest_owner: str, dest_repo: str,
                         project_name: Optional[str] = None, transforms: Optional[Dict] = None) -> bool:
        """Replicate secrets from source to destination repository"""
        
        self.console.print(f"\n[cyan]Replicating secrets from {source_owner}/{source_repo} to {dest_owner}/{dest_repo}...[/cyan]")
        
        source_secrets = self.github.list_secrets(source_owner, source_repo)
        if not source_secrets:
            self.console.print("[yellow]No secrets found in source repository[/yellow]")
            return False
        
        success_count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(f"Replicating {len(source_secrets)} secrets...", total=len(source_secrets))
            
            for secret in source_secrets:
                secret_name = secret['name']
                
                transformed_value = self._apply_transformation(secret_name, None, transforms)
                
                if self.github.create_secret(dest_owner, dest_repo, secret_name, transformed_value or secret_name):
                    success_count += 1
                
                progress.advance(task)
        
        self.console.print(f"[green]✓ Successfully replicated {success_count}/{len(source_secrets)} secrets[/green]")
        return success_count == len(source_secrets)
    
    def _apply_transformation(self, secret_name: str, project: Optional[Dict], 
                             transforms: Optional[Dict]) -> Optional[str]:
        """Apply transformations to secret values"""
        if not project:
            return None
        
        secrets_mapping = project.get('secrets', {})
        
        if secret_name in secrets_mapping:
            mapped_value = secrets_mapping[secret_name]
            if transforms and secret_name in transforms:
                return transforms[secret_name]
            return mapped_value
        
        return None


class GitHubRepositoryDiscovery:
    """Discover CI/CD-enabled repositories on GitHub"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.console = Console()
    
    def get_user_repositories(self) -> List[Dict]:
        """Get all repositories for authenticated user"""
        try:
            response = requests.get(
                f"{self.base_url}/user/repos?per_page=100&type=owner",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            self.console.print(f"[red]Error fetching repositories: {e}[/red]")
            return []
    
    def get_repo_workflows(self, owner: str, repo: str) -> List[Dict]:
        """Get GitHub Actions workflows in a repository"""
        try:
            response = requests.get(
                f"{self.base_url}/repos/{owner}/{repo}/actions/workflows",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get('workflows', [])
            return []
        except Exception as e:
            return []
    
    def get_workflow_file(self, owner: str, repo: str, workflow_id: str) -> Optional[str]:
        """Get the file path of a workflow"""
        try:
            response = requests.get(
                f"{self.base_url}/repos/{owner}/{repo}/actions/workflows/{workflow_id}",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get('path')
            return None
        except Exception as e:
            return None
    
    def find_deploy_workflows(self) -> List[Dict]:
        """Find all repositories with deploy-related workflows"""
        deploy_repos = []
        
        self.console.print("[cyan]Searching GitHub for deploy workflows...[/cyan]")
        repos = self.get_user_repositories()
        
        for repo in repos:
            owner = repo['owner']['login']
            repo_name = repo['name']
            workflows = self.get_repo_workflows(owner, repo_name)
            
            for workflow in workflows:
                workflow_name = workflow['name'].lower()
                if any(term in workflow_name for term in ['deploy', 'release', 'cd', 'production']):
                    workflow_path = self.get_workflow_file(owner, repo_name, workflow['id'])
                    deploy_repos.append({
                        'owner': owner,
                        'repo': repo_name,
                        'full_repo': f"{owner}/{repo_name}",
                        'workflow_name': workflow['name'],
                        'workflow_path': workflow_path or workflow['path'],
                        'workflow_id': workflow['id'],
                        'git_url': repo['clone_url'],
                        'html_url': repo['html_url']
                    })
        
        return deploy_repos


class RealtimePipelineDetector:
    """Real-time pipeline detection by querying VPS and GitHub"""
    
    def __init__(self, vps_discovery: 'ServerDiscovery', github_discovery: 'GitHubRepositoryDiscovery'):
        self.vps_discovery = vps_discovery
        self.github_discovery = github_discovery
        self.console = Console()
    
    def detect_pipelines(self, verbose: bool = False) -> Tuple[List[Dict], List[Dict]]:
        """
        Detect real-time pipelines by:
        1. Querying VPS for deployed sites with git repos
        2. For each site, querying GitHub for deploy workflows
        A pipeline exists only if BOTH conditions are true
        
        Returns: (configured_pipelines, unconfigured_apps)
        """
        pipelines = []
        unconfigured_apps = []
        
        try:
            if verbose:
                self.console.print(f"[cyan]Connecting to VPS ({self.vps_discovery.host}:{self.vps_discovery.port})...[/cyan]")
            
            if not self.vps_discovery.connect():
                if verbose:
                    self.console.print("[red]Failed to connect to VPS[/red]")
                return pipelines, unconfigured_apps
            
            if verbose:
                self.console.print(f"[green]✓ Connected to VPS[/green]")
            
            deployed_apps = self.vps_discovery.discover_deployed_apps(verbose=verbose)
            
            if verbose:
                self.console.print(f"[cyan]Total: {len(deployed_apps)} deployed app(s)[/cyan]")
            
            if not deployed_apps:
                self.vps_discovery.disconnect()
                return pipelines, unconfigured_apps
            
            for app_name, app_info in deployed_apps.items():
                if verbose:
                    self.console.print(f"\n[cyan]Checking app: {app_name}[/cyan]")
                    self.console.print(f"  Has git repo: {app_info.get('has_github_repo')}")
                
                if not app_info.get('has_github_repo'):
                    if verbose:
                        self.console.print(f"  [yellow]No git repository[/yellow]")
                    unconfigured_apps.append({'app_name': app_name, 'reason': 'No git repository'})
                    continue
                
                github_repo = app_info.get('github_repo')
                
                if not github_repo:
                    if verbose:
                        self.console.print(f"  [yellow]No GitHub repo configured[/yellow]")
                    unconfigured_apps.append({'app_name': app_name, 'reason': 'No GitHub remote'})
                    continue
                
                if verbose:
                    self.console.print(f"  GitHub repo: {github_repo}")
                
                parts = github_repo.split('/')
                if len(parts) != 2:
                    if verbose:
                        self.console.print(f"  [yellow]Invalid repo format: {github_repo}[/yellow]")
                    unconfigured_apps.append({'app_name': app_name, 'reason': 'Invalid repo format'})
                    continue
                
                owner, repo = parts
                
                workflows = self.github_discovery.get_repo_workflows(owner, repo)
                
                if verbose:
                    self.console.print(f"  Found {len(workflows)} workflow(s) on GitHub")
                
                deploy_workflows = [
                    w for w in workflows
                    if any(term in w['name'].lower() for term in ['deploy', 'release', 'cd', 'production'])
                ]
                
                if verbose:
                    self.console.print(f"  Found {len(deploy_workflows)} deploy workflow(s)")
                
                if not deploy_workflows:
                    if verbose:
                        self.console.print(f"  [yellow]No deploy workflow found[/yellow]")
                    unconfigured_apps.append({'app_name': app_name, 'reason': 'No deploy workflow'})
                    continue
                
                for workflow in deploy_workflows:
                    pipeline_data = {
                        'app_name': app_name,
                        'vps_domain': app_name,
                        'vps_path': app_info['path'],
                        'vps_status': 'running' if app_info.get('pm2_running') else 'stopped',
                        'github_repo': github_repo,
                        'owner': owner,
                        'repo': repo,
                        'workflow_name': workflow['name'],
                        'workflow_id': workflow['id'],
                        'workflow_path': workflow.get('path', '.github/workflows/deploy.yml'),
                        'detected_at': datetime.now().isoformat()
                    }
                    
                    pipelines.append(pipeline_data)
                    if verbose:
                        self.console.print(f"  [green]✓ Added pipeline: {workflow['name']}[/green]")
            
            self.vps_discovery.disconnect()
            
        except Exception as e:
            self.console.print(f"[red]Error detecting pipelines: {e}[/red]")
            import traceback
            traceback.print_exc()
            self.vps_discovery.disconnect()
        
        return pipelines, unconfigured_apps


class PipelineDashboard:
    """Live monitoring dashboard for CI/CD pipelines configuration management"""
    
    def __init__(self, pipeline_detector: RealtimePipelineDetector, secrets_manager: GitHubSecretsManager, vps_discovery: 'ServerDiscovery'):
        self.pipeline_detector = pipeline_detector
        self.secrets_manager = secrets_manager
        self.vps_discovery = vps_discovery
        self.console = Console()
    
    def _check_deploy_secrets(self, owner: str, repo: str) -> bool:
        """Check if deploy secrets are configured in GitHub"""
        try:
            secrets = self.secrets_manager.list_secrets(owner, repo)
            if not secrets:
                return False
            
            secret_names = [s['name'].upper() for s in secrets]
            
            required_patterns = ['DEPLOY', 'SSH', 'KEY', 'CREDENTIALS']
            found_required = any(
                any(pattern in name for pattern in required_patterns)
                for name in secret_names
            )
            
            return found_required
        except Exception:
            return False
    
    def generate_dashboard(self) -> Layout:
        """Generate dashboard layout showing all deployed apps and their configuration status"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # Header
        header = Panel(
            "[bold cyan]Pipeline Configuration Monitor[/bold cyan] - Real-Time Status",
            style="cyan"
        )
        layout["header"].update(header)
        
        # Get all deployed apps
        if not self.vps_discovery.ssh_client:
            self.vps_discovery.connect()
        
        all_deployed_apps = self.vps_discovery.discover_deployed_apps(verbose=False)
        pipelines, unconfigured_apps = self.pipeline_detector.detect_pipelines(verbose=False)
        
        if all_deployed_apps:
            config_table = Table(title=f"All Deployed Applications ({len(all_deployed_apps)})", box=box.ROUNDED)
            config_table.add_column("App", style="cyan", width=18)
            config_table.add_column("Deployed", justify="center", width=10)
            config_table.add_column("Git Repo", justify="center", width=10)
            config_table.add_column("Workflow", justify="center", width=10)
            config_table.add_column("Secrets", justify="center", width=10)
            config_table.add_column("Status", justify="center", width=10)
            
            for app_name, app_info in sorted(all_deployed_apps.items()):
                deployed_icon = "🟢"
                
                github_repo = app_info.get('github_repo')
                repo_icon = "🟢" if github_repo else "🔴"
                
                workflow_icon = "🔴"
                secrets_icon = "🔴"
                
                if github_repo:
                    parts = github_repo.split('/')
                    if len(parts) == 2:
                        owner, repo = parts
                        
                        workflows = self.pipeline_detector.github_discovery.get_repo_workflows(owner, repo)
                        deploy_workflows = [w for w in workflows if any(term in w['name'].lower() for term in ['deploy', 'release', 'cd', 'production'])]
                        workflow_icon = "🟢" if deploy_workflows else "🔴"
                        
                        secrets_installed = self._check_deploy_secrets(owner, repo)
                        secrets_icon = "🟢" if secrets_installed else "🔴"
                
                pm2_running = app_info.get('pm2_running', False)
                status_icon = "🟢 Running" if pm2_running else "🔴 Stopped"
                
                config_table.add_row(
                    app_name,
                    deployed_icon,
                    repo_icon,
                    workflow_icon,
                    secrets_icon,
                    status_icon
                )
            
            layout["body"].update(Panel(config_table, title="[bold]Configuration Status[/bold]"))
        else:
            no_apps = Panel(
                "[yellow]No deployed applications found[/yellow]",
                title="[bold]Configuration Status[/bold]"
            )
            layout["body"].update(no_apps)
        
        # Footer with legend
        footer_text = (
            "[dim]🟢 = Configured/Running | 🔴 = Missing/Stopped | "
            "Secrets = Deploy credentials installed | Ctrl+C to return[/dim]"
        )
        
        footer = Panel(footer_text, style="dim")
        layout["footer"].update(footer)
        
        return layout
    
    def run(self, interval: int = 3):
        """Run live monitoring dashboard"""
        try:
            with Live(self.generate_dashboard(), refresh_per_second=1, console=self.console) as live:
                while True:
                    time.sleep(interval)
                    live.update(self.generate_dashboard())
        except KeyboardInterrupt:
            pass


class ServerDiscovery:
    """Discover actual CI/CD pipelines and applications from VPS server"""
    
    def __init__(self, host: str, username: str, port: int = 22):
        self.host = host
        self.username = username
        self.port = port
        self.ssh_client: Optional[paramiko.SSHClient] = None
        self.console = Console()
    
    def connect(self) -> bool:
        """Establish SSH connection to VPS"""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            ssh_key_path = VPS_SSH_KEY
            if Path(ssh_key_path).exists():
                self.ssh_client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    key_filename=ssh_key_path,
                    timeout=10,
                    allow_agent=True
                )
            else:
                self.console.print(f"[yellow]SSH key not found at {ssh_key_path}, trying agent auth...[/yellow]")
                self.ssh_client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    timeout=10,
                    allow_agent=True
                )
            return True
        except Exception as e:
            self.console.print(f"[red]Failed to connect to VPS: {e}[/red]")
            return False
    
    def disconnect(self):
        """Close SSH connection"""
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None
    
    def execute(self, command: str, use_sudo: bool = False) -> Tuple[str, str, int]:
        """Execute command on VPS"""
        if not self.ssh_client:
            return "", "Not connected", 1
        
        try:
            if use_sudo:
                command = f"sudo {command}"
            
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            return stdout.read().decode(), stderr.read().decode(), exit_code
        except Exception as e:
            return "", str(e), 1
    
    def discover_domains(self) -> List[str]:
        """Discover all NGINX domains on VPS"""
        try:
            nginx_out, _, _ = self.execute("ls -1 /etc/nginx/sites-enabled/")
            domains = [d.strip() for d in nginx_out.split('\n') 
                      if d.strip() and d.strip() != 'default']
            return domains
        except Exception as e:
            self.console.print(f"[yellow]Failed to discover domains: {e}[/yellow]")
            return []
    
    def discover_deployed_apps(self, verbose: bool = False) -> Dict[str, Dict]:
        """Discover deployed applications and their configuration"""
        apps = {}
        
        try:
            deployer_apps_dir = "/home/deployer/apps"
            ls_out, ls_err, exit_code = self.execute(f"ls -1 {deployer_apps_dir}", use_sudo=True)
            
            if verbose:
                self.console.print(f"[cyan]Listing {deployer_apps_dir}[/cyan]")
                self.console.print(f"  Exit code: {exit_code}")
                if ls_err:
                    self.console.print(f"  Error: {ls_err}")
            
            if exit_code != 0:
                if verbose:
                    self.console.print(f"[yellow]Failed to list apps directory[/yellow]")
                return apps
            
            app_dirs = [d.strip() for d in ls_out.split('\n') if d.strip()]
            if verbose:
                self.console.print(f"  Found {len(app_dirs)} app(s): {', '.join(app_dirs) if app_dirs else 'none'}")
            
            for app_dir_name in app_dirs:
                app_path = f"{deployer_apps_dir}/{app_dir_name}"
                app_info = {
                    "domain": app_dir_name,
                    "path": app_path,
                    "has_github_repo": False,
                    "has_workflow": False,
                    "workflow_file": None,
                    "github_repo": None,
                    "pm2_running": False
                }
                
                git_dir = f"{app_path}/.git"
                git_check, _, git_exit = self.execute(f"test -d {git_dir} && echo 'yes' || echo 'no'", use_sudo=True)
                app_info["has_github_repo"] = "yes" in git_check.lower()
                
                if app_info["has_github_repo"]:
                    workflow_dir = f"{app_path}/.github/workflows"
                    workflow_check, _, wf_exit = self.execute(f"ls -1 {workflow_dir} 2>/dev/null | head -1", use_sudo=True)
                    if wf_exit == 0 and workflow_check.strip():
                        app_info["has_workflow"] = True
                        app_info["workflow_file"] = f".github/workflows/{workflow_check.strip()}"
                        
                        config_file = f"{app_path}/.git/config"
                        config_out, _, _ = self.execute(f"cat {config_file}", use_sudo=True)
                        
                        for line in config_out.split('\n'):
                            if 'url =' in line:
                                url_part = line.split('=')[-1].strip()
                                if 'github.com' in url_part:
                                    repo_match = url_part.split('github.com')[1]
                                    repo_match = repo_match.replace(':', '/').replace('.git', '').strip('/')
                                    app_info["github_repo"] = repo_match
                                    break
                
                pm2_check, pm2_err, pm2_exit = self.execute(f"pgrep -f 'node.*{app_dir_name}' > /dev/null && echo 'yes' || echo 'no'", use_sudo=True)
                app_info["pm2_running"] = "yes" in pm2_check.lower()
                
                if verbose and app_info["github_repo"]:
                    self.console.print(f"  PM2 Status: {'[green]RUNNING[/green]' if app_info['pm2_running'] else '[yellow]STOPPED[/yellow]'}")
                
                apps[app_dir_name] = app_info
        
        except Exception as e:
            self.console.print(f"[yellow]Error discovering apps: {e}[/yellow]")
        
        return apps
    
    def get_domain_details(self, domain: str) -> Optional[Dict]:
        """Get detailed information about a domain's deployment"""
        try:
            app_path = f"/home/deployer/apps/{domain}"
            
            details = {
                "domain": domain,
                "path": app_path,
                "nginx_enabled": False,
                "pm2_app_name": domain,
                "git_remote_url": None,
                "github_repo": None,
                "has_deploy_workflow": False,
                "workflow_file": None,
                "pm2_status": "unknown"
            }
            
            nginx_check, _, nginx_exit = self.execute(
                f"test -f /etc/nginx/sites-enabled/{domain} && echo 'yes' || echo 'no'"
            )
            details["nginx_enabled"] = "yes" in nginx_check.lower()
            
            git_check, _, git_dir_exit = self.execute(f"test -d {app_path}/.git && echo 'yes' || echo 'no'")
            if "yes" in git_check.lower():
                git_config, git_err, git_exit = self.execute(f"cat {app_path}/.git/config 2>/dev/null")
                if git_exit == 0 and git_config.strip():
                    for line in git_config.split('\n'):
                        if 'url' in line:
                            url = line.split('=')[-1].strip()
                            details["git_remote_url"] = url
                            if 'github.com' in url:
                                repo = url.replace('git@github.com:', '').replace('https://github.com/', '').replace('.git', '')
                                details["github_repo"] = repo
                            break
            
            if details.get("github_repo"):
                import requests
                try:
                    owner, repo_name = details["github_repo"].split('/')
                    check_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/.github/workflows/deploy.yml"
                    headers = {"Authorization": f"token {os.environ.get('GHT', '')}"}
                    response = requests.head(check_url, headers=headers, timeout=5)
                    if response.status_code == 200:
                        details["has_deploy_workflow"] = True
                        details["workflow_file"] = ".github/workflows/deploy.yml"
                except Exception as e:
                    pass
            
            pm2_info, _, pm2_exit = self.execute(
                f"sudo -u deployer /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2 show {domain} 2>/dev/null | grep -E 'status|online|stopped'"
            )
            if pm2_exit == 0:
                details["pm2_status"] = "online" if "online" in pm2_info.lower() else "stopped"
            
            return details
        
        except Exception as e:
            self.console.print(f"[yellow]Failed to get domain details: {e}[/yellow]")
            return None



class PipelineMonitor:
    """Real-time pipeline monitoring and metrics collection"""
    
    def __init__(self, github_token: str):
        self.token = github_token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.console = Console()
    
    def get_workflow_runs(self, owner: str, repo: str, workflow_file: str, limit: int = 10) -> List[Dict]:
        """Get recent workflow runs for a repository"""
        
        try:
            workflow_name = workflow_file.split('/')[-1]
            
            response = requests.get(
                f"{self.base_url}/repos/{owner}/{repo}/actions/workflows/{workflow_name}/runs",
                headers=self.headers,
                params={"per_page": limit},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('workflow_runs', [])
            
            return []
        
        except Exception as e:
            self.console.print(f"[yellow]Warning: Failed to fetch workflow runs: {e}[/yellow]")
            return []
    
    def get_pipeline_stats(self, pipeline: Dict) -> Dict:
        """Get current pipeline statistics"""
        
        try:
            repo = pipeline['repository']
            owner, repo_name = repo.split('/')
            workflow_file = pipeline['workflow_file']
            
            runs = self.get_workflow_runs(owner, repo_name, workflow_file, limit=10)
            
            last_run = None
            success_count = 0
            total_duration = 0
            
            for run in runs:
                if run['status'] == 'completed':
                    if not last_run:
                        last_run = {
                            "timestamp": run['created_at'],
                            "status": run['conclusion'],
                            "duration_seconds": int((
                                (datetime.fromisoformat(run['updated_at'].replace('Z', '+00:00')) -
                                 datetime.fromisoformat(run['created_at'].replace('Z', '+00:00')))
                            ).total_seconds()),
                            "branch": run['head_branch']
                        }
                    
                    if run['conclusion'] == 'success':
                        success_count += 1
                    
                    total_duration += int((
                        (datetime.fromisoformat(run['updated_at'].replace('Z', '+00:00')) -
                         datetime.fromisoformat(run['created_at'].replace('Z', '+00:00')))
                    ).total_seconds())
            
            success_rate = (success_count / len(runs) * 100) if runs else 0
            avg_duration = (total_duration / len([r for r in runs if r['status'] == 'completed'])) if runs else 0
            
            health_score = min(100, int(success_rate + (100 - avg_duration / 10)))
            
            return {
                "pipeline_id": pipeline['pipeline_id'],
                "status": pipeline['status'],
                "last_run": last_run,
                "metrics_24h": {
                    "run_count": len(runs),
                    "success_count": success_count,
                    "success_rate": success_rate,
                    "avg_duration_seconds": avg_duration
                },
                "health_score": max(0, min(100, health_score)),
                "active_runs": len([r for r in runs if r['status'] == 'in_progress']),
                "queue_length": len([r for r in runs if r['status'] == 'queued'])
            }
        
        except Exception as e:
            self.console.print(f"[yellow]Warning: Failed to get pipeline stats: {e}[/yellow]")
            return {
                "pipeline_id": pipeline.get('pipeline_id'),
                "status": "error",
                "last_run": None,
                "metrics_24h": {"run_count": 0, "success_count": 0, "success_rate": 0, "avg_duration_seconds": 0},
                "health_score": 0,
                "active_runs": 0,
                "queue_length": 0,
                "error": str(e)
            }


class CICDPipelineManager:
    """Manages CI/CD pipeline operations on VPS"""
    
    def __init__(self, host: str, username: str, port: int = 22):
        self.host = host
        self.username = username
        self.port = port
        self.ssh_client: Optional[paramiko.SSHClient] = None
        self.console = Console()
    
    def connect(self) -> bool:
        """Establish SSH connection to VPS"""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            ssh_key_path = VPS_SSH_KEY
            if Path(ssh_key_path).exists():
                self.ssh_client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    key_filename=ssh_key_path,
                    timeout=10,
                    allow_agent=True
                )
            else:
                self.ssh_client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    timeout=10,
                    allow_agent=True
                )
            self.console.print(f"[green]✓ Connected to VPS: {self.host}[/green]")
            return True
        except Exception as e:
            self.console.print(f"[red]SSH Connection failed: {e}[/red]")
            return False
    
    def disconnect(self):
        """Close SSH connection"""
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None
    
    def execute(self, command: str, use_sudo: bool = False) -> Tuple[str, str, int]:
        """Execute command on remote VPS"""
        if not self.ssh_client:
            return "", "Not connected", 1
        
        try:
            if use_sudo:
                command = f"sudo {command}"
            
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            
            return stdout.read().decode(), stderr.read().decode(), exit_code
        except Exception as e:
            return "", str(e), 1
    
    def setup_deployment_environment(self, app_name: str, app_path: str) -> bool:
        """Setup deployment environment on VPS"""
        self.console.print(f"[cyan]Setting up deployment environment for {app_name}...[/cyan]")
        
        commands = [
            f"mkdir -p {app_path}",
            f"mkdir -p {app_path}/logs",
            f"chown -R deployer:deployer {app_path}"
        ]
        
        for cmd in commands:
            _, stderr, exit_code = self.execute(cmd, use_sudo=True)
            if exit_code != 0:
                self.console.print(f"[red]Failed to setup environment: {stderr}[/red]")
                return False
        
        self.console.print(f"[green]✓ Deployment environment ready at {app_path}[/green]")
        return True
    
    def get_vps_status(self) -> Dict:
        """Get VPS system status"""
        status = {}
        
        cpu_out, _, _ = self.execute("top -bn1 | grep 'Cpu(s)' | awk '{print $2}'")
        status['cpu_usage'] = float(cpu_out.strip().replace('%', '')) if cpu_out.strip() else 0
        
        mem_out, _, _ = self.execute("free | grep Mem | awk '{print ($3/$2) * 100.0}'")
        status['memory_usage'] = float(mem_out.strip()) if mem_out.strip() else 0
        
        disk_out, _, _ = self.execute("df -h / | tail -1 | awk '{print $5}'")
        status['disk_usage'] = float(disk_out.strip().replace('%', '')) if disk_out.strip() else 0
        
        nginx_out, _, exit_code = self.execute("systemctl is-active nginx")
        status['nginx_running'] = exit_code == 0 and nginx_out.strip() == 'active'
        
        return status


class CICDManagerCLI:
    """Interactive CLI for CI/CD Manager"""
    
    def __init__(self):
        self.console = Console()
        self.secrets_manager = GitHubSecretsManager(GHT)
        self.repo_manager = RepositoryManager(GHT)
        self.secret_replicator = SecretReplicator(self.secrets_manager)
        self.vps_manager = CICDPipelineManager(VPS_HOST, VPS_SSH_USERNAME, VPS_SSH_PORT)
        
        self.github_discovery = GitHubRepositoryDiscovery(GHT)
        self.server_discovery = ServerDiscovery(VPS_HOST, VPS_SSH_USERNAME, VPS_SSH_PORT)
        
        self.pipeline_detector = RealtimePipelineDetector(self.server_discovery, self.github_discovery)
        self.pipeline_monitor = PipelineMonitor(GHT)
    
    def main_menu(self):
        """Display main menu"""
        while True:
            self.console.clear()
            
            panel = Panel(
                "[bold cyan]CI/CD Manager[/bold cyan]\nGitHub Actions & VPS Deployment Pipeline - Stage 2",
                style="bold blue"
            )
            self.console.print(panel)
            
            menu_items = [
                "[1] Live Monitoring Dashboard",
                "[2] Manage Secrets",
                "[3] Replicate Secrets",
                "[4] CI/CD Pipelines",
                "[5] VPS Management",
                "[6] Validate Setup",
                "[7] Check Connectivity",
                "[0] Exit"
            ]
            
            for item in menu_items:
                self.console.print(item)
            
            choice = Prompt.ask("\nSelect option")
            
            if choice == "1":
                self._live_dashboard()
            elif choice == "2":
                self.secrets_menu()
            elif choice == "3":
                self.replicate_menu()
            elif choice == "4":
                self.pipelines_menu()
            elif choice == "5":
                self.vps_menu()
            elif choice == "6":
                self.validate_setup()
            elif choice == "7":
                self.check_connectivity()
            elif choice == "0":
                self.console.print("[yellow]Exiting...[/yellow]")
                break
            else:
                self.console.print("[red]Invalid option[/red]")
                time.sleep(1)
    
    def secrets_menu(self):
        """Secrets management menu"""
        while True:
            self.console.clear()
            self.console.print("[bold]Secrets Management[/bold]")
            self.console.print("[1] List secrets in repository")
            self.console.print("[2] Create/Update secret")
            self.console.print("[3] Delete secret")
            self.console.print("[0] Back to main menu")
            
            choice = Prompt.ask("\nSelect option")
            
            if choice == "1":
                owner = Prompt.ask("GitHub owner")
                repo = Prompt.ask("Repository name")
                secrets = self.secrets_manager.list_secrets(owner, repo)
                
                if secrets:
                    table = Table(title=f"Secrets in {owner}/{repo}")
                    table.add_column("Name", style="cyan")
                    table.add_column("Updated", style="green")
                    
                    for secret in secrets:
                        table.add_row(secret['name'], secret.get('updated_at', 'N/A'))
                    
                    self.console.print(table)
                else:
                    self.console.print("[yellow]No secrets found[/yellow]")
                
                Prompt.ask("\nPress Enter to continue")
            
            elif choice == "2":
                owner = Prompt.ask("GitHub owner")
                repo = Prompt.ask("Repository name")
                secret_name = Prompt.ask("Secret name")
                secret_value = Prompt.ask("Secret value", password=True)
                
                if self.secrets_manager.create_secret(owner, repo, secret_name, secret_value):
                    self.console.print("[green]Secret created successfully[/green]")
                
                Prompt.ask("\nPress Enter to continue")
            
            elif choice == "3":
                owner = Prompt.ask("GitHub owner")
                repo = Prompt.ask("Repository name")
                secret_name = Prompt.ask("Secret name to delete")
                
                if Confirm.ask(f"Delete {secret_name}?"):
                    if self.secrets_manager.delete_secret(owner, repo, secret_name):
                        self.console.print("[green]Secret deleted successfully[/green]")
                
                Prompt.ask("\nPress Enter to continue")
            
            elif choice == "0":
                break
            else:
                self.console.print("[red]Invalid option[/red]")
                time.sleep(1)
    

    def replicate_menu(self):
        """Secret replication menu"""
        self.console.clear()
        self.console.print("[bold]Secret Replication[/bold]")
        
        source_owner = Prompt.ask("Source GitHub owner")
        source_repo = Prompt.ask("Source repository")
        dest_owner = Prompt.ask("Destination GitHub owner")
        dest_repo = Prompt.ask("Destination repository")
        
        self.secret_replicator.replicate_secrets(
            source_owner, source_repo,
            dest_owner, dest_repo
        )
        
        Prompt.ask("\nPress Enter to continue")
    
    def pipelines_menu(self):
        """CI/CD Pipelines management menu"""
        while True:
            self.console.clear()
            self.console.print("[bold]CI/CD Pipelines (Real-Time Detection)[/bold]")
            self.console.print("[1] List pipelines")
            self.console.print("[2] Monitor pipelines")
            self.console.print("[0] Back to main menu")
            
            choice = Prompt.ask("\nSelect option")
            
            if choice == "1":
                self._list_pipelines()
            elif choice == "2":
                self._monitor_pipelines()
            elif choice == "0":
                break
            else:
                self.console.print("[red]Invalid option[/red]")
                time.sleep(1)
    
    def _live_dashboard(self):
        """Live monitoring dashboard for CI/CD pipelines"""
        dashboard = PipelineDashboard(self.pipeline_detector, self.secrets_manager, self.server_discovery)
        dashboard.run()
    
    def _list_pipelines(self):
        """List real-time detected pipelines"""
        self.console.clear()
        self.console.print("[bold]CI/CD Pipelines (Real-Time Detection)[/bold]\n")
        
        self.console.print("[cyan]Detecting pipelines...[/cyan]\n")
        pipelines, unconfigured_apps = self.pipeline_detector.detect_pipelines(verbose=True)
        
        if not pipelines:
            self.console.print("[yellow]No pipelines detected[/yellow]")
            self.console.print("\n[cyan]A pipeline requires:[/cyan]")
            self.console.print("  1. A site deployed on the VPS (in /home/deployer/apps/)")
            self.console.print("  2. The site's git remote pointing to a GitHub repository")
            self.console.print("  3. The GitHub repository containing a deploy workflow")
            self.console.print("\n[cyan]Ensure your VPS site has a .git directory with a GitHub origin.[/cyan]")
            
            if unconfigured_apps:
                self.console.print(f"\n[yellow]Found {len(unconfigured_apps)} unconfigured site(s):[/yellow]")
                for app in unconfigured_apps:
                    self.console.print(f"  • {app['app_name']}: {app['reason']}")
            
            Prompt.ask("\nPress Enter to continue")
            return
        
        table = Table(title=f"Detected Pipelines ({len(pipelines)})")
        table.add_column("App", style="cyan", width=20)
        table.add_column("Repository", style="green", width=25)
        table.add_column("Workflow", style="yellow", width=25)
        table.add_column("VPS Status", style="blue", width=12)
        
        for pipeline in pipelines:
            app_name = pipeline.get('app_name', 'N/A')
            repository = pipeline.get('github_repo', 'N/A')
            workflow_name = pipeline.get('workflow_name', 'N/A')
            vps_status = pipeline.get('vps_status', 'unknown').upper()
            
            status_color = "[green]" if vps_status == "RUNNING" else "[yellow]"
            
            table.add_row(
                app_name,
                repository,
                workflow_name,
                f"{status_color}{vps_status}[/]"
            )
        
        self.console.print(table)
        
        if unconfigured_apps:
            self.console.print(f"\n[yellow]Unconfigured Sites ({len(unconfigured_apps)}):[/yellow]")
            for app in unconfigured_apps:
                self.console.print(f"  • {app['app_name']}: {app['reason']}")
        
        Prompt.ask("\nPress Enter to continue")
    
    def _monitor_pipelines(self):
        """Real-time pipeline monitoring dashboard"""
        self.console.clear()
        self.console.print("[bold]CI/CD Pipeline Monitor (Real-Time)[/bold]\n")
        self.console.print("[cyan]Detecting pipelines...[/cyan]\n")
        
        pipelines, unconfigured_apps = self.pipeline_detector.detect_pipelines(verbose=True)
        
        if not pipelines:
            self.console.print("[yellow]No pipelines detected[/yellow]")
            Prompt.ask("\nPress Enter to continue")
            return
        
        table = Table(title=f"Pipeline Status Dashboard ({len(pipelines)} pipelines)")
        table.add_column("App", style="cyan", width=20)
        table.add_column("Repository", style="green", width=25)
        table.add_column("Workflow", style="yellow", width=20)
        table.add_column("VPS Status", style="magenta", width=12)
        table.add_column("Last Detected", style="white", width=19)
        
        for pipeline in pipelines:
            app_name = pipeline.get('app_name', 'N/A')
            repository = pipeline.get('github_repo', 'N/A')
            workflow_name = pipeline.get('workflow_name', 'N/A')
            vps_status = pipeline.get('vps_status', 'unknown').upper()
            detected_at = pipeline.get('detected_at', 'N/A')[:19]
            
            status_emoji = "✓" if vps_status == "RUNNING" else "⏸"
            
            table.add_row(
                app_name,
                repository,
                workflow_name,
                f"{status_emoji} {vps_status}",
                detected_at
            )
        
        self.console.print(table)
        
        Prompt.ask("\nPress Enter to continue")
    
    def vps_menu(self):
        """VPS management menu"""
        while True:
            self.console.clear()
            self.console.print("[bold]VPS Management[/bold]")
            self.console.print("[1] Check VPS status")
            self.console.print("[2] Setup deployment environment")
            self.console.print("[3] Execute command")
            self.console.print("[0] Back to main menu")
            
            choice = Prompt.ask("\nSelect option")
            
            if choice == "1":
                if self.vps_manager.connect():
                    status = self.vps_manager.get_vps_status()
                    
                    table = Table(title="VPS Status")
                    table.add_column("Metric", style="cyan")
                    table.add_column("Value", style="green")
                    
                    table.add_row("CPU Usage", f"{status['cpu_usage']:.1f}%")
                    table.add_row("Memory Usage", f"{status['memory_usage']:.1f}%")
                    table.add_row("Disk Usage", f"{status['disk_usage']:.1f}%")
                    table.add_row("NGINX", "Running" if status['nginx_running'] else "Stopped")
                    
                    self.console.print(table)
                    self.vps_manager.disconnect()
                
                Prompt.ask("\nPress Enter to continue")
            
            elif choice == "2":
                app_name = Prompt.ask("Application name")
                app_path = Prompt.ask("Application path")
                
                if self.vps_manager.connect():
                    self.vps_manager.setup_deployment_environment(app_name, app_path)
                    self.vps_manager.disconnect()
                
                Prompt.ask("\nPress Enter to continue")
            
            elif choice == "3":
                command = Prompt.ask("Command to execute")
                use_sudo = Confirm.ask("Use sudo?", default=False)
                
                if self.vps_manager.connect():
                    stdout, stderr, exit_code = self.vps_manager.execute(command, use_sudo=use_sudo)
                    
                    if stdout:
                        self.console.print("[cyan]Output:[/cyan]")
                        self.console.print(stdout)
                    if stderr:
                        self.console.print("[red]Error:[/red]")
                        self.console.print(stderr)
                    
                    self.vps_manager.disconnect()
                
                Prompt.ask("\nPress Enter to continue")
            
            elif choice == "0":
                break
            else:
                self.console.print("[red]Invalid option[/red]")
                time.sleep(1)
    
    def validate_setup(self):
        """Validate CI/CD setup"""
        self.console.clear()
        self.console.print("[bold]Validating CI/CD Setup[/bold]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            task = progress.add_task("Checking GitHub credentials...", total=None)
            github_ok = self.secrets_manager.verify_credentials()
            progress.update(task, completed=True)
            
            task = progress.add_task("Checking VPS connectivity...", total=None)
            vps_ok = self.vps_manager.connect()
            if vps_ok:
                self.vps_manager.disconnect()
            progress.update(task, completed=True)
            
        
        self.console.print("\n[bold]Validation Results:[/bold]")
        self.console.print(f"  GitHub API: {'[green]✓[/green]' if github_ok else '[red]✗[/red]'}")
        self.console.print(f"  VPS SSH: {'[green]✓[/green]' if vps_ok else '[red]✗[/red]'}")
        
        Prompt.ask("\nPress Enter to continue")
    
    def check_connectivity(self):
        """Check connectivity to all services"""
        self.console.clear()
        self.console.print("[bold]Connectivity Check[/bold]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            task = progress.add_task("Testing GitHub API...", total=None)
            try:
                response = requests.get("https://api.github.com", timeout=5)
                github_ok = response.status_code == 200
            except:
                github_ok = False
            progress.update(task, completed=True)
            
            task = progress.add_task("Testing VPS SSH...", total=None)
            vps_ok = self.vps_manager.connect()
            if vps_ok:
                self.vps_manager.disconnect()
            progress.update(task, completed=True)
        
        self.console.print("\n[bold]Connectivity Results:[/bold]")
        self.console.print(f"  GitHub API: {'[green]✓[/green]' if github_ok else '[red]✗[/red]'}")
        self.console.print(f"  VPS SSH ({VPS_HOST}:{VPS_SSH_PORT}): {'[green]✓[/green]' if vps_ok else '[red]✗[/red]'}")
        
        Prompt.ask("\nPress Enter to continue")


def main():
    """Main entry point"""
    try:
        cli = CICDManagerCLI()
        cli.main_menu()
    except KeyboardInterrupt:
        print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
