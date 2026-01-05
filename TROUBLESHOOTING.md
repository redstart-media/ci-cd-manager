# CI/CD Manager - Troubleshooting Guide

## Overview

This guide covers common issues with the CI/CD Manager and how to fix them.

## Issues Fixed

### 1. **Environment Variable Mismatches**
**Problem**: The script expected `GHT`, `VPS_HOST`, `VPS_USER`, `VPS_PORT` but these weren't consistently configured across the codebase.

**Solution**: 
- Updated `ci-cd-manager.py` to accept multiple environment variable names:
  - `GHT` or `GITHUB_TOKEN` for GitHub token
  - `VPS_HOST` or `VPS_SRV1_IP` for VPS IP
  - `VPS_USER` or `VPS_SSH_USERNAME` for SSH username
  - `VPS_PORT` or `VPS_SRV1_PORT` for SSH port
- Added validation to ensure GitHub token is configured

### 2. **SSH Key Configuration Issues**
**Problem**: The script only looked for `~/.ssh/id_rsa` but the system uses `id_ed25519`.

**Solution**:
- Implemented automatic SSH key discovery that checks for:
  - `~/.ssh/id_ed25519` (first priority)
  - `~/.ssh/id_rsa`
  - `~/.ssh/id_ecdsa`
  - `~/.ssh/id_dsa`
- Updated SSH connection code in both `CICDPipelineManager` and `ServerDiscovery` to use `key_filename` parameter

### 3. **GitHub Secrets API - Missing Encryption**
**Problem**: The script tried to send secret values unencrypted, but GitHub Secrets API requires encryption with the repository's public key.

**Solution**:
- Added `PyNaCl` dependency to requirements.txt
- Implemented `_get_repo_public_key()` method to fetch repository public key
- Implemented `_encrypt_secret()` method to properly encrypt secrets using NaCl/libsodium
- Updated `create_secret()` to:
  1. Fetch the repository's public key
  2. Encrypt the secret value
  3. Send the encrypted value with the key_id

### 4. **Dependencies Missing**
**Problem**: `PyNaCl` was not in requirements.txt.

**Solution**: Added `PyNaCl>=1.5.0` to requirements.txt

## Diagnostics

### Run the Diagnostic Script

```bash
cd /Users/beinejd/Desktop/ci-cd-manager
./test-api.zsh
```

This script checks:
- ✓ Environment variables configuration
- ✓ SSH key existence
- ✓ GitHub API connectivity
- ✓ VPS SSH connectivity
- ✓ Python dependencies

### Expected Output

```
✓ GHT is set (40 chars)
✓ VPS_HOST: 23.29.114.83
✓ VPS username: beinejd
✓ SSH key found: /Users/beinejd/.ssh/id_ed25519
✓ GitHub API accessible
✓ VPS SSH connection successful
✓ All dependencies installed
```

## Common Issues

### Issue: "GitHub token not configured"

**Error**: 
```
Error: GitHub token not configured. Set GHT or GITHUB_TOKEN environment variable.
```

**Fix**:
```bash
# Add to ~/.zshrc or ~/.bashrc
export GHT="ghp_your_token_here"

# Reload shell
source ~/.zshrc
```

### Issue: "SSH Connection failed"

**Error**:
```
SSH Connection failed: Unable to establish SSH connection
```

**Fix**:
1. Verify SSH key exists:
   ```bash
   ls -la ~/.ssh/id_ed25519
   ```

2. Add key to ssh-agent:
   ```bash
   ssh-add ~/.ssh/id_ed25519
   ```

3. Test direct SSH connection:
   ```bash
   ssh -p 2223 beinejd@23.29.114.83 "echo test"
   ```

4. Add host key if needed:
   ```bash
   ssh-keyscan -p 2223 23.29.114.83 >> ~/.ssh/known_hosts
   ```

### Issue: "Failed to get public key for {owner}/{repo}"

**Error**:
```
[red]Failed to get public key for owner/repo[/red]
```

**Fix**:
1. Verify the GitHub token has the correct permissions (admin:repo_hook, repo)
2. Check the repository name is correct:
   ```bash
   # Test API access directly
   curl -H "Authorization: token $GHT" \
     https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key
   ```

3. Ensure the repository exists and is accessible to your token

### Issue: "PyNaCl Error"

**Error**:
```
Error encrypting secret: ...
```

**Fix**:
1. Reinstall PyNaCl:
   ```bash
   pip3 install --upgrade PyNaCl
   ```

2. Verify installation:
   ```bash
   python3 -c "import nacl.public; print('OK')"
   ```

## Installation & Setup

### 1. Install Dependencies
```bash
cd /Users/beinejd/Desktop/ci-cd-manager
pip3 install -r requirements.txt
```

### 2. Configure Environment
```bash
# Set GitHub token
export GHT="your_github_token_here"

# Set VPS details (optional - defaults are configured)
export VPS_HOST="23.29.114.83"
export VPS_PORT="2223"
export VPS_USER="beinejd"
```

### 3. Verify Setup
```bash
./test-api.zsh
```

### 4. Run the Manager
```bash
python3 ci-cd-manager.py
```

## Advanced Debugging

### Enable Verbose SSH Output
```bash
export PYTHONVERBOSE=1
python3 ci-cd-manager.py
```

### Test API Endpoints Manually

**List repositories:**
```bash
curl -H "Authorization: token $GHT" \
  https://api.github.com/user/repos
```

**List secrets in a repository:**
```bash
curl -H "Authorization: token $GHT" \
  https://api.github.com/repos/{owner}/{repo}/actions/secrets
```

**Get repository public key:**
```bash
curl -H "Authorization: token $GHT" \
  https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key
```

### Test VPS Connectivity

**Check VPS status:**
```bash
ssh -p 2223 beinejd@23.29.114.83 "uname -a"
```

**List deployed apps:**
```bash
ssh -p 2223 beinejd@23.29.114.83 "ls -la /home/deployer/apps/"
```

## Files Modified

- `ci-cd-manager.py`:
  - Added environment variable fallbacks
  - Added SSH key auto-detection
  - Added secret encryption with PyNaCl
  - Fixed GitHub API calls

- `requirements.txt`:
  - Added PyNaCl>=1.5.0

- `test-api.zsh` (new):
  - Diagnostic script for troubleshooting

## Next Steps

1. Run the diagnostic script to verify all systems are operational
2. Test with a sample repository to ensure API access works
3. Run the CI/CD manager to discover and register pipelines
4. Monitor pipeline execution through the dashboard

## Support

For additional help:
1. Check the diagnostic script output
2. Review API response codes using curl
3. Verify SSH connectivity independently
4. Check GitHub token permissions
