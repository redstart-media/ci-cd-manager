# Cloudflare DNS Integration Guide

## Overview

The VPS Manager now includes full Cloudflare DNS management via API. This automates DNS record creation during site provisioning and provides complete DNS management capabilities.

## Features

### 🎯 Automatic DNS Setup During Provisioning
- Creates A records for domain and www subdomain
- Points records to your VPS IP automatically
- Verifies DNS propagation before SSL certificate generation
- Prevents SSL failures due to DNS issues

### 🔧 Interactive DNS Management
- View all DNS records in your zone
- Manage DNS for specific domains
- Update records to point to your VPS
- Toggle Cloudflare proxy (orange cloud)
- Add/remove www subdomains
- Delete DNS records

### ✅ DNS Verification
- Checks DNS propagation before SSL setup
- Prevents certbot failures from premature certificate requests
- 60-second timeout with status updates

## Prerequisites

### 1. Cloudflare Account
You need a Cloudflare account with your domain's DNS managed by Cloudflare.

### 2. API Token
Create a Cloudflare API Token with **Zone:DNS:Edit** permissions:

**Steps:**
1. Log into Cloudflare Dashboard
2. Go to Profile → API Tokens
3. Click "Create Token"
4. Use template: "Edit zone DNS"
5. Select your zone (domain)
6. Create token and save it securely

**Token permissions needed:**
- Zone → DNS → Edit

### 3. Zone ID
Find your Zone ID in Cloudflare Dashboard:

**Steps:**
1. Select your domain
2. Look in the right sidebar under "API"
3. Copy the "Zone ID"

## Configuration

### Method 1: Environment Variables (Recommended)

Create a `.env` file or export variables:

```bash
# In your terminal or .bashrc/.zshrc
export CLOUDFLARE_API_TOKEN="your_api_token_here"
export CLOUDFLARE_ZONE_ID="your_zone_id_here"
```

**Benefits:**
- Keeps credentials out of code
- Easy to update
- Secure (not committed to git)

### Method 2: Direct Configuration

Edit `vps-manager.py` around line ~1217:

```python
# Replace these with your actual values
CLOUDFLARE_API_TOKEN = "your_api_token_here"
CLOUDFLARE_ZONE_ID = "your_zone_id_here"
```

**Note:** Only do this if you won't commit the file to git.

## Usage

### Starting the Script

```bash
# With environment variables set:
python3 vps-manager.py

# Output shows Cloudflare status:
✓ Cloudflare connected: yourdomain.com
✓ SSH Connected successfully!
```

### Provisioning a New Site with DNS

**Menu: Option 2 - Provision New Site**

```
Select an option: 2

Enter domain name: example.com
Enable www subdomain? (y/n): y
Configure DNS via Cloudflare? (y/n): y

Provisioning example.com...
⠋ Configuring DNS records...                    [Done]
  ✓ Created DNS A record: example.com → 23.29.114.83
  ✓ Created DNS A record: www.example.com → 23.29.114.83
⠋ Verifying DNS propagation...                  [Done]
  ✓ DNS propagated: example.com → 23.29.114.83
⠋ Creating directory structure...               [Done]
⠋ Creating Coming Soon page...                  [Done]
⠋ Configuring NGINX...                          [Done]
⠋ Testing NGINX configuration...                [Done]
⠋ Reloading NGINX...                            [Done]
⠋ Obtaining SSL certificate...                  [Done]

✓ Successfully provisioned example.com!
  Coming Soon page is now live at https://example.com
```

**What happens:**
1. Creates DNS A records in Cloudflare
2. Waits for DNS to propagate (up to 60 seconds)
3. Proceeds with NGINX, SSL, etc.
4. SSL setup succeeds because DNS is ready

### Managing DNS Records

**Menu: Option 3 - Manage DNS Records**

#### View All DNS Records
```
Select an option: 3
Select option: 1

╭────────────────── DNS Records ──────────────────╮
│ Type │ Name           │ Content       │ Proxied │
├──────┼────────────────┼───────────────┼─────────┤
│ A    │ example.com    │ 23.29.114.83  │ ⚪      │
│ A    │ www.example.com│ 23.29.114.83  │ ⚪      │
│ MX   │ example.com    │ mail.example  │ ⚪      │
╰─────────────────────────────────────────────────╯
```

**Proxied indicators:**
- 🟠 = Cloudflare proxy enabled (traffic through Cloudflare)
- ⚪ = DNS only (direct to your server)

#### Manage Specific Domain
```
Select an option: 3
Select option: 2
Enter domain name: example.com

╭────────────────── DNS Records - example.com ────╮
│ Type │ Name         │ Content      │ Proxied    │
├──────┼──────────────┼──────────────┼────────────┤
│ A    │ example.com  │ 23.29.114.83 │ ⚪         │
╰─────────────────────────────────────────────────╯

Options:
  1. Update DNS to point to this server
  2. Add www subdomain
  3. Delete DNS records
  4. Toggle Cloudflare proxy
  b. Back to main menu
```

**Option 1: Update DNS to this server**
- Points domain to your VPS IP
- Useful if DNS was pointing elsewhere

**Option 2: Add www subdomain**
- Creates www.example.com → VPS IP
- Quick way to add www after initial setup

**Option 3: Delete DNS records**
- Removes all DNS records for the domain
- **Destructive:** requires confirmation

**Option 4: Toggle Cloudflare proxy**
- Switches between 🟠 (proxied) and ⚪ (DNS only)
- Proxied = DDoS protection, caching, CDN
- DNS only = Required for Let's Encrypt during initial setup

## DNS Proxy Settings

### When to Use DNS Only (⚪)

