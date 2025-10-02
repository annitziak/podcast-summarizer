from .db import Base, engine
from .models import Episode, Transcript, Summary

def init_db():
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized.")

if __name__ == "__main__":
    init_db()
