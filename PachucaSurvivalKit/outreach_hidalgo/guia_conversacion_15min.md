# Guía de Conversación — Llamadas de 15 minutos (Hidalgo)

## Estructura de la llamada (15 min)

| Min | Bloque | Contenido clave |
|-----|--------|-----------------|
| 0-3 | Apertura y contexto | Presentarse, por qué llama (runbook CIS RHEL 9 + auditoría de vulnerabilidades), referencia a la actividad de la empresa. |
| 3-7 | Dolor del cliente | Preguntar sobre su stack Linux, hardening actual, auditorías recientes, incidentes de seguridad. |
| 7-11 | Solución propuesta | Sprint 48h, runbook CIS RHEL 9 con Ansible (85+ controles), auditoría de vulnerabilidades con CVSS, roadmap 30 días, evidencia audit-ready. |
| 11-14 | Próximo paso | Proponer reunión técnica de seguimiento o envío de demo del runbook. |
| 14-15 | Cierre | Agradecer, confirmar contacto decisor, enviar email de seguimiento. |

## Dolor → Beneficio por empresa

| Empresa | Dolor principal (pregunta clave) | Beneficio del runbook + auditoría |
|---------|----------------------------------|-----------------------------------|
| **GLTEC** | ¿Tienen estandarizado su stack Linux para soporte L3 a clientes? | Reducción de MTTR ≈ 80% y evidencia audit-ready para SOC2/PCI-DSS. |
| **Celmi Solutions** | ¿Ofrecen assessments y hardening con evidencia tangible a sus clientes? | Diferenciación competitiva con runbook automatizado y reportes listos para auditoría. |
| **GEIG** | ¿Sus clientes exigen evidencia de cumplimiento (SOC2, PCI-DSS)? | Entrega de runbook audit-ready que acelera certificaciones y cierra contratos. |
| **Infrusch** | ¿Tienen backlog de hardening y necesidad de quick wins sin downtime? | Identificación de 5-10 vulnerabilidades críticas en 48h y remediación sin tocar producción. |
| **oneTI** | ¿Tienen capacidad para diagnóstico Linux y automatización en overflow? | Runbook + auditoría = prueba de capacidad L3 y generación de propuesta de overflow. |
| **RED L3** | ¿Pueden demostrar cobertura y confiabilidad L3 en licitaciones? | Evidencia de 85+ controles CIS automatizados → mayor win-rate. |
| **NablaTi** | ¿Validan la postura de seguridad antes de migraciones de data center? | Auditoría de vulnerabilidades pre-migración → reducción de riesgos post-migración. |
| **STS Hidalgo** | ¿Tienen documentación operativa y pruebas de vulnerabilidad para sus clientes? | Paquete "listo para venta" con métricas de riesgo y mitigación. |
| **Grupo AxTic** | ¿Cierran la brecha entre desarrollo y operación de servidores? | Automatización y pruebas de seguridad → mayor estabilidad y menos incidentes. |
| **Site IK** | ¿Tienen un producto tangible para assessments de disponibilidad y hardening? | Runbook con evidencia audit-ready → contrato de mantenimiento y soporte continuo. |

## Objeciones comunes y respuestas

| Objeción | Respuesta sugerida |
|----------|-------------------|
| "Ya tenemos un proveedor de TI" | "El runbook es complementario: automatiza 85+ controles CIS y entrega evidencia audit-ready sin reemplazar a su proveedor actual." |
| "No tenemos presupuesto ahora" | "El sprint de 48h es una entrada de bajo riesgo. Si hay fit, escalamos a un roadmap de 30 días sin cambios en producción sin autorización." |
| "No tocamos producción" | "Exacto: todo el runbook es idempotente y reversible. No se realizan cambios en producción sin autorización previa." |
| "Ya pasamos una auditoría" | "La auditoría de vulnerabilidades valida que los controles sigan activos y identifica quick wins de mitigación antes del próximo ciclo." |

## Script de apertura (ejemplo)

> "Hola [Nombre], soy Ruben Ramírez, especialista Linux L3. Vi que [Empresa] trabaja en [actividad]. Llevo tiempo ayudando a empresas de Hidalgo a estandarizar su infraestructura Linux con un runbook CIS RHEL 9 automatizado (85+ controles) y una auditoría de vulnerabilidades que identifica riesgos críticos en 48 horas. ¿Tienen 15 minutos esta semana para conversar si esto encaja con su roadmap?"

## Después de la llamada
1. Enviar email de agradecimiento con el pitch adjunto.
2. Actualizar el tracker de outreach con el estado y próximo paso.
3. Si hay interés, agendar demo técnica del runbook CIS RHEL 9.