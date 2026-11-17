# WhatsApp Bot — Clínica de Masajes Holísticos ("Sintonía Zen")

> Bot de atención al cliente y gestión de citas por WhatsApp Cloud API.  
> Desarrollado en Python (FastAPI) bajo Arquitectura Hexagonal.

## 🌿 Funcionalidades
1. **Menú Interactivo:** Saludo, catálogo de masajes (Descontracturante, Aromaterapia, Piedras Calientes, Shiatsu), precios y duración.
2. **Asistente de Citas:** Flujo conversacional paso a paso para agendar, verificar disponibilidad y confirmar citas.
3. **Persistencia Local:** Base de datos SQLite para clientes, servicios y citas.

## 📁 Estructura Hexagonal
```
whatsapp-massage-bot/
├── requirements.txt
├── app/
│   ├── domain/           # Entidades y Reglas de Negocio (Cita, Masaje, Cliente)
│   ├── ports/            # Interfaces / Puertos de entrada y salida
│   ├── adapters/         # Adaptadores (FastAPI webhook, SQLite, WhatsApp API)
│   └── application/      # Casos de uso / Lógica de aplicación
└── main.py               # Punto de entrada FastAPI
```
