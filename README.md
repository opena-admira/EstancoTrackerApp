# EstancoTrackerApp
Herramienta de interfaz de línea de comandos (CLI) desarrollada en Python para la localización y consulta de datos en tiempo real de expendedurías de tabaco y timbre (estancos) en España.

El sistema actúa como un puente entre una base de datos de concesiones (archivo CSV o Google Sheets) y la API de Google Places (New), traduciendo identificadores administrativos (ej. MADRID-012) en direcciones físicas exactas para extraer su estado operativo, horarios, teléfono, enlace a Maps y reseñas de clientes.

# 🚀 Características Principales
- Búsqueda Inteligente: Localiza establecimientos mediante su ID de concesión completo, simplificado o únicamente por municipio, ignorando errores de formato, espacios o mayúsculas/minúsculas.
- Integración con Google Places API (New): Utiliza búsquedas ultra-precisas combinando Dirección + Código Postal + Municipio para evitar falsos positivos y "alucinaciones" de ubicación.
- Soporte de Datos Flexible: Compatible con bases de datos locales (estancos.csv) o sincronización en la nube mediante enlaces de Google Sheets exportados a CSV.
- Prevención de Errores de Codificación: Resuelve automáticamente problemas de separadores (; vs ,), caracteres fantasma (BOM) y codificación ANSI/UTF-8 generados habitualmente por Excel.
- Consola Interactiva: Interfaz de terminal de uso continuo que permite consultas consecutivas sin necesidad de reiniciar el script.

# 📋 Requisitos del Sistema
- Python 3.x
- Una clave de API de Google Cloud con la Places API (New) habilitada.
- Librerías de Python: requests

# ⚙️ Instalación y Configuración
1. Clonar el repositorio:
`Bash
git clone https://github.com/tu-usuario/EstancoTracker.git
cd EstancoTracker`

2. Instalar dependencias:
Bash
pip install -r requirements.txt

3. Configurar la Clave de API:
Por seguridad, la API Key no debe incluirse en el código fuente. Configura tu variable de entorno en tu sistema o terminal antes de ejecutar:
- Windows (CMD): set GOOGLE_API_KEY="tu_clave_aqui"
- Windows (PowerShell): $env:GOOGLE_API_KEY="tu_clave_aqui"
- Mac/Linux: export GOOGLE_API_KEY="tu_clave_aqui"
