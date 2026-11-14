#!/usr/bin/env python3
"""Generate the client-facing documentation for the Linux security auditor."""

from pathlib import Path
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs" / "Documentacion_Auditor_Seguridad_Linux.docx"

NAVY = "17324D"
CYAN = "0B7285"
LIGHT_BLUE = "EAF4F4"
LIGHT_GRAY = "F3F5F7"
DARK_GRAY = "334155"
RED = "B42318"
ORANGE = "C2410C"
GREEN = "18794E"


def set_cell_shading(cell, fill):
    properties = cell._tc.get_or_add_tcPr()
    shading = properties.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        properties.append(shading)
    shading.set(qn("w:fill"), fill)


def set_cell_border(cell, **kwargs):
    properties = cell._tc.get_or_add_tcPr()
    borders = properties.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        properties.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        if edge in kwargs:
            edge_data = kwargs.get(edge)
            tag = f"w:{edge}"
            element = borders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                borders.append(element)
            for key in ["val", "sz", "space", "color"]:
                if key in edge_data:
                    element.set(qn(f"w:{key}"), str(edge_data[key]))


def style_table(table, header_fill=NAVY):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for row_index, row in enumerate(table.rows):
        for cell in row.cells:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_border(
                cell,
                top={"val": "single", "sz": "4", "color": "D1D5DB"},
                bottom={"val": "single", "sz": "4", "color": "D1D5DB"},
                left={"val": "single", "sz": "4", "color": "D1D5DB"},
                right={"val": "single", "sz": "4", "color": "D1D5DB"},
            )
            if row_index == 0:
                set_cell_shading(cell, header_fill)
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.bold = True
                        run.font.color.rgb = RGBColor(255, 255, 255)
            elif row_index % 2 == 0:
                set_cell_shading(cell, LIGHT_GRAY)


def set_cell_text(cell, text, bold=False, color=None, size=9):
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(0)
    run = paragraph.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def add_bullet(document, text, level=0):
    paragraph = document.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
    paragraph.paragraph_format.space_after = Pt(3)
    paragraph.add_run(text)
    return paragraph


def add_code(document, text):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.left_indent = Inches(0.25)
    paragraph.paragraph_format.right_indent = Inches(0.25)
    paragraph.paragraph_format.space_before = Pt(4)
    paragraph.paragraph_format.space_after = Pt(8)
    run = paragraph.add_run(text)
    run.font.name = "Consolas"
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor.from_string(DARK_GRAY)
    paragraph._p.get_or_add_pPr().append(OxmlElement("w:shd"))
    paragraph._p.pPr[-1].set(qn("w:fill"), LIGHT_GRAY)
    return paragraph


def add_callout(document, title, body, fill=LIGHT_BLUE, title_color=CYAN):
    table = document.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    set_cell_shading(cell, fill)
    set_cell_border(
        cell,
        top={"val": "single", "sz": "8", "color": title_color},
        bottom={"val": "single", "sz": "8", "color": title_color},
        left={"val": "single", "sz": "18", "color": title_color},
        right={"val": "single", "sz": "8", "color": title_color},
    )
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(3)
    run = paragraph.add_run(title)
    run.bold = True
    run.font.color.rgb = RGBColor.from_string(title_color)
    body_paragraph = cell.add_paragraph(body)
    body_paragraph.paragraph_format.space_after = Pt(2)
    return table


def add_heading(document, text, level=1):
    paragraph = document.add_heading(text, level=level)
    if level == 1:
        paragraph.runs[0].font.color.rgb = RGBColor.from_string(NAVY)
    elif level == 2:
        paragraph.runs[0].font.color.rgb = RGBColor.from_string(CYAN)
    return paragraph


