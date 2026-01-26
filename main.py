import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# --- CONFIGURACIÓN DE PERMISOS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
DB_NAME = "move_travel.db"

def iniciar_db():
    """Crea la tabla de viajes si no existe y carga datos de prueba"""
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
    
    # Si la tabla está vacía, agregamos los viajes de prueba automáticamente
    c.execute('SELECT count(*) FROM viajes')
    cantidad = c.fetchone()[0]
    if cantidad == 0:
        viajes_iniciales = [
            ("Camboriú", "Brasil", 450.00, 7, False, "Viaje clásico en bus.", "https://images.unsplash.com/photo-1540206351-d6465b3ac5c1?w=500"),
            ("Punta Cana", "República Dominicana", 1200.50, 9, True, "All inclusive caribeño.", "https://images.unsplash.com/photo-1614312385003-dFb6d6e4a3b1?w=500"),
            ("Bariloche", "Argentina", 850.00, 6, True, "Nieve y chocolate.", "https://images.unsplash.com/photo-1612277685652-32961d6bc0cc?w=500"),
            ("Río de Janeiro", "Brasil", 900.00, 5, True, "Carnaval y playa.", "https://images.unsplash.com/photo-1483729558449-99ef09a8c325?w=500")
        ]
        c.executemany('INSERT INTO viajes (destino, pais, precio_usd, duracion_dias, incluye_aereo, descripcion, imagen_url) VALUES (?, ?, ?, ?, ?, ?, ?)', viajes_iniciales)
        conn.commit()
        print("Base de datos inicializada con datos de prueba.")
    
    conn.close()

# Ejecutamos esto al arrancar el programa
iniciar_db()

# --- MODELO DE DATOS (Pydantic) ---
class Viaje(BaseModel):
    id: Optional[int] = None
    destino: str
    pais: str
    precio_usd: float
    duracion_dias: int
    incluye_aereo: bool
    descripcion: str
    imagen_url: Optional[str] = "https://via.placeholder.com/400"

# --- RUTAS DE LA API ---

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Para que los resultados parezcan diccionarios
    return conn

@app.get("/")
def home():
    return {"mensaje": "API Move Travel con SQLite - Datos Persistentes 💾"}

@app.get("/viajes", response_model=List[Viaje])
def obtener_viajes(pais: Optional[str] = None, precio_max: Optional[float] = None):
    # --- AGREGA ESTE PRINT PARA VER EL TRUCO EN LA PANTALLA NEGRA ---
    print(f"🔎 Buscando: Pais/Destino='{pais}' - Precio='{precio_max}'") 
   

    conn = get_db_connection()
    
    query = "SELECT * FROM viajes WHERE 1=1"
    params = []

    if pais:
        # AQUI ESTA EL CAMBIO: 
        # Usamos "LIKE" y "%" para buscar texto parcial en AMBOS campos (Destino O País)
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

@app.post("/viajes", response_model=Viaje)
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

@app.delete("/viajes/{viaje_id}")
def borrar_viaje(viaje_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM viajes WHERE id = ?", (viaje_id,))
    conn.commit()
    filas_borradas = c.rowcount
    conn.close()

    if filas_borradas == 0:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    
    return {"mensaje": "Viaje eliminado correctamente"}