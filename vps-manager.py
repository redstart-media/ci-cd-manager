#!/usr/bin/env python3
"""
VPS Manager - Interactive server management tool
Manages NGINX, PM2, SSL certificates, site provisioning, and Cloudflare DNS
"""

import os
import sys
import time
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

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
    print("  pip install paramiko rich requests")
    sys.exit(1)


# ============================================================================
# CONFIGURATION - Edit these values OR set environment variables
# ============================================================================
# Environment variables take precedence over hardcoded values below.
# To set environment variables, run: ./setup-env.sh
#
# Required environment variables:
#   - CLOUDFLARE_API_TOKEN: Cloudflare API token for DNS management
#   - VPS_SRV1_IP: VPS server IP address
#   - VPS_SRV1_PORT: VPS SSH port
#
# Optional environment variables:
#   - CLAUDE_API_KEY: Claude API key (for future features)
#   - DEEPSEEK_API_KEY: DeepSeek API key (for future features)
# ============================================================================

# VPS Server Configuration
VPS_HOST = os.environ.get('VPS_SRV1_IP', "23.29.114.83")
VPS_SSH_USERNAME = "beinejd"  # Update this to your SSH username
VPS_SSH_PORT = int(os.environ.get('VPS_SRV1_PORT', "22"))

# Cloudflare API Configuration
# Get your API token from: https://dash.cloudflare.com/profile/api-tokens
# Required permission: Zone:DNS:Edit + Zone:Zone:Edit (for zone creation)
CLOUDFLARE_API_TOKEN = os.environ.get('CLOUDFLARE_API_TOKEN', "")

# AI API Keys (for future features)
CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY', "")
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', "")

# ============================================================================


