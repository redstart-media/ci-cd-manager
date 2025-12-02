# Cloudflare DNS - Quick Setup

## 1. Get Cloudflare API Credentials

### A. Create API Token
1. Log into Cloudflare → Profile → API Tokens
2. "Create Token" → Use template "Edit zone DNS"
3. Select your zone (domain)
4. Create token → **Copy and save it**

### B. Get Zone ID
1. Cloudflare Dashboard → Select your domain
2. Right sidebar under "API" section
3. **Copy Zone ID**

## 2. Configure VPS Manager

### Option A: Environment Variables (Recommended)
```bash
# Add to ~/.bashrc or ~/.zshrc
export CLOUDFLARE_API_TOKEN="your_api_token_here"
export CLOUDFLARE_ZONE_ID="your_zone_id_here"

# Reload shell
source ~/.bashrc
```

### Option B: Direct in Script
Edit `vps-manager.py` line ~1217:
```python
CLOUDFLARE_API_TOKEN = "your_token"
CLOUDFLARE_ZONE_ID = "your_zone_id"
```

## 3. Run VPS Manager

```bash
python3 vps-manager.py

# Should see:
✓ Cloudflare connected: yourdomain.com
✓ SSH Connected successfully!
```

## 4. Provision Site with DNS

```
Menu → 2 (Provision New Site)
Domain: example.com
Enable www? Yes
Configure DNS via Cloudflare? Yes

→ DNS automatically created and verified
→ SSL certificate obtained
→ Site live at https://example.com
```

## Features Available

### Automatic Provisioning
- ✅ Creates A records (domain + www)
- ✅ Points to your VPS IP
- ✅ Verifies DNS propagation
- ✅ Prevents SSL failures

### DNS Management (Menu → 3)
- View all DNS records
- Update DNS to point to server
- Add www subdomain
- Delete DNS records
- Toggle Cloudflare proxy (🟠/⚪)

## Important Notes

### DNS Proxy Setting
**During initial setup:** DNS only (⚪)
- Required for Let's Encrypt SSL validation
- The script automatically uses this

**After SSL works:** Can enable proxy (🟠)
- Menu → 3 → Toggle Cloudflare proxy
- Enables DDoS protection, CDN, etc.

### Troubleshooting

**"Cloudflare not configured"**
```bash
# Verify environment variables
echo $CLOUDFLARE_API_TOKEN
echo $CLOUDFLARE_ZONE_ID
```

**"Cloudflare credentials invalid"**
- Check token has "Zone:DNS:Edit" permission
- Verify Zone ID matches your domain
- Test manually:
```bash
curl -X GET "https://api.cloudflare.com/client/v4/zones/YOUR_ZONE_ID" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

**"DNS verification timed out"**
- Wait 5 minutes and retry
- Check: `dig example.com +short`
- Verify in Cloudflare dashboard

## Typical Workflow

### New Site
1. **Menu → 2** (Provision with DNS)
2. Enter domain
3. Script creates DNS + SSL + Coming Soon page
4. Visit https://yoursite.com

### Add www Later
1. **Menu → 3 → 2** (Manage DNS for site)
2. Choose "Add www subdomain"
3. Done!

### Move Site to This Server
1. **Menu → 3 → 2** (Manage DNS)
2. Choose "Update DNS to this server"
3. Wait for propagation
4. Provision site (Menu → 2)

## Security

✅ Use environment variables (not hardcoded)  
✅ Token has minimal permissions (DNS only)  
✅ Never commit credentials to git  
✅ Rotate tokens every 6-12 months  

## Summary

**What you need:**
- Cloudflare API Token (with DNS:Edit)
- Zone ID for your domain

**What you get:**
- Automated DNS setup during provisioning
- DNS verification before SSL
- Interactive DNS management
- Cloudflare proxy control
- No more manual DNS configuration!

---

**Ready?** Get your credentials and run `python3 vps-manager.py`
