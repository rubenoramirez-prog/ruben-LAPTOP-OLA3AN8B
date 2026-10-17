# CLAUDE.md — Proyecto Ruben Ramírez

Este documento sirve como la "constitución" y guía de contexto para Claude Code en todos los proyectos de Ruben Omar Ramírez Gutiérrez.

## 👤 Perfil del Usuario
- **Nombre:** Ruben Omar Ramírez Gutiérrez (Coach Ruben Ramírez).
- **Profesión:** Ingeniero en Computación (UNAM) y Coach de Running.
- **Expertise TI:** Infraestructura empresarial (L3), IBM AIX, RHEL, Nube Híbrida, Terraform, Ansible, Python/Bash.
- **Estilo de Trabajo:** Remoto, basado en objetivos (SLAs/KPIs), prefiere automatización agentless (Ansible).

## 🛠️ Reglas de Desarrollo y Estándares Técnicos

### Arquitectura y Código
- **Arquitectura Hexagonal (No Negociable):** Separación estricta de entidades, value objects, puertos y adaptadores. Los valores derivados nunca se persisten.
- **Pipeline de Desarrollo (SDD):** 
  1. DoD (Definition of Done) $\rightarrow$ 2. Arquitectura Hexagonal $\rightarrow$ 3. Modelado DDD $\rightarrow$ 4. Gherkin/BDD $\rightarrow$ 5. Roadmap.
- **Preferencias de Implementación:**
  - Parches incrementales (`str_replace`) sobre reescrituras completas.
  - Ejecución de suite completa y *smoke tests* antes de finalizar cualquier entregable.
  - Entregas limpias (sin `__pycache__`, `.pytest_cache`).
- **Stack Tecnológico Principal:** Flutter/Dart, Python (Click, Cryptography, FastAPI, Pytest), React, SQLite/SQLCipher.

### Guardrails de Calidad (L3 Standard)
- **Seguridad:** Todo script (Bash/Python) debe incluir manejo de errores robusto, validación de inputs y seguir el principio de *Least Privilege*.
- **Infraestructura:** En Terraform/Ansible, priorizar la idempotencia y la modularidad absoluta.
- **Testing:** Tarea no terminada sin un caso de prueba (pytest/Playwright) que valide tanto el camino feliz como el flujo de error.

### Design System (Apps HTML/Coaching)
- **Formato:** Un solo archivo HTML autocontenido (JS vanilla o Tailwind + Chart.js).
- **Estética:** "Modo Pista" (Azul marino/carbón).
  - Ámbar: Fuerza.
  - Verde azulado: Carrera.
- **Tipografías:** Oswald (Títulos), Inter (Texto), JetBrains Mono (Métricas).
- **Funcionalidades:** Persistencia en `localStorage`, export/import JSON, barras de progreso, SVG personalizados.

## 🏃 Práctica de Coaching ("A Tu Marca")
- **Público:** Adultos 35+ sedentarios o principiantes.
- **Tono:** Profesional, motivador pero realista, sin frases de "gurú".
- **Metodología:** Periodización (Base, Fuerza, Velocidad, Taper). Uso de RPE y diagnósticos fisiológicos (Cooper, VO2max).
- **Entregables:** Documentos Markdown $\rightarrow$ Apps HTML autocontenidas.

## ✍️ Comunicación y Tono por Audiencia

### Matriz de Estilo
- **Modo Corporativo (B2B/TCS):** Tono ejecutivo, basado en KPIs/SLAs, lenguaje técnico preciso, orientado a la eficiencia y cumplimiento.
- **Modo Coach (A Tu Marca):** Tono empático, motivador pero realista, lenguaje sencillo, enfocado en prevención de lesiones y superación personal.
- **Modo Freelance (Upwork/LinkedIn):** Tono persuasivo, orientado a resultados rápidos, resaltando ahorro de tiempo/dinero.

### Preferencias Generales
- **Idioma:** Bilingüe (ES/EN). Entregables usables de inmediato.
- **Tono General:** Empatía con franqueza; feedback directo, sin filtro, honestidad brutal sobre tiempos y posibilidades.
- **Formato:** Markdown estructurado (encabezados, tablas, bullets). No prosa densa.
- **Matemáticas:** LaTeX para fórmulas complejas (`$inline$`, `$$display$$`).
- **Ambigüedad:** Hacer preguntas de seguimiento expertas antes de proceder si el prompt es confuso.

## 🚀 Operaciones y Productización
### Pipeline de Lanzamiento Rápido
Para convertir ideas en micro-servicios rentables, seguir el flujo:
`Idea` $\rightarrow$ `One-Pager de Valor` $\rightarrow$ `MVP Técnico (Python/FastAPI)` $\rightarrow$ `Interfaz Simple (Tailwind)` $\rightarrow$ `Script de Demo`.

## 📂 Proyectos Activos (Referencia)
- **VaultKeeper:** Gestor de contraseñas local (AES-256-GCM).
- **Gym & Running Tracker:** Administración de gimnasio + seguimiento (FastAPI Hexagonal).
- **Runners Sin Edad:** Membresía coaching digital (Nicho 35+).
- **Auditoría Linux:** Microservicio de hardening (CIS Benchmark).
