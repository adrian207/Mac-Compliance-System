"""Initial schema - devices, telemetry, risk, compliance

Revision ID: 20251028_0000
Revises: 
Create Date: 2025-10-28 00:00:00.000000

Author: Adrian Johnson <adrian207@gmail.com>
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251028_0000'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    
    # Create devices table
    op.create_table(
        'devices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('device_id', sa.String(length=255), nullable=False),
        sa.Column('hostname', sa.String(length=255), nullable=False),
        sa.Column('serial_number', sa.String(length=255), nullable=True),
        sa.Column('uuid', sa.String(length=255), nullable=True),
        sa.Column('model', sa.String(length=255), nullable=True),
        sa.Column('os_version', sa.String(length=100), nullable=True),
        sa.Column('os_build', sa.String(length=100), nullable=True),
        sa.Column('cpu_type', sa.String(length=100), nullable=True),
        sa.Column('total_memory_gb', sa.Float(), nullable=True),
        sa.Column('total_disk_gb', sa.Float(), nullable=True),
        sa.Column('primary_user', sa.String(length=255), nullable=True),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.Column('department', sa.String(length=255), nullable=True),
        sa.Column('enrollment_status', sa.String(length=50), nullable=True),
        sa.Column('mdm_enrolled', sa.Boolean(), nullable=True),
        sa.Column('last_check_in', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('device_id'),
        sa.UniqueConstraint('serial_number'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_devices_device_id'), 'devices', ['device_id'], unique=False)
    
    # Create telemetry_snapshots table
    op.create_table(
        'telemetry_snapshots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('snapshot_time', sa.DateTime(), nullable=False),
        sa.Column('uptime_seconds', sa.Integer(), nullable=True),
        sa.Column('cpu_usage_percent', sa.Float(), nullable=True),
        sa.Column('memory_usage_percent', sa.Float(), nullable=True),
        sa.Column('disk_usage_percent', sa.Float(), nullable=True),
        sa.Column('filevault_enabled', sa.Boolean(), nullable=True),
        sa.Column('firewall_enabled', sa.Boolean(), nullable=True),
        sa.Column('gatekeeper_enabled', sa.Boolean(), nullable=True),
        sa.Column('sip_enabled', sa.Boolean(), nullable=True),
        sa.Column('xprotect_version', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('mac_address', sa.String(length=17), nullable=True),
        sa.Column('wifi_ssid', sa.String(length=255), nullable=True),
        sa.Column('vpn_connected', sa.Boolean(), nullable=True),
        sa.Column('screen_lock_enabled', sa.Boolean(), nullable=True),
        sa.Column('password_required', sa.Boolean(), nullable=True),
        sa.Column('touch_id_enabled', sa.Boolean(), nullable=True),
        sa.Column('installed_software_count', sa.Integer(), nullable=True),
        sa.Column('running_processes_count', sa.Integer(), nullable=True),
        sa.Column('active_network_connections', sa.Integer(), nullable=True),
        sa.Column('processes', sa.JSON(), nullable=True),
        sa.Column('network_connections', sa.JSON(), nullable=True),
        sa.Column('installed_applications', sa.JSON(), nullable=True),
        sa.Column('system_extensions', sa.JSON(), nullable=True),
        sa.Column('certificates', sa.JSON(), nullable=True),
        sa.Column('collection_duration_ms', sa.Integer(), nullable=True),
        sa.Column('collection_errors', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_telemetry_snapshots_device_id'), 'telemetry_snapshots', ['device_id'], unique=False)
    op.create_index(op.f('ix_telemetry_snapshots_snapshot_time'), 'telemetry_snapshots', ['snapshot_time'], unique=False)
    
    # Create risk_scores table
    op.create_table(
        'risk_scores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('assessment_time', sa.DateTime(), nullable=False),
        sa.Column('total_risk_score', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('security_posture_score', sa.Float(), nullable=True),
        sa.Column('compliance_score', sa.Float(), nullable=True),
        sa.Column('behavioral_score', sa.Float(), nullable=True),
        sa.Column('threat_indicator_score', sa.Float(), nullable=True),
        sa.Column('security_posture_weight', sa.Float(), nullable=True),
        sa.Column('compliance_weight', sa.Float(), nullable=True),
        sa.Column('behavioral_weight', sa.Float(), nullable=True),
        sa.Column('threat_indicator_weight', sa.Float(), nullable=True),
        sa.Column('risk_factors', sa.JSON(), nullable=True),
        sa.Column('high_risk_factors', sa.JSON(), nullable=True),
        sa.Column('recommendations', sa.JSON(), nullable=True),
        sa.Column('previous_score', sa.Float(), nullable=True),
        sa.Column('score_change', sa.Float(), nullable=True),
        sa.Column('score_trend', sa.String(length=20), nullable=True),
        sa.Column('assessment_version', sa.String(length=50), nullable=True),
        sa.Column('calculation_time_ms', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_scores_assessment_time'), 'risk_scores', ['assessment_time'], unique=False)
    op.create_index(op.f('ix_risk_scores_device_id'), 'risk_scores', ['device_id'], unique=False)
    op.create_index(op.f('ix_risk_scores_risk_level'), 'risk_scores', ['risk_level'], unique=False)
    op.create_index(op.f('ix_risk_scores_total_risk_score'), 'risk_scores', ['total_risk_score'], unique=False)
    
    # Create risk_factors table
    op.create_table(
        'risk_factors',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('risk_score_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('subcategory', sa.String(length=100), nullable=True),
        sa.Column('factor_name', sa.String(length=255), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('impact_score', sa.Float(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('current_value', sa.String(length=255), nullable=True),
        sa.Column('expected_value', sa.String(length=255), nullable=True),
        sa.Column('remediation_available', sa.String(length=50), nullable=True),
        sa.Column('remediation_priority', sa.String(length=20), nullable=True),
        sa.Column('remediation_effort', sa.String(length=20), nullable=True),
        sa.Column('detection_time', sa.DateTime(), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('occurrence_count', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['risk_score_id'], ['risk_scores.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_factors_category'), 'risk_factors', ['category'], unique=False)
    op.create_index(op.f('ix_risk_factors_risk_score_id'), 'risk_factors', ['risk_score_id'], unique=False)
    
    # Create risk_trends table
    op.create_table(
        'risk_trends',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('trend_date', sa.DateTime(), nullable=False),
        sa.Column('min_risk_score', sa.Float(), nullable=True),
        sa.Column('max_risk_score', sa.Float(), nullable=True),
        sa.Column('avg_risk_score', sa.Float(), nullable=True),
        sa.Column('median_risk_score', sa.Float(), nullable=True),
        sa.Column('time_in_low_risk', sa.Integer(), nullable=True),
        sa.Column('time_in_medium_risk', sa.Integer(), nullable=True),
        sa.Column('time_in_high_risk', sa.Integer(), nullable=True),
        sa.Column('time_in_critical_risk', sa.Integer(), nullable=True),
        sa.Column('risk_level_changes', sa.Integer(), nullable=True),
        sa.Column('high_risk_incidents', sa.Integer(), nullable=True),
        sa.Column('top_risk_factors', sa.JSON(), nullable=True),
        sa.Column('resolved_factors', sa.JSON(), nullable=True),
        sa.Column('new_factors', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_trends_device_id'), 'risk_trends', ['device_id'], unique=False)
    op.create_index(op.f('ix_risk_trends_trend_date'), 'risk_trends', ['trend_date'], unique=False)
    
    # Create security_events table
    op.create_table(
        'security_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('event_time', sa.DateTime(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=255), nullable=True),
        sa.Column('detection_method', sa.String(length=255), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('risk_score_impact', sa.Integer(), nullable=True),
        sa.Column('affected_resources', sa.JSON(), nullable=True),
        sa.Column('response_status', sa.String(length=50), nullable=True),
        sa.Column('automated_actions', sa.JSON(), nullable=True),
        sa.Column('raw_data', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_security_events_device_id'), 'security_events', ['device_id'], unique=False)
    op.create_index(op.f('ix_security_events_event_time'), 'security_events', ['event_time'], unique=False)
    op.create_index(op.f('ix_security_events_event_type'), 'security_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_security_events_severity'), 'security_events', ['severity'], unique=False)
    
    # Create compliance_results table
    op.create_table(
        'compliance_results',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('check_time', sa.DateTime(), nullable=False),
        sa.Column('is_compliant', sa.Boolean(), nullable=False),
        sa.Column('compliance_score', sa.Float(), nullable=True),
        sa.Column('total_checks', sa.Integer(), nullable=True),
        sa.Column('passed_checks', sa.Integer(), nullable=True),
        sa.Column('failed_checks', sa.Integer(), nullable=True),
        sa.Column('check_results', sa.JSON(), nullable=True),
        sa.Column('violations', sa.JSON(), nullable=True),
        sa.Column('policy_version', sa.String(length=50), nullable=True),
        sa.Column('policy_name', sa.String(length=255), nullable=True),
        sa.Column('remediation_required', sa.Boolean(), nullable=True),
        sa.Column('remediation_actions', sa.JSON(), nullable=True),
        sa.Column('remediation_status', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_compliance_results_check_time'), 'compliance_results', ['check_time'], unique=False)
    op.create_index(op.f('ix_compliance_results_device_id'), 'compliance_results', ['device_id'], unique=False)
    op.create_index(op.f('ix_compliance_results_is_compliant'), 'compliance_results', ['is_compliant'], unique=False)
    
    # Create network_connections table
    op.create_table(
        'network_connections',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('connection_time', sa.DateTime(), nullable=False),
        sa.Column('process_name', sa.String(length=255), nullable=True),
        sa.Column('process_id', sa.Integer(), nullable=True),
        sa.Column('local_address', sa.String(length=45), nullable=True),
        sa.Column('local_port', sa.Integer(), nullable=True),
        sa.Column('remote_address', sa.String(length=45), nullable=True),
        sa.Column('remote_port', sa.Integer(), nullable=True),
        sa.Column('protocol', sa.String(length=10), nullable=True),
        sa.Column('state', sa.String(length=50), nullable=True),
        sa.Column('bytes_sent', sa.Integer(), nullable=True),
        sa.Column('bytes_received', sa.Integer(), nullable=True),
        sa.Column('is_suspicious', sa.Boolean(), nullable=True),
        sa.Column('risk_indicators', sa.JSON(), nullable=True),
        sa.Column('threat_intel_match', sa.Boolean(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('first_seen', sa.DateTime(), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_network_connections_connection_time'), 'network_connections', ['connection_time'], unique=False)
    op.create_index(op.f('ix_network_connections_device_id'), 'network_connections', ['device_id'], unique=False)
    op.create_index(op.f('ix_network_connections_is_suspicious'), 'network_connections', ['is_suspicious'], unique=False)
    op.create_index(op.f('ix_network_connections_remote_address'), 'network_connections', ['remote_address'], unique=False)
    
    # Create software_inventory table
    op.create_table(
        'software_inventory',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('scan_time', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('version', sa.String(length=100), nullable=True),
        sa.Column('vendor', sa.String(length=255), nullable=True),
        sa.Column('install_date', sa.DateTime(), nullable=True),
        sa.Column('install_path', sa.String(length=500), nullable=True),
        sa.Column('is_signed', sa.Boolean(), nullable=True),
        sa.Column('is_notarized', sa.Boolean(), nullable=True),
        sa.Column('signing_certificate', sa.String(length=255), nullable=True),
        sa.Column('has_vulnerabilities', sa.Boolean(), nullable=True),
        sa.Column('vulnerability_count', sa.Integer(), nullable=True),
        sa.Column('vulnerability_details', sa.JSON(), nullable=True),
        sa.Column('is_approved', sa.Boolean(), nullable=True),
        sa.Column('is_blocked', sa.Boolean(), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('bundle_identifier', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_software_inventory_device_id'), 'software_inventory', ['device_id'], unique=False)
    op.create_index(op.f('ix_software_inventory_has_vulnerabilities'), 'software_inventory', ['has_vulnerabilities'], unique=False)
    op.create_index(op.f('ix_software_inventory_name'), 'software_inventory', ['name'], unique=False)
    op.create_index(op.f('ix_software_inventory_scan_time'), 'software_inventory', ['scan_time'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_index(op.f('ix_software_inventory_scan_time'), table_name='software_inventory')
    op.drop_index(op.f('ix_software_inventory_name'), table_name='software_inventory')
    op.drop_index(op.f('ix_software_inventory_has_vulnerabilities'), table_name='software_inventory')
    op.drop_index(op.f('ix_software_inventory_device_id'), table_name='software_inventory')
    op.drop_table('software_inventory')
    
    op.drop_index(op.f('ix_network_connections_remote_address'), table_name='network_connections')
    op.drop_index(op.f('ix_network_connections_is_suspicious'), table_name='network_connections')
    op.drop_index(op.f('ix_network_connections_device_id'), table_name='network_connections')
    op.drop_index(op.f('ix_network_connections_connection_time'), table_name='network_connections')
    op.drop_table('network_connections')
    
    op.drop_index(op.f('ix_compliance_results_is_compliant'), table_name='compliance_results')
    op.drop_index(op.f('ix_compliance_results_device_id'), table_name='compliance_results')
    op.drop_index(op.f('ix_compliance_results_check_time'), table_name='compliance_results')
    op.drop_table('compliance_results')
    
    op.drop_index(op.f('ix_security_events_severity'), table_name='security_events')
    op.drop_index(op.f('ix_security_events_event_type'), table_name='security_events')
    op.drop_index(op.f('ix_security_events_event_time'), table_name='security_events')
    op.drop_index(op.f('ix_security_events_device_id'), table_name='security_events')
    op.drop_table('security_events')
    
    op.drop_index(op.f('ix_risk_trends_trend_date'), table_name='risk_trends')
    op.drop_index(op.f('ix_risk_trends_device_id'), table_name='risk_trends')
    op.drop_table('risk_trends')
    
    op.drop_index(op.f('ix_risk_factors_risk_score_id'), table_name='risk_factors')
    op.drop_index(op.f('ix_risk_factors_category'), table_name='risk_factors')
    op.drop_table('risk_factors')
    
    op.drop_index(op.f('ix_risk_scores_total_risk_score'), table_name='risk_scores')
    op.drop_index(op.f('ix_risk_scores_risk_level'), table_name='risk_scores')
    op.drop_index(op.f('ix_risk_scores_device_id'), table_name='risk_scores')
    op.drop_index(op.f('ix_risk_scores_assessment_time'), table_name='risk_scores')
    op.drop_table('risk_scores')
    
    op.drop_index(op.f('ix_telemetry_snapshots_snapshot_time'), table_name='telemetry_snapshots')
    op.drop_index(op.f('ix_telemetry_snapshots_device_id'), table_name='telemetry_snapshots')
    op.drop_table('telemetry_snapshots')
    
    op.drop_index(op.f('ix_devices_device_id'), table_name='devices')
    op.drop_table('devices')

