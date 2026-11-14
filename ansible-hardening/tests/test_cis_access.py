"""
Tests for cis-access-control role.
"""
import os
import yaml

def test_access_defaults(project_root):
    defaults_file = os.path.join(project_root, "roles/cis-access-control/defaults/main.yml")
    assert os.path.isfile(defaults_file)
    with open(defaults_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["sshd_permit_root_login"] == "no"
    assert data["sshd_max_auth_tries"] == 4
    assert data["pam_minlen"] == 14
    assert data["pam_faillock_deny"] == 5
    assert data["pam_faillock_unlock_time"] == 900
    assert "chacha20-poly1305@openssh.com" in data["sshd_ciphers"]
    assert "hmac-sha2-512-etm@openssh.com" in data["sshd_macs"]
    assert "curve25519-sha256" in data["sshd_kex_algorithms"]

def test_access_tasks_exist(project_root):
    tasks_dir = os.path.join(project_root, "roles/cis-access-control/tasks")
    assert os.path.isdir(tasks_dir)
    for t in ["main.yml", "configure_cron.yml", "configure_sshd.yml", "configure_pam.yml", "user_environment.yml", "validate.yml"]:
        assert os.path.isfile(os.path.join(tasks_dir, t))
