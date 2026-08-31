import os
import requests
import pyodbc
from dotenv import load_dotenv

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

def get_book_categories(book_title):
    """Fetches the genre of a book using the free Google Books API."""
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
    """Matches Google's English categories to the database's Spanish tags."""
    matched_tags = set()
    for category in google_categories:
        for english_key, sql_tag in CATEGORY_MAP.items():
            if english_key.lower() in category.lower():
                matched_tags.add(sql_tag)
    return list(matched_tags)

def get_db_connection():
    """Establishes and returns a database connection."""
    connection_string = (
        f"DRIVER={DB_DRIVER};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD}"
    )
    return pyodbc.connect(connection_string)

def find_stores_by_tags(tags):
    """Queries active stores matching the provided genre tags."""
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
