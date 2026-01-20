-- This test validates that confidence_score is between 0 and 1.
-- In dbt, a test FAILS if the query returns any rows.
-- So, we select rows that are INVALID (less than 0 or greater than 1).

select *
from {{ ref('fct_image_detections') }}
where confidence_score < 0 OR confidence_score > 1