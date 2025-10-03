from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.db import get_db
from app.db.models import Episode

router = APIRouter()

@router.post("/")
def add_episode(title: str, audio_url: str, db: Session = Depends(get_db)):
    ep = Episode(title=title, audio_url=audio_url, status="queued") # default status
    db.add(ep)
    db.commit()
    db.refresh(ep)
    return {"id": ep.id, "status": ep.status}

@router.get("/{episode_id}") #retrieve episode by ID
def get_episode(episode_id: int, db: Session = Depends(get_db)):
    ep = db.query(Episode).filter(Episode.id == episode_id).first()
    return ep if ep else {"error": "Not found"}
