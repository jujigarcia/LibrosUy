import requests
import pyodbc

# 1. Connect to the local SQL Server Database
conn = pyodbc.connect(
    "Driver={SQL Server};"
    "Server=localhost\\SQLEXPRESS;"
    "Database=LibrosUyDB;"
    "Trusted_Connection=yes;"
)
cursor = conn.cursor()

# 2. Fetch the bookstore data from OpenStreetMap
print("Fetching bookstores from OpenStreetMap...")

# Added a timeout directly into the query
query = """
[out:json][timeout:25];
area["ISO3166-1"="UY"]->.searchArea;
nwr["shop"="books"](area.searchArea);
out center;
"""

url = "https://overpass-api.de/api/interpreter"

# Add headers to identify our app to the Overpass server
headers = {
    'User-Agent': 'LibrosUyApp/1.0 (Local Development)'
}

response = requests.post(url, data={'data': query}, headers=headers)

# 3. Check for errors before parsing JSON
if response.status_code != 200:
    print(f"API Error {response.status_code}: The server did not return JSON.")
    print("Response text:", response.text)
else:
    stores = response.json()
    
    # 4. Insert the data into your SQL table
    print("Inserting data into SQL Server...")
    for element in stores.get('elements', []):
        name = element.get('tags', {}).get('name', 'Librería Sin Nombre')
        lat = element.get('lat') or element.get('center', {}).get('lat')
        lon = element.get('lon') or element.get('center', {}).get('lon')
        
        if lat and lon:
            try:
                cursor.execute("""
                    INSERT INTO Stores (Name, Latitude, Longitude)
                    VALUES (?, ?, ?)
                """, (name, lat, lon))
            except pyodbc.Error:
                # Skips errors (like duplicates) without crashing the script
                pass

    # Save the changes
    conn.commit()
    print("Success! The LibrosUyDB database is now populated.")

# Close the connection
cursor.close()
conn.close()