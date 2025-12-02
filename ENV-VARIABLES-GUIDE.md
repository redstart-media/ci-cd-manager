# Environment Variables Configuration Guide

## Overview

The VPS Manager now supports environment variables for secure credential management. This is the **recommended approach** for managing API keys and server settings.

## Benefits of Environment Variables

✅ **Security:** Credentials stored in shell config, not in scripts  
✅ **Convenience:** Same credentials across all scripts  
✅ **Git-safe:** No risk of committing credentials  
✅ **Flexibility:** Easy to update without editing code  
✅ **Portability:** Works across different projects  

## Environment Variables Supported

| Variable | Purpose | Required |
|----------|---------|----------|
| `CLOUDFLARE_API_TOKEN` | Cloudflare DNS management | For DNS features |
| `VPS_SRV1_IP` | VPS server IP address | Yes |
| `VPS_SRV1_PORT` | VPS SSH port | Yes |
| `CLAUDE_API_KEY` | Claude AI API (future use) | Optional |
| `DEEPSEEK_API_KEY` | DeepSeek AI API (future use) | Optional |

## Quick Setup (Automated)

### Method 1: Interactive Setup Script

**Step 1:** Run the setup script
```bash
./setup-env.sh
```

**Step 2:** Follow the prompts
```
1. Cloudflare API Token: [paste your token]
2. Claude API Key: [paste your key or skip]
3. DeepSeek API Key: [paste your key or skip]
4. VPS Server IP: [enter IP or accept default]
5. VPS SSH Port: [enter port or accept default 22]
```

**Step 3:** Apply changes
```
Apply changes now? (y/n): y
```

**Done!** Your environment is configured.

## Manual Setup

### For Bash Users

Edit `~/.bashrc` or `~/.bash_profile`:
```bash
nano ~/.bashrc
```

Add these lines at the end:
```bash
# VPS Manager Environment Variables
export CLOUDFLARE_API_TOKEN="your_cloudflare_token_here"
export CLAUDE_API_KEY="your_claude_key_here"
export DEEPSEEK_API_KEY="your_deepseek_key_here"
export VPS_SRV1_IP="23.29.114.83"
export VPS_SRV1_PORT="22"
```

Apply changes:
```bash
source ~/.bashrc
```

### For Zsh Users

Edit `~/.zshrc`:
```bash
nano ~/.zshrc
```

Add the same exports as above, then:
```bash
source ~/.zshrc
```

## Verifying Configuration

### Check All Variables
```bash
printenv | grep -E 'CLOUDFLARE|CLAUDE|DEEPSEEK|VPS_SRV1'
```

Expected output:
```
CLOUDFLARE_API_TOKEN=your_token_here
CLAUDE_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here
VPS_SRV1_IP=23.29.114.83
VPS_SRV1_PORT=22
```

### Check Specific Variable
```bash
echo $CLOUDFLARE_API_TOKEN
echo $VPS_SRV1_IP
```

### Test with VPS Manager
```bash
python3 vps-manager.py
```

You should see:
```
Config: VPS from env, Cloudflare from env
✓ Cloudflare token found: XX chars
✓ Cloudflare API connected successfully!
```

## How It Works

### Priority Order

VPS Manager checks for configuration in this order:

1. **Environment Variables** (highest priority)
   - `CLOUDFLARE_API_TOKEN`
   - `VPS_SRV1_IP`
   - `VPS_SRV1_PORT`

2. **Hardcoded Values in Script** (fallback)
   - If environment variable not set
   - Uses default in vps-manager.py lines 32-55

### Example

**Environment variable set:**
```bash
export VPS_SRV1_IP="192.168.1.100"
```
→ VPS Manager uses: `192.168.1.100`

**Environment variable not set:**
```bash
# VPS_SRV1_IP not set
```
→ VPS Manager uses hardcoded default: `23.29.114.83`

## Configuration Combinations

### All from Environment (Recommended)
```bash
export CLOUDFLARE_API_TOKEN="abc123..."
export VPS_SRV1_IP="23.29.114.83"
export VPS_SRV1_PORT="2223"
```
Result: All from env vars ✅

### Mixed Configuration
```bash
export CLOUDFLARE_API_TOKEN="abc123..."
# VPS_SRV1_IP not set (uses default from script)
# VPS_SRV1_PORT not set (uses default from script)
```
Result: Cloudflare from env, VPS from script ✅

### All from Script (Legacy)
```bash
# No environment variables set
```
Edit vps-manager.py directly (lines 32-55)
Result: All from hardcoded values ✅

## Updating Values

### Update Single Variable
```bash
# Edit your shell config
nano ~/.zshrc  # or ~/.bashrc

# Find and update the line:
export CLOUDFLARE_API_TOKEN="new_token_here"

# Save and reload
source ~/.zshrc
```

### Update All Variables
```bash
# Run setup script again
./setup-env.sh

# It will show current values and let you update them
```

### Temporary Override (Current Session Only)
```bash
# Set for current terminal session only
export VPS_SRV1_IP="10.0.0.50"
python3 vps-manager.py

# In new terminal, original value is used
```

## Security Best Practices

### ✅ Do

