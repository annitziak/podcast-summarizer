from fastapi import FastAPI
from app.db.db import Base, engine
from app.routes import episodes, transcripts, summaries

# Create tables 
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(title="Podcast Summarizer API")

# Include routers : these handle different endpoints 
app.include_router(episodes.router, prefix="/episodes", tags=["Episodes"])
app.include_router(transcripts.router, prefix="/transcripts", tags=["Transcripts"])
app.include_router(summaries.router, prefix="/summaries", tags=["Summaries"])
