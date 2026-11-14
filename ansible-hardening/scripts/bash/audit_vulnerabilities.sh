#!/usr/bin/env bash
# ==============================================================================
# Enterprise Linux Security Vulnerability & Hardening Auditor
# Author: Ruben Omar Ramírez Gutiérrez
# Standard: Enterprise L3 Infrastructure / Non-Destructive / Modular Execution
# Deliverable: Console Report + Structured JSON + Self-Contained HTML Client Dashboard
# ==============================================================================

set -euo pipefail

# Script metadata
readonly SCRIPT_VERSION="2.1.0"
readonly SCRIPT_NAME="audit_vulnerabilities.sh"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Output formatting
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[1;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_CYAN='\033[0;36m'
readonly COLOR_MAGENTA='\033[0;35m'
readonly COLOR_BOLD='\033[1m'
readonly COLOR_RESET='\033[0m'

# Default Parameters
TARGET_MODULES="all"
OUTPUT_DIR="/tmp/security_audit_$(date +'%Y%m%d_%H%M%S')"
CLIENT_NAME="Enterprise Client"
OPERATOR_NAME="$(whoami)@$(hostname -s 2>/dev/null || echo 'localhost')"
ENABLE_HTML=1
ENABLE_JSON=1
QUIET_MODE=0

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
CRITICAL_COUNT=0
HIGH_COUNT=0
MEDIUM_COUNT=0
LOW_COUNT=0

# Temporary file to store JSON items
TMP_ITEMS_FILE="$(mktemp /tmp/audit_items.XXXXXX)"

cleanup() {
  rm -f "$TMP_ITEMS_FILE"
}
trap cleanup EXIT

# ------------------------------------------------------------------------------
# HELP AND CLI PARSING
# ------------------------------------------------------------------------------
show_help() {
  echo -e "${COLOR_BOLD}Enterprise Linux Security Vulnerability Auditor v${SCRIPT_VERSION}${COLOR_RESET}"
  echo -e "Author: Ruben Omar Ramírez Gutiérrez (Enterprise Infrastructure L3)"
  echo -e ""
  echo -e "${COLOR_CYAN}USO:${COLOR_RESET}"
  echo -e "  ./${SCRIPT_NAME} [OPCIONES]"
  echo -e ""
  echo -e "${COLOR_CYAN}OPCIONES:${COLOR_RESET}"
  echo -e "  -m, --modules LIST     Lista de módulos separados por coma a ejecutar:"
  echo -e "                         auth, ssh, network, fs, services, kernel, mac, updates, workload, all (Default: all)"
  echo -e "  -c, --client NAME      Nombre del cliente para el reporte/dashboard (Default: 'Enterprise Client')"
  echo -e "  -o, --output-dir DIR   Directorio donde se guardarán el reporte JSON y HTML"
  echo -e "                         (Default: /tmp/security_audit_<timestamp>)"
  echo -e "  --no-html              Desactivar la generación del dashboard HTML"
  echo -e "  --no-json              Desactivar la exportación en JSON"
  echo -e "  -q, --quiet            Modo silencioso (no muestra la salida detallada en consola)"
  echo -e "  -h, --help             Muestra esta ayuda y termina"
  echo -e ""
  echo -e "${COLOR_CYAN}EJEMPLOS:${COLOR_RESET}"
  echo -e "  # Ejecutar todos los módulos con reporte para cliente específico:"
  echo -e "  ./${SCRIPT_NAME} --client \"Banco Corporativo\" --output-dir ./reporte_cliente"
  echo -e ""
  echo -e "  # Ejecutar únicamente módulos de Red y SSH:"
  echo -e "  ./${SCRIPT_NAME} --modules network,ssh --output-dir /tmp/auditoria_red"
  echo -e ""
}

while [[ $# -gt 0 ]]; do
  case "$1" in
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
    --no-html)
      ENABLE_HTML=0
      shift
      ;;
    --no-json)
      ENABLE_JSON=0
      shift
      ;;
    -q|--quiet)
      QUIET_MODE=1
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo -e "${COLOR_RED}Opción desconocida: $1${COLOR_RESET}" >&2
      show_help
      exit 2
      ;;
  esac
done

# Validate module request
is_module_enabled() {
  local mod="$1"
  if [[ "$TARGET_MODULES" == "all" ]]; then
    return 0
  fi
  if echo ",$TARGET_MODULES," | grep -qi ",$mod,"; then
    return 0
  fi
  return 1
}

# ------------------------------------------------------------------------------
# RECORD CHECK FUNCTION
# ------------------------------------------------------------------------------
record_check() {
  local id="$1"
  local module="$2"
  local title="$3"
  local severity="$4"   # CRITICAL, HIGH, MEDIUM, LOW, INFO
  local status="$5"     # PASS o FAIL
  local impact="$6"
  local remediation="$7"
  local evidence="$8"

  ((TOTAL_CHECKS+=1))

  if [[ "$status" == "PASS" ]]; then
    ((PASSED_CHECKS+=1))
    if [[ $QUIET_MODE -eq 0 ]]; then
      echo -e "  [${COLOR_GREEN}PASS${COLOR_RESET}] [${severity}] ${title}"
    fi
  else
    ((FAILED_CHECKS+=1))
    case "$severity" in
      CRITICAL) ((CRITICAL_COUNT+=1)) ;;
      HIGH)     ((HIGH_COUNT+=1)) ;;
      MEDIUM)   ((MEDIUM_COUNT+=1)) ;;
      LOW)      ((LOW_COUNT+=1)) ;;
    esac
    if [[ $QUIET_MODE -eq 0 ]]; then
      echo -e "  [${COLOR_RED}FAIL${COLOR_RESET}] [${COLOR_BOLD}${severity}${COLOR_RESET}] ${title}"
      echo -e "         ${COLOR_YELLOW}Evidencia:${COLOR_RESET} ${evidence}"
    fi
  fi

  # Escape JSON special chars
  local esc_title="${title//\"/\\\"}"
  local esc_impact="${impact//\"/\\\"}"
  local esc_remediation="${remediation//\"/\\\"}"
  local esc_evidence="${evidence//\"/\\\"}"
  esc_evidence="${esc_evidence//$'\n'/\\n}"

  cat << EOF >> "$TMP_ITEMS_FILE"
  {
    "id": "$id",
    "module": "$module",
    "title": "$esc_title",
    "severity": "$severity",
    "status": "$status",
    "impact": "$esc_impact",
    "remediation": "$esc_remediation",
    "evidence": "$esc_evidence"
  },
EOF
}

# ------------------------------------------------------------------------------
# AUDIT MODULES
# ------------------------------------------------------------------------------

