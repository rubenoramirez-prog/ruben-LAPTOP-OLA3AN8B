#!/usr/bin/env bash
# ==============================================================================
# Enterprise System Baseline Snapshot Generator
# Captures comprehensive system state before/after hardening
# Author: Ruben Omar Ramírez Gutiérrez
# ==============================================================================

set -euo pipefail

LABEL="${1:-baseline}"
TIMESTAMP="$(date +'%Y%m%d_%H%M%S')"
BASE_DIR="/var/backups/ansible-hardening/baselines/${LABEL}_${TIMESTAMP}"

echo "Creating baseline snapshot in: ${BASE_DIR}"
mkdir -p "${BASE_DIR}"

# 1. OS & Kernel Information
uname -a > "${BASE_DIR}/uname.txt"
cat /etc/os-release > "${BASE_DIR}/os-release.txt" 2>/dev/null || true

# 2. Running Services
systemctl list-units --type=service --all --no-pager > "${BASE_DIR}/systemd_services.txt" 2>/dev/null || true
systemctl list-unit-files --no-pager > "${BASE_DIR}/unit_files.txt" 2>/dev/null || true

# 3. Listening Network Sockets
if command -v ss &>/dev/null; then
  ss -tulpn > "${BASE_DIR}/listening_sockets.txt" 2>/dev/null || true
elif command -v netstat &>/dev/null; then
  netstat -tulpn > "${BASE_DIR}/listening_sockets.txt" 2>/dev/null || true
fi

# 4. Kernel Parameters (sysctl)
sysctl -a > "${BASE_DIR}/sysctl_all.txt" 2>/dev/null || true

# 5. Loaded Kernel Modules
lsmod > "${BASE_DIR}/loaded_modules.txt" 2>/dev/null || true

# 6. Mounted Filesystems and Mount Options
mount > "${BASE_DIR}/mounts.txt" 2>/dev/null || true
cat /etc/fstab > "${BASE_DIR}/fstab.txt" 2>/dev/null || true

# 7. Security Settings
if command -v getenforce &>/dev/null; then
  getenforce > "${BASE_DIR}/selinux_state.txt" 2>/dev/null || true
fi
if command -v auditctl &>/dev/null; then
  auditctl -l > "${BASE_DIR}/audit_rules.txt" 2>/dev/null || true
fi

# 8. User Accounts & Groups (metadata only, no shadow secrets)
cut -d: -f1,3,4,6,7 /etc/passwd > "${BASE_DIR}/passwd_metadata.txt" 2>/dev/null || true

echo "Baseline snapshot successfully saved to ${BASE_DIR}"
