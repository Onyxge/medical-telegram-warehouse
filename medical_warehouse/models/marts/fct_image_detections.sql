{{ config(
    materialized='table',
    schema='marts'
) }}

WITH yolo AS (
    SELECT
        message_id,
        channel_name,
        image_path,
        detected_objects,
        confidence_score,
        image_category,
        -- [NEW] 1. Generate a row number for every duplicate pair
        ROW_NUMBER() OVER(
            PARTITION BY message_id, channel_name
            ORDER BY message_id
        ) as rn
    FROM {{ source('telegram', 'yolo_detections') }}
),

-- [NEW] 2. Filter out duplicates immediately
yolo_deduped AS (
    SELECT *
    FROM yolo
    WHERE rn = 1
),

messages AS (
    SELECT
        message_id,
        channel_key,
        date_key
    FROM {{ ref('fct_messages') }}
)

SELECT
    md5(
        concat(
            CAST(y.message_id AS varchar),
            y.channel_name
        )
    ) AS detection_key,
    m.message_id,
    m.channel_key,
    m.date_key,
    COALESCE(y.image_category, 'other') AS primary_category,
    y.detected_objects,
    y.confidence_score,
    y.image_path,
    CURRENT_TIMESTAMP AS enriched_at
FROM yolo_deduped AS y  -- [CHANGED] Joining the deduped version, not raw 'yolo'
INNER JOIN messages AS m
    ON CAST(y.message_id AS bigint) = m.message_id