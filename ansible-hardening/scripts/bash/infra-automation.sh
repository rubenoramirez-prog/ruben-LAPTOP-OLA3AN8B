#!/usr/bin/env bash
# =============================================================================
# Infrastructure Automation & Linux Hardening Orchestrator
# =============================================================================
# Author: Ruben Omar Ramírez Gutiérrez (Coach Ruben Ramírez)
# Description: Pre-flight checks, system baseline, Ansible hardening execution,
#              and compliance report generation.
# =============================================================================

set -Eeuo pipefail

# -- Colors & Formatting ------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

LOG_DIR="/var/log/ansible-hardening-reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${LOG_DIR}/automation_${TIMESTAMP}.log"

# -- Helper Functions ---------------------------------------------------------
print_banner() {
    echo -e "${CYAN}${BOLD}"
    echo "╔═════════════════════════════════════════════════════════════════╗"
    echo "║       LINUX SERVER HARDENING & INFRASTRUCTURE AUTOMATION        ║"
    echo "║       CIS Benchmark L1/L2 — Ansible & Bash Orchestrator         ║"
    echo "╚═════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log_info() {
    local msg="[INFO] $(date '+%Y-%m-%d %H:%M:%S') — $1"
    echo -e "${GREEN}${msg}${NC}"
    echo "$msg" >> "${LOG_FILE}" 2>/dev/null || true
}

log_warn() {
    local msg="[WARN] $(date '+%Y-%m-%d %H:%M:%S') — $1"
    echo -e "${YELLOW}${msg}${NC}"
    echo "$msg" >> "${LOG_FILE}" 2>/dev/null || true
}

log_error() {
    local msg="[ERROR] $(date '+%Y-%m-%d %H:%M:%S') — $1"
    echo -e "${RED}${msg}${NC}" >&2
    echo "$msg" >> "${LOG_FILE}" 2>/dev/null || true
}

usage() {
    echo -e "${BOLD}Usage:${NC} $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -i,-c, --inventory PATH    Path to Ansible inventory (default: inventories/development/hosts.yml)"
    echo "  -l, --level LEVEL          Hardening level: level1 or level2 (default: level1)"
    echo "  -d, --dry-run              Run Ansible playbook in check mode (--check --diff)"
    echo "  -b, --baseline             Capture system baseline before hardening"
    echo "  -r, --rollback             Execute emergency rollback playbook"
    echo "  -h, --help                 Display this help message"
    echo ""
    exit 0
}

# -- Default Configuration ----------------------------------------------------
INVENTORY="inventories/development/hosts.yml"
HARDENING_LEVEL="level1"
DRY_RUN=false
CAPTURE_BASELINE=false
DO_ROLLBACK=false

# -- Parse Arguments ----------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--inventory)
            INVENTORY="$2"
            shift 2
            ;;
        -l|--level)
            HARDENING_LEVEL="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -b|--baseline)
            CAPTURE_BASELINE=true
            shift
            ;;
        -r|--rollback)
            DO_ROLLBACK=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            ;;
    esac
done

# -- Initialization -----------------------------------------------------------
mkdir -p "${LOG_DIR}"
print_banner
log_info "Starting infrastructure automation pipeline..."

# -- Pre-flight Checks --------------------------------------------------------
log_info "Running pre-flight validation checks..."

# Check Ansible installation
if ! command -v ansible-playbook &>/dev/null; then
    log_error "Ansible is not installed or not in PATH. Please install ansible."
    exit 1
fi
log_info "Ansible version: $(ansible --version | head -n 1)"

# Check inventory file exists
if [[ ! -f "${INVENTORY}" ]]; then
    log_error "Inventory file not found at: ${INVENTORY}"
    exit 1
fi
log_info "Inventory verified: ${INVENTORY}"

# -- Execution Flow -----------------------------------------------------------

# 1. Rollback Mode
if [[ "${DO_ROLLBACK}" == true ]]; then
    log_warn "Executing emergency rollback playbook..."
    ansible-playbook playbooks/rollback.yml -i "${INVENTORY}"
    log_info "Rollback completed."
    exit 0
fi

# 2. System Baseline Capture
if [[ "${CAPTURE_BASELINE}" == true ]]; then
    log_info "Capturing system baseline..."
    if [[ -f "scripts/bash/system_baseline.sh" ]]; then
        bash scripts/bash/system_baseline.sh
    else
        log_warn "system_baseline.sh not found, skipping."
    fi
fi

# 3. Hardening Playbook Execution
PLAYBOOK="playbooks/site.yml"
if [[ ! -f "${PLAYBOOK}" ]]; then
    log_error "Main playbook not found at: ${PLAYBOOK}"
    exit 1
fi

CMD="ansible-playbook ${PLAYBOOK} -i ${INVENTORY} -e hardening_level=${HARDENING_LEVEL}"

if [[ "${DRY_RUN}" == true ]]; then
    log_info "Running in DRY-RUN mode (--check --diff)..."
    CMD="${CMD} --check --diff"
else
    log_warn "Running LIVE hardening playbook (CIS Benchmark ${HARDENING_LEVEL})..."
fi

log_info "Executing command: ${CMD}"
eval "${CMD}"

EXIT_CODE=$?

if [[ ${EXIT_CODE} -eq 0 ]]; then
    log_info "Infrastructure automation pipeline completed successfully!"

    # 4. Generate Compliance Dashboard if Python generator exists
    if [[ -f "scripts/python/cis_scanner.py" ]]; then
        log_info "Generating compliance report..."
        python3 scripts/python/cis_scanner.py --output "${LOG_DIR}/compliance_summary.json" || true
    fi
else
    log_error "Ansible playbook execution failed with exit code ${EXIT_CODE}."
    exit ${EXIT_CODE}
fi
