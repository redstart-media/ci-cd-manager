# PM2 Passwordless Sudo Configuration

## The Issue

PM2 is installed via NVM at:
```
/home/deployer/.nvm/versions/node/v24.11.1/bin/pm2
```

For the VPS Manager script to work without password prompts, we need to configure passwordless sudo for PM2 commands.

## Correct Sudoers Configuration

### Step 1: Edit Sudoers File
```bash
sudo visudo -f /etc/sudoers.d/pm2-nopasswd
```

### Step 2: Add This Exact Line
```
beinejd ALL=(deployer) NOPASSWD: /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2
```

**Important Notes:**
- Use the **full NVM path** (not /usr/bin/pm2 or /usr/local/bin/pm2)
- No trailing spaces
- File must be owned by root with 0440 permissions (visudo handles this)

### Step 3: Verify Permissions
```bash
# Check file permissions
ls -la /etc/sudoers.d/pm2-nopasswd

# Should show: -r--r----- 1 root root
```

### Step 4: Test Passwordless Sudo
```bash
# This should work WITHOUT asking for password:
sudo -u deployer /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2 list

# You should see your PM2 processes listed
```

## If Node Version Updates

When you update Node.js via NVM, the path will change (e.g., from v24.11.1 to v24.12.0).

**You'll need to update TWO places:**

### 1. Update Sudoers Rule
```bash
sudo visudo -f /etc/sudoers.d/pm2-nopasswd

# Change the path to match new Node version
beinejd ALL=(deployer) NOPASSWD: /home/deployer/.nvm/versions/node/vNEW.VERSION/bin/pm2
```

### 2. Update VPS Manager Script
Edit `vps-manager.py` around line 24:
```python
class VPSManager:
    """Manages SSH connection and VPS operations"""
    
    # PM2 path configuration (update if Node version changes)
    PM2_PATH = "/home/deployer/.nvm/versions/node/vNEW.VERSION/bin/pm2"
```

## Troubleshooting

### Test 1: Manual PM2 Command
```bash
# SSH to server
ssh beinejd@23.29.114.83 -p YOUR_PORT

# Test without password prompt
sudo -u deployer /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2 jlist

# Should output JSON immediately, no password prompt
```

**If it asks for password:**
- Sudoers rule is incorrect or missing
- Check the file exists: `ls -la /etc/sudoers.d/pm2-nopasswd`
- Verify the PM2 path is correct in the rule

### Test 2: PM2 Path Verification
```bash
# Verify PM2 location
sudo -i -u deployer which pm2

# Should output: /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2
```

**If path is different:**
- Update both sudoers rule and VPS Manager script to match

### Test 3: JSON Output
```bash
# Get PM2 process list as JSON
sudo -u deployer /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2 jlist

# Should output valid JSON like:
# [{"name":"topengineer","pm2_env":{"status":"online",...},...}]
```

**If output is empty or malformed:**
- PM2 might not have any processes: `sudo -u deployer /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2 list`
- Check PM2 daemon: `sudo -u deployer /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2 status`

## Why We Use Full Path

**Problem with `sudo -i -u deployer pm2`:**
- `-i` flag loads login environment (slow, complex)
- Can have timing issues with paramiko/SSH
- Requires full shell initialization

**Solution with full path:**
- Direct execution (fast, reliable)
- No environment loading needed
- Works consistently with automation tools

## Current Configuration Summary

**Sudoers Rule:**
```
/etc/sudoers.d/pm2-nopasswd
Contains: beinejd ALL=(deployer) NOPASSWD: /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2
```

**VPS Manager Script:**
```python
Line ~24: PM2_PATH = "/home/deployer/.nvm/versions/node/v24.11.1/bin/pm2"
```

**Commands the script executes:**
```bash
sudo -u deployer /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2 jlist
sudo -u deployer /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2 show {domain}
sudo -u deployer /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2 stop {domain}
sudo -u deployer /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2 delete {domain}
sudo -u deployer /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2 restart all
```

## Security Notes

This sudoers rule is secure because:
- ✅ Only allows specific command: PM2
- ✅ Only allows running as specific user: deployer
- ✅ Only allows from specific user: beinejd
- ✅ PM2 can only control processes owned by deployer
- ✅ No wildcard permissions
- ✅ No ability to escalate to root

## Alternative: System-Wide PM2 (Not Recommended)

If you wanted to avoid NVM paths, you could install PM2 system-wide:
```bash
sudo npm install -g pm2
```

But this is **NOT recommended** because:
- Mixes user and system Node installations
- Can cause version conflicts
- Loses NVM's version management benefits
- Your current setup (PM2 via NVM) is the correct approach

## Quick Reference

**View current sudoers rules:**
```bash
sudo cat /etc/sudoers.d/pm2-nopasswd
```

**Test passwordless sudo:**
```bash
sudo -u deployer /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2 list
```

**Check PM2 processes:**
```bash
sudo -u deployer /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2 status
```

**Monitor PM2 in real-time:**
```bash
sudo -u deployer /home/deployer/.nvm/versions/node/v24.11.1/bin/pm2 monit
```

---

After confirming the sudoers rule is correct, the VPS Manager script should now properly detect PM2!
