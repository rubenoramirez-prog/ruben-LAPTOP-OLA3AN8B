#!/usr/bin/env bash
# ==============================================================================
# Enterprise Linux Multiserver Security Auditor Orchestrator
# Author: Ruben Omar Ramírez Gutiérrez
# Standard: Enterprise L3 Infrastructure / Parallel SSH Execution / Non-Destructive
# ==============================================================================

set -euo pipefail

# Output formatting
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[1;33m'
readonly COLOR_CYAN='\033[0;36m'
readonly COLOR_BOLD='\033[1m'
readonly COLOR_RESET='\033[0m'

# Default Parameters
TARGET_HOSTS=""
SSH_USER="root"
SSH_KEY=""
SSH_PORT="22"
TARGET_MODULES="all"
CLIENT_NAME="Enterprise Multiserver Client"
OUTPUT_DIR="./reports/multiserver_$(date +'%Y%m%d_%H%M%S')"
PARALLEL_JOBS=5

show_help() {
  echo -e "${COLOR_BOLD}Enterprise Linux Multiserver Auditor v2.1.0${COLOR_RESET}"
  echo -e "Author: Ruben Omar Ramírez Gutiérrez (Enterprise Infrastructure L3)"
  echo -e ""
  echo -e "${COLOR_CYAN}USO:${COLOR_RESET}"
  echo -e "  $0 --hosts \"192.168.1.10,192.168.1.11,server.empresa.com\" [OPCIONES]"
  echo -e "  $0 --hosts-file ./servers.txt [OPCIONES]"
  echo -e ""
  echo -e "${COLOR_CYAN}OPCIONES:${COLOR_RESET}"
  echo -e "  -H, --hosts LIST       Lista de servidores separados por coma (IPs o hostnames)"
  echo -e "  -f, --hosts-file FILE  Archivo de texto con un servidor por línea"
  echo -e "  -u, --user USER        Usuario SSH para conexión (Default: root)"
  echo -e "  -i, --identity KEY     Ruta a la llave privada SSH (opcional)"
  echo -e "  -p, --port PORT        Puerto SSH (Default: 22)"
  echo -e "  -m, --modules MODULES  Módulos a ejecutar (Default: all)"
  echo -e "  -c, --client NAME      Nombre del cliente para reportes (Default: 'Enterprise Multiserver Client')"
  echo -e "  -o, --output-dir DIR   Directorio local para consolidar reportes (Default: ./reports/multiserver_<timestamp>)"
  echo -e "  -j, --jobs NUM         Número de trabajos paralelos (Default: 5)"
  echo -e "  --help                 Muestra esta ayuda y termina"
  echo -e ""
}

HOSTS_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -H|--hosts)
      TARGET_HOSTS="$2"
      shift 2
      ;;
    -f|--hosts-file)
      HOSTS_FILE="$2"
      shift 2
      ;;
    -u|--user)
      SSH_USER="$2"
      shift 2
      ;;
    -i|--identity)
      SSH_KEY="$2"
      shift 2
      ;;
    -p|--port)
      SSH_PORT="$2"
      shift 2
      ;;
    -m|--modules)
      TARGET_MODULES="$2"
      shift 2
      ;;
    -c|--client)
      CLIENT_NAME="$2"
      shift 2
      ;;
    -o|--output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    -j|--jobs)
      PARALLEL_JOBS="$2"
      shift 2
      ;;
    --help)
      show_help
      exit 0
      ;;
    *)
      echo -e "${COLOR_RED}Opción desconocida: $1${COLOR_RESET}" >&2
      show_help
      exit 1
      ;;
  esac
done

# Load hosts from file if specified
if [[ -n "$HOSTS_FILE" ]]; then
  if [[ ! -f "$HOSTS_FILE" ]]; then
    echo -e "${COLOR_RED}[ERROR] El archivo de hosts '$HOSTS_FILE' no existe.${COLOR_RESET}" >&2
    exit 1
  fi
  TARGET_HOSTS="$(grep -v '^#' "$HOSTS_FILE" | grep -v '^\s*$' | tr '\n' ',' | sed 's/,$//')"
fi

if [[ -z "$TARGET_HOSTS" ]]; then
  echo -e "${COLOR_RED}[ERROR] Debe especificar servidores mediante --hosts o --hosts-file.${COLOR_RESET}" >&2
  show_help
  exit 1
fi

mkdir -p "$OUTPUT_DIR"
SCRIPT_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/audit_vulnerabilities.sh"

if [[ ! -f "$SCRIPT_SRC" ]]; then
  echo -e "${COLOR_RED}[ERROR] No se encontró el script base 'audit_vulnerabilities.sh' en $SCRIPT_SRC${COLOR_RESET}" >&2
  exit 1
fi

