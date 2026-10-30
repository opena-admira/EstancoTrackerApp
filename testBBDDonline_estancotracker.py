import requests
import json
import csv
from io import StringIO

# Sustituye esto por tu clave de la API de Google Cloud
API_KEY = "AIzaSyCDBuHs5OPkOZTK6W5FG4ceqfFdn7XJfaA"

# URL modificada para forzar la descarga en formato CSV
URL_GOOGLE_SHEETS = "https://docs.google.com/spreadsheets/d/1ajQUyT_wT-nu8HykaughBzHrFed-YLdN7jTaNcueaIA/export?format=csv&gid=1095289606"

# ==========================================
# EL PUENTE DE DATOS (Google Sheets Online)
# ==========================================
def cargar_base_datos_online(url):
    """Descarga el archivo CSV desde Google Sheets y analiza la comunicación real"""
    print("[INFO] Descargando base de datos en tiempo real desde Google Sheets...")
    
    base_datos = {}
    try:
        response = requests.get(url)
        
        # --- NUEVO: DEBUG DE COMUNICACIÓN REAL ---
        print(f"[DEBUG] Código de respuesta HTTP de Google: {response.status_code}")
        
        # Si Google devuelve código HTML (una página web) en lugar de texto plano, el documento está bloqueado.
        tipo_contenido = response.headers.get('Content-Type', '')
        if 'text/html' in tipo_contenido:
            print("\n" + "!"*60)
            print("[ERROR CRÍTICO DE PERMISOS DETECTADO]")
            print("Google ha devuelto una página web de inicio de sesión en lugar del archivo CSV.")
            print("Esto significa que el enlace está en modo 'Restringido'.")
            print("Solución: Ve al Sheet > Compartir > Cambia a 'Cualquier persona con el enlace'.")
            print("!"*60 + "\n")
            return None
            
        response.raise_for_status() 
        response.encoding = 'utf-8'
        
        archivo_virtual = StringIO(response.text)
        lector = csv.DictReader(archivo_virtual, delimiter=',')
        
        cabeceras = lector.fieldnames
        if cabeceras and 'Nombre Estanco' not in cabeceras:
            print(f"[ERROR] No se detectó la columna 'Nombre Estanco'.")
            print(f"[DEBUG] Esto es lo que Python está leyendo en la primera fila: {cabeceras}")
            return None
            
        for fila in lector:
            if not fila.get('Nombre Estanco'):
                continue
                
            id_estanco = str(fila['Nombre Estanco']).strip().upper()
            direccion_cruda = fila.get('Dirección estanco', fila.get('Direccion estanco', ''))
            cp_crudo = fila.get('Codigo Postal', fila.get('Código Postal', fila.get('CP', '')))

            base_datos[id_estanco] = {
                "direccion": str(direccion_cruda).strip(),
                "municipio": str(fila.get('Municipio', '')).strip(),
                "codPostal": str(cp_crudo).strip()
            }
            
        print(f"[OK] Base de datos cargada: {len(base_datos)} estancos registrados.\n")
        return base_datos
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error de conexión de red: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Error inesperado al procesar los datos: {e}")
        return None

# Cargamos la base de datos a la memoria una sola vez al arrancar el script
BASE_DE_DATOS_ESTANCOS = cargar_base_datos_online(URL_GOOGLE_SHEETS)

def traducir_id_a_direccion(id_completo):
    """Busca el ID en nuestra base de datos cargada y chiva posibles errores de escritura"""
    if BASE_DE_DATOS_ESTANCOS is None:
        print("[ERROR] La base de datos no está conectada. Revisa los mensajes de arriba.")
        return None
        
    id_busqueda = id_completo.upper().strip()
    
    if id_busqueda in BASE_DE_DATOS_ESTANCOS:
        return BASE_DE_DATOS_ESTANCOS[id_busqueda]
    else:
        # --- NUEVO: MODO DETECTIVE ---
        print(f"\n[DEBUG] No hay coincidencia exacta para '{id_busqueda}'.")
        print("[DEBUG] Buscando variaciones similares en el documento...")
        
        # Cogemos la primera palabra de lo que has escrito (ej. "ABECHUCO") y buscamos similitudes
        primera_palabra = id_busqueda.split('-')[0] if '-' in id_busqueda else id_busqueda.split(' ')[0]
        coincidencias = [id_csv for id_csv in BASE_DE_DATOS_ESTANCOS.keys() if primera_palabra in id_csv]
        
        if coincidencias:
            print(f"[DEBUG] ¿Querías decir alguno de estos?")
            for c in coincidencias:
                print(f"   -> '{c}'")
        else:
            print(f"[DEBUG] No hay NINGÚN registro en tu Sheet que contenga la palabra '{primera_palabra}'.")
            
        return None

