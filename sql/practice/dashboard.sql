-- ============================================================
-- IPL Cricket Analytics - Domain D: Teams and Venues
-- All queries for the Streamlit dashboard (ipl.db)
-- Each query starts with a "-- name: xxx" line so the .py file can find it.
-- Ground name ALWAYS comes from matches_clean.venue_clean (never raw venue).
-- Parameters used: :min_matches (cut-off), :venue (selected ground), :team (selected team)
-- ============================================================


-- ############################################################
-- TAB 1 : OVERVIEW
-- ############################################################

-- name: card_scale
-- Card 1: how many teams and how many grounds are in the data
SELECT
    (SELECT COUNT(*) FROM (SELECT team1 AS team FROM matches
                           UNION
                           SELECT team2 FROM matches))        AS total_teams,
    (SELECT COUNT(DISTINCT venue_clean) FROM matches_clean)   AS total_grounds;


-- name: card_total_matches
-- Card 2: matches played across the whole data
SELECT COUNT(*) AS total_matches
FROM matches_clean;


-- name: card_chase
-- Card 3: chasing finding. Matches with a result, and how many the chasing side won.
-- (confidence interval + test are calculated in Python from these two numbers)
SELECT
    COUNT(*)        AS decided_matches,
    SUM(chase_won)  AS chase_wins
FROM v_match_totals;


-- name: chart_wins_played_by_team
-- Visual 4 (hero): matches won by each team, with matches played
SELECT
    t.team,
    COUNT(*) AS matches_played,
    SUM(CASE WHEN mc.match_winner = t.team THEN 1 ELSE 0 END) AS matches_won
FROM (
    SELECT match_id, team1 AS team FROM matches
    UNION ALL
    SELECT match_id, team2 AS team FROM matches
) t
JOIN matches_clean mc ON mc.match_id = t.match_id
GROUP BY t.team
ORDER BY matches_won DESC;


-- name: chart_matches_by_ground
-- Visual 5: matches held at each ground (cut-off line is drawn in Python)
SELECT
    venue_clean AS ground,
    COUNT(*)    AS matches_held
FROM matches_clean
GROUP BY venue_clean
ORDER BY matches_held DESC;


-- name: chart_bat_first_win_by_ground
-- Visual 6: how often the side batting first wins, at grounds with enough matches
SELECT
    venue_clean AS ground,
    COUNT(*)    AS decided_matches,
    ROUND(100.0 * SUM(1 - chase_won) / COUNT(*), 1) AS bat_first_win_pct
FROM v_match_totals
WHERE venue_clean IN (
    SELECT venue_clean
    FROM matches_clean
    GROUP BY venue_clean
    HAVING COUNT(*) >= :min_matches
)
GROUP BY venue_clean
ORDER BY bat_first_win_pct DESC;


-- name: league_bat_first_pct
-- Reference line for Visual 6: league-wide bat-first win %
SELECT ROUND(100.0 * SUM(1 - chase_won) / COUNT(*), 1) AS league_bat_first_pct
FROM v_match_totals;


-- name: chart_sixes_by_team
-- Own visual 1: sixes hit by each team (question: which team hits the most sixes?)
SELECT
    batting_team AS team,
    SUM(CASE WHEN batter_runs = 6 THEN 1 ELSE 0 END) AS sixes
FROM v_ball
GROUP BY batting_team
ORDER BY sixes DESC;


-- name: chart_grounds_by_season
-- Own visual 2: how many grounds were used in each season
-- (question: how did the ground list change over the years?)
SELECT
    season_year AS season,
    COUNT(DISTINCT venue_clean) AS grounds_used
FROM matches_clean
GROUP BY season_year
ORDER BY season_year;


-- ############################################################
-- TAB 2 : VENUE (one ground at a time)
-- ############################################################

-- name: venue_dropdown
-- Drop-down list: built from venue_clean, sorted by matches held, with the count
SELECT
    venue_clean AS ground,
    COUNT(*)    AS matches_held
FROM matches_clean
GROUP BY venue_clean
ORDER BY matches_held DESC, venue_clean;


-- name: venue_card_matches
-- Card 1: matches held at the selected ground
SELECT COUNT(*) AS matches_held
FROM matches_clean
WHERE venue_clean = :venue;