**Required for:**
- Initial SSL certificate setup (Let's Encrypt validation)
- SSH access to server
- Direct server access

**During provisioning**, the script automatically uses **DNS only** mode.

### When to Use Cloudflare Proxy (🟠)

**After SSL is set up**, you can enable proxy for:
- DDoS protection
- CDN/caching
- Analytics
- Firewall rules
- Rate limiting

**To enable:**
1. Menu → Option 3 → Manage DNS
2. Select your domain
3. Choose "Toggle Cloudflare proxy"

### SSL Certificate Renewal with Proxy

If you enable Cloudflare proxy (🟠), Let's Encrypt renewals may fail. 

**Solutions:**
1. Use Cloudflare Origin Certificates (recommended)
2. Temporarily disable proxy during renewal
3. Use DNS validation instead of HTTP validation

## Troubleshooting

### "Cloudflare not configured"

**Issue:** API token or Zone ID not set

**Fix:**
```bash
# Set environment variables
export CLOUDFLARE_API_TOKEN="your_token"
export CLOUDFLARE_ZONE_ID="your_zone_id"

# Then restart the script
python3 vps-manager.py
```

### "Cloudflare credentials invalid"

**Issue:** Token doesn't have permission or is wrong

**Check:**
1. Token has "Zone:DNS:Edit" permission
2. Token is for the correct zone
3. Token hasn't expired
4. Zone ID matches your domain

**Verify manually:**
```bash
curl -X GET "https://api.cloudflare.com/client/v4/zones/YOUR_ZONE_ID" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

### "DNS verification timed out"

**Issue:** DNS hasn't propagated yet

**Reasons:**
- Cloudflare propagation delay (usually < 5 minutes)
- ISP DNS caching
- Network issues

**Fix:**
1. Wait a few minutes and retry provisioning
2. Check DNS manually: `dig example.com`
3. Verify records exist in Cloudflare dashboard

### "Failed to create DNS record: already exists"

**Issue:** Record already exists (not actually an error)

**Result:** Script treats this as success and continues

### SSL Certificate Fails After DNS Setup

**Issue:** DNS propagation incomplete or proxy enabled

**Fix:**
1. Ensure DNS is in **DNS only** mode (⚪) not proxied (🟠)
2. Wait longer for DNS propagation
3. Verify DNS: `dig example.com +short`
4. Manually check: `nslookup example.com`

## API Rate Limits

Cloudflare API has rate limits:
- **1,200 requests per 5 minutes** (standard)

The script is conservative with API calls:
- Provisioning: ~4-6 calls
- DNS management: 1-3 calls per action

**Unlikely to hit limits** in normal use.

## Security Best Practices

### 1. Use Environment Variables
```bash
# Never commit credentials to git
echo "CLOUDFLARE_API_TOKEN=..." >> ~/.bashrc
echo "CLOUDFLARE_ZONE_ID=..." >> ~/.bashrc
source ~/.bashrc
```

### 2. Limit Token Permissions
- Only grant "Zone:DNS:Edit"
- Don't use Global API Key
- Create token for specific zone only

### 3. Rotate Tokens Periodically
- Create new token every 6-12 months
- Revoke old tokens
- Update environment variables

### 4. Monitor Token Usage
- Check Cloudflare audit logs
- Review API token activity
- Set up alerts for suspicious activity

## Advanced Usage

### DNS Verification Timeout

Default: 60 seconds

**To modify**, edit the provision_site function:
```python
dns_ready = self.cloudflare.verify_dns_propagation(domain, self.host, timeout=120)
```

### Proxied by Default

Currently, DNS records are created as **DNS only** (proxied=False).

**To change default**, edit ensure_a_record calls:
```python
self.cloudflare.ensure_a_record(domain, self.host, proxied=True)
```

### Multiple Zones

To manage multiple domains across different zones:
1. Create separate token for each zone
2. Run script with different credentials
3. Or extend script to support multiple CloudflareManager instances

## Integration with CI/CD

The Cloudflare integration prepares for future CI/CD features:

**Planned workflow:**
1. GitHub push triggers deployment
2. Code deployed to server
3. DNS automatically updated if needed
4. PM2 restarts application
5. Health check verifies site is live

**Current state:** Manual provisioning with DNS automation

## Example Workflows

### New Site from Scratch
```
1. Menu → Option 2 (Provision New Site)
2. Enter: newsite.com
3. Enable www: Yes
4. Configure DNS: Yes
5. Wait for provisioning to complete
6. Visit https://newsite.com (Coming Soon page)
```

### Add www to Existing Site
```
1. Menu → Option 3 (Manage DNS)
2. Select: 2 (Manage specific domain)
3. Enter: example.com
4. Select: 2 (Add www subdomain)
5. Update NGINX config to handle www
6. Reload NGINX
```

### Switch DNS to New Server
```
1. Menu → Option 3 (Manage DNS)
2. Select: 2 (Manage specific domain)
3. Enter: example.com
4. Select: 1 (Update DNS to this server)
5. Wait for DNS propagation
6. Site now points to new server
```

### Enable Cloudflare Protection
```
1. Ensure SSL is set up and working
2. Menu → Option 3 (Manage DNS)
3. Select: 2 (Manage specific domain)
4. Select: 4 (Toggle Cloudflare proxy)
5. Traffic now goes through Cloudflare
```

## Summary

✅ **Automatic DNS setup during provisioning**  
✅ **DNS propagation verification**  
✅ **Interactive DNS management**  
✅ **Cloudflare proxy toggle**  
✅ **Secure credential handling**  
✅ **Prevents SSL failures from DNS issues**  

The Cloudflare integration transforms site provisioning from a manual, multi-step process into a single automated workflow.

---

**Next Steps:**
1. Get your Cloudflare API token and Zone ID
2. Configure environment variables
3. Run the script and provision a site
4. Watch the automated DNS setup work!
