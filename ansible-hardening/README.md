# Ansible Hardening Framework
**Enterprise L3 Infrastructure Automation**

Ansible playbooks y scripts de hardening para RHEL siguiendo CIS Benchmark compliance.

## 🎯 Características

- **Idempotente:** Ejecución segura múltiples veces sin efectos adversos
- **Modular:** Roles independientes y reutilizables
- **Agentless:** Sin agentes en nodos target (SSH + Python)
- **CIS Compliant:** Implementa controles CIS Benchmark Level 1 & 2
- **Validación robusta:** Input validation, error handling, least privilege
- **Testing completo:** Smoke tests + test suite por rol

## 📁 Estructura del Proyecto

```
ansible-hardening/
├── playbooks/           # Playbooks principales
├── roles/              # Roles modulares
│   ├── cis-rhel-base/
│   ├── cis-filesystem/
│   ├── cis-services/
│   ├── cis-network/
│   ├── cis-logging/
│   └── cis-access-control/
├── inventories/        # Inventarios por ambiente
│   ├── production/
│   ├── staging/
│   └── development/
├── group_vars/         # Variables por grupo
├── host_vars/          # Variables por host
├── scripts/           # Scripts Python/Bash de hardening
├── tests/             # Tests automatizados
└── docs/              # Documentación técnica
```

## 🚀 Quick Start

### Prerrequisitos
- Ansible >= 2.15
- Python >= 3.9
- RHEL 8/9 target systems
- SSH key-based authentication

### Instalación
```bash
# Clonar repositorio
git clone <repo-url>
cd ansible-hardening

# Instalar dependencias de Ansible
ansible-galaxy install -r requirements.yml

# Validar sintaxis
ansible-playbook --syntax-check playbooks/site.yml

# Dry-run (check mode)
ansible-playbook -i inventories/development/hosts.yml playbooks/site.yml --check

# Ejecutar hardening
ansible-playbook -i inventories/development/hosts.yml playbooks/site.yml
```

## 🔒 Niveles de Hardening

### Level 1 (Baseline)
- Configuraciones básicas sin impacto en aplicaciones
- Filesystem hardening
- Service minimization
- Basic access control

### Level 2 (Strict)
- Configuraciones restrictivas
- Network hardening avanzado
- Mandatory logging
- Advanced access control (SELinux enforcing)

## 🧪 Testing

```bash
# Smoke tests (validación rápida)
./tests/smoke_test.sh

# Test suite completa
pytest tests/ -v

# Test específico de rol
pytest tests/test_cis_filesystem.py -v
```

## 📊 Compliance Reporting

```bash
# Generar reporte de compliance
ansible-playbook -i inventories/production/hosts.yml playbooks/compliance_report.yml

# Ver reporte
cat reports/compliance_$(date +%Y%m%d).html
```

## 🛡️ Seguridad

- **Least Privilege:** Todos los roles usan privilegios mínimos necesarios
- **Input Validation:** Validación exhaustiva de variables
- **Idempotencia:** Safe para re-ejecución
- **Rollback:** Scripts de rollback incluidos
- **Audit Trail:** Logging completo de cambios

## 📝 Autor

**Ruben Omar Ramírez Gutiérrez**  
Ingeniero en Computación (UNAM)  
Enterprise L3 Infrastructure Specialist

## 📄 Licencia

MIT License - Ver LICENSE para detalles
