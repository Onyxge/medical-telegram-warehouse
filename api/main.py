from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from . import database, schemas, crud
# ... imports ...

app = FastAPI(
    title="Medical Telegram Analytics API",
    description="REST API for accessing medical channel insights.",
    version="1.0.0"
)

# --- ADD THIS MISSING ROOT ENDPOINT ---
@app.get("/")
def read_root():
    return {"status": "online", "message": "Medical Data API is running. Go to /docs for the dashboard."}
# --------------------------------------

# ... rest of the code (get_db, endpoints) ...
# Dependency to get DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------
# ENDPOINT 1: Top Products
# ---------------------------------------------------------
@app.get("/api/reports/top-products", response_model=List[schemas.TopProduct])
def get_top_products(limit: int = 10, db: Session = Depends(get_db)):
    result = crud.get_top_products(db, limit)
    return [{"product_name": row[0], "mention_count": row[1]} for row in result]

# ---------------------------------------------------------
# ENDPOINT 2: Channel Activity
# ---------------------------------------------------------
@app.get("/api/channels/{channel_name}/activity", response_model=List[schemas.ChannelActivity])
def get_channel_activity(channel_name: str, db: Session = Depends(get_db)):
    result = crud.get_channel_activity(db, channel_name)
    if not result:
        raise HTTPException(status_code=404, detail=f"No activity found for channel '{channel_name}'")
    return [{"date": row[0], "post_count": row[1]} for row in result]

# ---------------------------------------------------------
# ENDPOINT 3: Message Search
# ---------------------------------------------------------
@app.get("/api/search/messages", response_model=List[schemas.SearchResult])
def search_messages(query: str, limit: int = 20, db: Session = Depends(get_db)):
    result = crud.search_messages(db, query, limit)
    return [
        {
            "message_id": row[0],
            "channel_name": row[1],
            "message_text": row[2],
            "message_date": row[3],
            "views": row[4]
        }
        for row in result
    ]

# ---------------------------------------------------------
# ENDPOINT 4: Visual Content Stats
# ---------------------------------------------------------
@app.get("/api/reports/visual-content", response_model=List[schemas.VisualContentStats])
def get_visual_content_stats(db: Session = Depends(get_db)):
    result = crud.get_visual_stats(db)
    return [
        {
            "channel_name": row[0],
            "total_images": row[1],
            "avg_confidence": round(float(row[2]), 3)
        }
        for row in result
    ]