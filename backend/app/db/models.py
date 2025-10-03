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

    transcript = relationship("Transcript", back_populates="episode", uselist=False) # link to the transcript object
    summary = relationship("Summary", back_populates="episode", uselist=False)
    #uselist=False means one-to-one relationship

class Transcript(Base):
    __tablename__ = "transcripts"
    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id")) #each transcript is linked to an episode
    text = Column(Text)
    segments_json = Column(Text)
    created_at = Column(TIMESTAMP)
    episode = relationship("Episode", back_populates="transcript") # link back to the episode object

class Summary(Base):
    __tablename__ = "summaries"
    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"))
    summary_text = Column(Text)
    chapters_json = Column(Text)
    quotes_json = Column(Text)
    created_at = Column(TIMESTAMP)
    episode = relationship("Episode", back_populates="summary")