def configure_document(document):
    section = document.sections[0]
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)

    styles = document.styles
    normal = styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(10)
    normal.font.color.rgb = RGBColor.from_string(DARK_GRAY)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.08

    for style_name, size, color in [("Title", 27, NAVY), ("Heading 1", 18, NAVY), ("Heading 2", 13, CYAN), ("Heading 3", 11, DARK_GRAY)]:
        style = styles[style_name]
        style.font.name = "Aptos Display"
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor.from_string(color)
        style.font.bold = True

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_run = footer.add_run("Auditor de Seguridad Linux  |  Documentación técnica  |  Uso autorizado")
    footer_run.font.size = Pt(8)
    footer_run.font.color.rgb = RGBColor.from_string("64748B")


def build_document():
    document = Document()
    configure_document(document)

    # Cover page
    cover = document.add_paragraph()
    cover.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cover.paragraph_format.space_before = Pt(80)
    run = cover.add_run("AUDITOR DE SEGURIDAD LINUX")
    run.bold = True
    run.font.size = Pt(28)
    run.font.color.rgb = RGBColor.from_string(NAVY)

    subtitle = document.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.paragraph_format.space_before = Pt(12)
    run = subtitle.add_run("Documentación funcional y técnica")
    run.font.size = Pt(16)
    run.font.color.rgb = RGBColor.from_string(CYAN)

    line = document.add_paragraph()
    line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    line.paragraph_format.space_before = Pt(35)
    line.paragraph_format.space_after = Pt(35)
    run = line.add_run("Auditoría modular de vulnerabilidades, hardening y postura de seguridad")
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor.from_string(DARK_GRAY)

    cover_table = document.add_table(rows=4, cols=2)
    cover_table.columns[0].width = Inches(1.8)
    cover_table.columns[1].width = Inches(4.8)
    cover_data = [
        ("Versión", "2.1.0"),
        ("Plataforma objetivo", "Linux / RHEL, Rocky, CentOS, Debian y derivados"),
        ("Tipo de ejecución", "No destructiva, modular y orientada a evidencias"),
        ("Salida", "JSON estructurado y dashboard HTML autocontenido"),
    ]
    for row, (label, value) in zip(cover_table.rows, cover_data):
        set_cell_text(row.cells[0], label, bold=True, color=NAVY)
        set_cell_text(row.cells[1], value)
        set_cell_shading(row.cells[0], LIGHT_BLUE)
    style_table(cover_table, header_fill=NAVY)
    # Restore cover table header styling because it has no header row.
    for row in cover_table.rows:
        set_cell_shading(row.cells[0], LIGHT_BLUE)
        for run in row.cells[0].paragraphs[0].runs:
            run.font.color.rgb = RGBColor.from_string(NAVY)
    document.add_page_break()

    add_heading(document, "1. Resumen ejecutivo", 1)
    document.add_paragraph(
        "El Auditor de Seguridad Linux es un script Bash modular para identificar configuraciones débiles, "
        "servicios heredados, exposición de red, permisos peligrosos y controles de seguridad ausentes en servidores Linux. "
        "Su propósito es producir evidencia técnica que pueda ser revisada por infraestructura, seguridad y el cliente final."
    )
    add_callout(
        document,
        "Alcance operativo",
        "El auditor únicamente revisa el estado del sistema y no aplica cambios de remediación. La corrección se ejecuta posteriormente mediante Ansible, procedimientos aprobados o herramientas de gestión de configuración.",
    )
    document.add_paragraph(
        "La información se presenta en dos formatos: un JSON consumible por automatizaciones y un dashboard HTML que puede abrirse localmente en un navegador para una presentación ejecutiva."
    )

    add_heading(document, "2. Objetivos", 1)
    for item in [
        "Detectar los puntos de seguridad más vulnerables de un servidor Linux.",
        "Organizar las revisiones por módulos independientes para facilitar su ejecución selectiva.",
        "Asignar severidad, impacto, evidencia y recomendación de remediación a cada control.",
        "Generar un puntaje de seguridad comprensible para un público técnico y ejecutivo.",
        "Entregar información reutilizable para dashboards, reportes, tickets y planes de remediación.",
        "Mantener una ejecución no destructiva y con manejo explícito de errores.",
    ]:
        add_bullet(document, item)

    add_heading(document, "3. Arquitectura funcional", 1)
    document.add_paragraph("El flujo de ejecución se divide en cinco etapas:")
    stages = [
        ("1", "Entrada", "El operador selecciona módulos, cliente y directorio de salida."),
        ("2", "Auditoría", "Cada módulo ejecuta comprobaciones independientes sobre el host."),
        ("3", "Normalización", "Cada resultado se convierte en un hallazgo con ID, severidad, estado y evidencia."),
        ("4", "Scoring", "Se calcula una puntuación de seguridad con penalización por severidad."),
        ("5", "Entrega", "Se generan JSON y dashboard HTML autocontenido."),
    ]
    table = document.add_table(rows=1, cols=3)
    for cell, text in zip(table.rows[0].cells, ["Etapa", "Componente", "Descripción"]):
        set_cell_text(cell, text, bold=True, size=9)
    for number, component, description in stages:
        cells = table.add_row().cells
        set_cell_text(cells[0], number, bold=True, color=CYAN, size=9)
        set_cell_text(cells[1], component, bold=True, size=9)
        set_cell_text(cells[2], description, size=9)
    style_table(table)

    add_heading(document, "4. Módulos de auditoría", 1)
    module_table = document.add_table(rows=1, cols=4)
    for cell, text in zip(module_table.rows[0].cells, ["Módulo", "Ámbito", "Controles principales", "Prioridad"]):
        set_cell_text(cell, text, bold=True, size=8.5)
    modules = [
        ("auth", "Identidad y privilegios", "UID 0, contraseñas vacías, NOPASSWD, permisos de /etc/shadow", "Crítica / Alta"),
        ("ssh", "Acceso remoto", "PermitRootLogin, PasswordAuthentication, MaxAuthTries, X11Forwarding", "Alta / Media"),
        ("network", "Red y firewall", "Firewall, IP forwarding, SYN cookies, sockets globales", "Crítica / Alta"),
        ("fs", "Sistema de archivos", "/dev/shm, binarios SUID temporales, sticky bit", "Crítica / Media"),
        ("services", "Servicios heredados", "Telnet, RSH, Rlogin, TFTP, FTP, NIS", "Alta"),
        ("kernel", "Kernel y memoria", "ASLR, core dumps SUID, dmesg", "Alta / Media"),
        ("mac", "MAC y auditoría", "SELinux/AppArmor y auditd", "Alta / Media"),
        ("all", "Auditoría completa", "Ejecuta todos los módulos", "Todas"),
    ]
    for module, scope, controls, priority in modules:
        cells = module_table.add_row().cells
        set_cell_text(cells[0], module, bold=True, color=CYAN, size=8.5)
        set_cell_text(cells[1], scope, size=8.5)
        set_cell_text(cells[2], controls, size=8.5)
        set_cell_text(cells[3], priority, size=8.5)
    style_table(module_table)

    add_heading(document, "5. Instalación y requisitos", 1)
    document.add_paragraph("El auditor no requiere paquetes externos para su ejecución en Linux. Se recomienda:")
    for item in [
        "Bash 4 o superior.",
        "Ejecutar con sudo o root para obtener resultados completos en /etc/shadow, auditd y systemctl.",
        "Herramientas habituales: awk, grep, sed, stat, find, sysctl, ss y systemctl.",
        "Acceso de lectura al sistema objetivo y permisos para consultar servicios y parámetros del kernel.",
    ]:
        add_bullet(document, item)
    add_code(document, "chmod +x scripts/bash/audit_vulnerabilities.sh")
    add_code(document, "sudo bash scripts/bash/audit_vulnerabilities.sh --help")
    add_callout(
        document,
        "Importante",
        "El auditor debe ejecutarse únicamente sobre activos autorizados. El reporte puede contener nombres de host, servicios, rutas y configuraciones sensibles; debe manejarse como información confidencial.",
        fill="FFF4E5",
        title_color=ORANGE,
    )

    add_heading(document, "6. Uso del script", 1)
    add_heading(document, "6.1 Auditoría completa", 2)
    add_code(document, "sudo bash scripts/bash/audit_vulnerabilities.sh \\\n  --client \"Cliente Corporativo\" \\\n  --output-dir ./reports/cliente_001")

    add_heading(document, "6.2 Ejecución modular", 2)
    add_code(document, "sudo bash scripts/bash/audit_vulnerabilities.sh \\\n  --modules auth,ssh \\\n  --client \"Cliente Corporativo\" \\\n  --output-dir ./reports/ssh_auth")
    add_code(document, "sudo bash scripts/bash/audit_vulnerabilities.sh \\\n  --modules network,kernel \\\n  --output-dir ./reports/network_kernel")

    add_heading(document, "6.3 Opciones disponibles", 2)
    options_table = document.add_table(rows=1, cols=3)
    for cell, text in zip(options_table.rows[0].cells, ["Opción", "Descripción", "Ejemplo"]):
        set_cell_text(cell, text, bold=True, size=9)
    options = [
        ("-m, --modules", "Módulos separados por coma.", "--modules auth,ssh"),
        ("-c, --client", "Nombre del cliente en el reporte.", "--client \"Cliente A\""),
        ("-o, --output-dir", "Directorio de salida.", "--output-dir ./reports/audit"),
        ("--no-html", "No generar dashboard HTML.", "--no-html"),
        ("--no-json", "No generar JSON.", "--no-json"),
        ("-q, --quiet", "Reducir salida en consola.", "--quiet"),
        ("-h, --help", "Mostrar ayuda.", "--help"),
    ]
    for option, description, example in options:
        cells = options_table.add_row().cells
        set_cell_text(cells[0], option, bold=True, color=CYAN, size=8.5)
        set_cell_text(cells[1], description, size=8.5)
        set_cell_text(cells[2], example, size=8.5)
    style_table(options_table)

    add_heading(document, "7. Interpretación de severidades", 1)
    severity_table = document.add_table(rows=1, cols=4)
    for cell, text in zip(severity_table.rows[0].cells, ["Severidad", "Criterio", "Ejemplos", "Acción recomendada"]):
        set_cell_text(cell, text, bold=True, size=8.5)
    severities = [
        ("CRITICAL", "Compromiso directo o privilegios absolutos.", "UID 0 no autorizado, root SSH por contraseña, firewall ausente.", "Atención inmediata; abrir incidente de seguridad."),
        ("HIGH", "Exposición importante o pérdida de control.", "SELinux desactivado, SSH débil, servicios heredados.", "Remediar con prioridad alta y validar después."),
        ("MEDIUM", "Debilidad relevante con condiciones adicionales.", "SYN cookies, /dev/shm, core dumps.", "Incluir en el plan de hardening cercano."),
        ("LOW", "Recomendación de reducción de superficie.", "X11Forwarding, MaxAuthTries, dmesg.", "Corregir durante mantenimiento programado."),
    ]
    for severity, criterion, examples, action in severities:
        cells = severity_table.add_row().cells
        color = {"CRITICAL": RED, "HIGH": ORANGE, "MEDIUM": "A16207", "LOW": "2563EB"}[severity]
        set_cell_text(cells[0], severity, bold=True, color=color, size=8.5)
        set_cell_text(cells[1], criterion, size=8.5)
        set_cell_text(cells[2], examples, size=8.5)
        set_cell_text(cells[3], action, size=8.5)
    style_table(severity_table)

    add_heading(document, "8. Cálculo del puntaje de seguridad", 1)
    document.add_paragraph(
        "El puntaje inicia en 100 puntos. Cada falla aplica una penalización según su severidad. El resultado mínimo es 0 y se expresa como porcentaje."
    )
    add_code(document, "Puntaje = max(0, 100 - (25 × críticas + 10 × altas + 5 × medias + 2 × bajas))")
    score_table = document.add_table(rows=1, cols=3)
    for cell, text in zip(score_table.rows[0].cells, ["Severidad", "Penalización", "Interpretación"]):
        set_cell_text(cell, text, bold=True, size=9)
    for severity, penalty, meaning in [
        ("CRITICAL", "25 puntos", "Riesgo inmediato y prioritario"),
        ("HIGH", "10 puntos", "Debilidad importante"),
        ("MEDIUM", "5 puntos", "Riesgo moderado"),
        ("LOW", "2 puntos", "Mejora recomendada"),
    ]:
        cells = score_table.add_row().cells
        set_cell_text(cells[0], severity, bold=True, size=9)
        set_cell_text(cells[1], penalty, size=9)
        set_cell_text(cells[2], meaning, size=9)
    style_table(score_table)

    add_heading(document, "9. Archivos de salida", 1)
    output_table = document.add_table(rows=1, cols=3)
    for cell, text in zip(output_table.rows[0].cells, ["Archivo", "Contenido", "Uso"]):
        set_cell_text(cell, text, bold=True, size=9)
    outputs = [
        ("audit_report.json", "Metadatos, resumen y hallazgos estructurados.", "Integración con dashboards, SIEM, APIs o automatizaciones."),
        ("client_dashboard.html", "Dashboard visual autocontenido con filtros y búsqueda.", "Presentación ejecutiva y revisión con el cliente."),
    ]
    for filename, content, usage in outputs:
        cells = output_table.add_row().cells
        set_cell_text(cells[0], filename, bold=True, color=CYAN, size=8.5)
        set_cell_text(cells[1], content, size=8.5)
        set_cell_text(cells[2], usage, size=8.5)
    style_table(output_table)

    add_heading(document, "10. Estructura del JSON", 1)
    document.add_paragraph("Cada hallazgo contiene los siguientes campos:")
    for item in [
        "id: identificador estable del control, por ejemplo SSH-01 o NET-02.",
        "module: módulo que originó la comprobación.",
        "title: descripción breve del control o hallazgo.",
        "severity: CRITICAL, HIGH, MEDIUM o LOW.",
        "status: PASS o FAIL.",
        "impact: consecuencia de mantener la configuración vulnerable.",
        "remediation: acción recomendada para corregirla.",
        "evidence: valor observado en el sistema.",
    ]:
        add_bullet(document, item)
    add_code(document, '{\n  "summary": {\n    "total_controls": 7,\n    "passed": 5,\n    "failed": 2,\n    "security_score_percent": 93\n  }\n}')

    add_heading(document, "11. Flujo recomendado para el cliente", 1)
    workflow_table = document.add_table(rows=1, cols=4)
    for cell, text in zip(workflow_table.rows[0].cells, ["Fase", "Actividad", "Responsable", "Evidencia"]):
        set_cell_text(cell, text, bold=True, size=8.5)
    workflow = [
        ("1. Preparación", "Autorizar activos y definir ventana de revisión.", "Cliente / Infraestructura", "Lista de hosts y autorización."),
        ("2. Baseline", "Ejecutar el auditor sin modificar el host.", "Consultor", "audit_report.json y dashboard."),
        ("3. Priorización", "Revisar fallas por severidad e impacto.", "Seguridad / Cliente", "Matriz de riesgos."),
        ("4. Remediación", "Aplicar cambios mediante Ansible o procedimiento aprobado.", "Infraestructura", "Playbook, ticket o change record."),
        ("5. Validación", "Reejecutar auditor y comparar resultados.", "Consultor / Cliente", "Reporte post-remediación."),
    ]
    for phase, activity, owner, evidence in workflow:
        cells = workflow_table.add_row().cells
        set_cell_text(cells[0], phase, bold=True, color=CYAN, size=8.5)
        set_cell_text(cells[1], activity, size=8.5)
        set_cell_text(cells[2], owner, size=8.5)
        set_cell_text(cells[3], evidence, size=8.5)
    style_table(workflow_table)

    add_heading(document, "12. Pruebas realizadas", 1)
    document.add_paragraph("La implementación fue validada con las siguientes pruebas:")
    tests_table = document.add_table(rows=1, cols=3)
    for cell, text in zip(tests_table.rows[0].cells, ["Prueba", "Resultado", "Alcance"]):
        set_cell_text(cell, text, bold=True, size=9)
    tests = [
        ("bash -n audit_vulnerabilities.sh", "PASS", "Validación sintáctica Bash."),
        ("tests/smoke_test.sh", "PASS", "Scripts, YAML y estructura del proyecto."),
        ("python -m pytest tests/ -q", "12 passed", "Pruebas unitarias de roles."),
        ("tests/test_audit_vulnerabilities.sh", "PASS", "Ejecución modular, JSON y HTML."),
        ("Auditoría auth,ssh", "7 controles / 93%", "Prueba funcional en entorno local de prueba."),
    ]
    for test, result, scope in tests:
        cells = tests_table.add_row().cells
        set_cell_text(cells[0], test, bold=True, size=8.5)
        set_cell_text(cells[1], result, bold=True, color=GREEN if "PASS" in result or "passed" in result else CYAN, size=8.5)
        set_cell_text(cells[2], scope, size=8.5)
    style_table(tests_table)
    add_callout(
        document,
        "Limitación de la prueba local",
        "La prueba realizada en el entorno de desarrollo no sustituye una auditoría sobre servidores Linux productivos. El resultado definitivo debe obtenerse ejecutando el script en cada activo autorizado.",
        fill="FFF4E5",
        title_color=ORANGE,
    )

    add_heading(document, "13. Consideraciones de seguridad", 1)
    for item in [
        "No almacenar los reportes en repositorios públicos ni enviarlos sin protección.",
        "Revisar la evidencia antes de compartirla: puede incluir nombres de servicios, sockets, rutas y configuraciones internas.",
        "No aplicar automáticamente las remediaciones sugeridas sin validar dependencias de la aplicación.",
        "Realizar una copia de seguridad y registrar el cambio antes de endurecer SSH, firewall o autenticación.",
        "Comparar el reporte pre-remediación con el reporte post-remediación para medir la mejora real.",
        "Documentar excepciones aprobadas por el cliente para evitar falsos positivos recurrentes.",
    ]:
        add_bullet(document, item)

    add_heading(document, "14. Próximas mejoras recomendadas", 1)
    for item in [
        "Añadir soporte de importación de múltiples JSON para tendencias históricas.",
        "Incorporar exportación CSV y PDF para entregables ejecutivos.",
        "Agregar una matriz de riesgo por activo y unidad de negocio.",
        "Integrar el resultado con Ansible para remediación controlada por tags.",
        "Agregar controles específicos para contenedores, Docker, Kubernetes y cloud.",
        "Implementar firma o hash de reportes para asegurar integridad de evidencia.",
    ]:
        add_bullet(document, item)

    add_heading(document, "15. Referencia rápida", 1)
    add_code(document, "# Ayuda\nsudo bash scripts/bash/audit_vulnerabilities.sh --help\n\n# Auditoría completa\nsudo bash scripts/bash/audit_vulnerabilities.sh --modules all --client \"Cliente\" --output-dir ./reports/cliente\n\n# Auditoría modular\nsudo bash scripts/bash/audit_vulnerabilities.sh --modules auth,ssh,network --output-dir ./reports/red\n\n# Abrir dashboard\nxdg-open ./reports/cliente/client_dashboard.html")

    document.add_paragraph()
    closing = document.add_paragraph()
    closing.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = closing.add_run("Fin del documento")
    run.bold = True
    run.font.color.rgb = RGBColor.from_string(NAVY)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build_document()
