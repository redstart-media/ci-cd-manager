#!/bin/bash
# =============================================================================
# Environment Variables Setup for VPS Manager
# =============================================================================
# This script helps you configure API keys and server settings as environment
# variables instead of hardcoding them in scripts.
#
# Usage: ./setup-env.sh
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "=========================================="
echo "  Environment Variables Setup"
echo "  VPS Manager Configuration"
echo "=========================================="
echo -e "${NC}"

# Detect shell configuration file
SHELL_CONFIG=""
if [[ "$SHELL" == *"zsh"* ]]; then
    SHELL_CONFIG="$HOME/.zshrc"
    echo -e "${CYAN}Detected: ZSH shell${NC}"
elif [[ "$SHELL" == *"bash"* ]]; then
    if [[ -f "$HOME/.bash_profile" ]]; then
        SHELL_CONFIG="$HOME/.bash_profile"
    else
        SHELL_CONFIG="$HOME/.bashrc"
    fi
    echo -e "${CYAN}Detected: Bash shell${NC}"
else
    echo -e "${YELLOW}Could not detect shell type. Please enter path to your shell config:${NC}"
    read -r SHELL_CONFIG
fi

echo -e "${GREEN}Will update: $SHELL_CONFIG${NC}\n"

# Backup existing config
BACKUP_FILE="${SHELL_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$SHELL_CONFIG" "$BACKUP_FILE"
echo -e "${GREEN}✓ Backup created: $BACKUP_FILE${NC}\n"

# Function to prompt for value
prompt_for_value() {
    local var_name=$1
    local description=$2
    local current_value=$3
    local allow_empty=$4
    
    echo -e "${CYAN}$description${NC}"
    if [[ -n "$current_value" ]]; then
        echo -e "${YELLOW}Current value: ${current_value:0:10}...${current_value: -4}${NC}"
        echo -e "Press Enter to keep current, or enter new value:"
    else
        echo -e "Enter value (or press Enter to skip):"
    fi
    
    read -r new_value
    
    if [[ -n "$new_value" ]]; then
        echo "$new_value"
    elif [[ -n "$current_value" ]]; then
        echo "$current_value"
    elif [[ "$allow_empty" == "true" ]]; then
        echo ""
    else
        echo ""
    fi
}

# Get current values if they exist
CURRENT_CLOUDFLARE=$(printenv CLOUDFLARE_API_TOKEN 2>/dev/null || echo "")
CURRENT_CLAUDE=$(printenv CLAUDE_API_KEY 2>/dev/null || echo "")
CURRENT_DEEPSEEK=$(printenv DEEPSEEK_API_KEY 2>/dev/null || echo "")
CURRENT_VPS_IP=$(printenv VPS_SRV1_IP 2>/dev/null || echo "")
CURRENT_VPS_PORT=$(printenv VPS_SRV1_PORT 2>/dev/null || echo "")

echo -e "${YELLOW}Configure your API keys and server settings:${NC}\n"

# Cloudflare API Token
CLOUDFLARE_TOKEN=$(prompt_for_value "CLOUDFLARE_API_TOKEN" \
    "1. Cloudflare API Token (for DNS management)" \
    "$CURRENT_CLOUDFLARE" \
    "true")

# Claude API Key
CLAUDE_KEY=$(prompt_for_value "CLAUDE_API_KEY" \
    "\n2. Claude API Key (for AI features)" \
    "$CURRENT_CLAUDE" \
    "true")

# DeepSeek API Key
DEEPSEEK_KEY=$(prompt_for_value "DEEPSEEK_API_KEY" \
    "\n3. DeepSeek API Key (for AI features)" \
    "$CURRENT_DEEPSEEK" \
    "true")

# VPS Server IP
VPS_IP=$(prompt_for_value "VPS_SRV1_IP" \
    "\n4. VPS Server IP Address (e.g., 23.29.114.83)" \
    "$CURRENT_VPS_IP" \
    "false")

if [[ -z "$VPS_IP" ]]; then
    VPS_IP="23.29.114.83"
    echo -e "${YELLOW}Using default: $VPS_IP${NC}"
fi

# VPS Server Port
VPS_PORT=$(prompt_for_value "VPS_SRV1_PORT" \
    "\n5. VPS SSH Port (default: 22)" \
    "$CURRENT_VPS_PORT" \
    "false")

if [[ -z "$VPS_PORT" ]]; then
    VPS_PORT="22"
    echo -e "${YELLOW}Using default: $VPS_PORT${NC}"
fi

