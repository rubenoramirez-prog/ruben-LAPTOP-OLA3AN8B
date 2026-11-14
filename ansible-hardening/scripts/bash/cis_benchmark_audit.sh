#!/usr/bin/env bash
# ==============================================================================
# Enterprise CIS Benchmark Audit Script for RHEL 8 / 9
# Author: Ruben Omar Ramírez Gutiérrez
# Standards: L3 Enterprise Infrastructure / Strict Validation / Error Handling
# ==============================================================================

set -euo pipefail

# Color formatting
readonly C_RED='\033[0;31m'
readonly C_GREEN='\033[0;32m'
readonly C_YELLOW='\033[1;33m'
readonly C_BLUE='\033[0;34m'
readonly C_CYAN='\033[0;36m'
readonly C_RESET='\033[0m'

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNED_CHECKS=0

TIMESTAMP="$(date +'%Y%m%d_%H%M%S')"
REPORT_FILE="/var/log/cis_audit_${TIMESTAMP}.log"

# Help menu
show_help() {
  cat << EOF
Usage: $(basename "$0") [OPTIONS]

Options:
  -h, --help        Show this help message and exit
  -o, --output FILE Set custom report output path (Default: /var/log/cis_audit_<timestamp>.log)
  -q, --quiet       Suppress console output, only write report file
  -s, --strict      Treat warnings as failures (Exit code 1 on warnings)

Description:
  Performs an agentless, non-destructive audit of CIS Benchmark controls
  for Red Hat Enterprise Linux 8 & 9.
EOF
}

OUTPUT_FILE="$REPORT_FILE"
QUIET_MODE=0
STRICT_MODE=0

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      show_help
      exit 0
      ;;
    -o|--output)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    -q|--quiet)
      QUIET_MODE=1
      shift
      ;;
    -s|--strict)
      STRICT_MODE=1
      shift
      ;;
    *)
      echo "Unknown option: $1" >&2
      show_help
      exit 2
      ;;
  esac
done

# Logging functions
log() {
  local msg="$1"
  echo -e "$msg" >> "$OUTPUT_FILE"
  if [[ $QUIET_MODE -eq 0 ]]; then
    echo -e "$msg"
  fi
}

report_pass() {
  local id="$1"
  local desc="$2"
  ((TOTAL_CHECKS++))
  ((PASSED_CHECKS++))
  log "  [${C_GREEN}PASS${C_RESET}] ${id} - ${desc}"
}

report_fail() {
  local id="$1"
  local desc="$2"
  local details="${3:-}"
  ((TOTAL_CHECKS++))
  ((FAILED_CHECKS++))
  log "  [${C_RED}FAIL${C_RESET}] ${id} - ${desc}"
  if [[ -n "$details" ]]; then
    log "         ${C_YELLOW}Detail: ${details}${C_RESET}"
  fi
}

report_warn() {
  local id="$1"
  local desc="$2"
  local reason="${3:-}"
  ((TOTAL_CHECKS++))
  ((WARNED_CHECKS++))
  log "  [${C_YELLOW}WARN${C_RESET}] ${id} - ${desc}"
  if [[ -n "$reason" ]]; then
    log "         ${C_YELLOW}Reason: ${reason}${C_RESET}"
  fi
}

mkdir -p "$(dirname "$OUTPUT_FILE")" 2>/dev/null || true
touch "$OUTPUT_FILE" 2>/dev/null || OUTPUT_FILE="/tmp/cis_audit_${TIMESTAMP}.log"

log "${C_CYAN}================================================================${C_RESET}"
log "${C_CYAN}         ENTERPRISE CIS BENCHMARK AUDITOR (RHEL 8/9)            ${C_RESET}"
log "${C_CYAN}================================================================${C_RESET}"
log "Host:        $(hostname -f 2>/dev/null || hostname)"
log "Audit Date:  $(date)"
log "Report File: $OUTPUT_FILE"
log "${C_CYAN}================================================================${C_RESET}\n"

# ------------------------------------------------------------------------------
# SECTION 1: INITIAL SETUP & FILESYSTEM
# ------------------------------------------------------------------------------
log "${C_BLUE}--- SECTION 1: Filesystem & Initial Setup ---${C_RESET}"

