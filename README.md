# VPS Manager

A comprehensive Python-based VPS management tool with a beautiful terminal UI for managing NGINX sites, SSL certificates, and services.

## Features

✨ **Live Monitoring Dashboard**
- Real-time system metrics (CPU, Memory, Disk)
- Service status (NGINX, PostgreSQL, PM2)
- Site health monitoring (HTTPS, SSL expiry, PM2 status)
- Auto-refreshing every 5 seconds

🚀 **Site Provisioning**
- One-command site setup
- **Automatic DNS configuration via Cloudflare API**
- **DNS propagation verification**
- Automatic NGINX configuration
- SSL certificate via Let's Encrypt (Certbot)
- Beautiful "Coming Soon" landing page
- www subdomain support
- Proper directory structure creation

🌐 **DNS Management (Cloudflare)**
- Automatic DNS record creation during provisioning
- View all DNS records in your zone
- Manage DNS for specific domains
- Update records to point to your VPS
- Toggle Cloudflare proxy (orange cloud on/off)
- Add/remove www subdomains
- Delete DNS records

🔧 **Site Management**
- Take sites offline (park mode with Coming Soon page)
- Complete site removal (NGINX, SSL, DNS, files)
- Individual service restarts (NGINX, PM2, PostgreSQL)
- Restart all services at once

🎨 **Beautiful Terminal UI**
- Color-coded status indicators
- Progress bars and spinners
- Clean table layouts
- Interactive menus

## Prerequisites

- Python 3.8 or higher
- Passwordless SSH access to your VPS
- VPS must have: NGINX, PM2, PostgreSQL, Certbot installed
- **(Optional) Cloudflare account** for automated DNS management

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

## Installation

1. **Clone or download the files:**
   ```bash
   # Download vps-manager.py and requirements.txt to your iMac
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure vps-manager.py (lines 31-42):**
   ```python
   # VPS Server Configuration
   VPS_HOST = "23.29.114.83"        # Your server IP
   VPS_SSH_USERNAME = "beinejd"     # Your SSH username
   VPS_SSH_PORT = 2223              # Your SSH port
   
   # Cloudflare API Configuration (optional)
   CLOUDFLARE_API_TOKEN = ""  # Add your API token (or leave empty to disable)
   ```

4. **Make the script executable:**
   ```bash
   chmod +x vps-manager.py
   ```

## Usage

### Start the Manager
```bash
python3 vps-manager.py
```

### Main Menu Options

**1. Live Monitoring Dashboard**
- Shows real-time server metrics
- Displays all sites with their status
- Press Ctrl+C to return to menu

**2. Provision New Site (with DNS)**
- Enter domain name (e.g., example.com)
- Choose whether to enable www subdomain
- **(If Cloudflare configured)** Automatically creates DNS records
- Verifies DNS propagation
- Automatically creates:
  - NGINX configuration
  - SSL certificate (Let's Encrypt)
  - Beautiful Coming Soon page
  - Directory structure at `/home/deployer/apps/{domain}/`

**3. Manage DNS Records** *(Requires Cloudflare)*
- View all DNS records in your zone
- Manage DNS for specific domains:
  - Update DNS to point to this server
  - Add www subdomain
  - Delete DNS records
  - Toggle Cloudflare proxy (🟠/⚪)

**4. Take Site Offline (Park)**
- Select a site from the list
- Switches site to Coming Soon page
- Stops PM2 process
- Keeps SSL certificate active

**5. Remove Site Provisioning**
- Complete removal of site
- Removes NGINX config
- Removes SSL certificate
- Optionally removes application files
- **Use with caution!**

**6. Restart Service**
- Restart individual services:
  - NGINX
  - PM2 (all processes)
  - PostgreSQL

**7. Restart All Services**
- Restarts NGINX, PM2, and PostgreSQL together
- Requires confirmation

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

## NGINX Configuration

The tool generates production-ready NGINX configs with:
- HTTP to HTTPS redirect
- SSL/TLS configuration
- Security headers
- Logging
- Support for both domain.com and www.domain.com

**For Coming Soon pages:**
- Serves static HTML from `/home/deployer/apps/{domain}/public/`

**For live applications:**
- Proxies to Next.js on specified port (default: 3000)
- WebSocket support for hot reload

## SSL Certificates

- Automatically obtained via Let's Encrypt (Certbot)
- 90-day validity
- Dashboard shows days remaining
- Color-coded warnings:
  - 🟢 Green: > 30 days
  - 🟡 Yellow: 7-30 days
  - 🔴 Red: < 7 days or expired

## User Permissions

The script uses appropriate user contexts:
- **beinejd** (via sudo): Manages NGINX, system services
- **deployer**: Manages PM2 processes, application files

## Coming Soon Page

The generated Coming Soon page features:
- Responsive design
- Animated gradient background
- Floating circles animation
- Fade-in effects
- Mobile-friendly
- Professional appearance

## SSH Connection

- Maintains persistent SSH connection during session
- Automatically handles authentication
- Requires passwordless SSH (key-based auth)

## Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### SSH connection fails
- Verify passwordless SSH works: `ssh beinejd@23.29.114.83 -p YOUR_PORT`
- Check that SSH keys are properly configured
- Update HOST, USERNAME, PORT in the script

### SSL certificate fails
- Ensure DNS is pointing to your server IP
- Check that ports 80 and 443 are open
- Verify domain is not already in use

### Permission denied errors
- Verify user `beinejd` has sudo access
- Verify user `deployer` exists and owns `/home/deployer/apps/`

## Planned Features (Future Versions)

- [ ] GitHub CI/CD integration
- [ ] Database backup/restore
- [ ] Log viewer
- [ ] Environment variable management
- [ ] Site deployment (pull from git, build, deploy)
- [ ] Rollback functionality
- [ ] Custom Coming Soon page templates
- [ ] Email notifications for SSL expiry
- [ ] Multi-server support

## Architecture Notes

**Current Focus:**
- Site provisioning and management
- Service monitoring and control
- SSL certificate automation

**Design Philosophy:**
- Reliability and safety first
- Clear visual feedback
- Confirmation for destructive actions
- Comprehensive error handling
- Maintainable code structure

## Support

For issues or questions:
1. Check the troubleshooting section
2. Verify SSH connection manually
3. Check server logs: `tail -f /var/log/nginx/error.log`

## License

Proprietary - Top Engineer / Redstart Media, Inc.

---

**Version:** 1.0.0  
**Last Updated:** December 2024
