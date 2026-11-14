"""
Tests for cis-filesystem role.
"""
import os
import yaml

def test_filesystem_defaults(project_root):
    defaults_file = os.path.join(project_root, "roles/cis-filesystem/defaults/main.yml")
    assert os.path.isfile(defaults_file)
    with open(defaults_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["backup_configs"] is True
    assert "cramfs" in data["disable_filesystems"]
    assert "freevxfs" in data["disable_filesystems"]
    assert "jffs2" in data["disable_filesystems"]
    assert data["aide_enabled"] is True

def test_filesystem_tasks_structure(project_root):
    tasks_dir = os.path.join(project_root, "roles/cis-filesystem/tasks")
    assert os.path.isdir(tasks_dir)

    expected_files = [
        "main.yml",
        "disable_filesystems.yml",
        "configure_tmp.yml",
        "configure_var.yml",
        "configure_home.yml",
        "configure_dev_shm.yml",
        "sticky_bit.yml",
        "disable_automount.yml",
        "package_manager.yml",
        "configure_aide.yml",
        "validate.yml"
    ]
    for filename in expected_files:
        assert os.path.isfile(os.path.join(tasks_dir, filename)), f"Missing {filename}"
