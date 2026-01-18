--facts
{{ config(
    materialized='table',
    schema='marts'
) }}

SELECT
    msg.message_id,
    ch.channel_key,
    dt.date_key,
    msg.message_text,
    msg.message_length,
    msg.views AS view_count,
    msg.forwards AS forward_count,
    msg.has_image
FROM {{ ref('stg_telegram_messages') }} msg
LEFT JOIN {{ ref('dim_channels') }} ch
    ON msg.channel_name = ch.channel_name
LEFT JOIN {{ ref('dim_dates') }} dt
    ON DATE(msg.message_date) = dt.full_date
