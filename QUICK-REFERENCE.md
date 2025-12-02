# VPS Manager - Quick Reference

## Installation (One-Time Setup)
```bash
# Install dependencies
pip install -r requirements.txt

# Edit vps-manager.py - Update line ~816:
PORT = YOUR_SSH_PORT  # Replace with actual port number

# Make executable
chmod +x vps-manager.py
```

## Start the Manager
```bash
python3 vps-manager.py
```

## Common Tasks

### Provision a New Site
```
Menu → 2 → Enter domain → Enable www? (y/n)
```
**Creates:** NGINX config, SSL cert, Coming Soon page

### Monitor Server Health
```
Menu → 1
```
**Shows:** CPU/RAM/Disk, Services, Sites, SSL expiry  
**Exit:** Ctrl+C

### Take Site Offline (Park)
```
Menu → 3 → Select site number
```
**Result:** Coming Soon page displayed, PM2 stopped

### Restart NGINX
```
Menu → 5 → 1
```

### Restart All Services
```
Menu → 6 → Confirm
```

### Remove a Site Completely
```
Menu → 4 → Select site → Confirm
```
**⚠️ DESTRUCTIVE:** Removes NGINX, SSL, optionally files

## Status Indicators

### Services
- 🟢 Running / Online
- 🔴 Stopped / Offline
- 🟡 Warning

### SSL Certificates
- 🟢 Green: > 30 days remaining
- 🟡 Yellow: 7-30 days remaining  
- 🔴 Red: < 7 days or expired

### HTTPS Status
- ✓ Site responding (HTTP 200)
- ✗ Site not responding

## File Locations on Server

```
/home/deployer/apps/{domain}/
├── public/index.html       # Coming Soon page
└── logs/
    ├── access.log
    └── error.log

/etc/nginx/sites-available/{domain}
/etc/nginx/sites-enabled/{domain}
```

## Keyboard Shortcuts

- **Ctrl+C** - Exit dashboard / Cancel operation
- **q** - Quit from main menu

## SSH Requirements

- Passwordless SSH must be configured
- Test with: `ssh beinejd@23.29.114.83 -p PORT`

## User Context

- **beinejd** - Manages NGINX, system services (sudo)
- **deployer** - Manages PM2, application files

## Troubleshooting Quick Fixes

**SSH fails:**
```bash
ssh beinejd@23.29.114.83 -p YOUR_PORT  # Test connection
```

**Missing dependencies:**
```bash
pip install paramiko rich
```

**Permission errors:**
```bash
# Verify deployer user exists
ssh beinejd@23.29.114.83 -p PORT "ls -la /home/deployer"
```

**SSL certificate fails:**
- Check DNS points to server IP
- Ensure ports 80, 443 are open
- Try manual certbot: `sudo certbot --nginx -d domain.com`

## Safety Features

✅ Confirmation prompts for destructive actions  
✅ NGINX config testing before reload  
✅ Error handling with clear messages  
✅ Non-root user execution (deployer)

## Next Steps

After provisioning a site with Coming Soon page:
1. Deploy your Next.js app to `/home/deployer/apps/{domain}/`
2. Configure PM2 to run your app
3. Update NGINX config to proxy to your app port
4. Reload NGINX

---

**Pro Tip:** Keep this script running in a dedicated terminal tab for quick access to monitoring and management features.
