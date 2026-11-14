#!/usr/bin/env python3
"""
Simple HTTP Server para probar las herramientas de coaching localmente.

Uso:
    python test-server.py

Luego abre en tu navegador: http://localhost:8000
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 8000
DIRECTORY = Path(__file__).parent

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

print(f"🏃 Servidor de prueba A Tu Marca iniciado")
print(f"📂 Directorio: {DIRECTORY}")
print(f"🌐 Abre tu navegador en: http://localhost:{PORT}")
print(f"📊 Dashboard principal: http://localhost:{PORT}/index.html")
print(f"\n✅ Herramientas disponibles:")
print(f"   • http://localhost:{PORT}/cooper-vo2max.html")
print(f"   • http://localhost:{PORT}/plan-semanal.html")
print(f"   • http://localhost:{PORT}/bitacora.html")
print(f"   • http://localhost:{PORT}/ritmos-edad.html")
print(f"\nPresiona Ctrl+C para detener el servidor\n")

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor detenido")
