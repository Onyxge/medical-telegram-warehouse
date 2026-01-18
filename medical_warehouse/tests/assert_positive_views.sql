-- This test fails if view counts are negative

SELECT
    message_id,
    views
FROM {{ ref('stg_telegram_messages') }}
WHERE views < 0
