# backend/app/db.py

# Database connection and session management
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load environment variables from .env file
load_dotenv()

# Get the database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL") 

# Ensure DATABASE_URL is set
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment variables")

# If Database is set, create the engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True) #pool_pre_ping to avoid timeout issues

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) #Used for CRUD operations

def get_db():
    with engine.connect() as conn:
        yield conn


#Test the connection
def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            value = result.scalar_one()  # fetch once
            print("Database connection successful:", value)
            return value
    except Exception as e:
        print("Database connection failed:", e)
        return None  # optional, but explicit
