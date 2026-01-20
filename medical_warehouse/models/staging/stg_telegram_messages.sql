{{ config(
    materialized='view',
    schema='staging'
) }}

WITH raw_messages AS (
    SELECT *
    FROM {{ source('raw', 'telegram_messages') }}
),

cleaned AS (
    SELECT
        message_id,
        channel_name,
        channel_title,
        CAST(message_date AS timestamp) AS message_date,
        COALESCE(message_text, '') AS message_text,
        has_media,
        image_path,
        COALESCE(views, 0) AS view_count,
        COALESCE(forwards, 0) AS forward_count,
        LENGTH(COALESCE(message_text, '')) AS message_length,
        CASE WHEN has_media = TRUE AND image_path IS NOT NULL THEN TRUE ELSE FALSE END AS has_image
    FROM raw_messages
    WHERE message_id IS NOT NULL
      AND channel_name IS NOT NULL
)

SELECT *
FROM cleaned