# MODULE 1: AUTHENTICATION & PRIVILEGED ACCOUNTS
run_module_auth() {
  echo -e "\n${COLOR_CYAN}--- [MODULO 1] Identidad, Accesos y Cuentas Privilegiadas ---${COLOR_RESET}"

  # 1.1 Cuentas con UID 0 duplicadas (Backdoors)
  local uid0_accounts=""
  if [[ -f /etc/passwd ]]; then
    uid0_accounts="$(awk -F: '($3 == 0) {print $1}' /etc/passwd 2>/dev/null | grep -v '^root$' || true)"
  fi
  if [[ -z "$uid0_accounts" ]]; then
    record_check "AUTH-01" "auth" "Sin cuentas no autorizadas con UID 0 (root)" "CRITICAL" "PASS" \
      "Cuentas secundarias con UID 0 otorgan control absoluto sin trazabilidad." \
      "Eliminar o revocar UID 0 a usuarios no legítimos." "Solo root posee UID 0"
  else
    record_check "AUTH-01" "auth" "Cuentas no autorizadas con UID 0 detectadas" "CRITICAL" "FAIL" \
      "Usuarios no autorizados tienen privilegios directos de superusuario." \
      "Modificar el UID en /etc/passwd o remover la cuenta no autorizada." "Cuentas con UID 0: $uid0_accounts"
  fi

  # 1.2 Cuentas con contraseña vacía en /etc/shadow
  if [[ -r /etc/shadow ]]; then
    local empty_pass
    empty_pass="$(awk -F: '($2 == "") {print $1}' /etc/shadow || true)"
    if [[ -z "$empty_pass" ]]; then
      record_check "AUTH-02" "auth" "No existen cuentas con contraseña en blanco" "CRITICAL" "PASS" \
        "Cuentas sin contraseña permiten login sin autenticación." \
        "Asignar password o bloquear con 'passwd -l <user>'." "Todas las cuentas poseen hash o están bloqueadas"
    else
      record_check "AUTH-02" "auth" "Cuentas con contraseña vacía detectadas" "CRITICAL" "FAIL" \
        "Cualquier atacante puede iniciar sesión en la cuenta sin credenciales." \
        "Bloquear cuentas con contraseña vacía inmediatamente: passwd -l <user>" "Cuentas vacías: $empty_pass"
    fi
  else
    record_check "AUTH-02" "auth" "Lectura de /etc/shadow restringida (Ejecute con privilegios)" "MEDIUM" "PASS" \
      "No se pudo auditar /etc/shadow." "Ejecutar con sudo/root." "Sin acceso de lectura"
  fi

  # 1.3 Permisos de sudo sin contraseña (NOPASSWD)
  if [[ -d /etc/sudoers.d || -f /etc/sudoers ]]; then
    local nopasswd_entries
    nopasswd_entries="$(grep -r -E '^\s*[^#].*NOPASSWD' /etc/sudoers /etc/sudoers.d/ 2>/dev/null | grep -v 'NOPASSWD: ALL' || true)"
    local nopasswd_all
    nopasswd_all="$(grep -r -E '^\s*[^#].*NOPASSWD:\s*ALL' /etc/sudoers /etc/sudoers.d/ 2>/dev/null || true)"

    if [[ -n "$nopasswd_all" ]]; then
      record_check "AUTH-03" "auth" "Reglas de Sudo NOPASSWD TOTAL activas" "HIGH" "FAIL" \
        "Permite elevación total a root sin ingresar clave en caso de compromiso de sesión." \
        "Requerir contraseña obligatoria en /etc/sudoers para comandos administrativos." "Reglas: $nopasswd_all"
    elif [[ -n "$nopasswd_entries" ]]; then
      record_check "AUTH-03" "auth" "Reglas de Sudo NOPASSWD específicas detectadas" "MEDIUM" "FAIL" \
        "Comandos específicos se ejecutan sin password." \
        "Auditar y limitar estrictamente comandos en NOPASSWD." "Reglas: $nopasswd_entries"
    else
      record_check "AUTH-03" "auth" "Autenticación obligatoria requerida para sudo" "HIGH" "PASS" \
        "Protege la elevación de privilegios." "Mantener requerimiento de contraseña en sudo." "Sin reglas permisivas NOPASSWD"
    fi
  fi

  # 1.4 Permisos críticos en /etc/shadow y /etc/passwd
  if [[ -f /etc/shadow ]]; then
    local shadow_perm
    shadow_perm="$(stat -c %a /etc/shadow 2>/dev/null || echo '')"
    if [[ "$shadow_perm" =~ ^(000|400|600|040|060)$ ]]; then
      record_check "AUTH-04" "auth" "Permisos restrictivos en /etc/shadow ($shadow_perm)" "HIGH" "PASS" \
        "Evita extracción de hashes de contraseñas por usuarios locales." \
        "Mantener permisos en 0600 o 0000." "Permisos: $shadow_perm"
    else
      record_check "AUTH-04" "auth" "Permisos inseguros en /etc/shadow ($shadow_perm)" "HIGH" "FAIL" \
        "Hashes de contraseñas accesibles para cracking offline." \
        "Ejecutar: chmod 0600 /etc/shadow && chown root:root /etc/shadow" "Permisos actuales: $shadow_perm (esperado 0600)"
    fi
  else
    record_check "AUTH-04" "auth" "Archivo /etc/shadow no presente en este entorno" "LOW" "PASS" \
      "Información no aplicable." "N/A" "No presente"
  fi
}

# MODULE 2: SSH HARDENING & REMOTE ACCESS
run_module_ssh() {
  echo -e "\n${COLOR_CYAN}--- [MODULO 2] Acceso Remoto y Hardening de SSH ---${COLOR_RESET}"
  local sshd_conf="/etc/ssh/sshd_config"

  if [[ ! -f "$sshd_conf" ]]; then
    record_check "SSH-00" "ssh" "Servidor OpenSSH no encontrado en /etc/ssh" "LOW" "PASS" \
      "No aplica si el servidor no ejecuta SSH." "N/A" "Archivo no presente"
    return
  fi

  # 2.1 PermitRootLogin
  local prl
  prl="$(grep -Ei '^\s*PermitRootLogin' "$sshd_conf" | tail -1 | awk '{print $2}' || echo 'prohibit-password')"
  if [[ "$prl" == "no" ]]; then
    record_check "SSH-01" "ssh" "Login directo de root por SSH deshabilitado (PermitRootLogin no)" "HIGH" "PASS" \
      "Fuerza a los administradores a ingresar con usuario nominal y escalar." \
      "Mantener 'PermitRootLogin no'." "PermitRootLogin=$prl"
  elif [[ "$prl" =~ ^(prohibit-password|without-password)$ ]]; then
    record_check "SSH-01" "ssh" "Root login solo por llave SSH (PermitRootLogin $prl)" "MEDIUM" "PASS" \
      "Evita ataques de fuerza bruta de contraseña en root." \
      "Recomendado migrar a 'PermitRootLogin no' para trazabilidad de usuario." "PermitRootLogin=$prl"
  else
    record_check "SSH-01" "ssh" "Login directo de root por contraseña habilitado" "CRITICAL" "FAIL" \
      "Root es blanco directo de ataques de fuerza bruta continuos por SSH." \
      "Establecer 'PermitRootLogin no' en $sshd_conf y reiniciar sshd." "PermitRootLogin=$prl"
  fi

  # 2.2 PasswordAuthentication
  local pass_auth
  pass_auth="$(grep -Ei '^\s*PasswordAuthentication' "$sshd_conf" | tail -1 | awk '{print $2}' || echo 'yes')"
  if [[ "$pass_auth" == "no" ]]; then
    record_check "SSH-02" "ssh" "Autenticación SSH restringida solo a llaves públicas" "HIGH" "PASS" \
      "Inmuniza el servicio ante ataques de diccionario o fuerza bruta." \
      "Mantener PasswordAuthentication no." "PasswordAuthentication=no"
  else
    record_check "SSH-02" "ssh" "Autenticación SSH por contraseña permitida" "MEDIUM" "FAIL" \
      "Permite vectores de fuerza bruta y contraseñas débiles." \
      "Distribuir llaves públicas y configurar 'PasswordAuthentication no'." "PasswordAuthentication=$pass_auth"
  fi

  # 2.3 MaxAuthTries
  local max_tries
  max_tries="$(grep -Ei '^\s*MaxAuthTries' "$sshd_conf" | tail -1 | awk '{print $2}' || echo '6')"
  if [[ "$max_tries" -le 4 ]]; then
    record_check "SSH-03" "ssh" "Límite estricto de intentos SSH (MaxAuthTries <= 4)" "MEDIUM" "PASS" \
      "Dificulta intentos iterativos de adivinación de clave." \
      "Mantener MaxAuthTries <= 4." "MaxAuthTries=$max_tries"
  else
    record_check "SSH-03" "ssh" "Intentos de autenticación SSH permisivos (MaxAuthTries > 4)" "LOW" "FAIL" \
      "Permite mayor ventana para ataques de fuerza bruta." \
      "Definir 'MaxAuthTries 4' en $sshd_conf." "MaxAuthTries=$max_tries"
  fi

  # 2.4 X11Forwarding
  local x11
  x11="$(grep -Ei '^\s*X11Forwarding' "$sshd_conf" | tail -1 | awk '{print $2}' || echo 'no')"
  if [[ "$x11" == "no" ]]; then
    record_check "SSH-04" "ssh" "Reenvío X11 deshabilitado (X11Forwarding no)" "LOW" "PASS" \
      "Reduce la superficie de ataque de captura de teclas o ventanas X." \
      "Mantener X11Forwarding no." "X11Forwarding=no"
  else
    record_check "SSH-04" "ssh" "Reenvío X11 habilitado en servidor SSH" "LOW" "FAIL" \
      "Posible intercepción de pulsaciones o pantalla si la sesión se compromete." \
      "Establecer 'X11Forwarding no' en servidores sin GUI." "X11Forwarding=$x11"
  fi
}