# ==========================================
# LA BÚSQUEDA EN GOOGLE PLACES API (NEW)
# ==========================================
def ejecutar_estancotracker(id_completo):
    print(f"\n[INFO] Iniciando rastreo para: Nombre Estanco {id_completo.upper()}...")
    
    # 1. TRADUCCIÓN: Pasamos de ID a Dirección Física consultando el CSV online
    datos_reales = traducir_id_a_direccion(id_completo)
    
    if not datos_reales:
        print(f"[ERROR] El Nombre Estanco '{id_completo}' no existe en la base de datos de Google Sheets.")
        return

    direccion = datos_reales['direccion']
    municipio = datos_reales['municipio']
    codPostal = datos_reales['codPostal']
    print(f"[OK] Nombre Estanco localizado. Buscando en Google: '{direccion}, {codPostal} {municipio}'")
    
    # 2. BÚSQUEDA EN GOOGLE: Usamos la dirección exacta y el municipio
    url = "https://places.googleapis.com/v1/places:searchText"
    
    payload = {
        "textQuery": f"Estanco {direccion}, {codPostal} {municipio}".strip(),
        "languageCode": "es"
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.businessStatus,places.nationalPhoneNumber,places.regularOpeningHours,places.reviews,places.googleMapsUri"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    
    if "error" in data:
        print(f"[ERROR] API de Google: {data['error'].get('message')}")
        return
        
    lugares = data.get("places", [])
    
    if not lugares:
        print(f"[ERROR] Google no ha encontrado ningún negocio en '{direccion}, {codPostal} {municipio}'.")
        return
        
    estanco = lugares[0]
    
    nombre = estanco.get("displayName", {}).get("text", "Nombre no disponible")
    url_maps = estanco.get("googleMapsUri", "Enlace no disponible")
    telefono = estanco.get("nationalPhoneNumber", "Dato no disponible")
    
    estado_raw = estanco.get("businessStatus", "UNKNOWN")
    estados_es = {
        "OPERATIONAL": "Abierto / Operativo",
        "CLOSED_TEMPORARILY": "Cerrado temporalmente",
        "CLOSED_PERMANENTLY": "Cerrado permanentemente"
    }
    estado = estados_es.get(estado_raw, "Estado no disponible")
    
    horarios_list = estanco.get("regularOpeningHours", {}).get("weekdayDescriptions", [])
    horarios = "\n    ".join(horarios_list) if horarios_list else "Dato no disponible"
        
    reseñas_texto = []
    for review in estanco.get("reviews", [])[:5]:
        puntuacion = review.get("rating", "-")
        texto = review.get("text", {}).get("text", "").strip()
        texto_limpio = " ".join(texto.split())
        if texto_limpio:
            reseñas_texto.append(f"Puntuación {puntuacion}/5: {texto_limpio[:120]}...")
            
    if not reseñas_texto:
        reseñas_texto = ["Sin reseñas textuales suficientes para analizar."]

    # 3. RESULTADO FINAL
    print("\n" + "="*60)
    print(f"REPORTE EXACTO: {nombre} (ID: {id_completo.upper()})")
    print("="*60)
    print(f"Dirección:   {direccion}, {codPostal} {municipio}")
    print(f"Enlace Maps: {url_maps}")
    print(f"Estado:      {estado}")
    print(f"Teléfono:    {telefono}")
    print(f"Horarios:\n    {horarios}")
    print("Muestra de Reseñas:")
    for r in reseñas_texto:
        print(f"    - {r}")
    print("="*60 + "\n")

# ==========================================
# INTERFAZ INTERACTIVA DE CONSOLA
# ==========================================
if __name__ == "__main__":
    print("="*60)
    print("     BIENVENIDO A ESTANCOTRACKER (NUBE)")
    print("="*60)
    print("Instrucciones: Introduce el Nombre del estanco (ej. MADRID-12 o ALOVERA)")
    print("Escribe 'salir' en cualquier momento para cerrar el programa.\n")
    
    while True:
        try:
            # Pedimos la entrada al usuario
            entrada = input("👉 Introduce el Nombre del estanco: ").strip()
            
            # Condición de salida
            if entrada.lower() in ['salir', 'exit', 'quit']:
                print("\n[INFO] Cerrando EstancoTracker. ¡Hasta pronto!")
                break
            
            if not entrada:
                continue
            
            # Ejecutamos con el texto introducido
            ejecutar_estancotracker(entrada)
            
        except KeyboardInterrupt:
            # Permite salir limpiamente si el usuario pulsa Ctrl+C
            print("\n[INFO] Cierre forzado. ¡Hasta pronto!")
            break
        except Exception as e:
            print(f"\n[ERROR] Ha ocurrido un error inesperado: {e}")