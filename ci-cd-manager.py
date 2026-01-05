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
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install paramiko rich requests pyyaml")
    sys.exit(1)


# ============================================================================
# CONFIGURATION
# ============================================================================

GHT = os.environ.get('GHT', "")
VPS_HOST = os.environ.get('VPS_HOST', "23.29.114.83")
VPS_SSH_USERNAME = os.environ.get('VPS_USER', "beinejd")
VPS_SSH_PORT = int(os.environ.get('VPS_PORT', "2223"))
CCM_CONFIG_PATH = os.environ.get('CCM_CONFIG', str(Path.home() / ".ccm" / "projects.json"))
CCM_LOG_PATH = Path.home() / ".ccm" / "logs"
DRY_RUN = os.environ.get('CCM_DRY_RUN', "false").lower() == "true"

# Ensure log directory exists
CCM_LOG_PATH.mkdir(parents=True, exist_ok=True)

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
    
    def create_secret(self, owner: str, repo: str, secret_name: str, secret_value: str) -> bool:
        """Create or update a secret in a repository"""
        if DRY_RUN:
            self.console.print(f"[cyan][DRY RUN] Would create secret: {secret_name}[/cyan]")
            return True
        
        try:
            data = {
                "encrypted_value": secret_value,
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


class ProjectConfiguration:
    """Manages project-specific CI/CD configurations"""
    
    def __init__(self, config_path: str = CCM_CONFIG_PATH):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.console = Console()
        self.projects = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    return data.get('projects', {})
            except Exception as e:
                self.console.print(f"[yellow]Warning: Failed to load config: {e}[/yellow]")
                return {}
        return {}
    
    def _save_config(self) -> bool:
        """Save configuration to file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump({'projects': self.projects}, f, indent=2)
            return True
        except Exception as e:
            self.console.print(f"[red]Error saving config: {e}[/red]")
            return False
    
    def list_projects(self) -> List[str]:
        """List all projects"""
        return list(self.projects.keys())
    
    def get_project(self, project_name: str) -> Optional[Dict]:
        """Get project configuration"""
        return self.projects.get(project_name)
    
    def create_project(self, project_name: str, github_owner: str, github_repo: str, 
                      vps_app_name: str, vps_app_path: str, vps_port: int = 3000) -> bool:
        """Create a new project configuration"""
        if project_name in self.projects:
            self.console.print(f"[yellow]Project {project_name} already exists[/yellow]")
            return False
        
        self.projects[project_name] = {
            "github": {
                "owner": github_owner,
                "repo": github_repo
            },
            "vps": {
                "app_name": vps_app_name,
                "app_path": vps_app_path,
                "port": vps_port
            },
            "secrets": {
                "VPS_HOST": "VPS_HOST",
                "VPS_USER": "VPS_USER",
                "VPS_SSH_KEY": "VPS_SSH_KEY",
                "VPS_PORT": "VPS_PORT",
                "VPS_APP_PATH": vps_app_path
            },
            "created_at": datetime.now().isoformat()
        }
        
        if self._save_config():
            self.console.print(f"[green]✓ Created project: {project_name}[/green]")
            return True
        return False
    
    def delete_project(self, project_name: str) -> bool:
        """Delete a project configuration"""
        if project_name not in self.projects:
            self.console.print(f"[red]Project {project_name} not found[/red]")
            return False
        
        del self.projects[project_name]
        if self._save_config():
            self.console.print(f"[green]✓ Deleted project: {project_name}[/green]")
            return True
        return False
    
    def get_secrets_mapping(self, project_name: str) -> Dict:
        """Get secret mappings for a project"""
        project = self.get_project(project_name)
        if not project:
            return {}
        return project.get('secrets', {})


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
    
    def __init__(self, github_manager: GitHubSecretsManager, project_config: ProjectConfiguration):
        self.github = github_manager
        self.project_config = project_config
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
                
                project = self.project_config.get_project(project_name) if project_name else None
                
                transformed_value = self._apply_transformation(secret_name, project, transforms)
                
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
            self.ssh_client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                timeout=10
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
        self.project_config = ProjectConfiguration()
        self.repo_manager = RepositoryManager(GHT)
        self.secret_replicator = SecretReplicator(self.secrets_manager, self.project_config)
        self.vps_manager = CICDPipelineManager(VPS_HOST, VPS_SSH_USERNAME, VPS_SSH_PORT)
    
    def main_menu(self):
        """Display main menu"""
        while True:
            self.console.clear()
            
            panel = Panel(
                "[bold cyan]CI/CD Manager[/bold cyan]\nGitHub Actions & VPS Deployment Pipeline",
                style="bold blue"
            )
            self.console.print(panel)
            
            menu_items = [
                "[1] Manage Secrets",
                "[2] Manage Projects",
                "[3] Replicate Secrets",
                "[4] VPS Management",
                "[5] Validate Setup",
                "[6] Check Connectivity",
                "[0] Exit"
            ]
            
            for item in menu_items:
                self.console.print(item)
            
            choice = Prompt.ask("\nSelect option")
            
            if choice == "1":
                self.secrets_menu()
            elif choice == "2":
                self.projects_menu()
            elif choice == "3":
                self.replicate_menu()
            elif choice == "4":
                self.vps_menu()
            elif choice == "5":
                self.validate_setup()
            elif choice == "6":
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
    
    def projects_menu(self):
        """Projects management menu"""
        while True:
            self.console.clear()
            self.console.print("[bold]Projects Management[/bold]")
            self.console.print("[1] List projects")
            self.console.print("[2] Create project")
            self.console.print("[3] View project")
            self.console.print("[4] Delete project")
            self.console.print("[0] Back to main menu")
            
            choice = Prompt.ask("\nSelect option")
            
            if choice == "1":
                projects = self.project_config.list_projects()
                if projects:
                    self.console.print("\n[cyan]Projects:[/cyan]")
                    for project in projects:
                        self.console.print(f"  • {project}")
                else:
                    self.console.print("[yellow]No projects configured[/yellow]")
                
                Prompt.ask("\nPress Enter to continue")
            
            elif choice == "2":
                project_name = Prompt.ask("Project name")
                github_owner = Prompt.ask("GitHub owner")
                github_repo = Prompt.ask("GitHub repository")
                vps_app_name = Prompt.ask("VPS app name")
                vps_app_path = Prompt.ask("VPS app path")
                vps_port = int(Prompt.ask("VPS port", default="3000"))
                
                self.project_config.create_project(
                    project_name, github_owner, github_repo,
                    vps_app_name, vps_app_path, vps_port
                )
                
                Prompt.ask("\nPress Enter to continue")
            
            elif choice == "3":
                projects = self.project_config.list_projects()
                if projects:
                    self.console.print("\nProjects:")
                    for i, project in enumerate(projects, 1):
                        self.console.print(f"  {i}. {project}")
                    
                    idx = int(Prompt.ask("Select project")) - 1
                    if 0 <= idx < len(projects):
                        project_name = projects[idx]
                        project = self.project_config.get_project(project_name)
                        
                        self.console.print(f"\n[bold]{project_name}[/bold]")
                        self.console.print(json.dumps(project, indent=2))
                
                Prompt.ask("\nPress Enter to continue")
            
            elif choice == "4":
                projects = self.project_config.list_projects()
                if projects:
                    self.console.print("\nProjects:")
                    for i, project in enumerate(projects, 1):
                        self.console.print(f"  {i}. {project}")
                    
                    idx = int(Prompt.ask("Select project")) - 1
                    if 0 <= idx < len(projects):
                        project_name = projects[idx]
                        if Confirm.ask(f"Delete {project_name}?"):
                            self.project_config.delete_project(project_name)
                
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
        
        projects = self.project_config.list_projects()
        project_name = None
        if projects:
            self.console.print("\nProjects (optional):")
            for i, project in enumerate(projects, 1):
                self.console.print(f"  {i}. {project}")
            
            choice = Prompt.ask("Select project [0 for none]")
            if choice != "0" and choice:
                idx = int(choice) - 1
                if 0 <= idx < len(projects):
                    project_name = projects[idx]
        
        self.secret_replicator.replicate_secrets(
            source_owner, source_repo,
            dest_owner, dest_repo,
            project_name=project_name
        )
        
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
            
            task = progress.add_task("Checking projects configuration...", total=None)
            projects = self.project_config.list_projects()
            projects_ok = len(projects) > 0
            progress.update(task, completed=True)
        
        self.console.print("\n[bold]Validation Results:[/bold]")
        self.console.print(f"  GitHub API: {'[green]✓[/green]' if github_ok else '[red]✗[/red]'}")
        self.console.print(f"  VPS SSH: {'[green]✓[/green]' if vps_ok else '[red]✗[/red]'}")
        self.console.print(f"  Projects: {'[green]✓[/green]' if projects_ok else '[yellow]No projects configured[/yellow]'}")
        
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
