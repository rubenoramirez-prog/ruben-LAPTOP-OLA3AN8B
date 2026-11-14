#!/usr/bin/env python3
"""
Enterprise CIS Remediation Helper
Author: Ruben Omar Ramírez Gutiérrez
Maps CIS findings to Ansible tags and remediation actions.
"""

import sys
import argparse

REMEDIATION_MAP = {
    "1.1.1": {
        "title": "Disable Unused Filesystems",
        "role": "cis-filesystem",
        "tags": ["filesystem", "filesystems"],
        "ad_hoc": "ansible-playbook -i inventories/development/hosts.yml playbooks/site.yml --tags filesystems"
    },
    "1.5.1": {
        "title": "Enable ASLR",
        "role": "cis-rhel-base",
        "tags": ["base", "process", "sysctl"],
        "ad_hoc": "ansible-playbook -i inventories/development/hosts.yml playbooks/site.yml --tags process"
    },
    "1.6.1": {
        "title": "SELinux Enforcing",
        "role": "cis-rhel-base",
        "tags": ["base", "selinux"],
        "ad_hoc": "ansible-playbook -i inventories/development/hosts.yml playbooks/site.yml --tags selinux"
    },
    "2.1.1": {
        "title": "Time Synchronization",
        "role": "cis-services",
        "tags": ["services", "time"],
        "ad_hoc": "ansible-playbook -i inventories/development/hosts.yml playbooks/site.yml --tags time"
    },
    "2.2": {
        "title": "Disable Insecure Services",
        "role": "cis-services",
        "tags": ["services"],
        "ad_hoc": "ansible-playbook -i inventories/development/hosts.yml playbooks/site.yml --tags services"
    },
    "3.2": {
        "title": "Network Kernel Parameters",
        "role": "cis-network",
        "tags": ["network", "kernel"],
        "ad_hoc": "ansible-playbook -i inventories/development/hosts.yml playbooks/site.yml --tags kernel"
    },
    "3.4": {
        "title": "Firewall Configuration",
        "role": "cis-network",
        "tags": ["network", "firewall"],
        "ad_hoc": "ansible-playbook -i inventories/development/hosts.yml playbooks/site.yml --tags firewall"
    },
    "4.1": {
        "title": "Auditd Rules & Storage",
        "role": "cis-logging",
        "tags": ["logging", "auditd"],
        "ad_hoc": "ansible-playbook -i inventories/development/hosts.yml playbooks/site.yml --tags auditd"
    },
    "5.2": {
        "title": "SSH Server Hardening",
        "role": "cis-access-control",
        "tags": ["access", "sshd"],
        "ad_hoc": "ansible-playbook -i inventories/development/hosts.yml playbooks/site.yml --tags sshd"
    }
}

def main():
    parser = argparse.ArgumentParser(description="Map CIS control IDs to Ansible remediation actions")
    parser.add_argument("cis_id", nargs="?", default="", help="CIS section or control ID (e.g., 5.2, 1.5.1, 4.1)")
    parser.add_argument("--list", action="store_true", help="List all available remediation mappings")
    args = parser.parse_args()

    if args.list or not args.cis_id:
        print("Available CIS Remediation Mappings:")
        print("--------------------------------------------------------------------------------")
        for cid, info in REMEDIATION_MAP.items():
            print(f"[{cid:6}] {info['title']:30} -> Role: {info['role']:18} (Tags: {','.join(info['tags'])})")
        print("--------------------------------------------------------------------------------")
        return

    matched = False
    for cid, info in REMEDIATION_MAP.items():
        if args.cis_id.startswith(cid) or cid.startswith(args.cis_id):
            matched = True
            print("================================================================================")
            print(f"CIS Control:      {cid} - {info['title']}")
            print(f"Target Role:      {info['role']}")
            print(f"Ansible Tags:     {', '.join(info['tags'])}")
            print(f"Remediation Exec: {info['ad_hoc']}")
            print("================================================================================")

    if not matched:
        print(f"No exact mapping found for CIS ID '{args.cis_id}'. Run with --list to see supported keys.")
        sys.exit(1)

if __name__ == "__main__":
    main()
