#!/bin/zsh
# Start CI/CD Manager with proper setup

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 CI/CD Manager Launcher"
echo "========================"

# Check environment
echo ""
echo "📋 Checking environment..."

if [[ -z "$GHT" ]]; then
    echo "❌ Error: GitHub token not configured"
    echo ""
    echo "Set the token in your shell:"
    echo "  export GHT='your_github_token'"
    echo ""
    echo "Or add to ~/.zshrc:"
    echo "  echo 'export GHT=\"your_github_token\"' >> ~/.zshrc"
    exit 1
fi

# Try to find SSH key and add to agent
echo "🔑 Checking SSH setup..."
SSH_KEY=""
for key in "$HOME/.ssh/id_ed25519" "$HOME/.ssh/id_rsa" "$HOME/.ssh/id_ecdsa"; do
    if [[ -f "$key" ]]; then
        SSH_KEY="$key"
        break
    fi
done

if [[ -n "$SSH_KEY" ]]; then
    ssh-add "$SSH_KEY" 2>/dev/null || true
    echo "✓ SSH key loaded"
else
    echo "⚠️  No SSH key found - remote operations may fail"
fi

# Check dependencies
echo ""
echo "📦 Checking dependencies..."
if ! python3 -c "import paramiko, rich, requests, nacl" 2>/dev/null; then
    echo "❌ Missing dependencies"
    echo "Install with: pip3 install -r requirements.txt"
    exit 1
fi
echo "✓ All dependencies installed"

# Run diagnostics if requested
if [[ "$1" == "test" ]]; then
    echo ""
    echo "Running diagnostics..."
    ./test-api.zsh
    exit 0
fi

# Start the manager
echo ""
echo "🎯 Starting CI/CD Manager..."
echo "========================"
python3 ci-cd-manager.py
