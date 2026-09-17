drop view if exists v_matches_venue;
create view v_matches_venue as
select *,
        replace(
            trim(
              substr(venue, 1,
                case when instr(venue, ',') > 0
                     then instr(venue,',') - 1
                     else length(venue)
                end)),
              'm.chinnaswamy','m chinnaswamy') as venue_clean
from matches;
