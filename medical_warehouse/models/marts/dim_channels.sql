-- Dimension_table
{{ config(
    materialized='table',
    schema='marts'
) }}

WITH channel_stats AS (
    SELECT
        channel_name,
        channel_title,
        COUNT(*) AS total_posts,
        AVG(view_count)::int AS avg_views,
        MIN(message_date) AS first_post_date,
        MAX(message_date) AS last_post_date
    FROM {{ ref('stg_telegram_messages') }}
    GROUP BY channel_name, channel_title
)

SELECT
    ROW_NUMBER() OVER () AS channel_key,
    channel_name,
    channel_title,
    'Medical' AS channel_type,
    first_post_date,
    last_post_date,
    total_posts,
    avg_views
FROM channel_stats
