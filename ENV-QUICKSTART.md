# Quick Start: Environment Variables

## 🚀 30-Second Setup

```bash
# 1. Make setup script executable
chmod +x setup-env.sh

# 2. Run setup
./setup-env.sh

# 3. Follow prompts and enter your:
#    - Cloudflare API Token
#    - VPS Server IP
#    - VPS SSH Port
#    (Skip Claude/DeepSeek if you don't have them)

# 4. Done!
```

## ✅ Verify It Works

```bash
# Check variables are set
printenv | grep CLOUDFLARE
printenv | grep VPS_SRV1

# Run VPS Manager
python3 vps-manager.py

# Should see:
# "Config: VPS from env, Cloudflare from env"
# "✓ Cloudflare API connected successfully!"
```

## 📋 What You Need

1. **Cloudflare API Token**
   - Get from: https://dash.cloudflare.com/profile/api-tokens
   - Click "Create Token"
   - Use template: "Edit zone DNS"
   - Add permission: Zone:Zone:Edit

2. **VPS Server Details**
   - IP address (e.g., 23.29.114.83)
   - SSH port (usually 22 or custom)

3. **(Optional) AI API Keys**
   - Claude API Key
   - DeepSeek API Key

## 🔄 Update Later

```bash
# Run setup again to change values
./setup-env.sh

# Or edit manually
nano ~/.zshrc  # (or ~/.bashrc)

# Then reload
source ~/.zshrc
```

## 🆘 Troubleshooting

**Problem:** "Cloudflare not configured"

**Solution:**
```bash
# Check if variable is set
echo $CLOUDFLARE_API_TOKEN

# If empty, run setup again
./setup-env.sh
```

**Problem:** Changes not taking effect

**Solution:**
```bash
# Reload shell config
source ~/.zshrc  # or source ~/.bashrc

# Or open a new terminal
```

## 📖 Full Documentation

See [ENV-VARIABLES-GUIDE.md](ENV-VARIABLES-GUIDE.md) for complete details.

## 🎯 Benefits

- ✅ No credentials in code
- ✅ Easy to update
- ✅ Safe for git
- ✅ Works across all scripts
- ✅ Secure and portable

---

**That's it!** Your credentials are now managed securely via environment variables.
