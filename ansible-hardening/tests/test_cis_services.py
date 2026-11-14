"""
Tests for cis-services role.
"""
import os
import yaml

def test_services_defaults(project_root):
    defaults_file = os.path.join(project_root, "roles/cis-services/defaults/main.yml")
    assert os.path.isfile(defaults_file)
    with open(defaults_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["time_sync_service"] == "chronyd"
    assert "telnet-server" in data["disable_services"]
    assert "vsftpd" in data["disable_services"]
    assert "httpd" in data["disable_services"]
    assert "cups" in data["disable_services"]
    assert "sshd" in data["essential_services"]

def test_services_tasks_exist(project_root):
    tasks_dir = os.path.join(project_root, "roles/cis-services/tasks")
    assert os.path.isdir(tasks_dir)
    for t in ["main.yml", "configure_time_sync.yml", "disable_services.yml", "remove_clients.yml", "mask_services.yml", "validate.yml"]:
        assert os.path.isfile(os.path.join(tasks_dir, t))
