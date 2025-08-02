#!/usr/bin/env bash
# 🚀 Continue-Witty v2.7 EXTERNAL - Installation Script
# =====================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation paths
INSTALL_DIR="$HOME/.continue-witty"
SCRIPTS_DIR="$INSTALL_DIR/scripts"
CONFIG_DIR="$INSTALL_DIR"

echo -e "${BLUE}🚀 Continue-Witty v2.7 EXTERNAL Installation${NC}"
echo "=============================================="
echo

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="Linux"
else
    print_error "Unsupported platform: $OSTYPE"
    exit 1
fi

print_status "Detected platform: $PLATFORM"

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

print_status "Python 3 found: $(python3 --version)"

# Create installation directories
print_status "Creating installation directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$SCRIPTS_DIR"
mkdir -p "$CONFIG_DIR"

# Copy scripts
print_status "Installing Continue-Witty scripts..."
cp -r scripts/* "$SCRIPTS_DIR/"

# Make scripts executable
chmod +x "$SCRIPTS_DIR/continue-witty"
chmod +x "$SCRIPTS_DIR/"*.py

# Create default configuration
print_status "Creating default configuration..."
cat > "$CONFIG_DIR/config.json" << 'EOF'
{
  "version": "2.7.0-external",
  "monitoring": {
    "context_window_threshold": 0.85,
    "credit_monitoring": true,
    "session_duration_hours": 4.5,
    "auto_backup": true
  },
  "packages": {
    "default_type": "full",
    "conversation_export": true,
    "max_exchanges": 10
  },
  "bloom_restoration": {
    "auto_show_instructions": true,
    "preserve_history": true
  }
}
EOF

# Add to PATH if not already there
SHELL_RC=""
if [[ "$SHELL" == *"zsh"* ]]; then
    SHELL_RC="$HOME/.zshrc"
elif [[ "$SHELL" == *"bash"* ]]; then
    SHELL_RC="$HOME/.bashrc"
fi

if [[ -n "$SHELL_RC" ]]; then
    if ! grep -q "$INSTALL_DIR/scripts" "$SHELL_RC" 2>/dev/null; then
        print_status "Adding Continue-Witty to PATH..."
        echo "" >> "$SHELL_RC"
        echo "# Continue-Witty v2.7 Application" >> "$SHELL_RC"
        echo "export PATH=\"\$PATH:$INSTALL_DIR/scripts\"" >> "$SHELL_RC"
        print_warning "Added to $SHELL_RC - restart terminal or run: source $SHELL_RC"
    else
        print_status "PATH already configured"
    fi
fi

# Test installation
print_status "Testing installation..."
if "$SCRIPTS_DIR/continue-witty" --version &> /dev/null; then
    print_status "Continue-Witty installed successfully!"
else
    print_warning "Installation completed but test failed - may need manual PATH setup"
fi

echo
echo -e "${BLUE}🎯 Installation Complete!${NC}"
echo "=========================="
echo
echo "Continue-Witty v2.7 Application has been installed to:"
echo "  📁 Installation: $INSTALL_DIR"
echo "  🔧 Scripts: $SCRIPTS_DIR"
echo "  ⚙️  Configuration: $CONFIG_DIR/config.json"
echo
echo "Available commands:"
echo "  📦 continue-witty light    # Create light context package"
echo "  📦 continue-witty full     # Create full context package"
echo "  📦 continue-witty complex  # Create complex context package"
echo "  🌸 /bloom                  # Restore from snapshot (use in Claude)"
echo
echo "Features included:"
echo "  ✅ Three-tier monitoring (context/credit/session)"
echo "  ✅ Conversation export (v2.7 reasoning preservation)"
echo "  ✅ Enhanced bloom restoration"
echo "  ✅ Unified monitoring coordinator"
echo "  ✅ Professional context preservation"
echo
echo -e "${GREEN}🚀 Ready for seamless AI collaboration continuity!${NC}"
echo
echo "Next steps:"
echo "1. Restart your terminal or run: source $SHELL_RC"
echo "2. Try: continue-witty --help"
echo "3. Use /continue-witty in Claude Code to get started"