# MODULE 3: NETWORK SURFACE & FIREWALL
run_module_network() {
  echo -e "\n${COLOR_CYAN}--- [MODULO 3] Superficie de Red, Sockets y Firewall ---${COLOR_RESET}"

  # 3.1 Firewall Activo
  local fw_active=0
  local fw_name="Ninguno"
  if systemctl is-active firewalld &>/dev/null; then
    fw_active=1; fw_name="firewalld"
  elif systemctl is-active iptables &>/dev/null; then
    fw_active=1; fw_name="iptables"
  elif systemctl is-active nftables &>/dev/null; then
    fw_active=1; fw_name="nftables"
  elif command -v ufw &>/dev/null && ufw status | grep -q "active"; then
    fw_active=1; fw_name="ufw"
  fi

  if [[ $fw_active -eq 1 ]]; then
    record_check "NET-01" "network" "Firewall perimetral local activo ($fw_name)" "HIGH" "PASS" \
      "Filtra conexiones entrantes no deseadas." \
      "Mantener el servicio de firewall habilitado y con política default drop." "Firewall activo: $fw_name"
  else
    record_check "NET-01" "network" "Sin servicio de Firewall local activo" "CRITICAL" "FAIL" \
      "Todos los puertos abiertos en el host quedan expuestos directamente a la red." \
      "Habilitar e iniciar firewalld/iptables inmediatamente: systemctl enable --now firewalld" "No se detectó firewall activo"
  fi

  # 3.2 IP Forwarding
  local ip_fwd
  ip_fwd="$(sysctl -n net.ipv4.ip_forward 2>/dev/null || echo 0)"
  if [[ "$ip_fwd" == "0" ]]; then
    record_check "NET-02" "network" "Reenvío de paquetes IP deshabilitado (ip_forward=0)" "HIGH" "PASS" \
      "Previene que el servidor actúe como router o puente no autorizado." \
      "Mantener net.ipv4.ip_forward = 0." "net.ipv4.ip_forward=0"
  else
    record_check "NET-02" "network" "Reenvío de paquetes IP habilitado (ip_forward=1)" "HIGH" "FAIL" \
      "El host puede enrutar tráfico malicioso entre diferentes subredes." \
      "Si el nodo no es router o nodo K8s/Docker, configurar: sysctl -w net.ipv4.ip_forward=0" "net.ipv4.ip_forward=1"
  fi

  # 3.3 TCP SYN Cookies
  local syn_cookies
  syn_cookies="$(sysctl -n net.ipv4.tcp_syncookies 2>/dev/null || echo 0)"
  if [[ "$syn_cookies" == "1" ]]; then
    record_check "NET-03" "network" "Protección TCP SYN Cookies habilitada" "MEDIUM" "PASS" \
      "Mitiga ataques de denegación de servicio SYN flood." \
      "Mantener net.ipv4.tcp_syncookies = 1." "net.ipv4.tcp_syncookies=1"
  else
    record_check "NET-03" "network" "Protección TCP SYN Cookies deshabilitada" "MEDIUM" "FAIL" \
      "Vulnerable a agotamiento de tabla de conexiones bajo SYN Flood." \
      "Configurar: sysctl -w net.ipv4.tcp_syncookies=1" "net.ipv4.tcp_syncookies=0"
  fi

  # 3.4 Puertos abiertos en todas las interfaces (0.0.0.0)
  if command -v ss &>/dev/null; then
    local open_ports
    open_ports="$(ss -tulpn 2>/dev/null | grep -E 'LISTEN' | grep -E '0\.0\.0\.0:\*|0\.0\.0\.0:[0-9]+|\*:[0-9]+' | awk '{print $5}' | sort -u || true)"
    if [[ -n "$open_ports" ]]; then
      local count_ports
      count_ports="$(echo "$open_ports" | wc -l)"
      record_check "NET-04" "network" "Servicios en escucha global (0.0.0.0 / *) detectados ($count_ports sockets)" "MEDIUM" "FAIL" \
        "Servicios expuestos en todas las interfaces de red pueden recibir conexiones directas." \
        "Vincular servicios a 127.0.0.1 o IP privada si no requieren acceso público." "Sockets: $(echo $open_ports | tr '\n' ' ')"
    else
      record_check "NET-04" "network" "No se detectaron sockets en escucha global 0.0.0.0" "MEDIUM" "PASS" \
        "Minimiza exposición perimetral." "Mantener servicios en interfaces locales." "Ninguno"
    fi
  fi
}

