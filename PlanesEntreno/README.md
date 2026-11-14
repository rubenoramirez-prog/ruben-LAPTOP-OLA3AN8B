# Planes de Entrenamiento - A Tu Marca

Suite de herramientas de coaching para corredores 35+ por Coach Ruben Ramírez.

## 🏃 Herramientas Disponibles

### 1. Test de Cooper + Diagnóstico VO2max
**Archivo:** `cooper-vo2max.html`

Calculadora que estima el VO2max basado en la distancia recorrida en 12 minutos, categorizando el nivel de fitness y proporcionando zonas de ritmo recomendadas.

**Características:**
- Cálculo de VO2max (fórmula de Cooper)
- Categorización por edad y género
- Zonas de ritmo personalizadas
- Historial de pruebas con localStorage

### 2. Generador de Plan Semanal
**Archivo:** `plan-semanal.html`

Genera planes de entrenamiento semanales basados en periodización (Base/Fuerza/Velocidad/Taper).

**Características:**
- Periodización estructurada
- Sesiones adaptadas a días disponibles
- Control de RPE por sesión
- Export/Import JSON

### 3. Bitácora de Entrenamiento
**Archivo:** `bitacora.html`

Sistema de registro completo de entrenamientos con análisis visual.

**Características:**
- Registro de sesiones (tipo, duración, distancia, RPE)
- Gráficos semanales/mensuales (Chart.js)
- Estadísticas de volumen y progreso
- Persistencia localStorage + Export/Import

### 4. Calculadora de Ritmos por Edad
**Archivo:** `ritmos-edad.html`

Calculadora de zonas de ritmo ajustadas por edad para objetivos realistas en corredores 35+.

**Características:**
- Ajuste por edad y nivel
- Ritmos para 5K, 10K, 21K
- Zonas de frecuencia cardíaca
- Planificación de objetivo de carrera

## 🎨 Design System

**Modo Pista:**
- Paleta: Azul marino (#1e3a5f), Carbón (#2a2a2a), Ámbar (#f59e0b), Verde azulado (#14b8a6)
- Tipografía: Oswald (títulos), Inter (texto), JetBrains Mono (métricas)
- Responsive, modo oscuro automático
- Un solo archivo HTML autocontenido por herramienta

## 📦 Uso

Cada herramienta es un archivo HTML independiente. Simplemente:
1. Abre el archivo en cualquier navegador moderno
2. Los datos se guardan automáticamente en localStorage
3. Exporta/importa JSON cuando necesites backup

## 🚀 Stack Técnico

- HTML5 + CSS3 (Tailwind CDN)
- JavaScript Vanilla (ES6+)
- Chart.js 4.x (para visualizaciones)
- localStorage para persistencia
- Diseño mobile-first

---

**Desarrollado por:** Coach Ruben Ramírez  
**Metodología:** A Tu Marca - Coaching para Corredores 35+  
**Versión:** 1.0.0 (2026-11-12)
