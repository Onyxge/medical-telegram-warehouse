from sqlalchemy.orm import Session
from sqlalchemy import text

def get_top_products(db: Session, limit: int):
    """
    Counts detected objects as a proxy for 'Top Products'.
    FIX: Uses 'translate' to strip ALL brackets [], braces {}, and quotes '' ""
    to ensure we get clean, merged counts (e.g., 'bottle' and '{bottle}' become one).
    """
    query = text("""
        WITH cleaned_objects AS (
            SELECT 
                -- TRANSLATE removes all characters listed in the second string
                -- We remove: [ ] { } " ' and spaces
                unnest(
                    string_to_array(
                        translate(detected_objects, '[]{}''"', ''), 
                        ','
                    )
                ) as raw_obj
            FROM staging_marts.fct_image_detections
            WHERE detected_objects IS NOT NULL 
        )
        SELECT 
            TRIM(raw_obj) as product_name,
            COUNT(*) as mention_count
        FROM cleaned_objects
        WHERE TRIM(raw_obj) <> ''  -- Filter out empty strings result from {}
        GROUP BY product_name
        ORDER BY mention_count DESC
        LIMIT :limit
    """)
    result = db.execute(query, {"limit": limit}).fetchall()
    return result

def get_channel_activity(db: Session, channel_name: str):
    """
    Gets daily post counts for a specific channel.
    FIX: Joins with dim_dates to get the actual date from date_key.
    """
    query = text("""
        SELECT 
            TO_CHAR(d.full_date, 'YYYY-MM-DD') as date,
            COUNT(m.message_id) as post_count
        FROM staging_marts.fct_messages m
        JOIN staging_marts.dim_channels c ON m.channel_key = c.channel_key
        JOIN staging_marts.dim_dates d ON m.date_key = d.date_key
        WHERE c.channel_name = :channel_name
        GROUP BY d.full_date
        ORDER BY d.full_date DESC
    """)
    result = db.execute(query, {"channel_name": channel_name}).fetchall()
    return result

def search_messages(db: Session, query_str: str, limit: int):
    """
    Case-insensitive search for messages.
    FIX: Joins with dim_dates to return the message date.
    """
    sql_query = text("""
        SELECT 
            m.message_id,
            c.channel_name,
            m.message_text,
            d.full_date as message_date,
            m.view_count as views
        FROM staging_marts.fct_messages m
        JOIN staging_marts.dim_channels c ON m.channel_key = c.channel_key
        JOIN staging_marts.dim_dates d ON m.date_key = d.date_key
        WHERE m.message_text ILIKE :search_term
        ORDER BY d.full_date DESC
        LIMIT :limit
    """)
    search_term = f"%{query_str}%"
    result = db.execute(sql_query, {"search_term": search_term, "limit": limit}).fetchall()
    return result
def get_visual_stats(db: Session):
    """
    Aggregates image stats per channel.
    """
    query = text("""
        SELECT 
            c.channel_name,
            COUNT(d.detection_key) as total_images,
            COALESCE(AVG(d.confidence_score), 0) as avg_confidence
        FROM staging_marts.dim_channels c
        LEFT JOIN staging_marts.fct_image_detections d ON c.channel_key = d.channel_key
        GROUP BY c.channel_name
        ORDER BY total_images DESC
    """)
    result = db.execute(query).fetchall()
    return result