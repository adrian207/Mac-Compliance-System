#!/bin/bash
#
# ZeroTrust Telemetry Agent Installer
# Author: Adrian Johnson <adrian207@gmail.com>
#
# Installs the telemetry agent as a LaunchDaemon on Mac OS
#

set -e

# Configuration
AGENT_NAME="zerotrust-agent"
INSTALL_DIR="/usr/local/zerotrust"
CONFIG_DIR="/etc/zerotrust-agent"
LOG_DIR="/var/log/zerotrust-agent"
LAUNCH_DAEMON_PLIST="/Library/LaunchDaemons/com.zerotrust.agent.plist"
AGENT_USER="root"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "This installer must be run as root (use sudo)"
        exit 1
    fi
}

check_macos() {
    if [ "$(uname)" != "Darwin" ]; then
        log_error "This agent is designed for Mac OS only"
        exit 1
    fi
}

check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    log_info "Found Python $PYTHON_VERSION"
}

create_directories() {
    log_info "Creating directories..."
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$LOG_DIR"
    
    chmod 755 "$INSTALL_DIR"
    chmod 755 "$CONFIG_DIR"
    chmod 755 "$LOG_DIR"
}

install_dependencies() {
    log_info "Installing Python dependencies..."
    
    python3 -m pip install --upgrade pip || true
    python3 -m pip install requests urllib3 || {
        log_error "Failed to install dependencies"
        exit 1
    }
}

copy_agent_files() {
    log_info "Copying agent files..."
    
    # Copy agent directory
    cp -R agent "$INSTALL_DIR/"
    
    # Make agent executable
    chmod +x "$INSTALL_DIR/agent/agent.py"
    
    log_info "Agent files installed to $INSTALL_DIR"
}

create_config() {
    log_info "Creating configuration file..."
    
    CONFIG_FILE="$CONFIG_DIR/config.json"
    
    if [ -f "$CONFIG_FILE" ]; then
        log_warn "Configuration file already exists, creating backup..."
        cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Prompt for configuration
    read -p "Enter API endpoint [http://localhost:8000]: " API_ENDPOINT
    API_ENDPOINT=${API_ENDPOINT:-http://localhost:8000}
    
    read -p "Enter API key (leave empty if none): " API_KEY
    
    read -p "Enter collection interval in seconds [300]: " COLLECTION_INTERVAL
    COLLECTION_INTERVAL=${COLLECTION_INTERVAL:-300}
    
    # Create config file
    cat > "$CONFIG_FILE" << EOF
{
    "api_endpoint": "$API_ENDPOINT",
    "api_key": ${API_KEY:+"\"$API_KEY\""}${API_KEY:-null},
    "collection_interval": $COLLECTION_INTERVAL,
    "device_name": "$(hostname)",
    "collectors_enabled": {
        "system_info": true,
        "security_status": true,
        "network_info": true,
        "process_info": true,
        "software_inventory": true
    },
    "log_level": "INFO"
}
EOF
    
    chmod 600 "$CONFIG_FILE"
    log_info "Configuration saved to $CONFIG_FILE"
}

create_launch_daemon() {
    log_info "Creating LaunchDaemon..."
    
    cat > "$LAUNCH_DAEMON_PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.zerotrust.agent</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$INSTALL_DIR/agent/agent.py</string>
        <string>--config</string>
        <string>$CONFIG_DIR/config.json</string>
    </array>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    
    <key>StandardOutPath</key>
    <string>$LOG_DIR/agent.log</string>
    
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/agent.error.log</string>
    
    <key>ThrottleInterval</key>
    <integer>60</integer>
    
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF
    
    chmod 644 "$LAUNCH_DAEMON_PLIST"
    log_info "LaunchDaemon created at $LAUNCH_DAEMON_PLIST"
}

start_agent() {
    log_info "Starting agent..."
    
    # Load the LaunchDaemon
    launchctl load "$LAUNCH_DAEMON_PLIST" 2>/dev/null || {
        log_warn "LaunchDaemon already loaded, restarting..."
        launchctl unload "$LAUNCH_DAEMON_PLIST" 2>/dev/null || true
        launchctl load "$LAUNCH_DAEMON_PLIST"
    }
    
    sleep 2
    
    # Check if agent is running
    if launchctl list | grep -q "com.zerotrust.agent"; then
        log_info "Agent started successfully!"
    else
        log_error "Agent failed to start"
        log_info "Check logs at $LOG_DIR/agent.error.log"
        exit 1
    fi
}

print_summary() {
    echo ""
    echo "============================================"
    echo "  ZeroTrust Agent Installation Complete!"
    echo "============================================"
    echo ""
    echo "Installation Directory: $INSTALL_DIR"
    echo "Configuration File:     $CONFIG_DIR/config.json"
    echo "Log Files:              $LOG_DIR/"
    echo "LaunchDaemon:           $LAUNCH_DAEMON_PLIST"
    echo ""
    echo "Management Commands:"
    echo "  Start:    sudo launchctl load $LAUNCH_DAEMON_PLIST"
    echo "  Stop:     sudo launchctl unload $LAUNCH_DAEMON_PLIST"
    echo "  Status:   sudo launchctl list | grep zerotrust"
    echo "  Logs:     tail -f $LOG_DIR/agent.log"
    echo ""
    echo "To test manually:"
    echo "  python3 $INSTALL_DIR/agent/agent.py --config $CONFIG_DIR/config.json --once"
    echo ""
}

# Main installation flow
main() {
    echo "=================================="
    echo " ZeroTrust Agent Installer v0.9.3"
    echo "=================================="
    echo ""
    
    check_root
    check_macos
    check_python
    
    create_directories
    install_dependencies
    copy_agent_files
    create_config
    create_launch_daemon
    start_agent
    
    print_summary
}

# Run installation
main

