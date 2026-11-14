"""
Tests for cis-logging role.
"""
import os
import yaml

def test_logging_defaults(project_root):
    defaults_file = os.path.join(project_root, "roles/cis-logging/defaults/main.yml")
    assert os.path.isfile(defaults_file)
    with open(defaults_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["auditd_enabled"] is True
    assert data["audit_backlog_limit"] == 8192
    assert data["audit_immutable"] is True
    assert data["rsyslog_enabled"] is True
    assert data["rsyslog_file_permissions"] == "0640"

def test_logging_tasks_exist(project_root):
    tasks_dir = os.path.join(project_root, "roles/cis-logging/tasks")
    assert os.path.isdir(tasks_dir)
    for t in ["main.yml", "configure_auditd.yml", "audit_log_storage.yml", "configure_audit_rules.yml", "configure_rsyslog.yml", "configure_journald.yml", "validate.yml"]:
        assert os.path.isfile(os.path.join(tasks_dir, t))
