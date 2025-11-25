"""
Script to initialize the database.
"""
from src.app.core.database import init_db

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")