# MODULE 4: FILESYSTEM, SUID & PERMISSIONS
run_module_fs() {
  echo -e "\n${COLOR_CYAN}--- [MODULO 4] Sistema de Archivos, Binarios SUID y Particiones ---${COLOR_RESET}"

  # 4.1 Opciones de montaje en /dev/shm
  local shm_mount
  shm_mount="$(mount | grep -E '\s/dev/shm\s' || true)"
  if [[ -n "$shm_mount" ]]; then
    local missing_opts=""
    echo "$shm_mount" | grep -q "nodev" || missing_opts+="nodev "
    echo "$shm_mount" | grep -q "nosuid" || missing_opts+="nosuid "
    echo "$shm_mount" | grep -q "noexec" || missing_opts+="noexec "

    if [[ -z "$missing_opts" ]]; then
      record_check "FS-01" "fs" "/dev/shm protegido con nodev, nosuid, noexec" "MEDIUM" "PASS" \
        "Impide ejecución de binarios maliciosos o abusos SUID en memoria compartida." \
        "Mantener fstab con defaults,nodev,nosuid,noexec." "Montaje: $shm_mount"
    else
      record_check "FS-01" "fs" "/dev/shm carece de opciones restrictivas: $missing_opts" "MEDIUM" "FAIL" \
        "Atacantes pueden compilar y ejecutar binarios o payloads en /dev/shm." \
        "Agregar 'nodev,nosuid,noexec' en /etc/fstab para /dev/shm." "Opciones faltantes: $missing_opts"
    fi
  fi

  # 4.2 Binarios SUID en directorios temporales o mundiales
  local suspicious_suid
  suspicious_suid="$(find /tmp /var/tmp /dev/shm -perm /4000 -type f 2>/dev/null || true)"
  if [[ -z "$suspicious_suid" ]]; then
    record_check "FS-02" "fs" "Sin ejecutables SUID sospechosos en /tmp, /var/tmp, /dev/shm" "HIGH" "PASS" \
      "Previene técnicas clásicas de persistencia o elevación de privilegios." \
      "Mantener particiones temporales limpias de binarios SUID." "Limpio"
  else
    record_check "FS-02" "fs" "Binarios SUID anómalos detectados en rutas temporales" "CRITICAL" "FAIL" \
      "Indicador crítico de intrusión o persistencia maliciosa para elevación de privilegios." \
      "Inspeccionar y eliminar inmediatamente los archivos listados." "Archivos: $suspicious_suid"
  fi

  # 4.3 Carpetas world-writable sin sticky bit
  local missing_sticky
  missing_sticky="$(find /tmp /var/tmp -maxdepth 2 -type d \( -perm -0002 -a ! -perm -1000 \) 2>/dev/null || true)"
  if [[ -z "$missing_sticky" ]]; then
    record_check "FS-03" "fs" "Sticky bit activo en directorios públicos de escritura" "MEDIUM" "PASS" \
      "Evita que usuarios no privilegiados borren o renombren archivos ajenos." \
      "Mantener permisos con sticky bit (chmod +t)." "Correcto"
  else
    record_check "FS-03" "fs" "Directorios públicos sin sticky bit detectados" "MEDIUM" "FAIL" \
      "Cualquier usuario local puede eliminar o sustituir archivos de otros usuarios." \
      "Ejecutar: chmod +t <directorio>" "Carpetas afectadas: $missing_sticky"
  fi
}

# MODULE 5: INSECURE SERVICES & DAEMONS
run_module_services() {
  echo -e "\n${COLOR_CYAN}--- [MODULO 5] Detección de Servicios Inseguros o Legacy ---${COLOR_RESET}"

  local legacy_services=(
    "telnet-server:Servicio Telnet sin cifrado de credenciales"
    "telnet.socket:Socket Telnet en escucha"
    "rsh.socket:Protocolo RSH sin autenticación robusta"
    "rlogin.socket:Rlogin expone contraseñas en texto claro"
    "tftp.socket:TFTP transfiere archivos sin autenticación"
    "vsftpd:Servidor FTP en texto plano sin TLS forzado"
    "ypserv:Servicio NIS inseguro"
  )

  local found_legacy=0
  for item in "${legacy_services[@]}"; do
    local srv="${item%%:*}"
    local desc="${item#*:}"

    if systemctl is-active "$srv" &>/dev/null; then
      ((found_legacy+=1))
      record_check "SRV-${srv}" "services" "Servicio inseguro activo: $srv" "HIGH" "FAIL" \
        "$desc. Permite sniffing de credenciales o accesos no autenticados." \
        "Detener, deshabilitar y desinstalar el servicio: systemctl disable --now $srv" "Estado: active"
    fi
  done

  if [[ $found_legacy -eq 0 ]]; then
    record_check "SRV-LEGACY" "services" "Sin servicios heredados inseguros activos (Telnet, RSH, TFTP)" "HIGH" "PASS" \
      "Evita vectores de ataque clásicos por protocolos en texto plano." \
      "Mantener deshabilitados servicios heredados." "Todos inactivos"
  fi
}

# MODULE 6: KERNEL & MEMORY HARDENING
run_module_kernel() {
  echo -e "\n${COLOR_CYAN}--- [MODULO 6] Protección de Kernel, Memoria y Procesos ---${COLOR_RESET}"

  # 6.1 ASLR (Address Space Layout Randomization)
  local aslr
  aslr="$(sysctl -n kernel.randomize_va_space 2>/dev/null || echo 0)"
  if [[ "$aslr" == "2" ]]; then
    record_check "KERN-01" "kernel" "ASLR totalmente habilitado (randomize_va_space=2)" "HIGH" "PASS" \
      "Dificulta ataques de explotación por desbordamiento de búfer (Buffer Overflow)." \
      "Mantener kernel.randomize_va_space = 2." "kernel.randomize_va_space=2"
  else
    record_check "KERN-01" "kernel" "ASLR deshabilitado o incompleto (actual: $aslr)" "HIGH" "FAIL" \
      "Memoria predecible facilita la ejecución de exploits binarios ROP / Shellcode." \
      "Configurar: sysctl -w kernel.randomize_va_space=2" "kernel.randomize_va_space=$aslr (esperado 2)"
  fi

  # 6.2 Restricción de Core Dumps para binarios SUID
  local suid_dump
  suid_dump="$(sysctl -n fs.suid_dumpable 2>/dev/null || echo 1)"
  if [[ "$suid_dump" == "0" ]]; then
    record_check "KERN-02" "kernel" "Volcados de memoria de binarios SUID restringidos" "MEDIUM" "PASS" \
      "Previene la extracción de credenciales o secretos en dumps de procesos privilegiados." \
      "Mantener fs.suid_dumpable = 0." "fs.suid_dumpable=0"
  else
    record_check "KERN-02" "kernel" "Volcados de memoria SUID permitidos (fs.suid_dumpable != 0)" "MEDIUM" "FAIL" \
      "Procesos privilegiados que caen pueden generar archivos core con datos sensibles." \
      "Configurar: sysctl -w fs.suid_dumpable=0" "fs.suid_dumpable=$suid_dump"
  fi

  # 6.3 Restricción de lectura de dmesg
  local dmesg_res
  dmesg_res="$(sysctl -n kernel.dmesg_restrict 2>/dev/null || echo 0)"
  if [[ "$dmesg_res" == "1" ]]; then
    record_check "KERN-03" "kernel" "Lectura de dmesg restringida a administradores" "LOW" "PASS" \
      "Impide que usuarios locales recopilen información interna de memoria y hardware." \
      "Mantener kernel.dmesg_restrict = 1." "kernel.dmesg_restrict=1"
  else
    record_check "KERN-03" "kernel" "Mensajes de kernel dmesg visibles para usuarios no privilegiados" "LOW" "FAIL" \
      "Filtración de direcciones de memoria del kernel a atacantes locales." \
      "Configurar: sysctl -w kernel.dmesg_restrict=1" "kernel.dmesg_restrict=0"
  fi
}

