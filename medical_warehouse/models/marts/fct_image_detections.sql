-- models/marts/fct_image_detections.sql

with yolo as (

    select 
        message_id,
        channel_name,
        image_path,
        -- Use COALESCE to provide default values if column is missing
        coalesce(primary_category, 'other') as primary_category,
        coalesce(confidence_score, 0.0) as confidence_score,
        coalesce(detected_objects::text[], array[]::text[]) as detected_objects
    from {{ source('telegram', 'yolo_detections') }}

),

messages as (

    select 
        message_id, 
        channel_key, 
        date_key
    from {{ ref('fct_messages') }}

)

select
    -- Surrogate key for detection
    md5(concat(cast(y.message_id as varchar), y.channel_name)) as detection_key,

    -- Foreign keys
    m.channel_key,
    m.date_key,
    y.message_id,

    -- YOLO insights
    y.primary_category,
    y.detected_objects,
    y.confidence_score,
    y.image_path,

    -- Metadata
    current_timestamp as enriched_at

from yolo y
inner join messages m
    on cast(y.message_id as bigint) = m.message_id
