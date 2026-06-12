import json
import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar variables de entorno
load_dotenv()

DB_FILE = "bonos.json"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def migrate():
    # Validar que no sean marcadores de posición
    if not SUPABASE_URL or "your-project-id" in SUPABASE_URL:
        print("[-] ERROR: Configura SUPABASE_URL en el archivo backend/.env antes de ejecutar la migración.")
        return
    if not SUPABASE_KEY or "your-supabase-service-role" in SUPABASE_KEY:
        print("[-] ERROR: Configura SUPABASE_KEY en el archivo backend/.env antes de ejecutar la migración.")
        return

    if not os.path.exists(DB_FILE):
        print(f"[-] ERROR: No se encontró el archivo local {DB_FILE} para migrar.")
        return

    print("[+] Conectando a Supabase...")
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"[-] ERROR al conectar a Supabase: {e}")
        return

    print(f"[+] Leyendo datos locales de {DB_FILE}...")
    with open(DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        print("[*] No hay bonos para migrar en el archivo local.")
        return

    print(f"[+] Migrando {len(data)} bono(s) a Supabase...")
    for bono_id, info in data.items():
        # Formatear la fecha a ISO timestamp para Supabase
        fecha_compra_str = info.get("fecha_compra", "")
        try:
            fecha_dt = datetime.strptime(fecha_compra_str, "%d/%m/%Y %H:%M")
            fecha_compra_iso = fecha_dt.isoformat()
        except Exception:
            fecha_compra_iso = datetime.now().isoformat()

        # Preparar registro
        record = {
            "id": bono_id,
            "cliente": info.get("cliente", ""),
            "telefono": info.get("telefono", None),
            "usos_totales": info.get("usos_totales", 1),
            "usos_restantes": info.get("usos_restantes", 1),
            "fecha_compra": fecha_compra_iso,
            "historial": info.get("historial", [])
        }

        print(f"[*] Insertando bono {bono_id} ({record['cliente']})...")
        try:
            # Insertar en Supabase (upsert para evitar duplicados si se vuelve a correr)
            response = supabase.table("bonos").upsert(record).execute()
            print(f"[+] Bono {bono_id} migrado correctamente.")
        except Exception as e:
            print(f"[-] Error al migrar bono {bono_id}: {e}")
            print("[!] Asegúrate de haber creado la tabla 'bonos' en Supabase.")
            print("[!] Estructura SQL requerida en Supabase:")
            print("""
            CREATE TABLE IF NOT EXISTS bonos (
                id VARCHAR(12) PRIMARY KEY,
                cliente VARCHAR(255) NOT NULL,
                telefono VARCHAR(50),
                usos_totales INTEGER NOT NULL DEFAULT 1,
                usos_restantes INTEGER NOT NULL DEFAULT 1,
                fecha_compra TIMESTAMPTZ DEFAULT NOW() NOT NULL,
                historial JSONB NOT NULL DEFAULT '[]'::jsonb
            );
            """)
            return

    print("[+] ¡Migración completada con éxito!")

if __name__ == "__main__":
    migrate()
