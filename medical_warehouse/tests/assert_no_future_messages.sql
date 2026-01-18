-- This test fails if any message has a future timestamp

SELECT
    message_id,
    message_date
FROM {{ ref('stg_telegram_messages') }}
WHERE message_date > CURRENT_TIMESTAMP
