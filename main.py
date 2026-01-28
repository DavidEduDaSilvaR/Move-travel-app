import sqlite3
import secrets
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# --- 1. SEGURIDAD ---
security = HTTPBasic()
USUARIO_ADMIN = "admin"
PASSWORD_ADMIN = "viajes2026"

def validar_admin(credentials: HTTPBasicCredentials = Depends(security)):
    is_user_ok = secrets.compare_digest(credentials.username, USUARIO_ADMIN)
    is_pass_ok = secrets.compare_digest(credentials.password, PASSWORD_ADMIN)
    
    if not (is_user_ok and is_pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# --- 2. CONFIGURACIÓN ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class Viaje(BaseModel):
    id: Optional[int] = None
    destino: str
    pais: str
    precio_usd: float
    duracion_dias: int
    incluye_aereo: bool
    descripcion: str
    imagen_url: Optional[str] = "https://via.placeholder.com/400"

# --- 3. RUTAS (PÁGINAS WEB) ---

@app.get("/", response_class=HTMLResponse)
def home():
    # Intenta abrir el archivo. Si falla, avisa en la terminal.
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Error: No encuentro el archivo index.html</h1>"

@app.get("/admin", response_class=HTMLResponse, dependencies=[Depends(validar_admin)])
def admin():
    try:
        with open("templates/admin.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Error: No encuentro el archivo admin.html</h1>"

# --- 4. RUTAS (API DE DATOS) ---

@app.get("/viajes")
def obtener_viajes(pais: Optional[str] = None, precio_max: Optional[float] = None):
    conn = get_db_connection()
    query = "SELECT * FROM viajes WHERE 1=1"
    params = []

    if pais:
        query += " AND (lower(pais) LIKE ? OR lower(destino) LIKE ?)"
        term = f"%{pais.lower()}%"
        params.extend([term, term])
    
    if precio_max:
        query += " AND precio_usd <= ?"
        params.append(precio_max)

    cursor = conn.execute(query, params)
    viajes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return viajes

@app.post("/viajes", dependencies=[Depends(validar_admin)])
def crear_viaje(viaje: Viaje):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO viajes (destino, pais, precio_usd, duracion_dias, incluye_aereo, descripcion, imagen_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (viaje.destino, viaje.pais, viaje.precio_usd, viaje.duracion_dias, viaje.incluye_aereo, viaje.descripcion, viaje.imagen_url)
    )
    conn.commit()
    viaje.id = c.lastrowid
    conn.close()
    return viaje

@app.put("/viajes/{viaje_id}", dependencies=[Depends(validar_admin)])
def actualizar_viaje(viaje_id: int, viaje_actualizado: Viaje):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute
#    .\venv\Scripts\activate
#    uvicorn main:app --reload