#!/bin/zsh
# API and connectivity diagnostic script

set -e

echo "==================================="
echo "  CI/CD Manager - Diagnostics"
echo "==================================="

# Check environment variables
echo ""
echo "📋 Checking environment variables..."
if [[ -z "$GHT" ]]; then
    echo "❌ GHT not set"
else
    echo "✓ GHT is set (${#GHT} chars)"
fi

if [[ -z "$VPS_HOST" ]]; then
    echo "❌ VPS_HOST not set (using default)"
else
    echo "✓ VPS_HOST: $VPS_HOST"
fi

if [[ -z "$VPS_USER" ]] && [[ -z "$VPS_SSH_USERNAME" ]]; then
    echo "⚠️  VPS_USER/VPS_SSH_USERNAME not set"
else
    echo "✓ VPS username: ${VPS_USER:-$VPS_SSH_USERNAME}"
fi

VPS_PORT=${VPS_PORT:-${VPS_SRV1_PORT:-2223}}
echo "✓ VPS_PORT: $VPS_PORT"

# Check SSH key
echo ""
echo "🔑 Checking SSH configuration..."
SSH_KEY=""
for key in "$HOME/.ssh/id_ed25519" "$HOME/.ssh/id_rsa" "$HOME/.ssh/id_ecdsa" "$HOME/.ssh/id_dsa"; do
    if [[ -f "$key" ]]; then
        SSH_KEY="$key"
        echo "✓ SSH key found: $SSH_KEY"
        break
    fi
done
if [[ -z "$SSH_KEY" ]]; then
    echo "❌ No SSH key found in ~/.ssh/"
fi

# Test GitHub API
echo ""
echo "🐙 Testing GitHub API..."
if [[ -z "$GHT" ]]; then
    echo "❌ Cannot test - GHT not set"
else
    echo "Testing authentication..."
    http_code=$(curl -s -o /tmp/gh_response.json -w "%{http_code}" \
        -H "Authorization: token $GHT" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/user")
    
    if [[ "$http_code" == "200" ]]; then
        login=$(grep -o '"login":"[^"]*' /tmp/gh_response.json | cut -d'"' -f4 || echo "unknown")
        echo "✓ GitHub API accessible, authenticated as: $login"
    else
        echo "❌ GitHub API error: HTTP $http_code"
        cat /tmp/gh_response.json 2>/dev/null || echo "(no response)"
    fi
fi

# Test VPS SSH connectivity
echo ""
echo "🖥️  Testing VPS SSH connectivity..."
VPS_HOST=${VPS_HOST:-23.29.114.83}
VPS_USER=${VPS_USER:-${VPS_SSH_USERNAME:-beinejd}}

# First, add the key to ssh-agent if available
if [[ -n "$SSH_KEY" ]]; then
    ssh-add "$SSH_KEY" 2>/dev/null || true
fi

if ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 \
    -p "$VPS_PORT" "$VPS_USER@$VPS_HOST" "echo 'SSH connection successful'" 2>&1 | grep -q "successful"; then
    echo "✓ VPS SSH connection successful"
else
    echo "❌ VPS SSH connection failed"
    echo "  Host: $VPS_HOST:$VPS_PORT"
    echo "  User: $VPS_USER"
    echo "  Key: $SSH_KEY"
    echo ""
    echo "  Debugging info:"
    echo "  - Check if host key is known: ssh-keygen -F $VPS_HOST"
    echo "  - Add host key: ssh-keyscan -p $VPS_PORT -t ed25519 $VPS_HOST >> ~/.ssh/known_hosts"
fi

# Check dependencies
echo ""
echo "📦 Checking Python dependencies..."
python3 -c "import paramiko; print('✓ paramiko installed')" 2>/dev/null || echo "❌ paramiko missing"
python3 -c "import rich; print('✓ rich installed')" 2>/dev/null || echo "❌ rich missing"
python3 -c "import requests; print('✓ requests installed')" 2>/dev/null || echo "❌ requests missing"
python3 -c "import nacl; print('✓ PyNaCl installed')" 2>/dev/null || echo "❌ PyNaCl missing"

echo ""
echo "==================================="
echo "  Diagnostics Complete"
echo "==================================="
