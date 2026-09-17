drop view if exists v_venues_clean;
create view v_venues_clean as
with ranked as (
    select venue_id, venue, city,
           row_number() over (
              partition by venue
              order by case when city is null or trim(city) = ''
                            then 1 else 0 end,
                        venue_id) as rn
    from venues)
select venue_id, venue, city
from ranked where rn = 1;
