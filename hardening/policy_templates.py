"""
Security Policy Templates

Author: Adrian Johnson <adrian207@gmail.com>

Predefined security policy templates for Mac OS hardening.
"""

from typing import Dict, Any, List


# CIS Mac OS Benchmark - Level 1 Profile
CIS_LEVEL_1 = {
    "name": "CIS Mac OS Benchmark - Level 1",
    "version": "1.0",
    "description": "Center for Internet Security Mac OS Benchmark Level 1 recommendations",
    "policies": [
        {
            "id": "1.1",
            "name": "Verify all Apple-provided software is current",
            "category": "software_updates",
            "severity": "high",
            "check": "os_version_current",
            "remediation": "automated"
        },
        {
            "id": "1.2",
            "name": "Enable Auto Update",
            "category": "software_updates",
            "severity": "medium",
            "check": "auto_update_enabled",
            "remediation": "automated"
        },
        {
            "id": "2.1.1",
            "name": "Turn on FileVault",
            "category": "encryption",
            "severity": "critical",
            "check": "filevault_enabled",
            "remediation": "automated"
        },
        {
            "id": "2.2.1",
            "name": "Enable Firewall",
            "category": "network_security",
            "severity": "high",
            "check": "firewall_enabled",
            "remediation": "automated"
        },
        {
            "id": "2.2.2",
            "name": "Enable Firewall Stealth Mode",
            "category": "network_security",
            "severity": "medium",
            "check": "firewall_stealth_mode",
            "remediation": "automated"
        },
        {
            "id": "2.3.1",
            "name": "Enable Gatekeeper",
            "category": "application_security",
            "severity": "high",
            "check": "gatekeeper_enabled",
            "remediation": "automated"
        },
        {
            "id": "2.5.1",
            "name": "Disable Bluetooth if not required",
            "category": "network_security",
            "severity": "low",
            "check": "bluetooth_disabled",
            "remediation": "manual"
        },
        {
            "id": "3.1",
            "name": "Enable security auditing",
            "category": "logging",
            "severity": "medium",
            "check": "audit_enabled",
            "remediation": "automated"
        },
        {
            "id": "5.1.1",
            "name": "Secure Home Folders",
            "category": "file_system",
            "severity": "medium",
            "check": "home_folders_secure",
            "remediation": "automated"
        },
        {
            "id": "5.2.1",
            "name": "Configure account lockout threshold",
            "category": "authentication",
            "severity": "high",
            "check": "account_lockout_configured",
            "remediation": "automated"
        },
        {
            "id": "5.3",
            "name": "Require password after sleep or screen saver",
            "category": "authentication",
            "severity": "high",
            "check": "screen_lock_enabled",
            "remediation": "automated"
        }
    ]
}


# NIST 800-53 Baseline
NIST_800_53 = {
    "name": "NIST 800-53 Security Controls for Mac OS",
    "version": "1.0",
    "description": "NIST 800-53 moderate baseline security controls",
    "policies": [
        {
            "id": "AC-2",
            "name": "Account Management",
            "category": "access_control",
            "severity": "high",
            "controls": [
                "disable_guest_account",
                "password_complexity",
                "account_lockout"
            ]
        },
        {
            "id": "AC-7",
            "name": "Unsuccessful Logon Attempts",
            "category": "access_control",
            "severity": "high",
            "check": "failed_login_lockout",
            "remediation": "automated"
        },
        {
            "id": "AC-11",
            "name": "Session Lock",
            "category": "access_control",
            "severity": "medium",
            "check": "screen_lock_enabled",
            "remediation": "automated"
        },
        {
            "id": "AU-2",
            "name": "Audit Events",
            "category": "audit_accountability",
            "severity": "medium",
            "check": "audit_logging_enabled",
            "remediation": "automated"
        },
        {
            "id": "CM-7",
            "name": "Least Functionality",
            "category": "configuration_management",
            "severity": "medium",
            "controls": [
                "disable_unused_services",
                "remove_unnecessary_software"
            ]
        },
        {
            "id": "IA-5",
            "name": "Authenticator Management",
            "category": "identification_authentication",
            "severity": "high",
            "controls": [
                "password_complexity",
                "password_expiration",
                "password_history"
            ]
        },
        {
            "id": "SC-7",
            "name": "Boundary Protection",
            "category": "system_communications",
            "severity": "high",
            "check": "firewall_enabled",
            "remediation": "automated"
        },
        {
            "id": "SC-8",
            "name": "Transmission Confidentiality",
            "category": "system_communications",
            "severity": "high",
            "check": "encryption_in_transit",
            "remediation": "automated"
        },
        {
            "id": "SC-28",
            "name": "Protection of Information at Rest",
            "category": "system_communications",
            "severity": "critical",
            "check": "filevault_enabled",
            "remediation": "automated"
        },
        {
            "id": "SI-2",
            "name": "Flaw Remediation",
            "category": "system_integrity",
            "severity": "high",
            "check": "patches_current",
            "remediation": "automated"
        }
    ]
}