class CloudflareManager:
    """Manages Cloudflare DNS via API"""
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        self.console = Console()
        self._zone_cache = {}  # Cache zone IDs by domain
        
        # Debug: Show token is being set
        self.console.print(f"[dim]CloudflareManager initialized with token: {api_token[:8]}...{api_token[-4:]}[/dim]")
    
    def verify_credentials(self) -> bool:
        """Verify API token is valid"""
        try:
            response = requests.get(
                f"{self.base_url}/user/tokens/verify",
                headers=self.headers,
                timeout=10
            )
            
            # Debug output
            if response.status_code != 200:
                self.console.print(f"[yellow]API Response Status: {response.status_code}[/yellow]")
                self.console.print(f"[yellow]Response: {response.text[:200]}[/yellow]")
                return False
            
            result = response.json()
            if not result.get('success', False):
                self.console.print(f"[yellow]API returned success=false[/yellow]")
                self.console.print(f"[yellow]Response: {result}[/yellow]")
                return False
            
            return True
            
        except requests.exceptions.RequestException as e:
            self.console.print(f"[red]Network error: {e}[/red]")
            return False
        except Exception as e:
            self.console.print(f"[red]Cloudflare API error: {e}[/red]")
            return False
    
    def get_root_domain(self, domain: str) -> str:
        """Extract root domain from subdomain (e.g., www.example.com -> example.com)"""
        parts = domain.split('.')
        if len(parts) >= 2:
            # Return last two parts (handles example.com, www.example.com, etc.)
            return '.'.join(parts[-2:])
        return domain
    
    def find_zone_by_domain(self, domain: str) -> Optional[Dict]:
        """Find a zone by domain name"""
        root_domain = self.get_root_domain(domain)
        
        # Check cache first
        if root_domain in self._zone_cache:
            return self._zone_cache[root_domain]
        
        try:
            response = requests.get(
                f"{self.base_url}/zones",
                headers=self.headers,
                params={"name": root_domain},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                zones = result.get('result', [])
                if zones:
                    zone = zones[0]
                    # Cache the zone
                    self._zone_cache[root_domain] = zone
                    return zone
            
            return None
        except Exception as e:
            self.console.print(f"[red]Error finding zone: {e}[/red]")
            return None
    
    def create_zone(self, domain: str) -> Optional[Dict]:
        """Create a new zone in Cloudflare"""
        root_domain = self.get_root_domain(domain)
        
        try:
            data = {
                "name": root_domain,
                "jump_start": True  # Auto-scan for DNS records
            }
            
            response = requests.post(
                f"{self.base_url}/zones",
                headers=self.headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                zone = result.get('result')
                if zone:
                    self.console.print(f"[green]✓ Created Cloudflare zone: {root_domain}[/green]")
                    # Cache the zone
                    self._zone_cache[root_domain] = zone
                    return zone
            else:
                error_msg = response.json().get('errors', [{}])[0].get('message', 'Unknown error')
                self.console.print(f"[red]Failed to create zone: {error_msg}[/red]")
                return None
        except Exception as e:
            self.console.print(f"[red]Error creating zone: {e}[/red]")
            return None
    
    def get_or_create_zone(self, domain: str) -> Optional[str]:
        """Get zone ID for domain, creating zone if it doesn't exist. Returns zone_id."""
        root_domain = self.get_root_domain(domain)
        
        # Try to find existing zone
        zone = self.find_zone_by_domain(root_domain)
        
        if zone:
            self.console.print(f"[cyan]Found existing zone: {root_domain}[/cyan]")
            return zone['id']
        
        # Zone doesn't exist, create it
        self.console.print(f"[yellow]Zone not found for {root_domain}, creating...[/yellow]")
        zone = self.create_zone(root_domain)
        
        if zone:
            return zone['id']
        
        self.console.print(f"[red]Failed to get or create zone for {root_domain}[/red]")
        return None
    
    def get_zone_id(self, domain: str) -> Optional[str]:
        """Get zone ID for a domain (must already exist)"""
        zone = self.find_zone_by_domain(domain)
        return zone['id'] if zone else None
    
    def list_dns_records(self, domain: str) -> List[Dict]:
        """List DNS records for a domain"""
        zone_id = self.get_zone_id(domain)
        if not zone_id:
            self.console.print(f"[red]No zone found for {domain}[/red]")
            return []
        
        try:
            params = {"name": domain}
            
            response = requests.get(
                f"{self.base_url}/zones/{zone_id}/dns_records",
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()['result']
            else:
                self.console.print(f"[red]Failed to list DNS records: {response.status_code}[/red]")
                return []
        except Exception as e:
            self.console.print(f"[red]Error listing DNS records: {e}[/red]")
            return []
    
    def create_a_record(self, name: str, ip_address: str, proxied: bool = True) -> bool:
        """Create an A record (auto-creates zone if needed)"""
        zone_id = self.get_or_create_zone(name)
        if not zone_id:
            return False
        
        try:
            data = {
                "type": "A",
                "name": name,
                "content": ip_address,
                "ttl": 1,  # Auto (required when proxied=True)
                "proxied": proxied
            }
            
            response = requests.post(
                f"{self.base_url}/zones/{zone_id}/dns_records",
                headers=self.headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.console.print(f"[green]✓ Created DNS A record: {name} → {ip_address}[/green]")
                return True
            elif response.status_code == 400:
                error_msg = response.json().get('errors', [{}])[0].get('message', 'Unknown error')
                if 'already exists' in error_msg.lower():
                    self.console.print(f"[yellow]DNS record {name} already exists[/yellow]")
                    return True  # Consider existing record as success
                else:
                    self.console.print(f"[red]Failed to create DNS record: {error_msg}[/red]")
                    return False
            else:
                self.console.print(f"[red]Failed to create DNS record: {response.status_code}[/red]")
                return False
        except Exception as e:
            self.console.print(f"[red]Error creating DNS record: {e}[/red]")
            return False
    
    def update_a_record(self, record_id: str, name: str, ip_address: str, proxied: bool = True) -> bool:
        """Update an existing A record"""
        zone_id = self.get_zone_id(name)
        if not zone_id:
            return False
        
        try:
            data = {
                "type": "A",
                "name": name,
                "content": ip_address,
                "ttl": 1,
                "proxied": proxied
            }
            
            response = requests.put(
                f"{self.base_url}/zones/{zone_id}/dns_records/{record_id}",
                headers=self.headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.console.print(f"[green]✓ Updated DNS A record: {name} → {ip_address}[/green]")
                return True
            else:
                self.console.print(f"[red]Failed to update DNS record: {response.status_code}[/red]")
                return False
        except Exception as e:
            self.console.print(f"[red]Error updating DNS record: {e}[/red]")
            return False
    
    def delete_dns_record(self, record_id: str, domain: str) -> bool:
        """Delete a DNS record"""
        zone_id = self.get_zone_id(domain)
        if not zone_id:
            return False
        
        try:
            response = requests.delete(
                f"{self.base_url}/zones/{zone_id}/dns_records/{record_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.console.print(f"[green]✓ Deleted DNS record[/green]")
                return True
            else:
                self.console.print(f"[red]Failed to delete DNS record: {response.status_code}[/red]")
                return False
        except Exception as e:
            self.console.print(f"[red]Error deleting DNS record: {e}[/red]")
            return False
    
    def get_record_by_name(self, name: str) -> Optional[Dict]:
        """Get a DNS record by name"""
        records = self.list_dns_records(domain=name)
        return records[0] if records else None
    
    def ensure_a_record(self, name: str, ip_address: str, proxied: bool = True) -> bool:
        """Create or update A record to ensure it points to the correct IP"""
        existing = self.get_record_by_name(name)
        
        if existing:
            if existing['content'] == ip_address and existing.get('proxied') == proxied:
                self.console.print(f"[cyan]DNS record {name} already correctly configured[/cyan]")
                return True
            else:
                self.console.print(f"[yellow]Updating DNS record {name}...[/yellow]")
                return self.update_a_record(existing['id'], name, ip_address, proxied)
        else:
            return self.create_a_record(name, ip_address, proxied)
    
    def verify_dns_propagation(self, domain: str, expected_ip: str, timeout: int = 60) -> bool:
        """Verify DNS has propagated (check via Cloudflare API)"""
        import socket
        
        self.console.print(f"[cyan]Verifying DNS propagation for {domain}...[/cyan]")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Check via DNS resolution
                resolved_ip = socket.gethostbyname(domain)
                if resolved_ip == expected_ip:
                    self.console.print(f"[green]✓ DNS propagated: {domain} → {expected_ip}[/green]")
                    return True
                else:
                    self.console.print(f"[yellow]DNS resolves to {resolved_ip}, waiting for {expected_ip}...[/yellow]")
            except socket.gaierror:
                self.console.print(f"[yellow]DNS not yet resolvable, waiting...[/yellow]")
            
            time.sleep(5)
        
        self.console.print(f"[red]DNS verification timed out after {timeout}s[/red]")
        return False


class VPSManager:
    """Manages SSH connection and VPS operations"""
    
    # PM2 path configuration (update if Node version changes)
    PM2_PATH = "/home/deployer/.nvm/versions/node/v24.11.1/bin/pm2"
    
    def __init__(self, host: str, username: str, port: int = 22, cloudflare: Optional['CloudflareManager'] = None):
        self.host = host
        self.username = username
        self.port = port
        self.cloudflare = cloudflare
        self.ssh_client: Optional[paramiko.SSHClient] = None
        self.console = Console()
        
    def connect(self) -> bool:
        """Establish SSH connection"""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                timeout=10
            )
            return True
        except Exception as e:
            self.console.print(f"[red]SSH Connection failed: {e}[/red]")
            return False
    
    def disconnect(self):
        """Close SSH connection"""
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None
    
    def execute(self, command: str, use_sudo: bool = False, sudo_user: str = None) -> Tuple[str, str, int]:
        """Execute command on remote server"""
        if not self.ssh_client:
            return "", "Not connected", 1
        
        try:
            if use_sudo and sudo_user:
                command = f"sudo -u {sudo_user} bash -c '{command}'"
            elif use_sudo:
                command = f"sudo {command}"
            
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            
            return stdout.read().decode(), stderr.read().decode(), exit_code
        except Exception as e:
            return "", str(e), 1
    
    def get_system_stats(self) -> Dict:
        """Get comprehensive system statistics"""
        stats = {}
        
        # CPU usage
        cpu_out, _, _ = self.execute("top -bn1 | grep 'Cpu(s)' | awk '{print $2}'")
        stats['cpu_usage'] = float(cpu_out.strip().replace('%', '')) if cpu_out.strip() else 0
        
        # Memory usage
        mem_out, _, _ = self.execute("free | grep Mem | awk '{print ($3/$2) * 100.0}'")
        stats['memory_usage'] = float(mem_out.strip()) if mem_out.strip() else 0
        
        # Disk usage
        disk_out, _, _ = self.execute("df -h / | tail -1 | awk '{print $5}'")
        stats['disk_usage'] = float(disk_out.strip().replace('%', '')) if disk_out.strip() else 0
        
        # NGINX status
        nginx_out, _, exit_code = self.execute("systemctl is-active nginx")
        stats['nginx_running'] = exit_code == 0 and nginx_out.strip() == 'active'
        
        # PostgreSQL status
        pg_out, _, exit_code = self.execute("systemctl is-active postgresql")
        stats['postgresql_running'] = exit_code == 0 and pg_out.strip() == 'active'
        
        # PM2 status (as deployer user - use full NVM path)
        pm2_cmd = f"sudo -u deployer {self.PM2_PATH} jlist"
        pm2_out, pm2_err, _ = self.execute(pm2_cmd)
        try:
            pm2_data = json.loads(pm2_out) if pm2_out.strip() else []
            stats['pm2_processes'] = len(pm2_data)
            stats['pm2_running'] = sum(1 for p in pm2_data if p.get('pm2_env', {}).get('status') == 'online')
        except Exception as e:
            # Debug: show what went wrong
            stats['pm2_processes'] = 0
            stats['pm2_running'] = 0
            stats['pm2_error'] = str(e)
        
        return stats
    
    def get_sites(self) -> List[Dict]:
        """Get list of configured sites"""
        sites = []
        
        # Get NGINX sites
        nginx_out, _, _ = self.execute("ls -1 /etc/nginx/sites-enabled/")
        site_files = [s.strip() for s in nginx_out.split('\n') if s.strip() and s.strip() != 'default']
        
        for site_file in site_files:
            site_info = {'name': site_file, 'nginx_enabled': True}
            
            # Check if site is responding
            https_out, _, exit_code = self.execute(f"curl -sk -o /dev/null -w '%{{http_code}}' https://{site_file}")
            site_info['https_status'] = https_out.strip() if exit_code == 0 else 'N/A'
            
            # Check SSL certificate expiry
            cert_out, _, exit_code = self.execute(
                f"echo | openssl s_client -servername {site_file} -connect {site_file}:443 2>/dev/null | "
                f"openssl x509 -noout -dates | grep notAfter | cut -d= -f2"
            )
            if exit_code == 0 and cert_out.strip():
                try:
                    expiry_date = datetime.strptime(cert_out.strip(), "%b %d %H:%M:%S %Y %Z")
                    days_left = (expiry_date - datetime.now()).days
                    site_info['ssl_days_left'] = days_left
                except:
                    site_info['ssl_days_left'] = None
            else:
                site_info['ssl_days_left'] = None
            
            # Check if PM2 app exists for this domain
            pm2_check_cmd = f"sudo -u deployer {self.PM2_PATH} show {site_file}"
            pm2_out, _, exit_code = self.execute(pm2_check_cmd)
            site_info['pm2_running'] = exit_code == 0 and "online" in pm2_out.lower()
            
            sites.append(site_info)
        
        return sites
    
    def provision_site(self, domain: str, enable_www: bool = True, app_port: int = 3000, setup_dns: bool = True) -> bool:
        """Provision a new site with NGINX, SSL, DNS (via Cloudflare), and Coming Soon page"""
        
        self.console.print(f"\n[cyan]Provisioning {domain}...[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            # Step 0: Configure DNS if Cloudflare is available and setup_dns is True
            if setup_dns and self.cloudflare:
                task = progress.add_task("Configuring DNS records...", total=None)
                
                # Create A record for main domain
                if not self.cloudflare.ensure_a_record(domain, self.host, proxied=False):
                    self.console.print("[yellow]Warning: Failed to create main domain DNS record[/yellow]")
                
                # Create A record for www subdomain if enabled
                if enable_www:
                    www_domain = f"www.{domain}"
                    if not self.cloudflare.ensure_a_record(www_domain, self.host, proxied=False):
                        self.console.print("[yellow]Warning: Failed to create www DNS record[/yellow]")
                
                progress.update(task, completed=True)
                
                # Step 0b: Verify DNS propagation
                task = progress.add_task("Verifying DNS propagation (this may take a moment)...", total=None)
                dns_ready = self.cloudflare.verify_dns_propagation(domain, self.host, timeout=60)
                if not dns_ready:
                    self.console.print("[yellow]Warning: DNS may not be fully propagated. SSL setup might fail.[/yellow]")
                    self.console.print("[yellow]You may need to run SSL setup again in a few minutes.[/yellow]")
                progress.update(task, completed=True)
            elif setup_dns and not self.cloudflare:
                self.console.print("[yellow]Cloudflare not configured - skipping DNS setup[/yellow]")
                self.console.print("[yellow]Please manually configure DNS before SSL will work[/yellow]")
            
            # Step 1: Create directory structure
            task = progress.add_task("Creating directory structure...", total=None)
            app_dir = f"/home/deployer/apps/{domain}"
            commands = [
                f"mkdir -p {app_dir}/public",
                f"mkdir -p {app_dir}/logs",
                f"chown -R deployer:deployer {app_dir}"
            ]
            
            for cmd in commands:
                _, stderr, exit_code = self.execute(cmd, use_sudo=True)
                if exit_code != 0:
                    self.console.print(f"[red]Failed to create directories: {stderr}[/red]")
                    return False
            progress.update(task, completed=True)
            
            # Step 2: Create Coming Soon page
            task = progress.add_task("Creating Coming Soon page...", total=None)
            coming_soon_html = self._generate_coming_soon_page(domain)
            
            # Write HTML file
            _, _, exit_code = self.execute(
                f"cat > {app_dir}/public/index.html << 'EOFHTML'\n{coming_soon_html}\nEOFHTML",
                use_sudo=True
            )
            if exit_code != 0:
                self.console.print("[red]Failed to create Coming Soon page[/red]")
                return False
            
            self.execute(f"chown deployer:deployer {app_dir}/public/index.html", use_sudo=True)
            progress.update(task, completed=True)
            
            # Step 3: Create NGINX configuration
            task = progress.add_task("Configuring NGINX...", total=None)
            nginx_config = self._generate_nginx_config(domain, enable_www, app_port, coming_soon=True)
            
            config_path = f"/etc/nginx/sites-available/{domain}"
            _, stderr, exit_code = self.execute(
                f"cat > {config_path} << 'EOFNGINX'\n{nginx_config}\nEOFNGINX",
                use_sudo=True
            )
            if exit_code != 0:
                self.console.print(f"[red]Failed to create NGINX config: {stderr}[/red]")
                return False
            
            # Enable site
            self.execute(f"ln -sf {config_path} /etc/nginx/sites-enabled/{domain}", use_sudo=True)
            progress.update(task, completed=True)
            
            # Step 4: Test NGINX configuration
            task = progress.add_task("Testing NGINX configuration...", total=None)
            _, stderr, exit_code = self.execute("nginx -t", use_sudo=True)
            if exit_code != 0:
                self.console.print(f"[red]NGINX config test failed: {stderr}[/red]")
                return False
            progress.update(task, completed=True)
            
            # Step 5: Reload NGINX
            task = progress.add_task("Reloading NGINX...", total=None)
            self.execute("systemctl reload nginx", use_sudo=True)
            progress.update(task, completed=True)
            
            # Step 6: Obtain SSL certificate
            task = progress.add_task("Obtaining SSL certificate (this may take a moment)...", total=None)
            
            domains_arg = f"-d {domain}"
            if enable_www:
                domains_arg += f" -d www.{domain}"
            
            certbot_cmd = f"certbot --nginx {domains_arg} --non-interactive --agree-tos --redirect --register-unsafely-without-email"
            _, stderr, exit_code = self.execute(certbot_cmd, use_sudo=True)
            
            if exit_code != 0:
                self.console.print(f"[yellow]Warning: SSL certificate setup had issues: {stderr}[/yellow]")
                self.console.print("[yellow]You may need to verify DNS is pointing to this server[/yellow]")
            else:
                progress.update(task, completed=True)
        
        self.console.print(f"\n[green]✓ Successfully provisioned {domain}![/green]")
        self.console.print(f"[dim]Coming Soon page is now live at https://{domain}[/dim]")
        return True
    
    def _generate_coming_soon_page(self, domain: str) -> str:
        """Generate a beautiful Coming Soon HTML page"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coming Soon - {domain}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            overflow: hidden;
            position: relative;
        }}
        
        .background-animation {{
            position: absolute;
            width: 100%;
            height: 100%;
            overflow: hidden;
            z-index: 0;
        }}
        
        .circle {{
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.1);
            animation: float 20s infinite ease-in-out;
        }}
        
        .circle:nth-child(1) {{
            width: 300px;
            height: 300px;
            top: 10%;
            left: 10%;
            animation-delay: 0s;
        }}
        
        .circle:nth-child(2) {{
            width: 200px;
            height: 200px;
            top: 60%;
            right: 15%;
            animation-delay: 4s;
        }}
        
        .circle:nth-child(3) {{
            width: 150px;
            height: 150px;
            bottom: 20%;
            left: 20%;
            animation-delay: 2s;
        }}
        
        @keyframes float {{
            0%, 100% {{
                transform: translateY(0px) scale(1);
            }}
            50% {{
                transform: translateY(-50px) scale(1.1);
            }}
        }}
        
        .container {{
            text-align: center;
            z-index: 1;
            max-width: 800px;
            padding: 40px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        
        h1 {{
            font-size: 4rem;
            font-weight: 700;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
            animation: fadeInDown 1s ease-out;
        }}
        
        .domain {{
            font-size: 2rem;
            font-weight: 300;
            margin-bottom: 30px;
            opacity: 0.9;
            animation: fadeInUp 1s ease-out 0.3s both;
        }}
        
        .message {{
            font-size: 1.5rem;
            margin-bottom: 40px;
            opacity: 0.8;
            line-height: 1.6;
            animation: fadeInUp 1s ease-out 0.6s both;
        }}
        
        .loader {{
            display: inline-block;
            width: 60px;
            height: 60px;
            border: 5px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s linear infinite, fadeInUp 1s ease-out 0.9s both;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        @keyframes fadeInDown {{
            from {{
                opacity: 0;
                transform: translateY(-50px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(50px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        @media (max-width: 768px) {{
            h1 {{
                font-size: 2.5rem;
            }}
            .domain {{
                font-size: 1.5rem;
            }}
            .message {{
                font-size: 1.2rem;
            }}
            .container {{
                padding: 30px 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="background-animation">
        <div class="circle"></div>
        <div class="circle"></div>
        <div class="circle"></div>
    </div>
    
    <div class="container">
        <h1>Coming Soon</h1>
        <div class="domain">{domain}</div>
        <div class="message">
            Something amazing is being built here.<br>
            Stay tuned for the launch!
        </div>
        <div class="loader"></div>
    </div>
</body>
</html>"""
    
    def _generate_nginx_config(self, domain: str, enable_www: bool, app_port: int, coming_soon: bool = False) -> str:
        """Generate NGINX configuration"""
        
        server_names = domain
        if enable_www:
            server_names += f" www.{domain}"
        
        if coming_soon:
            # Serve static Coming Soon page
            location_block = f"""
    location / {{
        root /home/deployer/apps/{domain}/public;
        index index.html;
        try_files $uri $uri/ =404;
    }}"""
        else:
            # Proxy to Next.js application
            location_block = f"""
    location / {{
        proxy_pass http://localhost:{app_port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }}"""
        
        return f"""# NGINX configuration for {domain}
# Generated by VPS Manager

server {{
    listen 80;
    listen [::]:80;
    server_name {server_names};
    
    # Redirect HTTP to HTTPS (will be configured by certbot)
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name {server_names};
    
    # SSL certificates (will be configured by certbot)
    # ssl_certificate /etc/letsencrypt/live/{domain}/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Logging
    access_log /home/deployer/apps/{domain}/logs/access.log;
    error_log /home/deployer/apps/{domain}/logs/error.log;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    {location_block}
}}"""
    
    def take_site_offline(self, domain: str) -> bool:
        """Take a site offline (park mode)"""
        self.console.print(f"\n[yellow]Taking {domain} offline...[/yellow]")
        
        # Update NGINX config to serve Coming Soon page
        app_dir = f"/home/deployer/apps/{domain}"
        
        # Check if Coming Soon page exists, create if not
        _, _, exit_code = self.execute(f"test -f {app_dir}/public/index.html")
        if exit_code != 0:
            coming_soon_html = self._generate_coming_soon_page(domain)
            self.execute(f"mkdir -p {app_dir}/public", use_sudo=True)
            self.execute(
                f"cat > {app_dir}/public/index.html << 'EOFHTML'\n{coming_soon_html}\nEOFHTML",
                use_sudo=True
            )
            self.execute(f"chown -R deployer:deployer {app_dir}/public", use_sudo=True)
        
        # Update NGINX to serve static page
        nginx_config = self._generate_nginx_config(domain, True, 3000, coming_soon=True)
        config_path = f"/etc/nginx/sites-available/{domain}"
        
        _, stderr, exit_code = self.execute(
            f"cat > {config_path} << 'EOFNGINX'\n{nginx_config}\nEOFNGINX",
            use_sudo=True
        )
        
        if exit_code != 0:
            self.console.print(f"[red]Failed to update NGINX config: {stderr}[/red]")
            return False
        
        # Test and reload NGINX
        _, stderr, exit_code = self.execute("nginx -t", use_sudo=True)
        if exit_code != 0:
            self.console.print(f"[red]NGINX test failed: {stderr}[/red]")
            return False
        
        self.execute("systemctl reload nginx", use_sudo=True)
        
        # Stop PM2 process if running
        self.execute(f"sudo -u deployer {self.PM2_PATH} stop {domain}")
        
        self.console.print(f"[green]✓ {domain} is now offline (Coming Soon page active)[/green]")
        return True
    
    def remove_site(self, domain: str) -> bool:
        """Completely remove a site provisioning"""
        
        if not Confirm.ask(f"[red]Are you sure you want to completely remove {domain}?[/red]"):
            return False
        
        self.console.print(f"\n[red]Removing {domain}...[/red]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            # Stop PM2 process
            task = progress.add_task("Stopping PM2 process...", total=None)
            self.execute(f"sudo -u deployer {self.PM2_PATH} delete {domain}")
            progress.update(task, completed=True)
            
            # Remove NGINX config
            task = progress.add_task("Removing NGINX configuration...", total=None)
            self.execute(f"rm -f /etc/nginx/sites-enabled/{domain}", use_sudo=True)
            self.execute(f"rm -f /etc/nginx/sites-available/{domain}", use_sudo=True)
            self.execute("systemctl reload nginx", use_sudo=True)
            progress.update(task, completed=True)
            
            # Remove SSL certificate
            task = progress.add_task("Removing SSL certificate...", total=None)
            self.execute(f"certbot delete --cert-name {domain} --non-interactive", use_sudo=True)
            progress.update(task, completed=True)
            
            # Remove application directory (ask for confirmation)
            if Confirm.ask(f"[yellow]Remove application directory /home/deployer/apps/{domain}?[/yellow]"):
                task = progress.add_task("Removing application files...", total=None)
                self.execute(f"rm -rf /home/deployer/apps/{domain}", use_sudo=True)
                progress.update(task, completed=True)
        
        self.console.print(f"[green]✓ {domain} has been completely removed[/green]")
        return True
    
    def restart_service(self, service: str) -> bool:
        """Restart a system service"""
        self.console.print(f"\n[cyan]Restarting {service}...[/cyan]")
        
        if service == "pm2":
            _, stderr, exit_code = self.execute(f"sudo -u deployer {self.PM2_PATH} restart all")
        elif service == "nginx":
            _, stderr, exit_code = self.execute("systemctl restart nginx", use_sudo=True)
        elif service == "postgresql":
            _, stderr, exit_code = self.execute("systemctl restart postgresql", use_sudo=True)
        else:
            self.console.print(f"[red]Unknown service: {service}[/red]")
            return False
        
        if exit_code != 0:
            self.console.print(f"[red]Failed to restart {service}: {stderr}[/red]")
            return False
        
        self.console.print(f"[green]✓ {service} restarted successfully[/green]")
        return True
    
    def restart_all_services(self) -> bool:
        """Restart all managed services"""
        if not Confirm.ask("[yellow]Restart ALL services (NGINX, PM2, PostgreSQL)?[/yellow]"):
            return False
        
        services = ["nginx", "pm2", "postgresql"]
        for service in services:
            self.restart_service(service)
        
        return True
    
    def view_dns_records(self, domain: str):
        """View DNS records for a domain"""
        if not self.cloudflare:
            self.console.print("[red]Cloudflare not configured[/red]")
            return
        
        self.console.print(f"\n[cyan]Fetching DNS records for {domain}...[/cyan]")
        records = self.cloudflare.list_dns_records(domain)
        
        if not records:
            self.console.print("[yellow]No DNS records found[/yellow]")
            return
        
        table = Table(title=f"DNS Records - {domain}", box=box.ROUNDED)
        table.add_column("Type", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Content", style="yellow")
        table.add_column("Proxied", justify="center")
        table.add_column("TTL", justify="center")
        
        for record in records:
            proxied = "🟠" if record.get('proxied') else "⚪"
            ttl = str(record.get('ttl', 'Auto')) if record.get('ttl') != 1 else "Auto"
            table.add_row(
                record['type'],
                record['name'],
                record['content'],
                proxied,
                ttl
            )
        
        self.console.print(table)
    
    def manage_dns_for_site(self, domain: str):
        """Interactive DNS management for a specific site"""
        if not self.cloudflare:
            self.console.print("[red]Cloudflare not configured[/red]")
            return
        
        while True:
            self.console.clear()
            self.console.print(f"[bold cyan]DNS Management - {domain}[/bold cyan]\n")
            
            # Show current DNS records
            self.view_dns_records(domain)
            
            self.console.print("\n[cyan]Options:[/cyan]")
            self.console.print("  1. Update DNS to point to this server")
            self.console.print("  2. Add www subdomain")
            self.console.print("  3. Delete DNS records")
            self.console.print("  4. Toggle Cloudflare proxy")
            self.console.print("  b. Back to main menu")
            
            choice = Prompt.ask("\n[cyan]Select an option[/cyan]", choices=["1", "2", "3", "4", "b"])
            
            if choice == "1":
                self.cloudflare.ensure_a_record(domain, self.host, proxied=False)
                Prompt.ask("\n[dim]Press Enter to continue[/dim]")
            
            elif choice == "2":
                www_domain = f"www.{domain}"
                self.cloudflare.ensure_a_record(www_domain, self.host, proxied=False)
                Prompt.ask("\n[dim]Press Enter to continue[/dim]")
            
            elif choice == "3":
                records = self.cloudflare.list_dns_records(domain)
                if records:
                    self.console.print("\n[yellow]Delete all DNS records for this domain?[/yellow]")
                    if Confirm.ask("Are you sure?"):
                        for record in records:
                            self.cloudflare.delete_dns_record(record['id'], domain)
                Prompt.ask("\n[dim]Press Enter to continue[/dim]")
            
            elif choice == "4":
                records = self.cloudflare.list_dns_records(domain)
                if records:
                    for record in records:
                        if record['type'] == 'A':
                            new_proxied = not record.get('proxied', False)
                            self.cloudflare.update_a_record(
                                record['id'],
                                record['name'],
                                record['content'],
                                proxied=new_proxied
                            )
                Prompt.ask("\n[dim]Press Enter to continue[/dim]")
            
            elif choice == "b":
                break


class MonitorDashboard:
    """Live monitoring dashboard"""
    
    def __init__(self, vps: VPSManager):
        self.vps = vps
        self.console = Console()
    
    def generate_dashboard(self) -> Layout:
        """Generate dashboard layout"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # Header
        header = Panel(
            f"[bold cyan]VPS Manager[/bold cyan] - {self.vps.host}:{self.vps.port}",
            style="cyan"
        )
        layout["header"].update(header)
        
        # Body - split into system stats and sites
        layout["body"].split_row(
            Layout(name="stats"),
            Layout(name="sites")
        )
        
        # System Stats
        stats = self.vps.get_system_stats()
        stats_table = Table(title="System Status", box=box.ROUNDED, show_header=False)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value")
        
        # CPU
        cpu_bar = self._create_bar(stats['cpu_usage'], 100)
        stats_table.add_row("CPU", f"{cpu_bar} {stats['cpu_usage']:.1f}%")
        
        # Memory
        mem_bar = self._create_bar(stats['memory_usage'], 100)
        stats_table.add_row("Memory", f"{mem_bar} {stats['memory_usage']:.1f}%")
        
        # Disk
        disk_bar = self._create_bar(stats['disk_usage'], 100)
        stats_table.add_row("Disk", f"{disk_bar} {stats['disk_usage']:.1f}%")
        
        stats_table.add_row("", "")
        
        # Services
        nginx_status = "🟢 Running" if stats['nginx_running'] else "🔴 Stopped"
        stats_table.add_row("NGINX", nginx_status)
        
        pg_status = "🟢 Running" if stats['postgresql_running'] else "🔴 Stopped"
        stats_table.add_row("PostgreSQL", pg_status)
        
        pm2_status = f"🟢 {stats['pm2_running']}/{stats['pm2_processes']} online"
        stats_table.add_row("PM2", pm2_status)
        
        layout["stats"].update(Panel(stats_table, title="[bold]System[/bold]"))
        
        # Sites Status
        sites = self.vps.get_sites()
        sites_table = Table(title="Sites", box=box.ROUNDED)
        sites_table.add_column("Domain", style="cyan")
        sites_table.add_column("HTTPS", justify="center")
        sites_table.add_column("SSL", justify="center")
        sites_table.add_column("PM2", justify="center")
        
        for site in sites:
            https_status = "✓" if site['https_status'] == "200" else "✗"
            
            if site['ssl_days_left'] is not None:
                if site['ssl_days_left'] > 30:
                    ssl_status = f"🟢 {site['ssl_days_left']}d"
                elif site['ssl_days_left'] > 7:
                    ssl_status = f"🟡 {site['ssl_days_left']}d"
                else:
                    ssl_status = f"🔴 {site['ssl_days_left']}d"
            else:
                ssl_status = "🔴 None"
            
            pm2_status = "🟢" if site['pm2_running'] else "🔴"
            
            sites_table.add_row(site['name'], https_status, ssl_status, pm2_status)
        
        layout["sites"].update(Panel(sites_table, title="[bold]Sites[/bold]"))
        
        # Footer
        footer = Panel(
            "[dim]Press Ctrl+C to return to menu | Updates every 5 seconds[/dim]",
            style="dim"
        )
        layout["footer"].update(footer)
        
        return layout
    
    def _create_bar(self, value: float, max_value: float, width: int = 20) -> str:
        """Create a visual bar for metrics"""
        filled = int((value / max_value) * width)
        bar = "█" * filled + "░" * (width - filled)
        
        if value < 60:
            color = "green"
        elif value < 80:
            color = "yellow"
        else:
            color = "red"
        
        return f"[{color}]{bar}[/{color}]"
    
    def run(self, interval: int = 5):
        """Run live monitoring dashboard"""
        try:
            with Live(self.generate_dashboard(), refresh_per_second=1, console=self.console) as live:
                while True:
                    time.sleep(interval)
                    live.update(self.generate_dashboard())
        except KeyboardInterrupt:
            pass


def main_menu(vps: VPSManager):
    """Display interactive main menu"""
    console = Console()
    
    while True:
        console.clear()
        
        # Title
        cf_status = "✓ Connected" if vps.cloudflare and vps.cloudflare.verify_credentials() else "✗ Not configured"
        title = Panel(
            f"[bold cyan]VPS Manager[/bold cyan]\n"
            f"Server: {vps.host}:{vps.port}\n"
            f"Cloudflare API: {cf_status}",
            style="cyan",
            box=box.DOUBLE
        )
        console.print(title)
        console.print()
        
        # Menu options
        menu = Table(show_header=False, box=None, padding=(0, 2))
        menu.add_column("Option", style="cyan bold")
        menu.add_column("Description")
        
        menu.add_row("1", "Live Monitoring Dashboard")
        menu.add_row("2", "Provision New Site (with DNS)")
        menu.add_row("3", "Manage DNS Records")
        menu.add_row("4", "Take Site Offline (Park)")
        menu.add_row("5", "Remove Site Provisioning")
        menu.add_row("6", "Restart Service")
        menu.add_row("7", "Restart All Services")
        menu.add_row("q", "Quit")
        
        console.print(menu)
        console.print()
        
        choice = Prompt.ask("[cyan]Select an option[/cyan]", choices=["1", "2", "3", "4", "5", "6", "7", "q"])
        
        if choice == "1":
            # Live monitoring
            dashboard = MonitorDashboard(vps)
            dashboard.run()
        
        elif choice == "2":
            # Provision new site
            domain = Prompt.ask("\n[cyan]Enter domain name[/cyan] (e.g., example.com)")
            enable_www = Confirm.ask("Enable www subdomain?", default=True)
            
            if vps.cloudflare:
                setup_dns = Confirm.ask("Configure DNS via Cloudflare?", default=True)
            else:
                setup_dns = False
                console.print("[yellow]Cloudflare not configured - DNS setup will be skipped[/yellow]")
            
            vps.provision_site(domain, enable_www, setup_dns=setup_dns)
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")
        
        elif choice == "3":
            # DNS management
            if not vps.cloudflare:
                console.print("\n[red]Cloudflare API not configured[/red]")
                console.print("[yellow]To enable DNS management, configure Cloudflare API credentials[/yellow]")
                Prompt.ask("\n[dim]Press Enter to continue[/dim]")
                continue
            
            console.print("\n[cyan]DNS Management Options:[/cyan]")
            console.print("  1. View DNS records for domain")
            console.print("  2. Manage DNS for specific domain")
            console.print("  3. Back")
            
            dns_choice = Prompt.ask("\nSelect option", choices=["1", "2", "3"])
            
            if dns_choice == "1":
                domain = Prompt.ask("\n[cyan]Enter domain name[/cyan]")
                vps.view_dns_records(domain)
                Prompt.ask("\n[dim]Press Enter to continue[/dim]")
            elif dns_choice == "2":
                domain = Prompt.ask("\n[cyan]Enter domain name[/cyan]")
                vps.manage_dns_for_site(domain)
        
        elif choice == "4":
            # Take site offline
            sites = vps.get_sites()
            if not sites:
                console.print("[yellow]No sites found[/yellow]")
                Prompt.ask("\n[dim]Press Enter to continue[/dim]")
                continue
            
            console.print("\n[cyan]Available sites:[/cyan]")
            for i, site in enumerate(sites, 1):
                console.print(f"  {i}. {site['name']}")
            
            site_choice = Prompt.ask("\nEnter site number")
            try:
                site_idx = int(site_choice) - 1
                if 0 <= site_idx < len(sites):
                    vps.take_site_offline(sites[site_idx]['name'])
                else:
                    console.print("[red]Invalid selection[/red]")
            except ValueError:
                console.print("[red]Invalid input[/red]")
            
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")
        
        elif choice == "4":
            # Remove site
            sites = vps.get_sites()
            if not sites:
                console.print("[yellow]No sites found[/yellow]")
                Prompt.ask("\n[dim]Press Enter to continue[/dim]")
                continue
            
            console.print("\n[cyan]Available sites:[/cyan]")
            for i, site in enumerate(sites, 1):
                console.print(f"  {i}. {site['name']}")
            
            site_choice = Prompt.ask("\nEnter site number")
            try:
                site_idx = int(site_choice) - 1
                if 0 <= site_idx < len(sites):
                    vps.remove_site(sites[site_idx]['name'])
                else:
                    console.print("[red]Invalid selection[/red]")
            except ValueError:
                console.print("[red]Invalid input[/red]")
            
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")
        
        elif choice == "5":
            # Restart service
            console.print("\n[cyan]Available services:[/cyan]")
            console.print("  1. NGINX")
            console.print("  2. PM2")
            console.print("  3. PostgreSQL")
            
            service_choice = Prompt.ask("\nEnter service number", choices=["1", "2", "3"])
            service_map = {"1": "nginx", "2": "pm2", "3": "postgresql"}
            vps.restart_service(service_map[service_choice])
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")
        
        elif choice == "6":
            # Restart all services
            vps.restart_all_services()
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")
        
        elif choice == "q":
            console.print("\n[cyan]Disconnecting...[/cyan]")
            break


def main():
    """Main entry point"""
    console = Console()
    
    console.print("\n[bold cyan]VPS Manager[/bold cyan]")
    
    # Show configuration source
    config_source = []
    if os.environ.get('VPS_SRV1_IP'):
        config_source.append("VPS from env")
    if os.environ.get('CLOUDFLARE_API_TOKEN'):
        config_source.append("Cloudflare from env")
    
    if config_source:
        console.print(f"[dim]Config: {', '.join(config_source)}[/dim]")
    
    console.print(f"Connecting to {VPS_SSH_USERNAME}@{VPS_HOST}:{VPS_SSH_PORT}...")
    
    # Initialize Cloudflare if API token is configured
    cloudflare = None
    
    # Debug: Show what we're checking
    console.print(f"[dim]Checking CLOUDFLARE_API_TOKEN variable...[/dim]")
    console.print(f"[dim]Token length: {len(CLOUDFLARE_API_TOKEN)}[/dim]")
    console.print(f"[dim]Token type: {type(CLOUDFLARE_API_TOKEN)}[/dim]")
    
    # Check if API token is set
    if not CLOUDFLARE_API_TOKEN or CLOUDFLARE_API_TOKEN.strip() == "":
        console.print("[yellow]⚠ Cloudflare not configured[/yellow]")
        console.print("[dim]To configure, either:[/dim]")
        console.print("[dim]  1. Run: ./setup-env.sh[/dim]")
        console.print("[dim]  2. Or edit CLOUDFLARE_API_TOKEN at line ~44[/dim]")
        console.print(f"[dim]Current value: '{CLOUDFLARE_API_TOKEN}'[/dim]")
    else:
        token_preview = f"{CLOUDFLARE_API_TOKEN[:8]}...{CLOUDFLARE_API_TOKEN[-4:]}"
        console.print(f"[green]✓ Cloudflare token found: {len(CLOUDFLARE_API_TOKEN)} chars[/green]")
        console.print(f"[dim]Token preview: {token_preview}[/dim]")
        
        try:
            cloudflare = CloudflareManager(CLOUDFLARE_API_TOKEN.strip())
            console.print("[dim]Verifying credentials with Cloudflare...[/dim]")
            
            if cloudflare.verify_credentials():
                console.print("[green]✓ Cloudflare API connected successfully![/green]")
            else:
                console.print("[red]✗ Cloudflare credentials verification failed[/red]")
                console.print("[yellow]Check your API token has these permissions:[/yellow]")
                console.print("[yellow]  - Zone:DNS:Edit[/yellow]")
                console.print("[yellow]  - Zone:Zone:Read[/yellow]")
                console.print("[yellow]  - Zone:Zone:Edit (for zone creation)[/yellow]")
                cloudflare = None
        except Exception as e:
            console.print(f"[red]✗ Cloudflare initialization failed: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
            cloudflare = None
    
    vps = VPSManager(VPS_HOST, VPS_SSH_USERNAME, VPS_SSH_PORT, cloudflare=cloudflare)
    
    if not vps.connect():
        console.print("[red]Failed to connect. Exiting.[/red]")
        sys.exit(1)
    
    console.print("[green]✓ SSH Connected successfully![/green]")
    time.sleep(1)
    
    try:
        main_menu(vps)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
    finally:
        vps.disconnect()
        console.print("[dim]Disconnected.[/dim]\n")


if __name__ == "__main__":
    main()