1. **Use environment variables** for all credentials
2. **Backup your shell config** before editing:
   ```bash
   cp ~/.zshrc ~/.zshrc.backup
   ```
3. **Verify permissions** on shell config:
   ```bash
   chmod 600 ~/.zshrc  # Only you can read/write
   ```
4. **Use different tokens** for different purposes
5. **Rotate tokens** every 6-12 months

### ❌ Don't

1. **Don't commit** shell config files to git
2. **Don't share** screenshots with tokens visible
3. **Don't use** Global API Keys (use tokens instead)
4. **Don't store** tokens in plain text files
5. **Don't give** tokens excessive permissions

## Troubleshooting

### Variable Not Found
```bash
echo $CLOUDFLARE_API_TOKEN
# Output: (empty)
```

**Fix:**
1. Check variable is set: `printenv | grep CLOUDFLARE`
2. If not, add to shell config: `nano ~/.zshrc`
3. Reload config: `source ~/.zshrc`

### Variable Set But Script Doesn't See It
```bash
# Check if script is using a different shell
echo $SHELL

# Make sure variable is in the correct config file:
# Bash: ~/.bashrc or ~/.bash_profile
# Zsh: ~/.zshrc
```

### Changes Not Taking Effect
```bash
# Reload shell configuration
source ~/.zshrc  # or ~/.bashrc

# Or start a new terminal session
```

### Script Still Uses Hardcoded Values
```bash
# Verify environment variable is actually set
printenv | grep VPS_SRV1_IP

# If empty, the variable isn't set
# Add to shell config and reload
```

## Advanced Usage

### Multiple VPS Servers

**Current setup:**
```bash
export VPS_SRV1_IP="23.29.114.83"
export VPS_SRV1_PORT="2223"
```

**Add second server:**
```bash
export VPS_SRV2_IP="192.168.1.100"
export VPS_SRV2_PORT="22"
```

**Use different servers:**
```bash
# Connect to server 1
python3 vps-manager.py

# Connect to server 2 (temporary override)
VPS_SRV1_IP=$VPS_SRV2_IP VPS_SRV1_PORT=$VPS_SRV2_PORT python3 vps-manager.py
```

### Per-Project Configuration

**Global config** (applies to all projects):
```bash
# ~/.zshrc
export CLOUDFLARE_API_TOKEN="global_token"
```

**Project-specific config:**
```bash
# ~/myproject/.env-local
export CLOUDFLARE_API_TOKEN="project_specific_token"

# Load before running
source ~/myproject/.env-local
python3 vps-manager.py
```

### Automated Deployment

```bash
#!/bin/bash
# deploy.sh

# Load environment
source ~/.zshrc

# Verify critical variables
if [[ -z "$CLOUDFLARE_API_TOKEN" ]]; then
    echo "Error: CLOUDFLARE_API_TOKEN not set"
    exit 1
fi

# Run deployment
python3 vps-manager.py
```

## Quick Reference

### View Configuration
```bash
cat ~/.vps-manager-env-reference.txt
```

### Check What's Set
```bash
printenv | grep -E 'CLOUDFLARE|CLAUDE|DEEPSEEK|VPS_SRV1'
```

### Re-run Setup
```bash
./setup-env.sh
```

### Edit Manually
```bash
nano ~/.zshrc  # or ~/.bashrc
```

### Apply Changes
```bash
source ~/.zshrc  # or source ~/.bashrc
```

### Test Configuration
```bash
python3 vps-manager.py
# Look for: "Config: VPS from env, Cloudflare from env"
```

## Migration from Hardcoded Values

**If you previously hardcoded values in vps-manager.py:**

1. **Run setup script:**
   ```bash
   ./setup-env.sh
   ```

2. **Enter your current values** when prompted

3. **Clear hardcoded values** (optional):
   ```python
   # In vps-manager.py, you can now remove hardcoded values:
   CLOUDFLARE_API_TOKEN = os.environ.get('CLOUDFLARE_API_TOKEN', "")
   # The "" means: use env var, or empty if not set
   ```

4. **Test:**
   ```bash
   python3 vps-manager.py
   ```

## Files Created

**Setup script:** `setup-env.sh`
- Interactive configuration tool
- Automatically updates your shell config
- Creates backup before modifying

**Reference file:** `~/.vps-manager-env-reference.txt`
- Quick reference for your configuration
- Shows which variables are set
- Includes backup location

**Backup file:** `~/.zshrc.backup.TIMESTAMP`
- Automatic backup of your shell config
- Created before any modifications
- Restore if needed: `cp ~/.zshrc.backup.TIMESTAMP ~/.zshrc`

## Summary

**Environment variables provide:**
- ✅ Better security (no credentials in code)
- ✅ Easier management (one place for all keys)
- ✅ Git safety (credentials not committed)
- ✅ Flexibility (easy to update)
- ✅ Portability (works across projects)

**Quick start:**
```bash
./setup-env.sh
# Follow prompts
# Done!
```

---

**For help:** See ~/.vps-manager-env-reference.txt  
**To update:** Run ./setup-env.sh again  
**To verify:** `printenv | grep -E 'CLOUDFLARE|VPS_SRV1'`
