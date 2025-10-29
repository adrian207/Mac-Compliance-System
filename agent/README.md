# ZeroTrust Telemetry Agent

**Author:** Adrian Johnson <adrian207@gmail.com>  
**Version:** 0.9.3  
**Platform:** Mac OS (10.15+)

## Overview

The ZeroTrust Telemetry Agent is a lightweight, autonomous agent that collects comprehensive device telemetry and security posture data from Mac OS endpoints. It reports to the central ZeroTrust platform for risk assessment, compliance monitoring, and Zero Trust enforcement.

### Key Features

- **Hybrid Architecture** - Works with or without Munki MDM
  - Leverages Munki data when available for efficiency
  - Falls back to direct collection when Munki is not present
  
- **Comprehensive Data Collection** 
  - System hardware and OS information
  - Security posture (FileVault, SIP, Firewall, Gatekeeper, etc.)
  - Network configuration and connectivity
  - Running processes and services
  - Software inventory

- **Lightweight & Efficient**
  - Minimal resource usage
  - Configurable collection intervals
  - Intelligent caching and deduplication

- **Reliable & Resilient**
  - Automatic retry with exponential backoff
  - Graceful degradation if collectors fail
  - Runs as LaunchDaemon for reliability

- **Easy Management**
  - Simple installer script
  - CLI management tool
  - Structured logging

## Architecture

### Collection Modules

The agent uses modular collectors that can be independently enabled/disabled:

1. **SystemInfoCollector** - Hardware and OS information
2. **SecurityStatusCollector** - Security posture and compliance
3. **NetworkInfoCollector** - Network configuration and connectivity
4. **ProcessInfoCollector** - Running processes and services
5. **SoftwareInventoryCollector** - Installed software (with Munki integration)

### Munki Integration

When Munki is detected, the agent:
- Reads `ManagedInstallReport.plist` for software inventory
- Uses Munki's hardware data to reduce collection overhead
- Falls back to direct collection for data Munki doesn't track

This hybrid approach provides:
- **Efficiency** - Leverages existing Munki data collection
- **Flexibility** - Works standalone without Munki
- **Completeness** - Collects security data Munki doesn't track

## Installation

### Prerequisites

- Mac OS 10.15 (Catalina) or later
- Python 3.7 or later
- Root/administrator access

### Quick Install

1. **Download the agent package:**
```bash
git clone https://github.com/adrian207/Mac-Compliance-System.git
cd Mac-Compliance-System
```

2. **Run the installer:**
```bash
sudo ./agent/install.sh
```

The installer will:
- Check system requirements
- Install Python dependencies
- Copy agent files to `/usr/local/zerotrust`
- Create configuration in `/etc/zerotrust-agent`
- Install LaunchDaemon for automatic startup
- Start the agent

3. **Verify installation:**
```bash
sudo python3 /usr/local/zerotrust/agent/manage.py status
```

### Manual Installation

If you prefer manual installation:

```bash
# Create directories
sudo mkdir -p /usr/local/zerotrust
sudo mkdir -p /etc/zerotrust-agent
sudo mkdir -p /var/log/zerotrust-agent

# Copy agent files
sudo cp -R agent /usr/local/zerotrust/

# Install dependencies
pip3 install requests urllib3

# Create configuration (see Configuration section)
sudo nano /etc/zerotrust-agent/config.json

# Create LaunchDaemon (see LaunchDaemon section)
sudo nano /Library/LaunchDaemons/com.zerotrust.agent.plist

# Load and start
sudo launchctl load /Library/LaunchDaemons/com.zerotrust.agent.plist
```

## Configuration

### Configuration File

Location: `/etc/zerotrust-agent/config.json`

```json
{
    "api_endpoint": "https://zerotrust.example.com",
    "api_key": "your-api-key-here",
    "device_id": null,
    "device_name": "MacBook-Pro",
    "collection_interval": 300,
    "collectors_enabled": {
        "system_info": true,
        "security_status": true,
        "network_info": true,
        "process_info": true,
        "software_inventory": true
    },
    "log_level": "INFO"
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `api_endpoint` | string | `http://localhost:8000` | Platform API URL |
| `api_key` | string | `null` | API authentication key |
| `device_id` | string | auto-detected | Unique device identifier |
| `device_name` | string | hostname | Human-readable device name |
| `collection_interval` | integer | `300` | Collection interval in seconds |
| `collectors_enabled` | object | all `true` | Enable/disable individual collectors |
| `log_level` | string | `INFO` | Logging level (DEBUG, INFO, WARN, ERROR) |

### Updating Configuration

Using the management CLI:
```bash
# Show current configuration
sudo python3 /usr/local/zerotrust/agent/manage.py config-show

# Update a value
sudo python3 /usr/local/zerotrust/agent/manage.py config-set api_endpoint "https://new-endpoint.com"
sudo python3 /usr/local/zerotrust/agent/manage.py config-set collection_interval 600

# Restart to apply changes
sudo python3 /usr/local/zerotrust/agent/manage.py restart
```

## Management

### Management CLI

The agent includes a comprehensive management tool at `/usr/local/zerotrust/agent/manage.py`.

**Status:**
```bash
sudo python3 /usr/local/zerotrust/agent/manage.py status
```

**Start/Stop/Restart:**
```bash
sudo python3 /usr/local/zerotrust/agent/manage.py start
sudo python3 /usr/local/zerotrust/agent/manage.py stop
sudo python3 /usr/local/zerotrust/agent/manage.py restart
```

**View Logs:**
```bash
# Last 50 lines
sudo python3 /usr/local/zerotrust/agent/manage.py logs

# Last N lines
sudo python3 /usr/local/zerotrust/agent/manage.py logs -n 100

# Follow logs in real-time
sudo python3 /usr/local/zerotrust/agent/manage.py logs -f
```

