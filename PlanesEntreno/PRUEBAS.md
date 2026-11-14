# Guía de Prueba y Publicación - A Tu Marca

## 📋 Estado del Proyecto

✅ **5 Herramientas HTML Creadas:**
- `index.html` - Dashboard principal (28 KB)
- `cooper-vo2max.html` - Test de Cooper + VO2max (15 KB)
- `plan-semanal.html` - Generador de planes semanales (22 KB)
- `bitacora.html` - Bitácora con gráficos Chart.js (20 KB)
- `ritmos-edad.html` - Calculadora de ritmos ajustados por edad (16 KB)

✅ **Commiteado:** Commit `b12c796` con las 4 herramientas + README

## 🧪 Opción 1: Prueba Local (Inmediata)

### Método A: Servidor Python
```bash
cd C:\ProyectosIA\PlanesEntreno
python test-server.py
```

Luego abre en tu navegador:
- Dashboard: http://localhost:8000/index.html
- Cooper Test: http://localhost:8000/cooper-vo2max.html
- Plan Semanal: http://localhost:8000/plan-semanal.html
- Bitácora: http://localhost:8000/bitacora.html
- Ritmos: http://localhost:8000/ritmos-edad.html

### Método B: Abrir directamente
Haz doble clic en cualquier archivo `.html` desde el Explorador de Windows. Los enlaces entre páginas funcionarán automáticamente.

## 📤 Opción 2: Publicar como Artifacts (Requiere Login)

Para obtener URLs públicas compartibles en claude.ai:

1. **Configurar autenticación:**
   ```bash
   # Desactivar ANTHROPIC_AUTH_TOKEN temporal
   $env:ANTHROPIC_AUTH_TOKEN = ""
   
   # Login con cuenta claude.ai
   /login
   # Selecciona: "Claude account with subscription"
   ```

2. **Publicar los 5 artifacts:**
   - Puedes pedirme que publique cada herramienta
   - Obtendrás URLs permanentes tipo `claude.ai/artifact/{id}`
   - Perfectas para compartir con clientes

## ✅ Checklist de Pruebas

### Test de Cooper (`cooper-vo2max.html`)
- [ ] Ingresar: 2400m, 40 años, Hombre
- [ ] Verificar: VO2max ≈ 42.4, categoría "Promedio"
- [ ] Verificar: 5 zonas de ritmo generadas
- [ ] Guardar test y verificar historial

### Plan Semanal (`plan-semanal.html`)
- [ ] Seleccionar: Base, Intermedio, 40km/semana
- [ ] Marcar: Sábado y Domingo disponibles
- [ ] Verificar: Plan de 7 días con sesiones específicas
- [ ] Probar: Export JSON y copiar plan

### Bitácora (`bitacora.html`)
- [ ] Registrar sesión: Hoy, Carrera, 45min, 7.5km, RPE 7
- [ ] Verificar: Estadísticas 4 semanas actualizadas
- [ ] Verificar: Gráfico de volumen semanal visible
- [ ] Probar: Export/Import JSON

### Ritmos por Edad (`ritmos-edad.html`)
- [ ] Ingresar: 40 años, Hombre, Intermedio
- [ ] Recent: 10K en 55 minutos
- [ ] FC reposo: 60 lpm
- [ ] Verificar: Predicciones 5K/10K/21K + zonas + FC zones

### Dashboard (`index.html`)
- [ ] Verificar: 4 tarjetas clicables
- [ ] Click en cada herramienta → navegación correcta
- [ ] Responsive: probar en ventana estrecha (móvil)
- [ ] Dark mode: verificar cambio automático

## 🎨 Características Implementadas

### Design System "Modo Pista"
- ✅ Paleta: Navy/Amber/Teal/Carbón
- ✅ Tipografía: Oswald/Inter/JetBrains Mono
- ✅ Dark mode automático (prefers-color-scheme)
- ✅ Mobile-first responsive
- ✅ Safe-area insets para móviles

### Funcionalidad
- ✅ localStorage persistence (cada app guarda datos localmente)
- ✅ Export/Import JSON (backup y transferencia)
- ✅ Chart.js visualizations (Bitácora)
- ✅ Age grading calculations (Ritmos)
- ✅ Periodization templates (Plan Semanal)
- ✅ VO2max + HR zones (Cooper Test)

## 🚀 Próximos Pasos Sugeridos

1. **Probar localmente ahora** → Servidor Python o doble-clic
2. **Ajustar si es necesario** → Feedback visual/funcional
3. **Publicar como Artifacts** → URLs permanentes compartibles
4. **Integrar con tu práctica** → Usar con clientes reales
5. **Hosting permanente** (opcional):
   - GitHub Pages (gratuito, público)
   - Netlify/Vercel (gratuito, custom domain)
   - Tu propio servidor

## 📊 Uso con Clientes

### Flujo recomendado:
1. **Diagnóstico inicial:** Cooper Test → VO2max + categoría
2. **Planificación:** Plan Semanal → según fase actual
3. **Ejecución:** Cliente usa Bitácora para registrar sesiones
4. **Ajuste:** Ritmos por Edad para objetivos de carrera específicos

### Datos persistentes:
- Cada cliente abre las herramientas en su navegador
- Sus datos se guardan localmente (privacidad)
- Pueden exportar JSON para respaldo
- Pueden importar en otro dispositivo

---

**Creado:** 2026-11-12  
**Coach:** Ruben Ramírez  
**Metodología:** A Tu Marca - Corredores 35+
