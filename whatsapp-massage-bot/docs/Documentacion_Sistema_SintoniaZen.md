# Documentación Técnica y Funcional — Sistema de Atención y Citas por WhatsApp ("Sintonía Zen")

> **Cliente:** Clínica de Masajes Holísticos "Sintonía Zen"  
> **Arquitectura:** Hexagonal (Python / FastAPI / SQLite / WhatsApp Cloud API)  
> **Autor:** Ruben Omar Ramírez Gutiérrez (Coach Ruben Ramírez)  
> **Fecha de Actualización:** 2026-11-17  

---

## 1. 🎯 Resumen Ejecutivo
El sistema **Sintonía Zen** es una solución automatizada de atención al cliente y gestión de citas operada directamente a través de **WhatsApp Business (Meta Cloud API)**, complementada con un **Panel de Administración Web** en tiempo real. Su propósito es automatizar la recepción de solicitudes, la presentación del catálogo de masajes holísticos, la selección de horarios y la confirmación de citas, reduciendo la fricción operativa y mejorando la experiencia del paciente.

---

## 2. 🏛️ Arquitectura del Sistema (Hexagonal)
El proyecto está construido bajo el principio estricto de **Arquitectura Hexagonal**, garantizando el desacoplamiento total entre las reglas de negocio, los adaptadores de entrada (Webhook de WhatsApp, Panel HTTP) y los adaptadores de salida (Base de datos SQLite, API de Meta).

```
whatsapp-massage-bot/
├── app/
│   ├── domain/           # Entidades puras y Modelos (Cita, Servicio, Sesión)
│   ├── ports/            # Definición de interfaces de comunicación
│   ├── adapters/         # Adaptadores externos (SQLite DB, WhatsApp Cloud API)
│   └── application/      # Casos de uso y Máquina de estados conversacional
├── admin/
│   └── index.html        # Panel de administración visual (Tailwind + Design System)
├── tests/
│   ├── test_api.py       # Pruebas de integración FastAPI / Webhook / Admin
│   └── test_bot.py       # Pruebas unitarias de flujo conversacional
├── main.py               # Servidor FastAPI y registro de rutas
└── README.md             # Guía de instalación y despliegue
```

---

## 3. 🌿 Catálogo de Servicios
El bot gestiona de forma automatizada los siguientes servicios holísticos:

| ID | Servicio | Duración | Inversión (MXN) | Descripción |
|----|----------|----------|-----------------|-------------|
| `s1` | Masaje Relajante / Sueco | 60 mins | $650 | Masaje suave con aceites esenciales para liberar tensión acumulada. |
| `s2` | Masaje Descontracturante | 60 mins | $800 | Presión media-alta enfocada en nudos musculares y espalda. |
| `s3` | Piedras Calientes (Basálticas) | 90 mins | $1,100 | Termoterapia profunda para relajación muscular total. |
| `s4` | Reflexología Podal & Holística | 45 mins | $500 | Estimulación de puntos reflejos en pies para equilibrar energía. |

---

## 4. 🤖 Flujo Conversacional del Bot (Asistente de Citas)
La máquina de estados gestiona interacciones personalizadas y robustas mediante comandos sencillos:

1. **Saludo / Menú Principal:**
   - El usuario escribe `hola`, `menu` o `inicio`.
   - El bot responde con el saludo institucional de *"Sintonía Zen"* y despliega el catálogo enumerado (1 al 4).
2. **Selección de Servicio:**
   - El usuario responde con el número de su preferencia (ej. `1`).
   - El sistema registra el servicio y solicita la fecha y hora deseada.
3. **Selección de Fecha y Hora:**
   - El usuario indica su disponibilidad (ej. `Mañana a las 5pm`).
   - El sistema almacena la fecha y solicita el nombre completo.
4. **Registro y Confirmación:**
   - El usuario ingresa su nombre (ej. `Carlos Gómez`).
   - El sistema almacena la cita en **SQLite** con estado `CONFIRMED` y genera un **Folio Único** (ej. `#1`), respondiendo con un resumen detallado y de confirmación.

---

## 5. 🎛️ Panel de Administración (`/admin`)
El panel web ofrece control operativo completo en tiempo real:
- **KPIs en Vivo:** Total histórico de citas, ingresos estimados en MXN (filtrando canceladas) y volumen de citas confirmadas.
- **Tabla de Citas & Clientes:** Visualización de folios, teléfonos de WhatsApp, servicios, horarios, precios y estados.
- **Acción Operativa:** Botones interactivos para marcar citas como **Completadas (✅)** o **Canceladas (❌)**.
- **Buscador Instantáneo:** Filtro en tiempo real por nombre de cliente o número de teléfono.

---

## 6. 🛠️ Stack Tecnológico & Calidad
- **Lenguaje:** Python 3.12+
- **Framework Web:** FastAPI (con Uvicorn ASGI)
- **Base de Datos:** SQLite (con inicialización automática y seed de servicios)
- **Frontend Admin:** HTML5 autocontenido con **Tailwind CSS** (Design System: *Modo Pista*, Oswald, Inter, JetBrains Mono)
- **Testing:** Pytest (100% verde, 6/6 pruebas superadas en validación de API, webhooks y máquina de estados).
- **Integración:** WhatsApp Business Cloud API (Meta Graph API) con verificación de webhook por token seguro.
