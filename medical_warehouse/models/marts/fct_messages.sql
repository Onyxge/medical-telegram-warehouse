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
    msg.view_count,
    msg.forward_count,
    msg.has_image
FROM {{ ref('stg_telegram_messages') }} AS msg
LEFT JOIN {{ ref('dim_channels') }} AS ch
    ON msg.channel_name = ch.channel_name
LEFT JOIN {{ ref('dim_dates') }} AS dt
    ON DATE(msg.message_date) = dt.full_date