# MODULE 7: MANDATORY ACCESS CONTROL & AUDITING
run_module_mac() {
  echo -e "\n${COLOR_CYAN}--- [MODULO 7] Control de Acceso Mandatorio (MAC) y Auditoría ---${COLOR_RESET}"

  # 7.1 SELinux o AppArmor (Soporte Universal RHEL/CentOS/Rocky/Fedora/Debian/Ubuntu/SLES)
  local mac_detected=0
  if command -v getenforce &>/dev/null; then
    local se_status
    se_status="$(getenforce 2>/dev/null || echo 'Disabled')"
    if [[ "$se_status" == "Enforcing" ]]; then
      mac_detected=1
      record_check "MAC-01" "mac" "SELinux activo en modo Enforcing" "HIGH" "PASS" \
        "Contención efectiva ante compromisos de servicios web o de base de datos." \
        "Mantener SELinux en modo Enforcing." "Estado: Enforcing"
    else
      record_check "MAC-01" "mac" "SELinux en modo permisivo o desactivado ($se_status)" "HIGH" "FAIL" \
        "Sin confinamiento mandatorio; procesos comprometidos tienen acceso discrecional total." \
        "Modificar /etc/selinux/config y fijar SELINUX=enforcing." "Estado actual: $se_status"
    fi
  elif command -v aa-status &>/dev/null || command -v apparmor_status &>/dev/null; then
    if (aa-status 2>/dev/null || apparmor_status 2>/dev/null) | grep -q "profiles are loaded"; then
      mac_detected=1
      record_check "MAC-01" "mac" "AppArmor activo con perfiles cargados" "HIGH" "PASS" \
        "Contención mandatoria activa en distribución basada en Debian/Ubuntu/SUSE." \
        "Mantener perfiles de AppArmor vigentes." "AppArmor activo"
    else
      record_check "MAC-01" "mac" "AppArmor presente pero sin perfiles estrictos enforcing" "HIGH" "FAIL" \
        "Sin confinamiento mandatorio estricto." "Cargar y activar perfiles en AppArmor." "Sin perfiles en enforce"
    fi
  else
    # Soporte openSUSE / SLES (AppArmor o YaST security)
    if [[ -f /etc/os-release ]] && grep -qiE 'suse|sles' /etc/os-release; then
      if systemctl is-active apparmor &>/dev/null; then
        mac_detected=1
        record_check "MAC-01" "mac" "AppArmor (SLES) activo y en ejecución" "HIGH" "PASS" \
          "Confinamiento mandatorio activo en SUSE." "Mantener servicio activo." "AppArmor activo en SLES"
      else
        record_check "MAC-01" "mac" "AppArmor en SLES inactivo o no configurado" "HIGH" "FAIL" \
          "Falta de aislamiento mandatorio en entorno SUSE." "Habilitar AppArmor via YaST o systemctl." "Inactivo"
      fi
    else
      record_check "MAC-01" "mac" "Sin sistema MAC (SELinux / AppArmor) detectado" "HIGH" "FAIL" \
        "El sistema carece de capa de confinamiento mandatorio L3." \
        "Instalar y habilitar SELinux o AppArmor según la distribución." "No instalado"
    fi
  fi

  # 7.2 Servicio Auditd (Universal)
  if systemctl is-active auditd &>/dev/null || service auditd status &>/dev/null; then
    record_check "MAC-02" "mac" "Servicio auditd en ejecución y capturando eventos" "MEDIUM" "PASS" \
      "Garantiza trazabilidad de acciones privilegiadas y modificaciones del sistema." \
      "Mantener auditd activo con reglas CIS cargadas." "auditd activo"
  else
    record_check "MAC-02" "mac" "Servicio de auditoría auditd inactivo" "MEDIUM" "FAIL" \
      "Pérdida de trazabilidad forense ante incidentes de seguridad." \
      "Habilitar e iniciar auditd: systemctl enable --now auditd" "auditd inactivo"
  fi
}

# MODULE 8: UNIVERSAL PACKAGE UPDATES & KERNEL CURRENCY
run_module_updates() {
  echo -e "\n${COLOR_CYAN}--- [MODULO 8] Detección de Actualizaciones y Versionamiento de Kernel ---${COLOR_RESET}"

  # 8.1 Detección de Distribución y Gestor de Paquetes
  local os_id=""
  local os_version=""
  if [[ -f /etc/os-release ]]; then
    os_id="$(grep -E '^ID=' /etc/os-release | cut -d= -f2 | tr -d '\"' || echo '')"
    os_version="$(grep -E '^VERSION_ID=' /etc/os-release | cut -d= -f2 | tr -d '\"' || echo '')"
  fi

  # 8.2 Comprobación de Actualizaciones de Seguridad Pendientes
  local security_updates_pending=0
  local update_mgr_name=""

  if command -v dnf &>/dev/null; then
    update_mgr_name="dnf (RHEL/Rocky/CentOS/Fedora)"
    if dnf check-update --security &>/dev/null; then
      security_updates_pending=0
    else
      # Exit code 100 in dnf means updates available
      local dnf_rc=$?
      if [[ $dnf_rc -eq 100 ]]; then
        security_updates_pending=1
      fi
    fi
  elif command -v yum &>/dev/null; then
    update_mgr_name="yum (CentOS/RHEL legacy)"
    if yum check-update --security &>/dev/null; then
      security_updates_pending=0
    else
      local yum_rc=$?
      if [[ $yum_rc -eq 100 ]]; then
        security_updates_pending=1
      fi
    fi
  elif command -v apt-get &>/dev/null; then
    update_mgr_name="apt (Debian/Ubuntu)"
    # Update package lists quietly if root
    if [[ $EUID -eq 0 ]]; then
      apt-get -qq update &>/dev/null || true
    fi
    local apt_upgrades
    apt_upgrades="$(apt-get -s upgrade 2>/dev/null | grep -i '^inst' || true)"
    if [[ -n "$apt_upgrades" ]]; then
      security_updates_pending=1
    fi
  elif command -v zypper &>/dev/null; then
    update_mgr_name="zypper (openSUSE/SLES)"
    local zypper_patch
    zypper_patch="$(zypper lp --severity important,moderate 2>/dev/null || true)"
    if echo "$zypper_patch" | grep -q "vulnerability" || [[ -n "$zypper_patch" ]]; then
      security_updates_pending=1
    fi
  else
    update_mgr_name="Gestor genérico"
  fi

  if [[ $security_updates_pending -eq 1 ]]; then
    record_check "UPD-01" "updates" "Actualizaciones de seguridad pendientes detectadas ($update_mgr_name)" "HIGH" "FAIL" \
      "El sistema operativo contiene parches de seguridad críticos o de kernel sin aplicar." \
      "Ejecutar el gestor de paquetes correspondiente para actualizar el sistema (ej: dnf upgrade --security o apt upgrade)." "Actualizaciones pendientes en $update_mgr_name"
  else
    record_check "UPD-01" "updates" "Sistema al día con paquetes y parches de seguridad ($update_mgr_name)" "HIGH" "PASS" \
      "Reduce la exposición a vulnerabilidades conocidas (CVEs)." \
      "Mantener política de parcheo mensual." "Sin parches críticos pendientes"
  fi

  # 8.3 Detección de Kernel y Necesidad de Reboot / Actualización
  local current_kernel
  current_kernel="$(uname -r)"

  # Check if running kernel matches latest installed kernel package
  local kernel_outdated=0
  local latest_kernel=""

  if command -v rpm &>/dev/null; then
    latest_kernel="$(rpm -q kernel --qf '%{VERSION}-%{RELEASE}.%{ARCH}\n' 2>/dev/null | tail -1 || echo '')"
    if [[ -n "$latest_kernel" && "$current_kernel" != *"$latest_kernel"* ]]; then
      # Check if newer version exists
      kernel_outdated=1
    fi
  elif command -v dpkg &>/dev/null; then
    latest_kernel="$(dpkg -l | grep linux-image | awk '{print $2}' | tail -1 || echo '')"
    if [[ -n "$latest_kernel" && "$current_kernel" != *"$latest_kernel"* ]]; then
      kernel_outdated=1
    fi
  fi

  if [[ $kernel_outdated -eq 1 ]]; then
    record_check "UPD-02" "updates" "Kernel desactualizado en memoria (Requiere Reinicio / Reboot)" "MEDIUM" "FAIL" \
      "El kernel activo en ejecución difiere del último paquete de kernel instalado." \
      "Programar ventana de mantenimiento y reiniciar el servidor para cargar el nuevo kernel: sudo reboot" "Kernel activo: $current_kernel | Último instalado: $latest_kernel"
  else
    record_check "UPD-02" "updates" "Kernel en ejecución sincronizado con la última versión instalada" "MEDIUM" "PASS" \
      "El kernel activo es el más reciente disponible en el sistema." \
      "Continuar monitoreo de releases de kernel." "Versión: $current_kernel"
  fi
}

