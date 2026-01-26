import sqlite3
import secrets # Librería para comparar contraseñas de forma segura
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials # Herramientas de seguridad
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# --- CONFIGURACIÓN DE SEGURIDAD ---
security = HTTPBasic()

# Define aquí tu usuario y contraseña MAESTROS
USUARIO_ADMIN = "admin"
PASSWORD_ADMIN = "viajes2026"  # ¡Cámbialo por lo que quieras!

def validar_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Esta función es el PORTERO. Verifica si las credenciales son correctas."""
    user_ok = secrets.compare_digest(credentials.username, USUARIO_ADMIN)
    pass_ok = secrets.compare_digest(credentials.password, PASSWORD_ADMIN)
    
    if not (user_ok and pass_ok):
        # Si falla, lanza un error 401 (No autorizado) y pide login de nuevo
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# --- CONFIGURACIÓN DE PERMISOS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- BASE DE DATOS ---
DB_NAME = "move_travel.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def iniciar_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS viajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destino TEXT NOT NULL,
            pais TEXT NOT NULL,
            precio_usd REAL NOT NULL,
            duracion_dias INTEGER NOT NULL,
            incluye_aereo BOOLEAN NOT NULL,
            descripcion TEXT,
            imagen_url TEXT
        )
    ''')
    conn.commit()
    conn.close()

iniciar_db()

# --- MODELO DE DATOS ---
class Viaje(BaseModel):
    id: Optional[int] = None
    destino: str
    pais: str
    precio_usd: float
    duracion_dias: int
    incluye_aereo: bool
    descripcion: str
    imagen_url: Optional[str] = "https://via.placeholder.com/400"

# --- RUTAS (ENDPOINTS) ---

# 1. RUTA PÚBLICA (Cualquiera puede entrar)
@app.get("/", response_class=HTMLResponse)
def home():
    with open("index.html", "r", encoding="utf-8") as f: # O "inicio.html" si le cambiaste el nombre
        return f.read()

# 2. RUTA PROTEGIDA: EL PANEL DE ADMIN (Solo con contraseña)
# Fíjate en el "dependencies=[Depends(validar_admin)]" -> Eso es el candado 🔒
@app.get("/admin", response_class=HTMLResponse, dependencies=[Depends(validar_admin)])
def admin():
    with open("admin.html", "r", encoding="utf-8") as f: # O "panel.html"
        return f.read()

# 3. RUTA PÚBLICA: VER VIAJES (Los clientes deben poder ver esto sin clave)
@app.get("/viajes", response_class=List[Viaje]) # Quitamos response_model temporalmente para evitar conflictos de tipo simples
def obtener_viajes(pais: Optional[str] = None, precio_max: Optional[float] = None):
    conn = get_db_connection()
    query = "SELECT * FROM viajes WHERE 1=1"
    params = []

    if pais:
        query += " AND (lower(pais) LIKE ? OR lower(destino) LIKE ?)"
        termino = f"%{pais.lower()}%"
        params.append(termino)
        params.append(termino)
    
    if precio_max:
        query += " AND precio_usd <= ?"
        params.append(precio_max)

    cursor = conn.execute(query, params)
    viajes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return viajes

# 4. RUTA PROTEGIDA: CREAR VIAJE 🔒
@app.post("/viajes", dependencies=[Depends(validar_admin)])
def crear_viaje(viaje: Viaje):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO viajes (destino, pais, precio_usd, duracion_dias, incluye_aereo, descripcion, imagen_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (viaje.destino, viaje.pais, viaje.precio_usd, viaje.duracion_dias, viaje.incluye_aereo, viaje.descripcion, viaje.imagen_url)
    )
    conn.commit()
    nuevo_id = c.lastrowid
    conn.close()
    viaje.id = nuevo_id
    return viaje

# 5. RUTA PROTEGIDA: BORRAR VIAJE 🔒
@app.delete("/viajes/{viaje_id}", dependencies=[Depends(validar_admin)])
def borrar_viaje(viaje_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM viajes WHERE id = ?", (viaje_id,))
    conn.commit()
    filas = c.rowcount
    conn.close()

    if filas == 0:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    
    return {"mensaje": "Eliminado"}


#    .\venv\Scripts\activate
#    uvicorn main:app --reload