-- name: venue_avg_score
-- Visual 2 (hero): average first-innings score at this ground vs the league average
SELECT
    ROUND((SELECT AVG(i.runs)
           FROM v_innings i
           JOIN matches_clean mc ON mc.match_id = i.match_id
           WHERE i.innings = 1 AND mc.venue_clean = :venue), 1) AS ground_avg,
    ROUND((SELECT AVG(runs) FROM v_innings WHERE innings = 1), 1) AS league_avg;


-- name: venue_bat_first_vs_chase
-- Visual 3: batting first vs chasing at this ground, with the match count
SELECT
    CASE WHEN chase_won = 0 THEN 'Batting first won'
         ELSE 'Chasing won' END AS outcome,
    COUNT(*) AS matches
FROM v_match_totals
WHERE venue_clean = :venue
GROUP BY chase_won
ORDER BY chase_won;


-- name: venue_avg_score_by_season
-- Own visual: average first-innings score at this ground by season
-- (question: is this ground getting higher or lower scoring over time?)
SELECT
    mc.season_year AS season,
    COUNT(*)       AS matches,
    ROUND(AVG(i.runs), 1) AS avg_first_innings
FROM v_innings i
JOIN matches_clean mc ON mc.match_id = i.match_id
WHERE i.innings = 1
  AND mc.venue_clean = :venue
GROUP BY mc.season_year
ORDER BY mc.season_year;


-- ############################################################
-- TAB 3 : TEAM (one side at a time)
-- ############################################################

-- name: team_dropdown
-- Drop-down list: built from team1 AND team2 together so no team is missed
SELECT team1 AS team FROM matches
UNION
SELECT team2 FROM matches
ORDER BY team;


-- name: team_card_record
-- Card 1: matches played, matches won and win rate of the selected team
SELECT
    COUNT(*) AS matches_played,
    SUM(CASE WHEN match_winner = :team THEN 1 ELSE 0 END) AS matches_won,
    ROUND(100.0 * SUM(CASE WHEN match_winner = :team THEN 1 ELSE 0 END) / COUNT(*), 1) AS win_rate
FROM matches_clean
WHERE match_id IN (SELECT match_id FROM matches
                   WHERE team1 = :team OR team2 = :team);


-- name: team_win_rate_by_season
-- Visual 2 (hero): win rate by season (50% reference line is drawn in Python)
SELECT
    mc.season_year AS season,
    COUNT(*) AS matches_played,
    ROUND(100.0 * SUM(CASE WHEN mc.match_winner = :team THEN 1 ELSE 0 END) / COUNT(*), 1) AS win_rate
FROM matches_clean mc
WHERE mc.match_id IN (SELECT match_id FROM matches
                      WHERE team1 = :team OR team2 = :team)
GROUP BY mc.season_year
ORDER BY mc.season_year;


-- name: team_vs_opponent
-- Visual 3: record against each opponent, sorted, with matches played
SELECT
    CASE WHEN m.team1 = :team THEN m.team2 ELSE m.team1 END AS opponent,
    COUNT(*) AS matches_played,
    SUM(CASE WHEN mc.match_winner = :team THEN 1 ELSE 0 END) AS matches_won,
    ROUND(100.0 * SUM(CASE WHEN mc.match_winner = :team THEN 1 ELSE 0 END) / COUNT(*), 1) AS win_rate
FROM matches m
JOIN matches_clean mc ON mc.match_id = m.match_id
WHERE m.team1 = :team OR m.team2 = :team
GROUP BY opponent
ORDER BY win_rate DESC, matches_played DESC;


-- name: team_bat_first_vs_chase
-- Own visual: the team's record batting first vs chasing
-- (question: does this team do better setting a target or chasing one?)
SELECT
    CASE WHEN vt.bat_first_team = :team THEN 'Batting first'
         ELSE 'Chasing' END AS batting_order,
    COUNT(*) AS matches_played,
    SUM(CASE WHEN vt.match_winner = :team THEN 1 ELSE 0 END) AS matches_won
FROM v_match_totals vt
JOIN matches m ON m.match_id = vt.match_id
WHERE m.team1 = :team OR m.team2 = :team
GROUP BY batting_order;