# MODULE 9: APPLICATION ROLE & WORKLOAD FINGERPRINTING
run_module_workload() {
  echo -e "\n${COLOR_CYAN}--- [MODULO 9] Detección de Roles y Aplicaciones en el Servidor ---${COLOR_RESET}"

  local detected_roles=()

  # 9.1 Base de Datos (DB Server)
  local db_detected=""
  if pgrep -x "mysqld" &>/dev/null || pgrep -x "mariadbd" &>/dev/null || systemctl is-active mysql mariadb &>/dev/null; then
    db_detected+="MySQL/MariaDB "
  fi
  if pgrep -x "postgres" &>/dev/null || systemctl is-active postgresql &>/dev/null; then
    db_detected+="PostgreSQL "
  fi
  if pgrep -x "mongod" &>/dev/null || systemctl is-active mongod &>/dev/null; then
    db_detected+="MongoDB "
  fi
  if pgrep -x "oracle" &>/dev/null || pgrep -x tslsnr &>/dev/null; then
    db_detected+="Oracle Database "
  fi
  if pgrep -x "redis-server" &>/dev/null || systemctl is-active redis &>/dev/null; then
    db_detected+="Redis "
  fi

  if [[ -n "$db_detected" ]]; then
    record_check "APP-01" "workload" "Servidor clasificado como Base de Datos (DB Server)" "INFO" "PASS" \
      "Rol detectado: Bases de datos activas ($db_detected)." \
      "Asegurar hardening específico de DB (contraseñas fuertes, cifrado en tránsito, puertos restringidos)." "Detectado: $db_detected"
  else
    record_check "APP-01" "workload" "Sin motores de base de datos principales activos" "INFO" "PASS" \
      "No se detectaron daemons de DB en ejecución." "N/A" "Sin daemons de DB"
  fi

  # 9.2 Servidor Web (Web Server)
  local web_detected=""
  if pgrep -x "nginx" &>/dev/null || systemctl is-active nginx &>/dev/null; then
    web_detected+="Nginx "
  fi
  if pgrep -x "httpd" &>/dev/null || pgrep -x "apache2" &>/dev/null || systemctl is-active httpd apache2 &>/dev/null; then
    web_detected+="Apache HTTPD "
  fi
  if pgrep -x "lighttpd" &>/dev/null || systemctl is-active lighttpd &>/dev/null; then
    web_detected+="Lighttpd "
  fi

  if [[ -n "$web_detected" ]]; then
    record_check "APP-02" "workload" "Servidor clasificado como Servidor Web (Web Server)" "INFO" "PASS" \
      "Rol detectado: Servidores web activos ($web_detected)." \
      "Revisar directivas SSL/TLS, ocultar versión de servidor y deshabilitar módulos innecesarios." "Detectado: $web_detected"
  else
    record_check "APP-02" "workload" "Sin servidores web HTTP principales activos" "INFO" "PASS" \
      "No se detectaron daemons web en ejecución." "N/A" "Sin daemons web"
  fi

  # 9.3 Servidor de Aplicaciones / Runtime (App Server)
  local app_detected=""
  if pgrep -f "java" &>/dev/null || pgrep -f "tomcat" &>/dev/null; then
    app_detected+="Java/Tomcat "
  fi
  if pgrep -f "node" &>/dev/null || pgrep -f "npm" &>/dev/null; then
    app_detected+="Node.js "
  fi
  if pgrep -f "python" &>/dev/null || pgrep -f "gunicorn" &>/dev/null || pgrep -f "uwsgi" &>/dev/null; then
    app_detected+="Python/WSGI "
  fi
  if pgrep -x "php-fpm" &>/dev/null || systemctl is-active php-fpm &>/dev/null; then
    app_detected+="PHP-FPM "
  fi

  if [[ -n "$app_detected" ]]; then
    record_check "APP-03" "workload" "Servidor clasificado como Servidor de Aplicaciones (App Server)" "INFO" "PASS" \
      "Rol detectado: Runtimes de aplicación activos ($app_detected)." \
      "Mantener dependencias actualizadas y aislar permisos de ejecución de procesos." "Detectado: $app_detected"
  else
    record_check "APP-03" "workload" "Sin runtimes de aplicaciones principales activos" "INFO" "PASS" \
      "No se detectaron daemons de app server." "N/A" "Sin app servers"
  fi
}

# ------------------------------------------------------------------------------
# REPORT GENERATORS
# ------------------------------------------------------------------------------
generate_json_report() {
  local json_file="$1"
  local score="$2"
  local host_name
  host_name="$(hostname -f 2>/dev/null || hostname)"
  local os_name
  os_name="$(grep -E '^PRETTY_NAME=' /etc/os-release 2>/dev/null | cut -d= -f2 | tr -d '\"' || uname -sr)"

  cat << EOF > "$json_file"
{
  "audit_metadata": {
    "tool": "Enterprise Linux Vulnerability Auditor",
    "version": "$SCRIPT_VERSION",
    "client": "$CLIENT_NAME",
    "operator": "$OPERATOR_NAME",
    "host": "$host_name",
    "os": "$os_name",
    "kernel": "$(uname -r)",
    "timestamp": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
    "modules_audited": "$TARGET_MODULES"
  },
  "summary": {
    "total_controls": $TOTAL_CHECKS,
    "passed": $PASSED_CHECKS,
    "failed": $FAILED_CHECKS,
    "security_score_percent": $score,
    "critical_failures": $CRITICAL_COUNT,
    "high_failures": $HIGH_COUNT,
    "medium_failures": $MEDIUM_COUNT,
    "low_failures": $LOW_COUNT
  },
  "findings": [
$(sed '$ s/,$//' "$TMP_ITEMS_FILE")
  ]
}
EOF
}

