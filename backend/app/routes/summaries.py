from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.db import get_db
from app.db.models import Episode, Transcript, Summary
from app.services.summarize_service import summarize_segments  
import json

router = APIRouter()

@router.post("/{episode_id}")
def summarize_episode(episode_id: int, db: Session = Depends(get_db)):
    ep = db.query(Episode).filter(Episode.id == episode_id).first()
    tr = db.query(Transcript).filter(Transcript.episode_id == episode_id).first()
    if not ep or not tr:
        return {"error": "Missing episode or transcript"}

    # Parse transcript segments from DB
    segments = json.loads(tr.segments_json)

    result = summarize_segments(segments)

    sm = Summary(
        episode_id=ep.id,
        summary_text=json.dumps(result["episode_summary"]),
        quotes_json=json.dumps(result["key_quotes"]),
        chapters_json=json.dumps(result["chapters"])
    )
    db.add(sm)
    ep.status = "done"
    db.commit()
    return {
        "episode_id": ep.id,
        "summary": " ".join(result["episode_summary"]), #flatten list
        "quotes": result["key_quotes"],
        "chapters": result["chapters"]
    }
