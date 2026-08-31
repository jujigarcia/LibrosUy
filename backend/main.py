import requests
import pyodbc

# 1. The Translation Dictionary
# The Google Books API returns categories in standard English (BISAC codes).
# We map these external categories to the strict Spanish tags in your SQL Server database.
CATEGORY_MAP = {
    "Fiction": "Fantasía", # Note: Google often uses 'Fiction' broadly; you can map this as needed
    "Juvenile Fiction": "Juvenil",
    "Young Adult Fiction": "Juvenil",
    "History": "Historia",
    "Romance": "Romance"
}

def get_book_categories(book_title):
    """Fetches the genre of a book using the free Google Books API."""
    url = "https://www.googleapis.com/books/v1/volumes"
    # We limit to 1 result since we just want the top match to identify the genre
    params = {"q": book_title, "maxResults": 1} 
    
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        print("API Connection Error")
        return []

    data = response.json()
    
    # Check if the API found the book
    if "items" not in data:
        print(f"No results found for: {book_title}")
        return []
    
    # Extract the categories from the first result
    volume_info = data["items"][0].get("volumeInfo", {})
    categories = volume_info.get("categories", [])
    
    print(f"API Returned Categories: {categories}")
    return categories

def map_categories_to_tags(google_categories):
    """Matches Google's English categories to the database's Spanish tags."""
    matched_tags = set()
    
    for category in google_categories:
        # Google sometimes returns nested strings like "Fiction / Fantasy / Epic"
        # We loop through our map to catch partial string matches
        for english_key, sql_tag in CATEGORY_MAP.items():
            if english_key.lower() in category.lower():
                matched_tags.add(sql_tag)
                
    return list(matched_tags)

def find_stores(tags):
    """Queries the SQL Server database to find stores matching ANY of the tags."""
    if not tags:
        return []
        
    # Connect to your SQL Server instance
    # connection_string = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=YOUR_SERVER;DATABASE=YourDB;UID=user;PWD=password"
    # conn = pyodbc.connect(connection_string)
    # cursor = conn.cursor()
    
    # Create the dynamic SQL query based on how many tags were found
    # This generates a string of question marks like (?, ?) for parameterized execution
    placeholders = ', '.join('?' for _ in tags)
    
    query = f"""
        SELECT DISTINCT s.Name, s.WhatsAppNumber, s.City 
        FROM Stores s
        JOIN Store_Tags st ON s.StoreID = st.StoreID
        JOIN Tags t ON st.TagID = t.TagID
        WHERE t.TagName IN ({placeholders}) 
        AND s.IsActive = 1;
    """
    
    # Execute the query safely to prevent SQL injection
    # cursor.execute(query, tags)
    # stores = cursor.fetchall()
    # conn.close()
    
    # return stores
    return [] # Placeholder return so the script runs without a live DB

# --- The Execution Flow ---
if __name__ == "__main__":
    
    search_query = "Fourth Wing"
    print(f"Searching for: '{search_query}'...\n")
    
    # Step 1: Hit the API
    google_cats = get_book_categories(search_query)
    
    # Step 2: Translate the data
    sql_tags = map_categories_to_tags(google_cats)
    print(f"Translated to SQL Tags: {sql_tags}\n")
    
    # Step 3: Find the stores
    # matched_stores = find_stores(sql_tags)
    # if matched_stores:
    #     print("--- Matchmaker Results ---")
    #     for store in matched_stores:
    #         print(f"Librería: {store.Name} | WhatsApp: {store.WhatsAppNumber} | Ciudad: {store.City}")
    # else:
    #     print("No stores found matching these categories.")