generate_html_dashboard() {
  local html_file="$1"
  local score="$2"
  local host_name
  host_name="$(hostname -f 2>/dev/null || hostname)"
  local os_name
  os_name="$(grep -E '^PRETTY_NAME=' /etc/os-release 2>/dev/null | cut -d= -f2 | tr -d '\"' || uname -sr)"
  local date_str
  date_str="$(date +'%Y-%m-%d %H:%M:%S')"

  # Calculate stroke dash for SVG ring
  local stroke_dash=$(( (score * 283) / 100 ))
  local score_color="#22c55e"
  if [[ $score -lt 70 ]]; then score_color="#eab308"; fi
  if [[ $score -lt 50 ]]; then score_color="#ef4444"; fi

  cat << 'EOF' > "$html_file"
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard de Seguridad Linux - Auditoría</title>
  <style>
    :root {
      --bg-dark: #0f172a;
      --card-bg: #1e293b;
      --card-border: #334155;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --critical: #ef4444;
      --high: #f97316;
      --medium: #eab308;
      --low: #3b82f6;
      --pass: #22c55e;
      --accent-cyan: #06b6d4;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    body { background-color: var(--bg-dark); color: var(--text-main); padding: 24px; line-height: 1.5; }
    .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--card-border); padding-bottom: 20px; margin-bottom: 24px; flex-wrap: wrap; gap: 16px; }
    .header-title h1 { font-size: 24px; font-weight: 700; color: #fff; letter-spacing: -0.5px; }
    .header-title p { color: var(--text-muted); font-size: 14px; margin-top: 4px; }
    .badge-client { background: rgba(6, 182, 212, 0.15); color: var(--accent-cyan); padding: 6px 14px; border-radius: 9999px; font-weight: 600; font-size: 13px; border: 1px solid rgba(6, 182, 212, 0.3); }

    .grid-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }
    .kpi-card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 10px; padding: 18px; text-align: center; }
    .kpi-title { font-size: 12px; font-weight: 600; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.5px; }
    .kpi-val { font-size: 32px; font-weight: 800; margin-top: 6px; }

    .grid-main { display: grid; grid-template-columns: 320px 1fr; gap: 24px; margin-bottom: 24px; }
    @media (max-width: 900px) { .grid-main { grid-template-columns: 1fr; } }

    .card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 12px; padding: 20px; }
    .card h2 { font-size: 16px; font-weight: 700; margin-bottom: 16px; color: #fff; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 10px; }

    .score-circle { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 10px 0; }
    .score-text { font-size: 38px; font-weight: 800; fill: #fff; }
    .meta-list { margin-top: 16px; font-size: 13px; color: var(--text-muted); }
    .meta-list li { margin-bottom: 8px; display: flex; justify-content: space-between; }
    .meta-list strong { color: #e2e8f0; }

    .controls-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; gap: 12px; flex-wrap: wrap; }
    .search-box { background: #0f172a; border: 1px solid var(--card-border); color: #fff; padding: 8px 14px; border-radius: 6px; font-size: 14px; width: 260px; outline: none; }
    .search-box:focus { border-color: var(--accent-cyan); }
    .btn-filter { background: #0f172a; border: 1px solid var(--card-border); color: var(--text-muted); padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600; transition: all 0.2s; }
    .btn-filter.active, .btn-filter:hover { background: #334155; color: #fff; border-color: #64748b; }

    .table-container { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; text-align: left; font-size: 13px; }
    th { background: #0f172a; color: var(--text-muted); font-weight: 600; padding: 12px 14px; border-bottom: 1px solid var(--card-border); text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px; }
    td { padding: 14px; border-bottom: 1px solid var(--card-border); vertical-align: top; }
    tr:hover { background: rgba(255, 255, 255, 0.02); }

    .badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; text-transform: uppercase; }
    .badge-CRITICAL { background: rgba(239, 68, 68, 0.2); color: var(--critical); border: 1px solid rgba(239, 68, 68, 0.4); }
    .badge-HIGH { background: rgba(249, 115, 22, 0.2); color: var(--high); border: 1px solid rgba(249, 115, 22, 0.4); }
    .badge-MEDIUM { background: rgba(234, 179, 8, 0.2); color: var(--medium); border: 1px solid rgba(234, 179, 8, 0.4); }
    .badge-LOW { background: rgba(59, 130, 246, 0.2); color: var(--low); border: 1px solid rgba(59, 130, 246, 0.4); }
    .badge-PASS { background: rgba(34, 197, 94, 0.2); color: var(--pass); border: 1px solid rgba(34, 197, 94, 0.4); }
    .badge-FAIL { background: rgba(239, 68, 68, 0.2); color: var(--critical); border: 1px solid rgba(239, 68, 68, 0.4); }

    .evidence-box { font-family: monospace; font-size: 11px; background: #0b0f19; padding: 6px 10px; border-radius: 4px; border: 1px solid #1e293b; color: #38bdf8; margin-top: 6px; word-break: break-all; }
    .remed-box { margin-top: 6px; color: #94a3b8; font-size: 12px; }
    .remed-box strong { color: #e2e8f0; }
  </style>
</head>
<body>

  <div class="header">
    <div class="header-title">
      <h1>Auditoría de Vulnerabilidades y Seguridad Linux</h1>
      <p>Reporte Técnico de Postura de Seguridad y Hardening Enterprise</p>
    </div>
    <div>
      <span class="badge-client">CLIENTE: <span id="clientName"></span></span>
    </div>
  </div>

  <div class="grid-kpis">
    <div class="kpi-card">
      <div class="kpi-title">Puntaje de Seguridad</div>
      <div class="kpi-val" id="scoreVal" style="color: var(--pass);">--%</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Fallas Críticas</div>
      <div class="kpi-val" style="color: var(--critical);" id="critVal">0</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Fallas Altas</div>
      <div class="kpi-val" style="color: var(--high);" id="highVal">0</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Fallas Medias</div>
      <div class="kpi-val" style="color: var(--medium);" id="medVal">0</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Controles Aprobados</div>
      <div class="kpi-val" style="color: var(--pass);" id="passVal">0</div>
    </div>
  </div>

  <div class="grid-main">
    <div class="card">
      <h2>Resumen Ejecutivo</h2>
      <div class="score-circle">
        <svg width="180" height="180" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="45" fill="none" stroke="#334155" stroke-width="8"></circle>
          <circle id="scoreRing" cx="50" cy="50" r="45" fill="none" stroke="#22c55e" stroke-width="8"
                  stroke-dasharray="283" stroke-dashoffset="283" stroke-linecap="round"
                  transform="rotate(-90 50 50)" style="transition: stroke-dashoffset 1s ease;"></circle>
          <text id="scoreSvgText" x="50" y="55" text-anchor="middle" class="score-text">0%</text>
        </svg>
      </div>
      <ul class="meta-list">
        <li><span>Servidor / Host:</span> <strong id="hostVal">--</strong></li>
        <li><span>Sistema Operativo:</span> <strong id="osVal">--</strong></li>
        <li><span>Kernel:</span> <strong id="kernelVal">--</strong></li>
        <li><span>Fecha Auditoría:</span> <strong id="dateVal">--</strong></li>
        <li><span>Auditor:</span> <strong id="opVal">--</strong></li>
      </ul>
    </div>

    <div class="card">
      <h2>Detalle de Puntos de Control y Remediación</h2>
      <div class="controls-bar">
        <input type="text" id="searchInput" class="search-box" placeholder="Buscar control, módulo o palabra...">
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="btn-filter active" onclick="setFilter('ALL')">Todos</button>
          <button class="btn-filter" onclick="setFilter('FAIL')">Solo Fallas</button>
          <button class="btn-filter" onclick="setFilter('CRITICAL')">Críticos</button>
          <button class="btn-filter" onclick="setFilter('HIGH')">Altos</button>
          <button class="btn-filter" onclick="setFilter('PASS')">Aprobados</button>
        </div>
      </div>
      <div class="table-container">
        <table id="findingsTable">
          <thead>
            <tr>
              <th style="width: 80px;">ID</th>
              <th style="width: 100px;">Módulo</th>
              <th>Hallazgo / Control</th>
              <th style="width: 90px;">Severidad</th>
              <th style="width: 90px;">Estado</th>
              <th>Impacto y Remediación</th>
            </tr>
          </thead>
          <tbody id="tableBody"></tbody>
        </table>
      </div>
    </div>
  </div>

  <script>
    // Embedded JSON Audit Data
    const AUDIT_DATA =
EOF

  # Append JSON content directly into the HTML
  cat "$OUTPUT_DIR/audit_report.json" >> "$html_file"

  cat << 'EOF' >> "$html_file"
;

    // Render Dashboard
    document.getElementById('clientName').textContent = AUDIT_DATA.audit_metadata.client;
    document.getElementById('hostVal').textContent = AUDIT_DATA.audit_metadata.host;
    document.getElementById('osVal').textContent = AUDIT_DATA.audit_metadata.os;
    document.getElementById('kernelVal').textContent = AUDIT_DATA.audit_metadata.kernel;
    document.getElementById('dateVal').textContent = AUDIT_DATA.audit_metadata.timestamp;
    document.getElementById('opVal').textContent = AUDIT_DATA.audit_metadata.operator;

    const summary = AUDIT_DATA.summary;
    const score = summary.security_score_percent;
    document.getElementById('scoreVal').textContent = score + '%';
    document.getElementById('scoreSvgText').textContent = score + '%';
    document.getElementById('critVal').textContent = summary.critical_failures;
    document.getElementById('highVal').textContent = summary.high_failures;
    document.getElementById('medVal').textContent = summary.medium_failures;
    document.getElementById('passVal').textContent = summary.passed;

    // SVG Score Circle
    const ring = document.getElementById('scoreRing');
    const offset = 283 - ((score * 283) / 100);
    ring.style.strokeDashoffset = offset;
    let ringColor = "#22c55e";
    if (score < 70) ringColor = "#eab308";
    if (score < 50) ringColor = "#ef4444";
    ring.style.stroke = ringColor;
    document.getElementById('scoreVal').style.color = ringColor;

    let currentFilter = 'ALL';
    let searchQuery = '';

    function renderTable() {
      const tbody = document.getElementById('tableBody');
      tbody.innerHTML = '';

      AUDIT_DATA.findings.forEach(f => {
        // Filter logic
        if (currentFilter === 'FAIL' && f.status !== 'FAIL') return;
        if (currentFilter === 'PASS' && f.status !== 'PASS') return;
        if (currentFilter === 'CRITICAL' && (f.severity !== 'CRITICAL' || f.status !== 'FAIL')) return;
        if (currentFilter === 'HIGH' && (f.severity !== 'HIGH' || f.status !== 'FAIL')) return;

        // Search logic
        if (searchQuery) {
          const text = (f.id + ' ' + f.module + ' ' + f.title + ' ' + f.impact + ' ' + f.remediation).toLowerCase();
          if (!text.includes(searchQuery.toLowerCase())) return;
        }

        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${f.id}</strong></td>
          <td><span style="color:var(--text-muted);font-weight:600;">${f.module.toUpperCase()}</span></td>
          <td>
            <strong>${f.title}</strong>
            <div class="evidence-box">Evidencia: ${f.evidence}</div>
          </td>
          <td><span class="badge badge-${f.severity}">${f.severity}</span></td>
          <td><span class="badge badge-${f.status}">${f.status}</span></td>
          <td>
            <div>${f.impact}</div>
            <div class="remed-box"><strong>Remediación:</strong> ${f.remediation}</div>
          </td>
        `;
        tbody.appendChild(tr);
      });
    }

    function setFilter(type) {
      currentFilter = type;
      document.querySelectorAll('.btn-filter').forEach(btn => btn.classList.remove('active'));
      event.target.classList.add('active');
      renderTable();
    }

    document.getElementById('searchInput').addEventListener('input', (e) => {
      searchQuery = e.target.value;
      renderTable();
    });

    renderTable();
  </script>
</body>
</html>
EOF
}

# ------------------------------------------------------------------------------
# MAIN EXECUTION FLOW
# ------------------------------------------------------------------------------
main() {
  mkdir -p "$OUTPUT_DIR"

  echo -e "${COLOR_BOLD}${COLOR_CYAN}========================================================================${COLOR_RESET}"
  echo -e "${COLOR_BOLD}${COLOR_CYAN}       ENTERPRISE LINUX SECURITY AUDITOR - VULNERABILITY SCANNER        ${COLOR_RESET}"
  echo -e "${COLOR_BOLD}${COLOR_CYAN}========================================================================${COLOR_RESET}"
  echo -e "Cliente Objetivo:  ${COLOR_BOLD}$CLIENT_NAME${COLOR_RESET}"
  echo -e "Host:              $(hostname -f 2>/dev/null || hostname)"
  echo -e "Módulos:           $TARGET_MODULES"
  echo -e "Directorio Salida: $OUTPUT_DIR"
  echo -e "${COLOR_CYAN}========================================================================${COLOR_RESET}"

  # Execute requested modules
  if is_module_enabled "auth"; then run_module_auth; fi
  if is_module_enabled "ssh"; then run_module_ssh; fi
  if is_module_enabled "network"; then run_module_network; fi
  if is_module_enabled "fs"; then run_module_fs; fi
  if is_module_enabled "services"; then run_module_services; fi
  if is_module_enabled "kernel"; then run_module_kernel; fi
  if is_module_enabled "mac"; then run_module_mac; fi
  if is_module_enabled "updates"; then run_module_updates; fi
  if is_module_enabled "workload"; then run_module_workload; fi

  # Calculate score
  local score=100
  if [[ $TOTAL_CHECKS -gt 0 ]]; then
    # Penalty-based scoring formula:
    # Critical: -25 pts, High: -10 pts, Medium: -5 pts, Low: -2 pts
    local penalty=$(( (CRITICAL_COUNT * 25) + (HIGH_COUNT * 10) + (MEDIUM_COUNT * 5) + (LOW_COUNT * 2) ))
    score=$(( 100 - penalty ))
    if [[ $score -lt 0 ]]; then score=0; fi
  fi

  echo -e "\n${COLOR_CYAN}========================================================================${COLOR_RESET}"
  echo -e "${COLOR_BOLD}                        RESUMEN DE AUDITORÍA                            ${COLOR_RESET}"
  echo -e "${COLOR_CYAN}========================================================================${COLOR_RESET}"
  echo -e "Total Controles Evaluados: $TOTAL_CHECKS"
  echo -e "Aprobados (PASS):          ${COLOR_GREEN}${PASSED_CHECKS}${COLOR_RESET}"
  echo -e "Fallas Totales (FAIL):     ${COLOR_RED}${FAILED_CHECKS}${COLOR_RESET}"
  echo -e "  - Críticas:              ${COLOR_RED}${CRITICAL_COUNT}${COLOR_RESET}"
  echo -e "  - Altas:                 ${COLOR_YELLOW}${HIGH_COUNT}${COLOR_RESET}"
  echo -e "  - Medias:                ${COLOR_YELLOW}${MEDIUM_COUNT}${COLOR_RESET}"
  echo -e "  - Bajas:                 ${COLOR_BLUE}${LOW_COUNT}${COLOR_RESET}"
  echo -e "Puntuación de Seguridad:   ${COLOR_BOLD}${score}%${COLOR_RESET}"
  echo -e "${COLOR_CYAN}========================================================================${COLOR_RESET}"

  # 1. Export JSON
  if [[ $ENABLE_JSON -eq 1 ]]; then
    local json_report="$OUTPUT_DIR/audit_report.json"
    generate_json_report "$json_report" "$score"
    echo -e "[*] Reporte JSON generado en:     ${COLOR_GREEN}${json_report}${COLOR_RESET}"
  fi

  # 2. Export HTML Client Dashboard
  if [[ $ENABLE_HTML -eq 1 ]]; then
    local html_dashboard="$OUTPUT_DIR/client_dashboard.html"
    generate_html_dashboard "$html_dashboard" "$score"
    echo -e "[*] Dashboard HTML generado en:   ${COLOR_GREEN}${html_dashboard}${COLOR_RESET}"
    echo -e "    ${COLOR_CYAN}-> Abra este archivo en el navegador para la presentación al cliente.${COLOR_RESET}"
  fi

  echo -e "${COLOR_CYAN}========================================================================${COLOR_RESET}"

  if [[ $CRITICAL_COUNT -gt 0 || $HIGH_COUNT -gt 0 ]]; then
    exit 1
  else
    exit 0
  fi
}

main
