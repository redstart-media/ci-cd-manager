# VPS Manager - Configuration Update Guide

## What's New

The VPS Manager configuration has been simplified and improved:

1. **Hardcoded configuration at top of file** - Easy to find and edit
2. **Automatic zone detection** - No more Zone ID needed, just domain names
3. **Automatic zone creation** - Cloudflare zones created on-demand
4. **Single API token** - Manages all domains across all zones

## Breaking Changes

### ❌ Old Configuration (Environment Variables)
```bash
export CLOUDFLARE_API_TOKEN="..."
export CLOUDFLARE_ZONE_ID="..."  # ← No longer needed!
```

### ✅ New Configuration (Top of File)
Edit `vps-manager.py` lines 31-42:

```python
# ============================================================================
# CONFIGURATION - Edit these values for your setup
# ============================================================================

# VPS Server Configuration
VPS_HOST = "23.29.114.83"
VPS_SSH_USERNAME = "beinejd"
VPS_SSH_PORT = 22  # Update with your actual SSH port

# Cloudflare API Configuration
CLOUDFLARE_API_TOKEN = ""  # Add your Cloudflare API token here

# ============================================================================
```

## Key Improvements

### 1. No More Zone ID Required

**Before:**
```python
# Needed both:
CLOUDFLARE_API_TOKEN = "..."
CLOUDFLARE_ZONE_ID = "..."  # Had to look this up manually
```

**After:**
```python
# Only need:
CLOUDFLARE_API_TOKEN = "..."
# Zone automatically detected from domain name!
```

### 2. Automatic Zone Creation

**Before:**
- Domain had to already exist in Cloudflare
- Had to manually add domain to Cloudflare first
- Then find Zone ID
- Then configure script

**After:**
- Just provision any domain
- Script automatically creates Cloudflare zone if needed
- No manual Cloudflare setup required
- Seamless workflow

### 3. Multi-Domain Support

**Before:**
- One Zone ID = one domain/zone
- Managing multiple domains required multiple configurations
- Had to track which Zone ID was for which domain

**After:**
- One API token works for ALL domains
- Script automatically finds/creates zones per domain
- Manage example.com, another-site.com, test.dev all from one script
- No zone tracking needed

### 4. Centralized Configuration

**Before:**
- Configuration spread across multiple places
- Environment variables
- Hard to know what needs changing

**After:**
- Everything at top of file (lines 31-42)
- Single place to edit
- Clear comments
- No environment variables needed

## Migration Guide

### Step 1: Get Your API Token

Your existing token should work, but verify it has these permissions:

**Required Permissions:**
- `Zone:DNS:Edit` - Edit DNS records
- `Zone:Zone:Read` - Read zone information
- `Zone:Zone:Edit` - Create new zones (optional, only if creating zones)

**To check/update token:**
1. Cloudflare Dashboard → Profile → API Tokens
2. Find your existing token → Edit
3. Ensure permissions listed above
4. Or create new token with "Edit zone DNS" template + Zone:Zone:Edit

### Step 2: Update vps-manager.py

Edit lines 31-42:

```python
# VPS Server Configuration
VPS_HOST = "23.29.114.83"           # Your server IP
VPS_SSH_USERNAME = "beinejd"        # Your SSH username
VPS_SSH_PORT = 2223                 # Your SSH port

# Cloudflare API Configuration
CLOUDFLARE_API_TOKEN = "your_token_here"  # Paste your token
```

### Step 3: Remove Environment Variables (Optional)

You no longer need these:
```bash
# Can remove from ~/.bashrc or ~/.zshrc:
# export CLOUDFLARE_API_TOKEN="..."
# export CLOUDFLARE_ZONE_ID="..."
```

### Step 4: Test

```bash
python3 vps-manager.py

# Should see:
✓ Cloudflare API connected
✓ SSH Connected successfully!
```

## Usage Changes

### Provisioning a New Domain

**Before:**
1. Add domain to Cloudflare manually
2. Find Zone ID
3. Update script configuration
4. Run provisioning

**After:**
1. Run provisioning
   - Script creates zone if needed
   - Script creates DNS records
   - Done!

```bash
Menu → 2 (Provision New Site)
Enter domain: brandnew-site.com
Enable www? Yes
Configure DNS? Yes

→ Zone automatically created (if needed)
→ DNS records created
→ Site provisioned
```

### Viewing DNS Records

**Before:**
```
Menu → 3 → 1 (View all DNS records)
→ Shows all records in configured zone
```

**After:**
```
Menu → 3 → 1 (View DNS records for domain)
Enter domain: example.com
→ Script finds zone for domain
→ Shows DNS records
```

### Managing Multiple Domains

**Before:**
- Switch between different ZONE_ID configurations
- Or run multiple instances with different configs
- Complex zone management

**After:**
```
Menu → 3 → 2 (Manage DNS for specific domain)
Enter domain: example.com
→ Manages example.com zone

Menu → 3 → 2 (Manage DNS for specific domain)
Enter domain: another-site.com
→ Manages another-site.com zone

All from same script instance!
```

## Technical Details

### How Zone Detection Works

1. User enters domain (e.g., `example.com` or `www.example.com`)
2. Script extracts root domain (`example.com`)
3. Script queries Cloudflare API: "Do I have a zone for example.com?"
4. **If zone exists:** Use it
5. **If zone doesn't exist:** Create it (if API token has permission)
6. Cache zone ID for future use in this session

### Zone Caching

Zones are cached in memory during script execution:
- First lookup: API call to Cloudflare
- Subsequent lookups: Uses cached zone ID
- Fast performance for multiple operations on same domain
- Cache clears when script exits

### Subdomain Handling