IFS=',' read -ra HOST_ARRAY <<< "$TARGET_HOSTS"
TOTAL_HOSTS=${#HOST_ARRAY[@]}

echo -e "${COLOR_BOLD}${COLOR_CYAN}========================================================================${COLOR_RESET}"
echo -e "${COLOR_BOLD}${COLOR_CYAN}    ORQUESTADOR MULTISERVER - AUDITORÍA DE SEGURIDAD LINUX (L3)         ${COLOR_RESET}"
echo -e "${COLOR_BOLD}${COLOR_CYAN}========================================================================${COLOR_RESET}"
echo -e "Cliente:          ${COLOR_BOLD}$CLIENT_NAME${COLOR_RESET}"
echo -e "Servidores Target: $TOTAL_HOSTS host(s) configurados"
echo -e "Usuario SSH:      $SSH_USER"
echo -e "Módulos:          $TARGET_MODULES"
echo -e "Directorio Salida: $OUTPUT_DIR"
echo -e "Concurrencia:     $PARALLEL_JOBS trabajos paralelos"
echo -e "${COLOR_CYAN}========================================================================${COLOR_RESET}"

audit_single_host() {
  local host="$1"
  local host_dir="$OUTPUT_DIR/$host"
  mkdir -p "$host_dir"

  local ssh_opts="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 -p $SSH_PORT"
  if [[ -n "$SSH_KEY" ]]; then
    ssh_opts+=" -i $SSH_KEY"
  fi

  local remote_target="$SSH_USER@$host"
  local remote_tmp="/var/tmp/audit_run_$$"

  echo -e "[*] [$host] Conectando y preparando entorno remoto..."

  # 1. Create remote workspace
  if ! ssh $ssh_opts "$remote_target" "mkdir -p $remote_tmp"; then
    echo -e "${COLOR_RED}[ERROR] [$host] No se pudo establecer conexión SSH o crear directorio temporal.${COLOR_RESET}"
    echo '{"error": "SSH connection failed"}' > "$host_dir/audit_report.json"
    return 1
  fi

  # 2. Upload auditor script
  if ! scp $ssh_opts "$SCRIPT_SRC" "$remote_target:$remote_tmp/audit_vulnerabilities.sh" &>/dev/null; then
    echo -e "${COLOR_RED}[ERROR] [$host] Falló la transferencia del script de auditoría.${COLOR_RESET}"
    return 1
  fi

  # 3. Execute remote audit
  echo -e "[*] [$host] Ejecutando auditoría de vulnerabilidades..."
  ssh $ssh_opts "$remote_target" "chmod +x $remote_tmp/audit_vulnerabilities.sh && $remote_tmp/audit_vulnerabilities.sh --modules '$TARGET_MODULES' --client '$CLIENT_NAME' --output-dir $remote_tmp/report --quiet" || true

  # 4. Fetch reports back
  echo -e "[*] [$host] Descargando reportes JSON y HTML..."
  scp $ssh_opts "$remote_target:$remote_tmp/report/audit_report.json" "$host_dir/audit_report.json" &>/dev/null || true
  scp $ssh_opts "$remote_target:$remote_tmp/report/client_dashboard.html" "$host_dir/client_dashboard.html" &>/dev/null || true

  # 5. Cleanup remote temp
  ssh $ssh_opts "$remote_target" "rm -rf $remote_tmp" &>/dev/null || true

  if [[ -f "$host_dir/audit_report.json" ]]; then
    echo -e "${COLOR_GREEN}[OK] [$host] Auditoría finalizada con éxito. Reportes guardados en $host_dir${COLOR_RESET}"
  else
    echo -e "${COLOR_YELLOW}[WARN] [$host] La auditoría finalizó pero no se pudieron recuperar los reportes JSON.${COLOR_RESET}"
  fi
}

export -f audit_single_host
export SSH_USER SSH_KEY SSH_PORT TARGET_MODULES CLIENT_NAME OUTPUT_DIR COLOR_RED COLOR_GREEN COLOR_YELLOW COLOR_RESET SCRIPT_SRC

# Run in parallel using xargs or background loop
active_jobs=0
for host in "${HOST_ARRAY[@]}"; do
  host="$(echo "$host" | tr -d '[:space:]')"
  [[ -z "$host" ]] && continue

  audit_single_host "$host" &

  ((active_jobs+=1))
  if [[ $active_jobs -ge $PARALLEL_JOBS ]]; then
    wait -n
    ((active_jobs-=1))
  fi
done

wait

echo -e "\n${COLOR_CYAN}========================================================================${COLOR_RESET}"
echo -e "${COLOR_BOLD}               AUDITORÍA MULTISERVER FINALIZADA                         ${COLOR_RESET}"
echo -e "${COLOR_CYAN}========================================================================${COLOR_RESET}"
echo -e "Reportes consolidados en: ${COLOR_BOLD}$OUTPUT_DIR${COLOR_RESET}"
echo -e "${COLOR_CYAN}========================================================================${COLOR_RESET}"