**View Errors:**
```bash
sudo python3 /usr/local/zerotrust/agent/manage.py errors
```

**Test Collection:**
```bash
# Run single collection cycle
sudo python3 /usr/local/zerotrust/agent/manage.py test
```

**Uninstall:**
```bash
sudo python3 /usr/local/zerotrust/agent/manage.py uninstall
```

### Direct Management (launchctl)

```bash
# Load/start agent
sudo launchctl load /Library/LaunchDaemons/com.zerotrust.agent.plist

# Unload/stop agent
sudo launchctl unload /Library/LaunchDaemons/com.zerotrust.agent.plist

# Check status
sudo launchctl list | grep zerotrust
```

### Log Files

- **Agent Log:** `/var/log/zerotrust-agent/agent.log`
- **Error Log:** `/var/log/zerotrust-agent/agent.error.log`

```bash
# View logs
tail -f /var/log/zerotrust-agent/agent.log

# View errors
tail -f /var/log/zerotrust-agent/agent.error.log
```

## Data Collection

### Collection Frequency

By default, the agent collects telemetry every 5 minutes (300 seconds). This can be adjusted in the configuration:

```bash
sudo python3 /usr/local/zerotrust/agent/manage.py config-set collection_interval 600
```

### What Data is Collected

#### System Information
- Hardware model, serial number, processor, memory
- OS version, build, architecture
- System uptime and boot time
- Munki status (if installed)

#### Security Status
- FileVault encryption status
- System Integrity Protection (SIP)
- Firewall configuration
- Gatekeeper status
- XProtect version
- Secure Boot (Apple Silicon)
- Remote access services (SSH, Screen Sharing)
- Authentication policies

#### Network Information
- Active network interfaces
- IP addresses and MAC addresses
- DNS configuration
- VPN connections
- Proxy settings
- Wi-Fi information

#### Process Information
- Running security tools
- Launch agents and daemons
- System load
- Top CPU-consuming processes
- Kernel extensions

#### Software Inventory
- Installed applications (via Munki or system_profiler)
- Application versions
- Homebrew packages
- Critical software detection

### Privacy & Security

- **No Personal Data** - Agent does not collect user files, documents, or personal information
- **No Credentials** - No passwords or authentication tokens are collected
- **Secure Transmission** - Data is sent over HTTPS with API key authentication
- **Local Only** - All data stays on the device until sent to the configured platform
- **Audit Trail** - All collection activity is logged

## Troubleshooting

### Agent Not Starting

1. **Check LaunchDaemon status:**
```bash
sudo launchctl list | grep zerotrust
```

2. **Check error logs:**
```bash
sudo python3 /usr/local/zerotrust/agent/manage.py errors
```

3. **Test manual run:**
```bash
sudo python3 /usr/local/zerotrust/agent/agent.py --config /etc/zerotrust-agent/config.json --once
```

### Collection Failures

**Symptom:** Agent runs but collections fail

**Check:**
1. API endpoint is reachable
2. API key is correct
3. Agent has necessary permissions

**Test connectivity:**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" https://your-api-endpoint.com/api/v1/health
```

### High Resource Usage

**Symptom:** Agent consuming excessive CPU or memory

**Solutions:**
1. Increase collection interval
2. Disable unnecessary collectors
3. Check for conflicting security software

```bash
# Increase interval to 10 minutes
sudo python3 /usr/local/zerotrust/agent/manage.py config-set collection_interval 600

# Disable process collector (most resource-intensive)
sudo python3 /usr/local/zerotrust/agent/manage.py config-set collectors_enabled.process_info false
sudo python3 /usr/local/zerotrust/agent/manage.py restart
```

### Munki Integration Issues

**Symptom:** Agent not detecting Munki

**Check:**
1. Munki is installed: `which managedsoftwareupdate`
2. ManagedInstallReport exists: `ls -l /Library/Managed\ Installs/ManagedInstallReport.plist`
3. Agent has read permissions

The agent will automatically fall back to direct collection if Munki is unavailable.

## Deployment at Scale

### MDM Deployment

Deploy via MDM (Jamf, Kandji, Intune, etc.):

1. Package the agent as a .pkg installer
2. Pre-configure `config.json` with your settings
3. Deploy via MDM policy
4. Monitor installation via MDM reporting

### Munki Deployment

If you're already using Munki:

1. Create a Munki package (pkginfo)
2. Add to your Munki repository
3. Assign to device manifests
4. Let Munki handle installation and updates

### Configuration Management

For managing configuration at scale:

1. **Use a configuration profile** (Managed Preferences)
2. **Template configuration** with device-specific variables
3. **Centrally manage** via MDM or configuration management tool

## Integration with ZeroTrust Platform

The agent reports to the ZeroTrust platform API:

**Endpoint:** `POST /api/v1/telemetry`

**Authentication:** Bearer token (API key)

**Payload:**
```json
{
    "device_id": "C02XYZ123ABC",
    "agent_version": "0.9.3",
    "collection_time": "2025-10-29T12:00:00Z",
    "hostname": "MacBook-Pro.local",
    "os_type": "Darwin",
    "os_version": "14.1.1",
    "system_info": { ... },
    "security_status": { ... },
    "network_info": { ... },
    "process_info": { ... },
    "software_inventory": { ... }
}
```

## Support

For issues, questions, or feature requests:

- **GitHub:** https://github.com/adrian207/Mac-Compliance-System
- **Email:** adrian207@gmail.com
- **Documentation:** See `docs/` directory

## License

See LICENSE file in the project root.

