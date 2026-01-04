# VPS Manager

A comprehensive Python-based VPS management tool with a beautiful terminal UI for managing NGINX sites, SSL certificates, and services. This tool remotely manages a VPS server via SSH and integrates with Cloudflare for DNS automation.

## How It Works

**VPS Manager** is a **local client application** that connects to your VPS server via **SSH key-based authentication** and provides an interactive terminal interface to manage your infrastructure. It does not run on the server—it runs on your local machine (Mac, Linux, etc.) and sends commands to the remote VPS.

### Architecture

```
Your Local Machine (iMac)
    ↓ SSH Connection (key-based auth)
    ↓
VPS Server (Remote)
    ├── NGINX (web server)
    ├── PM2 (process manager)
    ├── PostgreSQL (database)
    ├── Certbot (SSL certificates)
    └── Application files
```

**VPS Manager** connects to your VPS and:
1. Executes remote commands via SSH (using Paramiko library)
2. Retrieves system information (CPU, memory, disk usage)
3. Manages NGINX configurations
4. Obtains SSL certificates via Let's Encrypt
5. Creates DNS records via Cloudflare API

## Features

✨ **Live Monitoring Dashboard**
- Real-time system metrics (CPU, Memory, Disk)
- Service status (NGINX, PostgreSQL, PM2)
- Site health monitoring (HTTPS status, SSL expiry, PM2 process status)
- Auto-refreshing every 5 seconds
- Color-coded health indicators

🚀 **Site Provisioning**
- One-command site setup with complete automation
- **Automatic DNS configuration via Cloudflare API**
- **Automatic DNS propagation verification**
- Automatic NGINX configuration generation
- SSL certificate automatic retrieval via Let's Encrypt (Certbot)
- Beautiful responsive "Coming Soon" landing page with animations
- www subdomain support (optional)
- Proper directory structure creation (`/home/deployer/apps/{domain}/`)

🌐 **DNS Management (Cloudflare)**
- Automatic DNS record creation during provisioning
- View all DNS records in your zone
- Manage DNS for specific domains
- Update records to point to your VPS
- Toggle Cloudflare proxy settings (orange cloud on/off)
- Add/remove www subdomains
- Delete DNS records
- Automatic zone creation if domain not yet in Cloudflare

🔧 **Site Management**
- Take sites offline (park mode with Coming Soon page)
- Complete site removal (NGINX config, SSL certificate, DNS records, files)
- Individual service restarts (NGINX, PM2, PostgreSQL)
- Restart all services at once
- Confirmation prompts for destructive operations

🎨 **Beautiful Terminal UI**
- Color-coded status indicators (green, yellow, red)
- Progress bars and spinners for long operations
- Clean table layouts for data presentation
- Interactive menus with validation
- Rich text formatting and visual hierarchy

## Prerequisites

**Local Machine:**
- Python 3.8 or higher
- SSH key pair already generated and added to your VPS (`~/.ssh/id_rsa`, `~/.ssh/id_ed25519`, etc.)
- Network access to your VPS (open SSH port)

