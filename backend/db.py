import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

DB_SERVER = os.getenv("DB_SERVER", "localhost\\SQLEXPRESS")
DB_NAME = os.getenv("DB_NAME", "LibrosUyDB")
DB_DRIVER = os.getenv("DB_DRIVER", "{SQL Server}")


def get_db_connection():
    """Shared SQL Server connection (Windows auth) for the API and ETL scripts."""
    return pyodbc.connect(
        f"Driver={DB_DRIVER};"
        f"Server={DB_SERVER};"
        f"Database={DB_NAME};"
        "Trusted_Connection=yes;"
    )
