import os
import requests
import pyodbc
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# Database configuration
DB_SERVER = os.getenv("DB_SERVER", "localhost\\SQLEXPRESS")
DB_NAME = os.getenv("DB_NAME", "LibrosUyDB")

CATEGORY_MAP = {
    "Fiction": "Fantasía",
    "Juvenile Fiction": "Juvenil",
    "Young Adult Fiction": "Juvenil",
    "History": "Historia",
    "Romance": "Romance"
}

app = FastAPI(title="LibrosUy API", description="API para mapear y buscar librerías en Uruguay.")

# CORS setup so React on port 3000 can communicate with FastAPI on port 8000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    return pyodbc.connect(
        f"Driver={{SQL Server}};"
        f"Server={DB_SERVER};"
        f"Database={DB_NAME};"
        "Trusted_Connection=yes;"
    )

def get_book_categories(book_title: str):
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {"q": book_title, "maxResults": 1}
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code != 200:
            return []
        data = response.json()
        if "items" not in data:
            return []
        volume_info = data["items"][0].get("volumeInfo", {})
        return volume_info.get("categories", [])
    except Exception:
        return []

def map_categories_to_tags(google_categories):
    matched_tags = set()
    for category in google_categories:
        for english_key, sql_tag in CATEGORY_MAP.items():
            if english_key.lower() in category.lower():
                matched_tags.add(sql_tag)
    return list(matched_tags)

def find_stores_by_tags(tags):
    if not tags:
        return []

    conn = get_db_connection()
    cursor = conn.cursor()
    placeholders = ", ".join("?" for _ in tags)

    query = f"""
        SELECT DISTINCT s.Name, s.WhatsAppNumber, s.Address, s.City, s.Department
        FROM Stores s
        JOIN Store_Tags st ON s.StoreID = st.StoreID
        JOIN Tags t ON st.TagID = t.TagID
        WHERE t.TagName IN ({placeholders}) 
        AND s.IsActive = 1;
    """

    cursor.execute(query, tags)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        {"name": row[0], "whatsapp": row[1], "address": row[2], "city": row[3], "department": row[4]}
        for row in rows
    ]

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"message": "LibrosUy API operational."}

@app.get("/api/stores")
def get_stores():
    """Serves all seeded stores with valid coordinates for the React map."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Name, Latitude, Longitude FROM Stores WHERE Latitude IS NOT NULL AND Longitude IS NOT NULL")
        rows = cursor.fetchall()
        
        stores = [
            {
                "name": row[0],
                "latitude": float(row[1]),
                "longitude": float(row[2])
            }
            for row in rows
        ]
        cursor.close()
        conn.close()
        return stores
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/search")
def search_book(title: str):
    """Matches book titles through Google Books categories to local tagged stores."""
    google_cats = get_book_categories(title)
    if not google_cats:
        return {"book_title": title, "genres": [], "stores": [], "message": "Libro no encontrado en la base global."}

    sql_tags = map_categories_to_tags(google_cats)
    if not sql_tags:
        return {"book_title": title, "genres": google_cats, "stores": [], "message": "No hay tiendas registradas para esta categoría."}

    try:
        matched_stores = find_stores_by_tags(sql_tags)
        return {
            "book_title": title,
            "matched_genres": sql_tags,
            "stores": matched_stores
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")