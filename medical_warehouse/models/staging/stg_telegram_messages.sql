{{ config(
    materialized='view'
) }}

with raw_messages as (

    select *
    from {{ source('raw', 'telegram_messages') }}

),

cleaned as (

    select
        message_id,
        channel_name,
        channel_title,
        -- Convert message_date to timestamp
        cast(message_date as timestamp) as message_date,
        coalesce(message_text, '') as message_text,
        has_media,
        image_path,
        coalesce(views, 0) as views,
        coalesce(forwards, 0) as forwards,
        -- Calculated field: message length
        length(coalesce(message_text, '')) as message_length,
        -- Flag for images
        case when has_media = true and image_path is not null then true else false end as has_image
    from raw_messages

    where message_id is not null
      and channel_name is not null

)

select * from cleaned
