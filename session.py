import os
from sqlalchemy import create_engine

# Try to read DATABASE_URL from env, otherwise use a local SQLite file
DB_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./baseball.db"   # file will be created next to where you run Python
)

engine = create_engine(DB_URL, echo=False, future=True)