**VPS Server Requirements:**
- NGINX (web server)
- PM2 (Node.js process manager)
- PostgreSQL (database server)
- Certbot (Let's Encrypt SSL certificates)
- Passwordless sudo access for the SSH user (required for managing services)
- NVM with Node.js (for PM2 operations)

**Optional:**
- Cloudflare account with API token (for automated DNS management)
- If using Cloudflare, domains must be registered and accessible

## Cloudflare Configuration (Optional but Recommended)

The VPS Manager includes Cloudflare DNS integration for automated DNS record management.

### Quick Setup

1. **Get Cloudflare API Token:**
   - Cloudflare Dashboard → Profile → API Tokens → Create Token
   - Use template: "Edit zone DNS"
   - Add permission: Zone:Zone:Edit (for automatic zone creation)
   - Create token and copy it

2. **Edit vps-manager.py (lines 31-42):**
   ```python
   # Cloudflare API Configuration
   CLOUDFLARE_API_TOKEN = "your_token_here"  # Paste your token
   ```

3. **That's it!** No Zone ID needed - zones are auto-detected

**With Cloudflare configured:**
- ✅ Automatic DNS record creation during provisioning
- ✅ Automatic zone creation (if domain not in Cloudflare yet)
- ✅ DNS propagation verification before SSL setup
- ✅ Interactive DNS management for all your domains
- ✅ Toggle Cloudflare proxy settings

**Without Cloudflare:**
- ⚠️ Manual DNS configuration required
- ⚠️ Must wait for DNS propagation before running provisioning

See [CLOUDFLARE-QUICKSTART.md](CLOUDFLARE-QUICKSTART.md) for detailed setup.

## Authentication & SSH Connection

VPS Manager uses **SSH key-based authentication** (no passwords needed). It requires:
1. SSH key pair generated on your local machine
2. Public key added to your VPS's `~/.ssh/authorized_keys`
3. SSH key in your local `~/.ssh/` directory

The tool uses Paramiko (Python SSH library) which automatically tries SSH keys in standard locations:
- `~/.ssh/id_rsa`
- `~/.ssh/id_dsa`
- `~/.ssh/id_ecdsa`
- `~/.ssh/id_ed25519`

**To verify SSH access works:**
```bash
ssh -p YOUR_SSH_PORT username@your-vps-ip.com
# Should connect without prompting for a password
```

## Installation

1. **Clone or download the files:**
   ```bash
   # Download vps-manager.py and requirements.txt to your local machine
   git clone <repo> vps-manager
   cd vps-manager
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify requirements.txt contains:**
   ```
   paramiko
   rich
   requests
   ```

4. **Configure vps-manager.py (lines 48-60):**
   Edit the configuration at the top of the file or use environment variables:
   ```python
   # VPS Server Configuration
   VPS_HOST = "23.29.114.83"           # Your server IP address
   VPS_SSH_USERNAME = "beinejd"        # Your SSH username
   VPS_SSH_PORT = 2223                 # Your custom SSH port
   
   # Cloudflare API Configuration (optional)
   CLOUDFLARE_API_TOKEN = ""           # Add your API token (or leave empty to disable)
   ```

5. **OR set environment variables (recommended for security):**
   ```bash
   export VPS_HOST="your-vps-ip.com"
   export VPS_PORT="2223"
   export CLOUDFLARE_API_TOKEN="your-token-here"
   ```
   
   Or use the setup script:
   ```bash
   ./setup-env.sh
   ```

6. **Make the script executable:**
   ```bash
   chmod +x vps-manager.py
   ```

## Usage

### Start the Manager
```bash
python3 vps-manager.py
```

The tool will:
1. Check configuration (VPS host, SSH credentials, Cloudflare API)
2. Attempt SSH connection to your VPS
3. Verify Cloudflare API credentials (if configured)
4. Display the interactive main menu

### Main Menu Options

#### **1. Live Monitoring Dashboard**
Displays real-time system monitoring with auto-refresh every 5 seconds.

**Shows:**
- **System Stats**: CPU usage, Memory usage, Disk usage
- **Service Status**: NGINX, PostgreSQL, PM2 (running/down)
- **Sites Table**: All provisioned sites with:
  - Domain name
  - NGINX status (enabled/disabled)
  - HTTPS response code (200, 404, etc.)
  - SSL certificate days remaining with color coding:
    - 🟢 Green: > 30 days remaining
    - 🟡 Yellow: 7-30 days remaining  
    - 🔴 Red: < 7 days or expired
  - PM2 process status (running/stopped)

**Controls:**
- Automatically refreshes every 5 seconds
- Press `Ctrl+C` to return to main menu

---

#### **2. Provision New Site (with DNS)**
Complete automated site setup in one command.

**Process:**
1. Enter domain name (e.g., `example.com`)
2. Choose whether to enable www subdomain (optional)
3. Choose whether to set up DNS via Cloudflare (if configured)
4. Tool automatically:
   - Creates DNS A records (if Cloudflare configured)
   - Verifies DNS propagation (waits up to 60 seconds)
   - Creates directory structure at `/home/deployer/apps/{domain}/`
   - Generates NGINX configuration with HTTP→HTTPS redirect
   - Creates beautiful animated Coming Soon page
   - Obtains SSL certificate from Let's Encrypt via Certbot
   - Enables the site and reloads NGINX

**Results:**
- Site is live at `https://domain.com` with Coming Soon page
- SSL certificate auto-renewed before expiry
- Ready for application deployment
- Full logging at `/home/deployer/apps/{domain}/logs/`

---

#### **3. Manage DNS Records** *(Requires Cloudflare)*
Interactive DNS management for your domains.

**Submenu Options:**

**3a. View DNS records for domain**
- Select a domain
- Shows all DNS records in that domain's zone:
  - Record type (A, CNAME, MX, etc.)
  - Record name
  - Current IP/target
  - TTL
  - Cloudflare proxy status (🟠 proxied / ⚪ DNS only)

**3b. Manage DNS for specific domain**
- Select a domain
- Interactive options for that domain:
  - **Update DNS to point to this server**: Creates/updates A record to VPS IP
  - **Add www subdomain**: Creates A record for `www.domain.com`
  - **Delete DNS record**: Remove unwanted records
  - **Toggle Cloudflare proxy**: Enable/disable orange cloud proxy

**Features:**
- Automatic zone creation if domain doesn't exist in Cloudflare
- Zone caching for faster operations
- Error handling and confirmation prompts

---

#### **4. Take Site Offline (Park)**
Temporarily take a site offline while keeping infrastructure intact.

**Process:**
1. Select site from list of provisioned sites
2. Tool detects original site configuration (www setting, app port)
3. Switches site to Coming Soon page
4. Preserves SSL certificate and HTTPS access
5. Stops PM2 application process (if running)
6. NGINX remains serving Coming Soon page on HTTPS

**Features:**
- ✓ SSL certificate preserved (auto-detected from existing config)
- ✓ Original site configuration preserved (www subdomain, app port)
- ✓ Maintains HTTPS access with existing certificate
- ✓ PM2 process gracefully stopped

**Use Cases:**
- Temporary maintenance
- Holiday/seasonal closures
- Before re-deploying
- Database migrations with minimal downtime

**Note:** DNS records remain unchanged; site is still accessible at HTTPS

---

#### **5. Remove Site Provisioning**
Completely remove a site and its infrastructure.

**Removes:**
- NGINX configuration (`/etc/nginx/sites-enabled/{domain}`)
- SSL certificate (Let's Encrypt)
- Application directory (`/home/deployer/apps/{domain}/`)
- DNS records (if Cloudflare configured)

**Confirmation:**
- Tool prompts for confirmation before deletion
- Shows what will be removed

⚠️ **Warning:** This is irreversible. Backup application files first if needed.

---

#### **6. Clone Site Configuration**
Clone all settings from an existing site to create a new site with identical configuration.

**How It Works:**

1. Select source site (e.g., TopEngineer.US)
2. Tool auto-detects settings:
   - www subdomain enabled/disabled
   - Live app mode or Coming Soon page
   - Application port (if live app)
3. Enter new domain name (e.g., RedStartMedia.com)
4. Confirm detected settings
5. Tool provisions new site with same config + new domain

**What Gets Cloned:**
- ✓ www subdomain setting
- ✓ Application mode (Coming Soon or live app)
- ✓ Application port (if applicable)
- ✓ NGINX configuration structure
- ✓ Security headers and logging setup

**What's Created New:**
- ✓ New SSL certificate (Let's Encrypt)
- ✓ New DNS records (if Cloudflare configured)
- ✓ New application directory
- ✓ New PM2 process

**Example Workflow:**

```
Existing site: TopEngineer.US
  ├─ www enabled
  ├─ Live app mode on port 3000
  └─ SSL certificate (active)
        ↓ CLONE
New site: RedStartMedia.com
  ├─ www enabled (copied)
  ├─ Live app mode on port 3000 (copied)
  ├─ SSL certificate (new)
  ├─ DNS records (new)
  └─ Ready for application deployment
```

**Benefits:**
- Saves time (no need to re-enter settings)
- Ensures consistency across sites
- Reduces configuration errors
- Maintains same infrastructure patterns

---

#### **7. Restart Service**
Restart individual services on the VPS.

**Available Services:**
- **NGINX**: Web server (handles HTTP/HTTPS traffic)
- **PM2**: Node.js process manager (runs applications)
- **PostgreSQL**: Database server

**Uses:**
- After deploying application updates
- Troubleshooting service issues
- Clearing service caches

---

#### **8. Restart All Services**
Simultaneously restart NGINX, PM2, and PostgreSQL.

**Requires confirmation before proceeding**

**Use when:**
- Deploying major updates
- Troubleshooting multiple service issues
- Resetting entire application stack

**Note:** This causes temporary downtime (a few seconds)

## Directory Structure Created

When provisioning a new site, the following structure is created:

```
/home/deployer/apps/{domain}/
├── public/
│   └── index.html          # Coming Soon page
└── logs/
    ├── access.log          # NGINX access logs
    └── error.log           # NGINX error logs
```

## System Architecture & Technologies

### Remote VPS Components

**NGINX** (Web Server)
- Acts as reverse proxy for Node.js applications
- Handles SSL/TLS termination
- Serves static files and Coming Soon pages
- Location: `/etc/nginx/sites-enabled/{domain}`
- Reloaded (not restarted) to apply changes without downtime

**PM2** (Process Manager)
- Manages Node.js application processes
- Auto-restart on crash
- Provides process monitoring and logging
- Installed via NVM at: `/home/deployer/.nvm/versions/node/v24.11.1/bin/pm2`

**PostgreSQL** (Database)
- Database server for applications
- Can be restarted independently

**Certbot** (Let's Encrypt)
- Automatically obtains SSL/TLS certificates
- Handles automatic renewal before expiry (90-day certificates)
- Stores certificates in `/etc/letsencrypt/`

### NGINX Configuration

The tool generates production-ready NGINX configurations with:

**For Coming Soon Pages (Provisioning):**
```
HTTP traffic → HTTPS redirect
↓
HTTPS traffic → Serves index.html from /home/deployer/apps/{domain}/public/
```

**For Live Applications (Ready for deployment):**
```
HTTP traffic → HTTPS redirect
↓
HTTPS traffic → Proxies to Node.js app (default port 3000)
                ├── WebSocket support
                └── X-Forwarded-* headers
```

**Features:**
- HTTP/2 support
- Security headers (X-Frame-Options, X-Content-Type-Options)
- Proper logging to `/home/deployer/apps/{domain}/logs/`
- Support for both `domain.com` and `www.domain.com`
- Automatic HTTPS enforcement

### SSL Certificates

**Let's Encrypt Integration:**
- Automatically obtained during provisioning via Certbot
- 90-day validity period
- Automatic renewal handled by Certbot (runs daily)
- No manual intervention needed

**Monitoring:**
- Dashboard shows days remaining for each certificate
- Color-coded warnings:
  - 🟢 Green: > 30 days remaining
  - 🟡 Yellow: 7-30 days remaining
  - 🔴 Red: < 7 days or expired
  - ❌ Red: Certificate does not exist

### User Permissions on VPS

The tool operates as two different users for security:

**beinejd** (SSH user with sudo access):
- Manages NGINX (start, stop, reload, test)
- Manages system services (PostgreSQL, nginx)
- Creates directories and system files
- Executes: `systemctl`, `nginx`, `certbot`

**deployer** (Application user):
- Manages application files
- Runs PM2 processes
- Owns application directory `/home/deployer/apps/{domain}/`
- Executed via: `sudo -u deployer` when needed

### Coming Soon Page

The automatically generated landing page features:

**Design:**
- Responsive mobile-friendly layout
- Animated gradient background (purple to pink)
- Floating circle animations
- Smooth fade-in transitions
- Professional appearance
- Fast load time (pure HTML/CSS, no external dependencies)

**Customization:**
- Displays the domain name in the title
- Can be manually edited at `/home/deployer/apps/{domain}/public/index.html`
- Replace with your own HTML once application is ready

### DNS Management (Cloudflare)

**How it works:**
1. **Automatic zone detection/creation**: 
   - Checks if domain exists in Cloudflare
   - Auto-creates zone if it doesn't exist
   - Caches zone IDs for speed

2. **DNS propagation verification**:
   - After creating DNS records, tool waits up to 60 seconds
   - Performs DNS resolution check to verify propagation
   - Warns if propagation fails (SSL setup may still work after more time)

3. **Record management**:
   - Creates A records pointing domain to VPS IP
   - Supports www subdomain
   - Can toggle Cloudflare proxy (orange cloud)
   - Can delete records

**Integration during provisioning:**
- Creates DNS records BEFORE running Certbot
- Verifies DNS propagation BEFORE SSL setup
- This ensures Let's Encrypt can validate domain ownership

## SSH Connection Details

**Connection Method:**
- Uses Paramiko (Python SSH library)
- Key-based authentication (no password)
- Maintains persistent connection during session
- Auto-closes on exit

**SSH Key Locations Tried (in order):**
1. `~/.ssh/id_rsa`
2. `~/.ssh/id_dsa`
3. `~/.ssh/id_ecdsa`
4. `~/.ssh/id_ed25519`

**Connection timeout:** 10 seconds per command

**Error Handling:**
- Graceful connection failure if SSH key not found
- Clear error messages if authentication fails
- Automatic reconnection if connection drops

## Troubleshooting

### SSH Connection Issues

**Error: "SSH Connection failed" or "Authentication failed"**
- Verify SSH key exists: `ls -la ~/.ssh/`
- Verify passwordless SSH works:
  ```bash
  ssh -p YOUR_SSH_PORT username@your-vps-ip.com
  # Should connect without prompting for password
  ```
- Verify public key is in VPS's `~/.ssh/authorized_keys`
- Check VPS SSH port is accessible (may be blocked by firewall)
- Ensure SSH username matches (beinejd in default config)

### Cloudflare Configuration Issues

**Error: "Cloudflare credentials verification failed"**
- Verify API token has correct permissions:
  - Zone:DNS:Edit
  - Zone:Zone:Read
  - Zone:Zone:Edit
- Create new token at: https://dash.cloudflare.com/profile/api-tokens
- Ensure token is not expired
- Copy token exactly without extra spaces

**DNS records not created**
- Verify domain is accessible on Cloudflare
- Check if domain needs to be added to Cloudflare first
- Ensure you have permission to manage that domain on Cloudflare

### Site Provisioning Issues

**Error: "DNS verification timed out"**
- This is a warning, not a fatal error
- DNS may still propagate after the timeout
- Try provisioning again in a few minutes
- Verify domain points to correct IP: `nslookup domain.com`

**Error: "SSL certificate setup had issues"**
- Ensure DNS is pointing to your VPS IP
- Verify ports 80 and 443 are open and accessible
- Check that domain is not already in use on another server
- Try again in a few minutes (DNS propagation may be delayed)

**Error: "Failed to create directories"**
- Ensure user `beinejd` has sudo access without password
- Verify `/home/deployer/` directory exists
- Check disk space: `ssh user@vps df -h`

### NGINX Configuration Issues

**Error: "NGINX config test failed"**
- Syntax error in generated config
- Usually due to special characters in domain name
- Check NGINX error logs: `ssh user@vps sudo tail -f /var/log/nginx/error.log`

**Domain not responding**
- Verify NGINX is running: Dashboard shows NGINX status
- Check DNS is pointing to VPS: `nslookup domain.com`
- Check firewall allows ports 80/443
- Verify SSL certificate exists: `ssh user@vps sudo certbot certificates`

### PM2 Process Issues

**Error: "PM2 processes: 0" on dashboard**
- Ensure NVM and Node.js are installed on VPS
- Check PM2 path in code matches: `/home/deployer/.nvm/versions/node/v24.11.1/bin/pm2`
- Verify user `deployer` exists
- PM2 may need processes started manually

**Process not running after provisioning**
- Coming Soon page is served by NGINX (no PM2 needed during provisioning)
- Deploy your application to start PM2 process
- SSH to VPS and use PM2 to start your app: `pm2 start app.js --name domain.com`

### Permission Errors

**Error: "Permission denied" when managing files**
- Verify user `beinejd` has sudo access: `ssh user@vps sudo -v`
- Verify user `deployer` exists: `ssh user@vps id deployer`
- Verify directory ownership: `ssh user@vps ls -la /home/deployer/apps/{domain}`

### General Debugging

**Enable debug output:**
- The tool prints configuration details on startup
- Look for token previews and connection status messages
- SSH errors are printed to console

**Check VPS logs:**
```bash
# NGINX errors
ssh user@vps sudo tail -f /var/log/nginx/error.log

# System messages  
ssh user@vps sudo journalctl -xe

# Certbot/Let's Encrypt logs
ssh user@vps sudo tail -f /var/log/letsencrypt/letsencrypt.log

# Application logs
ssh user@vps tail -f /home/deployer/apps/{domain}/logs/error.log
```

**Test connectivity manually:**
```bash
# Test HTTPS connection
curl -I https://domain.com

# Check DNS
nslookup domain.com
dig domain.com

# Check ports
nc -zv domain.com 80
nc -zv domain.com 443
```

## Typical Usage Workflow

### New Site Setup (Complete Example)

1. **Prepare**
   - Register domain on Cloudflare
   - Generate SSH key for local machine
   - Add public key to VPS

2. **Run VPS Manager**
   ```bash
   python3 vps-manager.py
   ```

3. **Provision Site** (Menu option 2)
   - Enter domain: `myapp.com`
   - Enable www subdomain: Yes
   - Configure DNS via Cloudflare: Yes
   - Wait for provisioning to complete (2-3 minutes)

4. **Verify** (Menu option 1)
   - Check Live Monitoring Dashboard
   - Site appears in list
   - NGINX status: enabled
   - HTTPS status: 200
   - SSL expires in: ~89 days

5. **Deploy Application**
   - SSH to VPS: `ssh -p 2223 user@vps`
   - Clone your repo to `/home/deployer/apps/myapp.com/`
   - Start PM2 process: `pm2 start app.js --name myapp.com`
   - Save PM2: `pm2 save`

6. **Test**
   - Visit `https://myapp.com` in browser
   - Should load your application
   - NGINX proxies to your PM2 process

### Maintenance Tasks

**Monitor Site Health**
```bash
# Daily check
python3 vps-manager.py → Menu option 1 (Dashboard)
```

**Update Application**
```bash
# SSH to VPS
ssh -p 2223 user@vps

# Pull latest code
cd /home/deployer/apps/myapp.com
git pull origin main

# Restart application
pm2 restart myapp.com
```

**Temporary Downtime (e.g., database migration)**
```bash
# Menu option 4: Take Site Offline
# Site shows Coming Soon page
# PM2 process stops
```

**Resume Service**
```bash
# SSH to VPS
ssh -p 2223 user@vps

# Start PM2 process
pm2 start app.js --name domain.com
```

**SSL Certificate Check**
- Monitor in Dashboard (Menu option 1)
- Automatic renewal handles 90-day rotation
- No action needed (Certbot handles renewal)

**Remove Site**
```bash
# Menu option 5: Remove Site Provisioning
# Confirms what will be deleted
# Removes everything
```

## Code Structure

### Main Classes

**CloudflareManager** (`vps-manager.py:65-370`)
- Manages Cloudflare DNS API interactions
- Methods for creating, updating, deleting DNS records
- Zone management and caching
- DNS propagation verification

**VPSManager** (`vps-manager.py:373-1083`)
- Core SSH connection and remote command execution
- System monitoring (CPU, memory, disk)
- Site provisioning and management
- Service control (NGINX, PM2, PostgreSQL)
- NGINX and Coming Soon page generation

**MonitorDashboard** (`vps-manager.py:1087-1203`)
- Real-time monitoring display
- Rich terminal UI with live updates
- System stats and site health visualization

**Main Functions**
- `main_menu()`: Interactive CLI menu
- `main()`: Entry point, configuration, initialization

### Key Methods

**Provisioning:**
- `provision_site()`: Complete site setup with DNS and SSL
- `_generate_nginx_config()`: Generate NGINX configuration
- `_generate_coming_soon_page()`: Generate landing page HTML

**Site Configuration Detection (NEW):**
- `detect_site_config()`: Parse NGINX config and extract settings
- `_read_nginx_config()`: Read existing NGINX configuration file
- `_extract_ssl_lines_from_config()`: Extract SSL cert lines from config

**Site Management:**
- `clone_site()`: Clone configuration from existing site (NEW)
- `take_site_offline()`: Park site with Coming Soon (ENHANCED)
- `remove_site()`: Complete removal
- `get_sites()`: List provisioned sites
- `get_system_stats()`: Retrieve system metrics

**Services:**
- `restart_service()`: Restart single service
- `restart_all_services()`: Restart all services

**DNS:**
- `view_dns_records()`: Display DNS records
- `manage_dns_for_site()`: Interactive DNS management

## System Requirements Summary

**Development/Local Machine:**
- Python 3.8+
- Paramiko, Rich, Requests libraries
- SSH key pair
- Network access to VPS

**VPS Server:**
- NGINX configured and running
- PM2 with Node.js via NVM
- PostgreSQL installed
- Certbot for SSL
- Sudo access without password for SSH user
- Ports 80/443 open (for Let's Encrypt and users)
- Port 22 (or custom) open for SSH

**DNS/Domain:**
- Cloudflare account (optional but recommended)
- Domain registered and pointing to VPS IP

## Performance Characteristics

- **Provisioning new site:** 2-3 minutes
- **Service restart:** < 1 second
- **Dashboard refresh:** 5 seconds
- **DNS propagation check:** up to 60 seconds
- **Dashboard metrics update:** real-time (1-2 second latency)
- **SSH command timeout:** 10 seconds per command

## Limitations

- **Single VPS support:** Configured for one primary server
- **No multi-server dashboard:** Each server needs separate manager instance
- **Manual application deployment:** Git pull and PM2 start done manually
- **PM2 path hardcoded:** Node.js version change requires code update
- **No database backups:** Backup/restore handled separately
- **No CI/CD integration:** Build and deploy done manually
- **No log viewer:** Logs accessed via SSH

## Design Philosophy

**Reliability First:**
- Confirmation prompts for destructive actions
- Comprehensive error handling and reporting
- Safe defaults and validation

**User-Friendly:**
- Beautiful terminal UI with Rich library
- Color-coded status indicators
- Progress spinners for long operations
- Clear error messages with troubleshooting hints

**Maintainability:**
- Clean code structure with separate classes
- Type hints for better IDE support
- Comprehensive documentation
- Modular functions for single responsibility

**Security:**
- Key-based authentication (no password storage)
- Dual-user permission model
- No secrets in code (uses environment variables)
- Proper user context for operations (beinejd vs deployer)

## Recent Updates (v1.2.0)

### Bug Fixes

**✓ Fixed SSL Certificate Preservation**
- `take_site_offline()` now preserves Certbot-managed SSL certificates
- Detects existing SSL cert lines and re-injects them into regenerated config
- HTTPS remains active during park mode
- Previously: SSL cert would break when taking site offline

**✓ Fixed Site Configuration Detection**
- `take_site_offline()` now detects and preserves original www subdomain setting
- `take_site_offline()` now detects and preserves original app port
- If site was configured differently, those settings are maintained
- Previously: Always hardcoded www=True and port=3000, breaking inconsistent sites

### New Features

**✓ Clone Site Configuration (Menu Option 6)**
- Automatically detect settings from existing site
- Clone configuration to new domain
- Auto-detects: www subdomain, app mode, app port
- Creates new SSL certificate and DNS records
- Saves time and ensures consistency
- Use case: Copy TopEngineer.US settings → RedStartMedia.com

**✓ Enhanced Site Configuration Detection**
- New `detect_site_config()` method parses NGINX configs
- Accurate detection of: www subdomain, Coming Soon vs live app mode, app port
- Used by clone feature and take_site_offline
- Reads actual running configuration (source of truth)

---

## Planned Features (Future Versions)

- [ ] GitHub CI/CD integration
- [ ] Database backup/restore
- [ ] Log viewer in dashboard
- [ ] Environment variable management UI
- [ ] Automated site deployment (git pull → build → start)
- [ ] Rollback to previous version
- [ ] Custom Coming Soon page templates
- [ ] Email notifications for SSL expiry warnings
- [ ] Multi-server support with unified dashboard
- [ ] Application performance metrics (p95 latency, throughput)
- [ ] Database migration helpers
- [ ] Automated security scanning

## License

Proprietary - Top Engineer / Redstart Media, Inc.

---

**Version:** 1.2.0  
**Last Updated:** January 4, 2025  
**Maintainer:** Development Team

### Changelog

**v1.2.0 (Current)**
- ✓ Fixed SSL certificate preservation in take_site_offline()
- ✓ Fixed site configuration detection (www, app port) in take_site_offline()
- ✓ Added clone_site() method with auto-detection
- ✓ Added menu option 6: Clone Site Configuration
- ✓ Updated menu numbering (options 7-8 for services)
- ✓ Fixed duplicate menu handler bug

**v1.1.0**
- Comprehensive documentation updates
- Enhanced README with architecture details
- Added troubleshooting section

**v1.0.0**
- Initial release
- Site provisioning with DNS and SSL
- Live monitoring dashboard
- Service management
