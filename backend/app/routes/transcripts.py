from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.db import get_db
from app.db.models import Transcript, Episode
from app.services.transcript_service import transcribe_with_whisperx
import json

router = APIRouter()

@router.post("/{episode_id}")
def transcribe_episode(episode_id: int, db: Session = Depends(get_db)):
    ep = db.query(Episode).filter(Episode.id == episode_id).first()
    if not ep:
        return {"error": "Episode not found"}

    result = transcribe_with_whisperx(ep.audio_url) # assuming this returns {"text": ..., "segments": [...]}
    tr = Transcript(episode_id=ep.id, text=result["text"], segments_json=json.dumps(result["segments"]))
    db.add(tr)
    ep.status = "transcribed" # update episode status
    db.commit()
    return {"episode_id": ep.id, "preview": result["text"][:200]}
