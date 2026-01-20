from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ChannelActivity(BaseModel):
    date: str
    post_count: int

class TopProduct(BaseModel):
    product_name: str
    mention_count: int

class SearchResult(BaseModel):
    message_id: int
    channel_name: str
    message_text: str
    message_date: datetime
    views: int

class VisualContentStats(BaseModel):
    channel_name: str
    total_images: int
    avg_confidence: float