# Zero Trust Baseline
ZERO_TRUST_BASELINE = {
    "name": "Zero Trust Security Baseline",
    "version": "1.0",
    "description": "Baseline security requirements for Zero Trust architecture",
    "policies": [
        {
            "id": "ZT-1",
            "name": "Device Enrollment Required",
            "category": "device_management",
            "severity": "critical",
            "check": "mdm_enrolled",
            "remediation": "manual"
        },
        {
            "id": "ZT-2",
            "name": "Full Disk Encryption",
            "category": "encryption",
            "severity": "critical",
            "check": "filevault_enabled",
            "remediation": "automated"
        },
        {
            "id": "ZT-3",
            "name": "Endpoint Security Agent",
            "category": "endpoint_security",
            "severity": "critical",
            "check": "security_agent_installed",
            "remediation": "automated"
        },
        {
            "id": "ZT-4",
            "name": "Operating System Currency",
            "category": "patching",
            "severity": "high",
            "check": "os_version_current",
            "remediation": "automated"
        },
        {
            "id": "ZT-5",
            "name": "Multi-Factor Authentication",
            "category": "authentication",
            "severity": "high",
            "check": "mfa_enabled",
            "remediation": "manual"
        },
        {
            "id": "ZT-6",
            "name": "Network Firewall Enabled",
            "category": "network_security",
            "severity": "high",
            "check": "firewall_enabled",
            "remediation": "automated"
        },
        {
            "id": "ZT-7",
            "name": "Screen Lock Required",
            "category": "physical_security",
            "severity": "medium",
            "check": "screen_lock_enabled",
            "remediation": "automated"
        },
        {
            "id": "ZT-8",
            "name": "Gatekeeper Protection",
            "category": "application_security",
            "severity": "high",
            "check": "gatekeeper_enabled",
            "remediation": "automated"
        },
        {
            "id": "ZT-9",
            "name": "System Integrity Protection",
            "category": "system_security",
            "severity": "critical",
            "check": "sip_enabled",
            "remediation": "manual"
        },
        {
            "id": "ZT-10",
            "name": "Security Updates Automated",
            "category": "patching",
            "severity": "high",
            "check": "auto_security_updates",
            "remediation": "automated"
        }
    ]
}


# Corporate Standard Baseline
CORPORATE_STANDARD = {
    "name": "Corporate Security Standard",
    "version": "1.0",
    "description": "Standard corporate security requirements for Mac OS devices",
    "policies": [
        {
            "id": "CORP-1",
            "name": "Operating System Requirements",
            "category": "os_requirements",
            "severity": "high",
            "requirements": {
                "minimum_os_version": "13.0",
                "auto_updates": True,
                "patch_lag_max_days": 30
            }
        },
        {
            "id": "CORP-2",
            "name": "Encryption Requirements",
            "category": "encryption",
            "severity": "critical",
            "requirements": {
                "filevault": True,
                "secure_boot": True
            }
        },
        {
            "id": "CORP-3",
            "name": "Network Security",
            "category": "network",
            "severity": "high",
            "requirements": {
                "firewall": True,
                "firewall_stealth_mode": True,
                "vpn_required_on_untrusted_networks": True
            }
        },
        {
            "id": "CORP-4",
            "name": "Authentication Requirements",
            "category": "authentication",
            "severity": "high",
            "requirements": {
                "password_required": True,
                "min_password_length": 12,
                "password_complexity": True,
                "max_password_age_days": 90,
                "screen_lock": True,
                "screen_lock_timeout_minutes": 10
            }
        },
        {
            "id": "CORP-5",
            "name": "Application Security",
            "category": "applications",
            "severity": "medium",
            "requirements": {
                "gatekeeper": True,
                "require_app_signatures": True,
                "block_unsigned_apps": True
            }
        },
        {
            "id": "CORP-6",
            "name": "System Protection",
            "category": "system",
            "severity": "critical",
            "requirements": {
                "sip_enabled": True,
                "disable_guest_account": True,
                "disable_auto_login": True,
                "require_admin_password_system_prefs": True
            }
        },
        {
            "id": "CORP-7",
            "name": "Audit and Logging",
            "category": "logging",
            "severity": "medium",
            "requirements": {
                "audit_logs_enabled": True,
                "firewall_logging": True,
                "log_retention_days": 180
            }
        },
        {
            "id": "CORP-8",
            "name": "Required Software",
            "category": "software",
            "severity": "high",
            "required_software": [
                "Corporate Antivirus",
                "Corporate VPN Client",
                "MDM Agent"
            ]
        }
    ]
}


def get_policy_template(template_name: str) -> Dict[str, Any]:
    """
    Get a policy template by name.
    
    Args:
        template_name: Name of the template (cis_level_1, nist_800_53, zero_trust, corporate)
    
    Returns:
        Policy template dictionary
    """
    templates = {
        "cis_level_1": CIS_LEVEL_1,
        "nist_800_53": NIST_800_53,
        "zero_trust": ZERO_TRUST_BASELINE,
        "corporate": CORPORATE_STANDARD
    }
    
    return templates.get(template_name.lower(), CORPORATE_STANDARD)


def get_available_templates() -> List[str]:
    """
    Get list of available policy templates.
    
    Returns:
        List of template names
    """
    return ["cis_level_1", "nist_800_53", "zero_trust", "corporate"]