Script automatically handles subdomains:
- `www.example.com` → finds/creates zone for `example.com`
- `api.mysite.com` → finds/creates zone for `mysite.com`
- `subdomain.example.com` → finds/creates zone for `example.com`

Root domain extraction is automatic!

## Configuration File Structure

```python
# Lines 31-42: Configuration Block
# ============================================================================
# CONFIGURATION - Edit these values for your setup
# ============================================================================

# VPS Server Configuration
VPS_HOST = "23.29.114.83"           # Your VPS IP address
VPS_SSH_USERNAME = "beinejd"        # SSH user (with sudo access)
VPS_SSH_PORT = 22                   # SSH port number

# Cloudflare API Configuration
CLOUDFLARE_API_TOKEN = ""           # Your Cloudflare API token
                                    # No Zone ID needed!

# ============================================================================
```

**What to edit:**
- ✅ `VPS_HOST` - Your server IP
- ✅ `VPS_SSH_USERNAME` - Your SSH username  
- ✅ `VPS_SSH_PORT` - Your SSH port (not 22 if customized)
- ✅ `CLOUDFLARE_API_TOKEN` - Your API token (leave empty to disable)

**What NOT to edit:**
- PM2_PATH (line 260) - Only change if Node version updates
- Don't modify imports or class definitions
- Don't change the configuration comment block markers

## API Token Requirements

### Minimum Permissions (DNS only)
```
Zone:DNS:Edit
Zone:Zone:Read
```
**Allows:**
- Edit DNS records in existing zones
- View zone information
- Does NOT allow zone creation

### Recommended Permissions (Full features)
```
Zone:DNS:Edit
Zone:Zone:Read
Zone:Zone:Edit
```
**Allows:**
- Edit DNS records
- View zone information
- Create new zones automatically
- Full automated provisioning

### How to Create Token

1. **Cloudflare Dashboard** → Profile → API Tokens
2. **Create Token** → "Edit zone DNS" template
3. **Add permission:** Zone:Zone:Edit (for zone creation)
4. **Zone Resources:**
   - Include → All zones
   - Or: Specific zones only (limits what script can manage)
5. **Create Token** → Copy and save

## Troubleshooting

### "Cloudflare not configured"

**Issue:** Script shows Cloudflare disabled

**Fix:**
1. Check line 41 in vps-manager.py
2. Ensure `CLOUDFLARE_API_TOKEN = "your_actual_token"`
3. Token should be in quotes
4. No trailing spaces

### "Cloudflare credentials invalid"

**Issue:** Token doesn't work

**Check:**
1. Token has required permissions (see above)
2. Token hasn't expired
3. No extra spaces in token string
4. Token is from correct Cloudflare account

**Test manually:**
```bash
curl -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### "No zone found for domain"

**Issue:** Script can't find zone and can't create it

**Reasons:**
1. Domain doesn't exist in Cloudflare
2. Token lacks Zone:Zone:Edit permission
3. Domain not managed by this Cloudflare account

**Fix:**
- Add Zone:Zone:Edit permission to token
- Or manually add domain to Cloudflare first

### "Failed to create zone"

**Issue:** Zone creation fails

**Common causes:**
1. Domain already exists in Cloudflare (on different account)
2. Token lacks Zone:Zone:Edit permission
3. Domain is invalid or reserved
4. Account at zone limit (free tier: 1000 zones)

**Fix:**
1. Check domain isn't already added to Cloudflare
2. Verify token permissions
3. Check account quota in Cloudflare dashboard

## Configuration Examples

### Example 1: Single Domain Setup
```python
VPS_HOST = "192.168.1.100"
VPS_SSH_USERNAME = "admin"
VPS_SSH_PORT = 2222
CLOUDFLARE_API_TOKEN = "abc123..."

# Manages: example.com
```

### Example 2: Multiple Domains
```python
VPS_HOST = "23.29.114.83"
VPS_SSH_USERNAME = "deployer"
VPS_SSH_PORT = 22
CLOUDFLARE_API_TOKEN = "xyz789..."

# Manages: example.com, site2.com, test.dev, etc.
# All from same configuration!
```

### Example 3: No Cloudflare
```python
VPS_HOST = "192.168.1.100"
VPS_SSH_USERNAME = "admin"  
VPS_SSH_PORT = 22
CLOUDFLARE_API_TOKEN = ""  # Empty = Cloudflare disabled

# DNS features disabled
# Manual DNS configuration required
```

## Security Best Practices

### ✅ Do
- Keep API token in the script file (not committed to git)
- Use `.gitignore` to exclude configured script
- Rotate tokens every 6-12 months
- Use minimum required permissions
- Monitor API token usage in Cloudflare

### ❌ Don't
- Commit configured script to public repositories
- Share scripts with API tokens included
- Use Global API Key (always use tokens)
- Give tokens more permissions than needed
- Leave default empty config in production

## Version Control

If using git:

```bash
# Option 1: Don't commit configured script
echo "vps-manager.py" >> .gitignore

# Option 2: Commit template, maintain local config
cp vps-manager.py vps-manager-template.py
echo "vps-manager.py" >> .gitignore
# Edit vps-manager.py with real credentials
# Commit vps-manager-template.py (with placeholders)
```

## Summary of Changes

| Feature | Old | New |
|---------|-----|-----|
| Zone ID | Required | Not needed |
| Configuration | Environment variables | Top of file |
| Zone creation | Manual | Automatic |
| Multi-domain | Complex | Built-in |
| Setup time | 5-10 minutes | 30 seconds |

**Migration time:** ~2 minutes  
**Complexity:** Much simpler  
**Flexibility:** Much better  

---

**Ready to update?** Just edit lines 31-42 in vps-manager.py!
