"""
Configuration Management Module

Author: Adrian Johnson <adrian207@gmail.com>

Loads and manages platform configuration from YAML files and environment variables.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseModel):
    """Database configuration settings."""
    type: str = "postgresql"
    host: str = "localhost"
    port: int = 5432
    database: str = "zerotrust_security"
    username: str
    password: str
    pool_size: int = 20
    max_overflow: int = 10
    ssl_mode: str = "require"

    @property
    def connection_string(self) -> str:
        """Generate database connection string."""
        return (
            f"{self.type}://{self.username}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )


class RedisConfig(BaseModel):
    """Redis configuration settings."""
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    ssl: bool = False


class APIConfig(BaseModel):
    """API server configuration settings."""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    reload: bool = False
    access_log: bool = True
    cors_origins: list[str] = Field(default_factory=list)
    api_key_header: str = "X-API-Key"


class IntegrationConfig(BaseModel):
    """Base integration configuration."""
    enabled: bool = True
    api_url: str
    timeout_seconds: int = 30
    retry_attempts: int = 3


class KandjiConfig(IntegrationConfig):
    """Kandji MDM integration configuration."""
    api_token: str
    tenant_id: str
    sync_interval_minutes: int = 15
    device_inventory_sync: bool = True
    policy_sync: bool = True
    auto_deploy_policies: bool = True
    auto_remediate_compliance: bool = True


class ZscalerConfig(IntegrationConfig):
    """Zscaler network security integration configuration."""
    cloud: str = "zscalerthree"
    username: str
    password: str
    api_key: str
    ztna_enabled: bool = True
    auto_revoke_tokens: bool = True
    apply_policies_by_risk: bool = True
    high_risk_policy_id: Optional[str] = None
    medium_risk_policy_id: Optional[str] = None
    low_risk_policy_id: Optional[str] = None


class SeraphicConfig(IntegrationConfig):
    """Seraphic browser security integration configuration."""
    api_key: str
    organization_id: str
    auto_apply_policies: bool = True
    isolation_on_high_risk: bool = True


class RiskWeights(BaseModel):
    """Risk assessment scoring weights."""
    security_posture: int = 40
    compliance: int = 30
    behavioral: int = 20
    threat_indicators: int = 10


class RiskThresholds(BaseModel):
    """Risk score thresholds."""
    critical: int = 90
    high: int = 75
    medium: int = 50
    low: int = 25


class RiskAssessmentConfig(BaseModel):
    """Risk assessment configuration."""
    weights: RiskWeights = Field(default_factory=RiskWeights)
    thresholds: RiskThresholds = Field(default_factory=RiskThresholds)
    continuous_assessment: bool = True
    assessment_interval_minutes: int = 5


class WorkflowAction(BaseModel):
    """Workflow action configuration."""
    type: str
    enabled: bool = True
    platform: Optional[str] = None
    hours: Optional[int] = None
    user_notification: Optional[bool] = None


class WorkflowConfig(BaseModel):
    """Individual workflow configuration."""
    enabled: bool = True
    trigger_threshold: Optional[int] = None
    trigger_violations: Optional[int] = None
    trigger: Optional[str] = None
    actions: list[WorkflowAction] = Field(default_factory=list)
    grace_period_hours: Optional[int] = None


class HardeningConfig(BaseModel):
    """Mac OS hardening policy configuration."""
    minimum_os_version: str = "13.0"
    require_latest_patches: bool = True
    patch_age_threshold_days: int = 30
    require_filevault: bool = True
    require_firewall: bool = True
    require_gatekeeper: bool = True
    require_sip: bool = True
    require_secure_boot: bool = True
    require_password: bool = True
    min_password_length: int = 12
    require_complex_password: bool = True
    max_password_age_days: int = 90
    require_screen_lock: bool = True
    screen_lock_timeout_minutes: int = 10


class Config(BaseSettings):
    """Main configuration class."""
    
    # Platform settings
    platform_name: str = "Mac OS Zero Trust Security Platform"
    platform_version: str = "1.0.0"
    environment: str = "production"
    log_level: str = "INFO"
    timezone: str = "UTC"
    
    # Component configurations
    database: Optional[DatabaseConfig] = None
    redis: Optional[RedisConfig] = None
    api: Optional[APIConfig] = None
    kandji: Optional[KandjiConfig] = None
    zscaler: Optional[ZscalerConfig] = None
    seraphic: Optional[SeraphicConfig] = None
    risk_assessment: Optional[RiskAssessmentConfig] = None
    hardening: Optional[HardeningConfig] = None
    
    # Raw config for dynamic access
    _raw_config: Dict[str, Any] = {}
    
    class Config:
        env_prefix = "ZEROTRUST_"
        case_sensitive = False


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from YAML file and environment variables.
    
    Configuration priority:
    1. Environment variables (highest)
    2. config.yaml file
    3. config.example.yaml file (fallback)
    4. Default values (lowest)
    
    Args:
        config_path: Optional path to config file. If None, searches default locations.
    
    Returns:
        Config: Loaded configuration object
    
    Raises:
        FileNotFoundError: If no configuration file is found
        yaml.YAMLError: If configuration file is invalid
    """
    # Determine config file path
    if config_path:
        config_file = Path(config_path)
    else:
        # Search for config in standard locations
        possible_paths = [
            Path("config/config.yaml"),
            Path("config/config.yml"),
            Path("config.yaml"),
            Path("config.yml"),
        ]
        
        config_file = None
        for path in possible_paths:
            if path.exists():
                config_file = path
                break
        
        # Fallback to example config
        if not config_file:
            example_path = Path("config/config.example.yaml")
            if example_path.exists():
                config_file = example_path
            else:
                raise FileNotFoundError(
                    "No configuration file found. Please create config/config.yaml"
                )
    
    # Load YAML configuration
    with open(config_file, 'r') as f:
        yaml_config = yaml.safe_load(f)
    
    # Parse nested configurations
    config_dict = {}
    
    # Platform settings
    if 'platform' in yaml_config:
        platform = yaml_config['platform']
        config_dict['platform_name'] = platform.get('name')
        config_dict['platform_version'] = platform.get('version')
        config_dict['environment'] = platform.get('environment')
        config_dict['log_level'] = platform.get('log_level')
        config_dict['timezone'] = platform.get('timezone')
    
    # Parse component configs
    if 'database' in yaml_config:
        config_dict['database'] = DatabaseConfig(**yaml_config['database'])
    
    if 'redis' in yaml_config:
        config_dict['redis'] = RedisConfig(**yaml_config['redis'])
    
    if 'api' in yaml_config:
        config_dict['api'] = APIConfig(**yaml_config['api'])
    
    if 'kandji' in yaml_config:
        config_dict['kandji'] = KandjiConfig(**yaml_config['kandji'])
    
    if 'zscaler' in yaml_config:
        config_dict['zscaler'] = ZscalerConfig(**yaml_config['zscaler'])
    
    if 'seraphic' in yaml_config:
        config_dict['seraphic'] = SeraphicConfig(**yaml_config['seraphic'])
    
    if 'risk_assessment' in yaml_config:
        risk_config = yaml_config['risk_assessment']
        config_dict['risk_assessment'] = RiskAssessmentConfig(
            weights=RiskWeights(**risk_config.get('weights', {})),
            thresholds=RiskThresholds(**risk_config.get('thresholds', {})),
            continuous_assessment=risk_config.get('continuous_assessment', True),
            assessment_interval_minutes=risk_config.get('assessment_interval_minutes', 5)
        )
    
    if 'hardening' in yaml_config:
        config_dict['hardening'] = HardeningConfig(**yaml_config['hardening'])
    
    # Create config instance
    config = Config(**config_dict)
    config._raw_config = yaml_config
    
    return config


def get_workflow_config(config: Config, workflow_name: str) -> Optional[WorkflowConfig]:
    """
    Get configuration for a specific workflow.
    
    Args:
        config: Main configuration object
        workflow_name: Name of the workflow
    
    Returns:
        WorkflowConfig if found, None otherwise
    """
    workflows = config._raw_config.get('workflows', {})
    workflow_data = workflows.get(workflow_name)
    
    if not workflow_data:
        return None
    
    # Parse actions
    actions = []
    for action_data in workflow_data.get('actions', []):
        actions.append(WorkflowAction(**action_data))
    
    workflow_data['actions'] = actions
    return WorkflowConfig(**workflow_data)


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Returns:
        Config: Global configuration object
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config(config_path: Optional[str] = None) -> Config:
    """
    Reload configuration from file.
    
    Args:
        config_path: Optional path to config file
    
    Returns:
        Config: Newly loaded configuration object
    """
    global _config
    _config = load_config(config_path)
    return _config

