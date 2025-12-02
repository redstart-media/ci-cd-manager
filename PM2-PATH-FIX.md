# VPS Manager - PM2 Path Fix (NVM)

## Problem Identified
PM2 is installed via NVM at:
```
/home/deployer/.nvm/versions/node/v24.11.1/bin/pm2
```

Previous attempts using `sudo -i -u deployer pm2` were inconsistent with automated SSH execution.

## Solution Applied
**Use full path to PM2 binary** instead of relying on environment PATH.

## Changes Made to vps-manager.py

### 1. Added PM2_PATH Constant (Line ~24)
```python
class VPSManager:
    """Manages SSH connection and VPS operations"""
    
    # PM2 path configuration (update if Node version changes)
    PM2_PATH = "/home/deployer/.nvm/versions/node/v24.11.1/bin/pm2"
```

**Benefits:**
- Easy to update if Node version changes
- Single point of configuration
- Self-documenting code

### 2. Updated All PM2 Commands
Changed from:
```python
sudo -i -u deployer pm2 jlist
```

To:
```python
sudo -u deployer /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2 jlist
```

**Locations updated:**
- `get_system_stats()` - PM2 process counting
- `get_sites()` - Per-site PM2 status
- `take_site_offline()` - Stop PM2 process
- `remove_site()` - Delete PM2 process
- `restart_service()` - Restart all PM2 processes

## Required Sudoers Configuration

**File:** `/etc/sudoers.d/pm2-nopasswd`

**Content:**
```
beinejd ALL=(deployer) NOPASSWD: /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2
```

**Create/Edit with:**
```bash
sudo visudo -f /etc/sudoers.d/pm2-nopasswd
```

## Verification Steps

### ✅ Step 1: Verify Sudoers Rule
```bash
# On VPS - should NOT ask for password:
sudo -u deployer /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2 list

# Expected output: PM2 process table
```

### ✅ Step 2: Test JSON Output
```bash
# Should output valid JSON:
sudo -u deployer /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2 jlist

# Expected output:
# [{"name":"topengineer","pm2_env":{"status":"online",...},...}]
```

### ✅ Step 3: Run VPS Manager
```bash
# On your iMac:
python3 vps-manager.py

# Select: 1 (Live Monitoring Dashboard)
```

### ✅ Step 4: Check Dashboard Display

**System Status panel should show:**
```
PM2    🟢 1/1 online
```

**Sites table should show:**
```
Domain            HTTPS  SSL      PM2
topengineer.us    ✓      🟢 77d   🟢
```

## Troubleshooting

### Issue: "Permission denied" or password prompt
**Fix:** Verify sudoers rule:
```bash
sudo cat /etc/sudoers.d/pm2-nopasswd
```
Should contain the exact path with NOPASSWD.

### Issue: PM2 still shows "0/0 online"
**Diagnose:**
```bash
# Test manually on VPS:
sudo -u deployer /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2 jlist

# Check for errors:
sudo -u deployer /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2 status
```

### Issue: "command not found"
**Check PM2 path:**
```bash
sudo -i -u deployer which pm2
```
If path is different, update both:
1. `/etc/sudoers.d/pm2-nopasswd`
2. `vps-manager.py` line ~24 (PM2_PATH constant)

## When Node Version Changes

If you update Node.js (e.g., from v24.11.1 to v24.12.0):

**Update 1: Sudoers Rule**
```bash
sudo visudo -f /etc/sudoers.d/pm2-nopasswd
# Change: v24.11.1 → v24.12.0
```

**Update 2: VPS Manager Script**
```python
# vps-manager.py line ~24
PM2_PATH = "/home/deployer/.nvm/versions/node/v24.12.0/bin/pm2"
```

## Files Updated

📥 **Download latest version:**
- [vps-manager.py](computer:///mnt/user-data/outputs/vps-manager.py) - Now uses full PM2 path
- [SUDOERS-GUIDE.md](computer:///mnt/user-data/outputs/SUDOERS-GUIDE.md) - Detailed sudoers setup

## Expected Behavior After Fix

✅ Dashboard shows accurate PM2 process count  
✅ Per-site PM2 status displays correctly  
✅ No password prompts during execution  
✅ All PM2 operations (stop/restart/delete) work smoothly  

## Quick Test Command

Run this on your VPS to verify everything is ready:
```bash
# Should execute without password and show JSON:
sudo -u deployer /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2 jlist && echo "✓ PM2 access works!"
```

If this works, the VPS Manager script will work too!

---

**Next Step:** Download the updated `vps-manager.py` and run it. The PM2 detection should now work perfectly.
