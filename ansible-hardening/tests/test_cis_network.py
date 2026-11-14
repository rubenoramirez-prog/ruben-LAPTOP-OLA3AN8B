"""
Tests for cis-network role.
"""
import os
import yaml

def test_network_defaults(project_root):
    defaults_file = os.path.join(project_root, "roles/cis-network/defaults/main.yml")
    assert os.path.isfile(defaults_file)
    with open(defaults_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["network_host_only"]["ipv4_forwarding"] is False
    assert data["network_parameters"]["rp_filter"] is True
    assert "dccp" in data["disable_protocols"]
    assert "sctp" in data["disable_protocols"]
    assert data["firewall_enabled"] is True

def test_network_tasks_exist(project_root):
    tasks_dir = os.path.join(project_root, "roles/cis-network/tasks")
    assert os.path.isdir(tasks_dir)
    for t in ["main.yml", "kernel_network_params.yml", "disable_protocols.yml", "disable_wireless.yml", "configure_firewall.yml", "configure_firewalld.yml", "configure_iptables.yml", "configure_ipv6.yml", "tcp_wrappers.yml", "validate.yml"]:
        assert os.path.isfile(os.path.join(tasks_dir, t))