# 1.1.1.1 - Cramfs disabled
if modprobe -n -v cramfs 2>&1 | grep -qE "(install /bin/true|install /bin/false)" || ! lsmod | grep -q "^cramfs\s"; then
  report_pass "1.1.1.1" "Ensure mounting of cramfs is disabled"
else
  report_fail "1.1.1.1" "cramfs kernel module is active or loadable"
fi

# 1.1.1.2 - Squashfs / UDF
if modprobe -n -v udf 2>&1 | grep -qE "(install /bin/true|install /bin/false)" || ! lsmod | grep -q "^udf\s"; then
  report_pass "1.1.1.2" "Ensure mounting of udf is disabled"
else
  report_warn "1.1.1.2" "udf module may be loadable"
fi

# 1.1.17 - /dev/shm nodev, nosuid, noexec
if mount | grep -E '\s/dev/shm\s' | grep -q "nodev" && \
   mount | grep -E '\s/dev/shm\s' | grep -q "nosuid" && \
   mount | grep -E '\s/dev/shm\s' | grep -q "noexec"; then
  report_pass "1.1.17" "/dev/shm mounted with nodev, nosuid, noexec"
else
  report_fail "1.1.17" "/dev/shm lacks required mount options (nodev, nosuid, noexec)"
fi

# 1.5.1 - ASLR
if [[ "$(sysctl -n kernel.randomize_va_space 2>/dev/null || echo 0)" == "2" ]]; then
  report_pass "1.5.1" "Address Space Layout Randomization (ASLR) enabled (2)"
else
  report_fail "1.5.1" "ASLR is not fully enabled (sysctl kernel.randomize_va_space != 2)"
fi

# 1.6.1.1 - SELinux Enforcing
if command -v getenforce &>/dev/null; then
  SE_STATE="$(getenforce)"
  if [[ "$SE_STATE" == "Enforcing" ]]; then
    report_pass "1.6.1" "SELinux state is Enforcing"
  else
    report_fail "1.6.1" "SELinux is in $SE_STATE mode (expected Enforcing)"
  fi
else
  report_fail "1.6.1" "SELinux tools not installed"
fi

# ------------------------------------------------------------------------------
# SECTION 2: SERVICES
# ------------------------------------------------------------------------------
log "\n${C_BLUE}--- SECTION 2: Services & Daemon Minimization ---${C_RESET}"

# 2.1.1 - Time synchronization
if systemctl is-active chronyd &>/dev/null || systemctl is-active systemd-timesyncd &>/dev/null; then
  report_pass "2.1.1" "Time synchronization service is active and running"
else
  report_fail "2.1.1" "Neither chronyd nor systemd-timesyncd is active"
fi

# 2.2.x - Insecure services disabled
for srv in telnet-server rsh ypserv tftp-server vsftpd httpd nginx; do
  if systemctl is-active "$srv" &>/dev/null; then
    report_fail "2.2.x" "Unnecessary service '$srv' is running"
  else
    report_pass "2.2.x" "Service '$srv' is not running"
  fi
done

# ------------------------------------------------------------------------------
# SECTION 3: NETWORK CONFIGURATION
# ------------------------------------------------------------------------------
log "\n${C_BLUE}--- SECTION 3: Network Parameters & Firewall ---${C_RESET}"

# 3.2.1 - IP forwarding
if [[ "$(sysctl -n net.ipv4.ip_forward 2>/dev/null || echo 1)" == "0" ]]; then
  report_pass "3.2.1" "IP forwarding is disabled (net.ipv4.ip_forward = 0)"
else
  report_fail "3.2.1" "IP forwarding is enabled"
fi

# 3.2.2 - Packet redirect sending
if [[ "$(sysctl -n net.ipv4.conf.all.send_redirects 2>/dev/null || echo 1)" == "0" ]]; then
  report_pass "3.2.2" "Packet redirect sending is disabled"
else
  report_fail "3.2.2" "net.ipv4.conf.all.send_redirects is enabled"
fi

# 3.2.10 - TCP SYN Cookies
if [[ "$(sysctl -n net.ipv4.tcp_syncookies 2>/dev/null || echo 0)" == "1" ]]; then
  report_pass "3.2.10" "TCP SYN Cookies is enabled"
else
  report_fail "3.2.10" "net.ipv4.tcp_syncookies is disabled"
fi

