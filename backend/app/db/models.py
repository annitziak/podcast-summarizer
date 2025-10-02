from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from .db import Base

class Episode(Base):
    __tablename__ = "episodes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    audio_url = Column(String)
    duration = Column(Integer)
    status = Column(String, default="queued")
    created_at = Column(TIMESTAMP)

    transcript = relationship("Transcript", back_populates="episode", uselist=False)
    summary = relationship("Summary", back_populates="episode", uselist=False)

class Transcript(Base):
    __tablename__ = "transcripts"
    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"))
    text = Column(Text)
    segments_json = Column(Text)
    created_at = Column(TIMESTAMP)
    episode = relationship("Episode", back_populates="transcript")

class Summary(Base):
    __tablename__ = "summaries"
    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"))
    summary_text = Column(Text)
    chapters_json = Column(Text)
    quotes_json = Column(Text)
    created_at = Column(TIMESTAMP)
    episode = relationship("Episode", back_populates="summary")
