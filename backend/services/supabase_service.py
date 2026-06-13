from datetime import datetime
import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client

        clean_url = SUPABASE_URL.split("/rest/v1")[0].strip()
        supabase = create_client(clean_url, SUPABASE_KEY)
        print(f"[+] Supabase cliente iniciado correctamente en {clean_url}.")
    except Exception as e:
        print(f"[-] Error al iniciar cliente de Supabase: {e}")
else:
    print("[!] ADVERTENCIA: Supabase no está configurado o tiene valores por defecto en .env.")


def get_all_bonos():
    if supabase is None:
        print("[-] Error: Cliente Supabase no configurado.")
        return []
    try:
        response = supabase.table("bonos").select("*").execute()
        bonos = []
        for b in response.data:
            try:
                fecha_dt = datetime.fromisoformat(b["fecha_compra"].replace("Z", "+00:00"))
                fecha_str = fecha_dt.strftime("%d/%m/%Y %H:%M")
            except Exception:
                fecha_str = b["fecha_compra"]

            bonos.append({
                "id": b["id"],
                "cliente": b["cliente"],
                "telefono": b.get("telefono") or "",
                "usos_totales": b["usos_totales"],
                "usos_restantes": b["usos_restantes"],
                "fecha_compra": fecha_str,
                "usos_realizados": len(b.get("historial") or [])
            })

        try:
            bonos.sort(key=lambda x: datetime.strptime(x["fecha_compra"], "%d/%m/%Y %H:%M"), reverse=True)
        except Exception:
            bonos.sort(key=lambda x: x["fecha_compra"], reverse=True)

        return bonos
    except Exception as e:
        print(f"[-] Error al listar bonos en Supabase: {e}")
        return []


def get_bono(bono_id):
    if supabase is None:
        return None
    try:
        response = supabase.table("bonos").select("*").eq("id", bono_id).execute()
        if response.data:
            b = response.data[0]
            try:
                fecha_dt = datetime.fromisoformat(b["fecha_compra"].replace("Z", "+00:00"))
                b["fecha_compra"] = fecha_dt.strftime("%d/%m/%Y %H:%M")
            except Exception:
                pass
            if not b.get("historial"):
                b["historial"] = []
            return b
    except Exception as e:
        print(f"[-] Error al obtener bono {bono_id} de Supabase: {e}")
    return None


def create_bono_db(bono_id, cliente, telefono, usos, fecha_iso):
    if supabase is None:
        return False
    try:
        record = {
            "id": bono_id,
            "cliente": cliente,
            "telefono": telefono if telefono else None,
            "usos_totales": usos,
            "usos_restantes": usos,
            "fecha_compra": fecha_iso,
            "historial": []
        }
        supabase.table("bonos").insert(record).execute()
        return True
    except Exception as e:
        print(f"[-] Error al crear bono en Supabase: {e}")
        return False


def update_bono_usages(bono_id, nuevos_usos, historial):
    if supabase is None:
        return False
    try:
        supabase.table("bonos").update({
            "usos_restantes": nuevos_usos,
            "historial": historial
        }).eq("id", bono_id).execute()
        return True
    except Exception as e:
        print(f"[-] Error al actualizar bono {bono_id} en Supabase: {e}")
        return False