# 3.4.1 - Firewall active
if systemctl is-active firewalld &>/dev/null || systemctl is-active iptables &>/dev/null || systemctl is-active nftables &>/dev/null; then
  report_pass "3.4.1" "A firewall service (firewalld/iptables/nftables) is active"
else
  report_fail "3.4.1" "No active firewall detected"
fi

# ------------------------------------------------------------------------------
# SECTION 4: LOGGING AND AUDITING
# ------------------------------------------------------------------------------
log "\n${C_BLUE}--- SECTION 4: Logging and Auditing ---${C_RESET}"

# 4.1.1.2 - Auditd active
if systemctl is-active auditd &>/dev/null; then
  report_pass "4.1.1.2" "Auditd service is active"
else
  report_fail "4.1.1.2" "Auditd service is not active"
fi

# 4.1.3 - Audit rules count
if command -v auditctl &>/dev/null; then
  RULES_COUNT="$(auditctl -l 2>/dev/null | grep -cv "No rules" || echo 0)"
  if [[ "$RULES_COUNT" -gt 10 ]]; then
    report_pass "4.1.x" "Auditd rules loaded ($RULES_COUNT active rules)"
  else
    report_fail "4.1.x" "Auditd has insufficient rules loaded (Count: $RULES_COUNT)"
  fi
else
  report_fail "4.1.x" "auditctl command not available"
fi

# 4.2.1 - Rsyslog active
if systemctl is-active rsyslog &>/dev/null || systemctl is-active systemd-journald &>/dev/null; then
  report_pass "4.2.1" "System logging service is active"
else
  report_fail "4.2.1" "No active system logger found"
fi

# ------------------------------------------------------------------------------
# SECTION 5: ACCESS, AUTHENTICATION & SSH
# ------------------------------------------------------------------------------
log "\n${C_BLUE}--- SECTION 5: Access Control & SSH Hardening ---${C_RESET}"

# 5.1.2 - /etc/crontab permissions
if [[ -f /etc/crontab ]]; then
  PERM="$(stat -c %a /etc/crontab 2>/dev/null || echo "")"
  if [[ "$PERM" =~ ^[0-6]00$ ]]; then
    report_pass "5.1.2" "/etc/crontab permissions are secure ($PERM)"
  else
    report_fail "5.1.2" "/etc/crontab permissions too open ($PERM, expected 0600)"
  fi
else
  report_pass "5.1.2" "/etc/crontab does not exist"
fi

# 5.2.8 - SSH PermitRootLogin
if [[ -f /etc/ssh/sshd_config ]]; then
  PRL="$(grep -Ei '^\s*PermitRootLogin' /etc/ssh/sshd_config | tail -1 | awk '{print $2}' || echo 'unset')"
  if [[ "$PRL" =~ ^(no|prohibit-password|without-password)$ ]]; then
    report_pass "5.2.8" "SSHD PermitRootLogin is hardened ($PRL)"
  else
    report_fail "5.2.8" "SSHD PermitRootLogin is '$PRL' (expected 'no')"
  fi
else
  report_warn "5.2.8" "/etc/ssh/sshd_config not present on this host"
fi

# ------------------------------------------------------------------------------
# SUMMARY AND SCORE
# ------------------------------------------------------------------------------
SCORE=0
if [[ $TOTAL_CHECKS -gt 0 ]]; then
  SCORE=$(( (PASSED_CHECKS * 100) / TOTAL_CHECKS ))
fi

log "\n${C_CYAN}================================================================${C_RESET}"
log "${C_CYAN}                     AUDIT RESULTS SUMMARY                      ${C_RESET}"
log "${C_CYAN}================================================================${C_RESET}"
log "Total Controls Evaluated: $TOTAL_CHECKS"
log "Passed:                   ${C_GREEN}${PASSED_CHECKS}${C_RESET}"
log "Failed:                   ${C_RED}${FAILED_CHECKS}${C_RESET}"
log "Warnings:                 ${C_YELLOW}${WARNED_CHECKS}${C_RESET}"
log "Compliance Score:         ${C_CYAN}${SCORE}%${C_RESET}"
log "${C_CYAN}================================================================${C_RESET}"

if [[ $FAILED_CHECKS -gt 0 ]]; then
  exit 1
elif [[ $STRICT_MODE -eq 1 && $WARNED_CHECKS -gt 0 ]]; then
  exit 1
else
  exit 0
fi
