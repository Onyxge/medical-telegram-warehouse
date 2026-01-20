import os
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# -------------------------------
# Environment & DB Setup
# -------------------------------
# Using the PG_ variable names from your snippet
DB_URI = (
    f"postgresql://{os.getenv('PG_USER')}:"
    f"{os.getenv('PG_PASSWORD')}@"
    f"{os.getenv('PG_HOST')}:{os.getenv('PG_PORT')}/{os.getenv('PG_DB')}"
)
engine = create_engine(DB_URI, pool_size=10, max_overflow=20)

app = FastAPI(
    title="Medical Telegram Analytics API",
    description="API exposing Telegram analytics for medical/pharma channels",
    version="1.0.0"
)

# -------------------------------
# Pydantic Response Models
# -------------------------------
class CategoryViews(BaseModel):
    primary_category: str
    avg_views: float

class TopChannel(BaseModel):
    channel_name: str
    metric_value: int

class ChannelVisualStats(BaseModel):
    channel_name: str
    visual_pct: float

class ImageSummary(BaseModel):
    primary_category: str
    count: int
    avg_confidence: float

# -------------------------------
# API Endpoints
# -------------------------------

@app.get("/")
def read_root():
    return {"status": "online", "message": "Medical Data API is running. Go to /docs for the dashboard."}

@app.get("/category_views", response_model=List[CategoryViews])
def get_category_views():
    """
    Compare average views per YOLO primary_category.
    Source: staging_marts.fct_image_detections
    """
    # UPDATED: Pointing to 'staging_marts'
    query = """
        SELECT d.primary_category, ROUND(AVG(m.view_count), 0) AS avg_views
        FROM staging_marts.fct_image_detections d
        JOIN staging_marts.fct_messages m ON CAST(d.message_id AS bigint) = m.message_id
        GROUP BY d.primary_category
        ORDER BY avg_views DESC
    """
    with engine.connect() as conn:
        result = conn.execute(text(query)).fetchall()
        if not result:
            raise HTTPException(status_code=404, detail="No data found")
        return [{"primary_category": r[0], "avg_views": r[1]} for r in result]


@app.get("/top_channels", response_model=List[TopChannel])
def get_top_channels(limit: int = Query(5, ge=1), metric: str = Query("message_count")):
    """
    Return top channels by message_count or image_count.
    Source: staging_marts.dim_channels
    """
    if metric not in ["message_count", "image_count"]:
        raise HTTPException(status_code=400, detail="Invalid metric. Use 'message_count' or 'image_count'")

    if metric == "message_count":
        sql_metric = "COUNT(DISTINCT m.message_id)"
    else:
        sql_metric = "COUNT(DISTINCT d.detection_key)"

    # UPDATED: Pointing to 'staging_marts' for all tables
    query = f"""
        SELECT c.channel_name, {sql_metric} as val
        FROM staging_marts.dim_channels c
        LEFT JOIN staging_marts.fct_messages m ON c.channel_key = m.channel_key
        LEFT JOIN staging_marts.fct_image_detections d ON c.channel_key = d.channel_key
        GROUP BY c.channel_name
        ORDER BY val DESC
        LIMIT :limit
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"limit": limit}).fetchall()
        return [{"channel_name": r[0], "metric_value": r[1]} for r in result]


@app.get("/channel_visual_content", response_model=List[ChannelVisualStats])
def channel_visual_content(limit: int = Query(5, ge=1)):
    """
    Return percentage of messages that contain an image (YOLO detected).
    Source: staging_marts...
    """
    # UPDATED: Pointing to 'staging_marts' for all tables
    query = """
        SELECT 
            c.channel_name,
            ROUND(
                (COUNT(DISTINCT d.detection_key)::numeric / NULLIF(COUNT(DISTINCT m.message_id), 0)) * 100, 
            2) AS visual_pct
        FROM staging_marts.dim_channels c
        JOIN staging_marts.fct_messages m ON c.channel_key = m.channel_key
        LEFT JOIN staging_marts.fct_image_detections d ON m.message_id = CAST(d.message_id AS bigint)
        GROUP BY c.channel_name
        ORDER BY visual_pct DESC
        LIMIT :limit
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"limit": limit}).fetchall()
        return [
            {"channel_name": r[0], "visual_pct": float(r[1]) if r[1] is not None else 0.0}
            for r in result
        ]


@app.get("/image_summary", response_model=List[ImageSummary])
def image_summary():
    """
    Returns overall stats for YOLO detections.
    Source: staging_marts.fct_image_detections
    """
    # UPDATED: Pointing to 'staging_marts'
    query = """
        SELECT primary_category,
               COUNT(detection_key) AS count,
               ROUND(AVG(confidence_score)::numeric, 3) AS avg_confidence
        FROM staging_marts.fct_image_detections
        GROUP BY primary_category
        ORDER BY count DESC
    """
    with engine.connect() as conn:
        result = conn.execute(text(query)).fetchall()
        return [
            {"primary_category": r[0], "count": r[1], "avg_confidence": float(r[2])}
            for r in result
        ]