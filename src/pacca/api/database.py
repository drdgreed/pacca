from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. This is the URL for our database. 
# It tells SQLite to create a file named "pacca.db" in your current folder.
SQLALCHEMY_DATABASE_URL = "sqlite:///./pacca.db"

# 2. The "engine" is the actual engine that runs the database connections.
# (The 'check_same_thread' part is a specific requirement just for SQLite)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. A "Session" is a single conversation with the database. 
# Whenever a user logs in, we will open a session, ask the database if the user exists, and close it.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. We will use this "Base" class in our next file to build our database tables.
Base = declarative_base()