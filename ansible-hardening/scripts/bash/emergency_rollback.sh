#!/usr/bin/env bash
# ==============================================================================
# Enterprise Emergency Rollback Utility
# Restores configurations backed up by Ansible Hardening Framework
# Author: Ruben Omar Ramírez Gutiérrez
# ==============================================================================

set -euo pipefail

BACKUP_ROOT="/var/backups/ansible-hardening"

echo "======================================================"
echo "      ANSIBLE HARDENING EMERGENCY ROLLBACK TOOL       "
echo "======================================================"

if [[ ! -d "$BACKUP_ROOT" ]]; then
  echo "Error: Backup root directory '$BACKUP_ROOT' does not exist." >&2
  exit 1
fi

echo "Available backup files:"
find "$BACKUP_ROOT" -type f | sort | head -50

echo ""
echo "To restore a file, copy the backup version over the target:"
echo "Example:"
echo "  cp /var/backups/ansible-hardening/cis-access-control/sshd_config.<epoch> /etc/ssh/sshd_config"
echo "  systemctl restart sshd"
echo "======================================================"