# Summary
echo -e "\n${CYAN}=========================================="
echo "Summary of Configuration:"
echo -e "==========================================${NC}"
echo -e "CLOUDFLARE_API_TOKEN: ${GREEN}$(if [[ -n "$CLOUDFLARE_TOKEN" ]]; then echo "Set (${#CLOUDFLARE_TOKEN} chars)"; else echo "Not set"; fi)${NC}"
echo -e "CLAUDE_API_KEY:       ${GREEN}$(if [[ -n "$CLAUDE_KEY" ]]; then echo "Set (${#CLAUDE_KEY} chars)"; else echo "Not set"; fi)${NC}"
echo -e "DEEPSEEK_API_KEY:     ${GREEN}$(if [[ -n "$DEEPSEEK_KEY" ]]; then echo "Set (${#DEEPSEEK_KEY} chars)"; else echo "Not set"; fi)${NC}"
echo -e "VPS_SRV1_IP:          ${GREEN}$VPS_IP${NC}"
echo -e "VPS_SRV1_PORT:        ${GREEN}$VPS_PORT${NC}"

echo -e "\n${YELLOW}Add these variables to $SHELL_CONFIG? (y/n)${NC}"
read -r confirm

if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo -e "${RED}Cancelled. No changes made.${NC}"
    rm "$BACKUP_FILE"
    exit 0
fi

# Remove old entries if they exist
echo -e "\n${CYAN}Updating $SHELL_CONFIG...${NC}"

# Create temporary file
TMP_FILE=$(mktemp)

# Copy existing config, removing old VPS Manager entries
grep -v "# VPS Manager Environment Variables" "$SHELL_CONFIG" | \
grep -v "export CLOUDFLARE_API_TOKEN=" | \
grep -v "export CLAUDE_API_KEY=" | \
grep -v "export DEEPSEEK_API_KEY=" | \
grep -v "export VPS_SRV1_IP=" | \
grep -v "export VPS_SRV1_PORT=" > "$TMP_FILE" || true

# Add new entries
cat >> "$TMP_FILE" << EOF

# =============================================================================
# VPS Manager Environment Variables
# Generated: $(date)
# =============================================================================

# Cloudflare API Configuration
export CLOUDFLARE_API_TOKEN="$CLOUDFLARE_TOKEN"

# AI API Keys
export CLAUDE_API_KEY="$CLAUDE_KEY"
export DEEPSEEK_API_KEY="$DEEPSEEK_KEY"

# VPS Server Configuration
export VPS_SRV1_IP="$VPS_IP"
export VPS_SRV1_PORT="$VPS_PORT"

# =============================================================================
EOF

# Replace original config
mv "$TMP_FILE" "$SHELL_CONFIG"

echo -e "${GREEN}✓ Configuration updated successfully!${NC}\n"

# Offer to apply immediately
echo -e "${YELLOW}Apply changes now? This will reload your shell configuration. (y/n)${NC}"
read -r apply_now

if [[ "$apply_now" == "y" || "$apply_now" == "Y" ]]; then
    # Export for current session
    export CLOUDFLARE_API_TOKEN="$CLOUDFLARE_TOKEN"
    export CLAUDE_API_KEY="$CLAUDE_KEY"
    export DEEPSEEK_API_KEY="$DEEPSEEK_KEY"
    export VPS_SRV1_IP="$VPS_IP"
    export VPS_SRV1_PORT="$VPS_PORT"
    
    echo -e "${GREEN}✓ Variables exported to current session${NC}"
    echo -e "${CYAN}To apply in other terminals, run:${NC}"
    echo -e "  source $SHELL_CONFIG"
else
    echo -e "${CYAN}Changes will take effect in new terminal sessions.${NC}"
    echo -e "${CYAN}Or run: source $SHELL_CONFIG${NC}"
fi

echo -e "\n${GREEN}=========================================="
echo "  Setup Complete!"
echo -e "==========================================${NC}"
echo -e "${CYAN}Your environment is now configured for VPS Manager${NC}\n"

# Create a quick reference file
cat > "$HOME/.vps-manager-env-reference.txt" << EOF
VPS Manager Environment Variables
==================================
Generated: $(date)

To view current values:
  printenv | grep -E 'CLOUDFLARE|CLAUDE|DEEPSEEK|VPS_SRV1'

To edit values:
  nano $SHELL_CONFIG
  (Look for "VPS Manager Environment Variables" section)

To reload after editing:
  source $SHELL_CONFIG

Backup location:
  $BACKUP_FILE

Variables configured:
  - CLOUDFLARE_API_TOKEN $(if [[ -n "$CLOUDFLARE_TOKEN" ]]; then echo "(set)"; else echo "(not set)"; fi)
  - CLAUDE_API_KEY $(if [[ -n "$CLAUDE_KEY" ]]; then echo "(set)"; else echo "(not set)"; fi)
  - DEEPSEEK_API_KEY $(if [[ -n "$DEEPSEEK_KEY" ]]; then echo "(set)"; else echo "(not set)"; fi)
  - VPS_SRV1_IP: $VPS_IP
  - VPS_SRV1_PORT: $VPS_PORT
EOF

echo -e "${CYAN}Quick reference saved to: ~/.vps-manager-env-reference.txt${NC}\n"
