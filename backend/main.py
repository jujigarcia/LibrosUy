import os
import requests
import pyodbc
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Load credentials from a local .env file (not tracked in Git)
load_dotenv()

# Database connection variables
DB_SERVER = os.getenv("DB_SERVER", "localhost")
DB_NAME = os.getenv("DB_NAME", "LibrosUyDB")
DB_USER = os.getenv("DB_USER", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "YourPasswordHere")
DB_DRIVER = os.getenv("DB_DRIVER", "{ODBC Driver 17 for SQL Server}")

# The Translation Dictionary
CATEGORY_MAP = {
    "Fiction": "Fantasía", 
    "Juvenile Fiction": "Juvenil",
    "Young Adult Fiction": "Juvenil",
    "History": "Historia",
    "Romance": "Romance"
}

# --- FastAPI Initialization ---
app = FastAPI(title="LibrosUy API", description="API to match books to local Uruguayan bookstores.")

# Allow the frontend to communicate with this backend (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, this will be your actual website URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Core Logic Functions ---
def get_book_categories(book_title):
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {"q": book_title, "maxResults": 1} 
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return []

    data = response.json()
    if "items" not in data:
        return []
    
    volume_info = data["items"][0].get("volumeInfo", {})
    return volume_info.get("categories", [])

def map_categories_to_tags(google_categories):
    matched_tags = set()
    for category in google_categories:
        for english_key, sql_tag in CATEGORY_MAP.items():
            if english_key.lower() in category.lower():
                matched_tags.add(sql_tag)
    return list(matched_tags)

def get_db_connection():
    connection_string = (
        f"DRIVER={DB_DRIVER};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD}"
    )
    return pyodbc.connect(connection_string)

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
    conn.close()

    return [{"name": row[0], "whatsapp": row[1], "address": row[2], "city": row[3], "department": row[4]} for row in rows]

# --- API Endpoints ---

@app.get("/")
def read_root():
    """Health check endpoint to ensure the server is running."""
    return {"message": "Welcome to the LibrosUy API!"}

@app.get("/api/search")
def search_book(title: str):
    """The main endpoint the frontend will call when a user searches for a book."""
    
    # 1. Hit the Google API
    google_cats = get_book_categories(title)
    if not google_cats:
        return {"book_title": title, "genres": [], "stores": [], "message": "Libro no encontrado en la base global."}
    
    # 2. Translate to SQL Tags
    sql_tags = map_categories_to_tags(google_cats)
    if not sql_tags:
        return {"book_title": title, "genres": google_cats, "stores": [], "message": "No hay tiendas registradas para esta categoría."}
    
    # 3. Query the Database
    try:
        matched_stores = find_stores_by_tags(sql_tags)
        return {
            "book_title": title,
            "matched_genres": sql_tags,
            "stores": matched_stores
        }
    except Exception as e:
        # Returns a clear error if the database connection fails during testing
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")
