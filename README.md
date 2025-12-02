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
- Automatic NGINX configuration
- SSL certificate via Let's Encrypt (Certbot)
- Beautiful "Coming Soon" landing page
- www subdomain support
- Proper directory structure creation

🔧 **Site Management**
- Take sites offline (park mode with Coming Soon page)
- Complete site removal (NGINX, SSL, files)
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

## Installation

1. **Clone or download the files:**
   ```bash
   # Download vps-manager.py and requirements.txt to your iMac
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Update SSH configuration in vps-manager.py:**
   ```python
   # Line ~816 - Update these values:
   HOST = "23.29.114.83"
   USERNAME = "beinejd"
   PORT = 22  # Update with your actual SSH port
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

**2. Provision New Site**
- Enter domain name (e.g., example.com)
- Choose whether to enable www subdomain
- Automatically creates:
  - NGINX configuration
  - SSL certificate (Let's Encrypt)
  - Beautiful Coming Soon page
  - Directory structure at `/home/deployer/apps/{domain}/`

**3. Take Site Offline (Park)**
- Select a site from the list
- Switches site to Coming Soon page
- Stops PM2 process
- Keeps SSL certificate active

**4. Remove Site Provisioning**
- Complete removal of site
- Removes NGINX config
- Removes SSL certificate
- Optionally removes application files
- **Use with caution!**

**5. Restart Service**
- Restart individual services:
  - NGINX
  - PM2 (all processes)
  - PostgreSQL

**6. Restart All Services**
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
     Project: vps-manager - Initialized
