from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite URL for local development
DATABASE_URL = "sqlite:///podcast.db"



# Create engine and session
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}) # SQLAlchemy and SQLite connection
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
