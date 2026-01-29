import sqlite3
import secrets
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# --- SEGURIDAD ---
security = HTTPBasic()
USUARIO_ADMIN = "admin"
PASSWORD_ADMIN = "viajes2026"

def validar_admin(credentials: HTTPBasicCredentials = Depends(security)):
    is_user_ok = secrets.compare_digest(credentials.username, USUARIO_ADMIN)
    is_pass_ok = secrets.compare_digest(credentials.password, PASSWORD_ADMIN)
    if not (is_user_ok and is_pass_ok):
        raise HTTPException(status_code=401, detail="Incorrecto", headers={"WWW-Authenticate": "Basic"})
    return credentials.username

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
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
    c.execute('''CREATE TABLE IF NOT EXISTS viajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destino TEXT NOT NULL, pais TEXT NOT NULL, precio_usd REAL NOT NULL,
            duracion_dias INTEGER NOT NULL, incluye_aereo BOOLEAN NOT NULL,
            descripcion TEXT, imagen_url TEXT)''')
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

# --- RUTAS DE PÁGINAS WEB (HTML) ---

@app.get("/", response_class=HTMLResponse)
def home():
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f: return f.read()
    except FileNotFoundError: return "<h1>Error: Falta templates/index.html</h1>"

@app.get("/admin", response_class=HTMLResponse, dependencies=[Depends(validar_admin)])
def admin():
    try:
        with open("templates/admin.html", "r", encoding="utf-8") as f: return f.read()
    except FileNotFoundError: return "<h1>Error: Falta templates/admin.html</h1>"

# 👇 ESTA ES LA RUTA NUEVA PARA VER DETALLES 👇
@app.get("/detalle", response_class=HTMLResponse)
def ver_detalle():
    try:
        with open("templates/detalle.html", "r", encoding="utf-8") as f: return f.read()
    except FileNotFoundError: return "<h1>Error: Falta templates/detalle.html</h1>"

# --- RUTAS DE DATOS (API) ---

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

# 👇 ESTA ES LA API NUEVA PARA OBTENER 1 SOLO VIAJE 👇
@app.get("/viajes/{viaje_id}")
def obtener_un_viaje(viaje_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM viajes WHERE id = ?", (viaje_id,))
    viaje = c.fetchone()
    conn.close()
    if viaje is None:
        raise HTTPException(status_code=404, detail="No encontrado")
    return dict(viaje)

@app.post("/viajes", dependencies=[Depends(validar_admin)])
def crear_viaje(viaje: Viaje):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO viajes (destino, pais, precio_usd, duracion_dias, incluye_aereo, descripcion, imagen_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (viaje.destino, viaje.pais, viaje.precio_usd, viaje.duracion_dias, viaje.incluye_aereo, viaje.descripcion, viaje.imagen_url))
    conn.commit()
    viaje.id = c.lastrowid
    conn.close()
    return viaje

@app.put("/viajes/{viaje_id}", dependencies=[Depends(validar_admin)])
def actualizar_viaje(viaje_id: int, viaje_actualizado: Viaje):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE viajes SET destino=?, pais=?, precio_usd=?, duracion_dias=?, incluye_aereo=?, descripcion=?, imagen_url=? WHERE id=?", 
        (viaje_actualizado.destino, viaje_actualizado.pais, viaje_actualizado.precio_usd, viaje_actualizado.duracion_dias, viaje_actualizado.incluye_aereo, 
         viaje_actualizado.descripcion, viaje_actualizado.imagen_url, viaje_id))
    conn.commit()
    conn.close()
    return {"mensaje": "Actualizado"}

@app.delete("/viajes/{viaje_id}", dependencies=[Depends(validar_admin)])
def borrar_viaje(viaje_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM viajes WHERE id = ?", (viaje_id,))
    conn.commit()
    conn.close()
    return {"mensaje": "Eliminado"}

#    .\venv\Scripts\activate
#    uvicorn main:app --reload