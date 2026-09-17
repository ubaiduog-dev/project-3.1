--deliveries.bowler_type
--players.field_pos
--matches.player_of_match
--contains fix 1,2,3

drop view if exists v_deliveries_clean;
create view v_deliveries_clean as
select *,
nullif(trim(bowler_type), '') as bowler_type_clean
from deliveries;
drop view if exists v_players_clean;
create view v_players_clean as
select *,
nullif(trim(field_pos), '') as field_pos_clean
from players;
drop view if exists v_matches_pom;
create view v_matches_pom as
select *,
nullif(trim(player_of_match), '') as pom_clean
from matches;


