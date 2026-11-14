"""
Tests for cis-rhel-base role.
"""
import os
import yaml

def test_base_defaults(project_root):
    defaults_file = os.path.join(project_root, "roles/cis-rhel-base/defaults/main.yml")
    assert os.path.isfile(defaults_file)
    with open(defaults_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["aslr_enabled"] is True
    assert data["selinux_state"] == "enforcing"
    assert data["core_dumps_restricted"] is True
    assert "AUTHORIZED ACCESS ONLY" in data["banner_content"]

def test_base_tasks_exist(project_root):
    tasks_dir = os.path.join(project_root, "roles/cis-rhel-base/tasks")
    assert os.path.isdir(tasks_dir)

    expected_tasks = [
        "main.yml",
        "configure_boot.yml",
        "process_hardening.yml",
        "configure_selinux.yml",
        "configure_banners.yml",
        "kernel_hardening.yml",
        "validate.yml"
    ]
    for task in expected_tasks:
        assert os.path.isfile(os.path.join(tasks_dir, task)), f"Missing {task}"
