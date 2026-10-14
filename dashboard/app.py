import sqlite3                  # the same driver the notebooks use
import math                     # only for the chasing test numbers
import pandas as pd             # only to hold the rows a query returns
import plotly.express as px     # every chart on the page is drawn with this
import plotly.graph_objects as go   # only for the coloured table
import streamlit as st          # the page itself

st.set_page_config(page_title='IPL - Teams & Venues', layout='wide')   # wide, always
DB = r'C:\Users\ubaid\OneDrive\Desktop\sem-3\project 3.1\data\raw\ipl.db'   # the same file the notebooks read

# ---- professional, muted palette (replaces the bright Dark24 colours)
ORANGE, BLUE, LIGHT = '#d98324', '#1f3a5f', '#8fa9c4'   # accent, navy, soft blue used everywhere
TEAL, GREY = '#3f7f6e', '#c9ced6'                        # "good / enough" and "neutral / too few"
INK = '#1f2d3d'                                          # text colour
PALETTE = ['#1f3a5f', '#d98324', '#3f7f6e', '#7a5c8e', '#a64b4b', '#4a7aa8',
           '#8c8c3a', '#5b6770', '#b08d57', '#2f6f8f', '#8a5a44', '#6b8e4e'] * 4   # muted, repeated so we never run out


@st.cache_data                  # run each query once, not on every click
def q(sql, params=()):          # one helper for every query on the page
    with sqlite3.connect(DB) as con:        # opened and closed per call
        return pd.read_sql_query(sql, con, params=params)


def look(fig, x_title, y_title, height=420, legend=False, legend_title=''):   # the same clean look for every chart
    fig.update_layout(xaxis_title=x_title, yaxis_title=y_title, height=height, showlegend=legend,
                      legend_title_text=legend_title, plot_bgcolor='white', coloraxis_showscale=False,
                      font=dict(color=INK, size=14), margin=dict(t=30, b=10),
                      xaxis=dict(title_font=dict(size=15), automargin=True),
                      yaxis=dict(title_font=dict(size=15), automargin=True))
    fig.update_xaxes(showgrid=False, linecolor='#b8c2cc')
    fig.update_yaxes(gridcolor='#e8eef5')


# header and cards
st.markdown('''
<style>
.banner {background: linear-gradient(90deg, #1f3a5f, #2f5d7c); padding: 20px 26px; border-radius: 12px; color: white;}
.banner .big {font-size: 34px; font-weight: 700;}
[data-testid="stMetric"] {background: #f3f6fa; border-left: 5px solid #1f3a5f; padding: 12px 16px; border-radius: 8px;}
[data-testid="stMetricValue"], [data-testid="stMetricLabel"] {color: #1f2d3d;}
.stTabs [data-baseweb="tab"] {font-size: 18px; font-weight: 600;}
h3 {border-left: 5px solid #1f3a5f; padding-left: 10px;}
</style>
<div class="banner">
  <span class="big">IPL Cricket Analytics</span><br>
  Domain D - Teams &amp; Venues &nbsp;|&nbsp; For the team manager: where we play well, and who we play well against.
</div>
''', unsafe_allow_html=True)
st.write('')

# lists used on more than one tab
venues = q('''
    SELECT venue_clean AS ground, COUNT(*) AS matches
    FROM matches_clean
    GROUP BY venue_clean
    ORDER BY matches DESC, venue_clean
''')                                                          # grounds, most matches first
teams = q('''
    SELECT team1 AS t FROM matches
    UNION
    SELECT team2 FROM matches
    ORDER BY t
''')['t'].tolist()                                            # both team columns, so no team is missed
TEAM_COLORS = dict(zip(teams, PALETTE))                       # every team keeps its colour on every chart
GROUND_COLORS = dict(zip(venues['ground'], PALETTE))          # every ground keeps its colour on every chart

tab1, tab2, tab3 = st.tabs(['Overview', 'Venue', 'Team'])


# ============================================================
# TAB 1 : OVERVIEW (all teams, all grounds)
# ============================================================
with tab1:

    # ---- cards 1 and 2: how big is the data
    n_teams = int(q('SELECT COUNT(*) AS n FROM (SELECT team1 FROM matches UNION SELECT team2 FROM matches)').iloc[0]['n'])
    n_grounds = int(q('SELECT COUNT(DISTINCT venue_clean) AS n FROM matches_clean').iloc[0]['n'])
    n_raw = int(q('SELECT COUNT(DISTINCT venue) AS n FROM matches').iloc[0]['n'])     # names before cleaning
    n_matches = int(q('SELECT COUNT(*) AS n FROM matches_clean').iloc[0]['n'])

    # ---- card 3: the chasing test
    chase = q('SELECT COUNT(*) AS decided, SUM(chase_won) AS wins FROM v_match_totals')
    decided = int(chase.iloc[0]['decided'])
    chase_wins = int(chase.iloc[0]['wins'])
    p = chase_wins / decided                                  # share of matches the chasing side won
    se = math.sqrt(p * (1 - p) / decided)                     # standard error
    low, high = 100 * (p - 1.96 * se), 100 * (p + 1.96 * se)  # 95% interval
    z = (p - 0.5) / math.sqrt(0.25 / decided)                 # test against 50%
    p_value = math.erfc(abs(z) / math.sqrt(2))                # two-sided p-value
    p_text = 'p < 0.001' if p_value < 0.001 else f'p = {p_value:.3f}'

    c1, c2, c3 = st.columns([1, 1, 2])
    c1.metric('Teams', n_teams)
    c1.metric('Grounds', n_grounds)
    c1.caption(f'After cleaning. The raw data spells these {n_grounds} grounds {n_raw} different ways.')
    c2.metric('Matches played', n_matches)
    c2.caption('Every team and ground figure below is a share of this.')
    c3.metric('Chasing win %', f'{100 * p:.1f}%')
    c3.caption(f'{chase_wins} chasing wins in {decided} decided matches. 95% interval {low:.1f}% to {high:.1f}%. '
               f'Test against 50%: z = {z:.2f}, {p_text}.')
    if p_value < 0.05:
        c3.caption('Result: chasing is clearly different from a coin toss.')
    else:
        c3.caption('Result: chasing and batting first win about equally often. The gap from 50% could be luck.')

    # ---- chart 4 (hero): matches won by each team, with matches played
    wins = q('''
        SELECT t.team,
               COUNT(*) AS played,
               SUM(CASE WHEN mc.match_winner = t.team THEN 1 ELSE 0 END) AS won
        FROM (SELECT match_id, team1 AS team FROM matches
              UNION ALL
              SELECT match_id, team2 AS team FROM matches) t
        JOIN matches_clean mc ON mc.match_id = t.match_id
        GROUP BY t.team
        ORDER BY won DESC
    ''')
    wins['label'] = (wins['won'].astype(str) + ' won of ' + wins['played'].astype(str) + ' played ('
                     + (100 * wins['won'] / wins['played']).round(0).astype(int).astype(str) + '%)')

    fig = px.bar(wins, x='won', y='team', orientation='h', text='label', color_discrete_sequence=[BLUE])
    fig.update_traces(textposition='outside')
    fig.update_yaxes(categoryorder='total ascending')         # biggest bar on top
    fig.update_xaxes(range=[0, wins['won'].max() * 1.4])      # room for the labels
    look(fig, 'Matches won', 'Team', height=max(400, 35 * len(wins)))

    st.subheader(f'{wins.iloc[0]["team"]} have won the most matches: {int(wins.iloc[0]["won"])} of {int(wins.iloc[0]["played"])}')
    st.plotly_chart(fig, use_container_width=True)
    st.caption('Each bar is matches won. The label shows matches played too, because a team that has played more has had more chances to win.')

    # ---- chart 5: matches held at each ground, with the cut-off line
    min_matches = st.slider('Cut-off: minimum matches before we trust a ground', 5, 50, 20)
    grounds = venues.copy()
    grounds['enough'] = grounds['matches'].apply(lambda x: 'Enough to judge' if x >= min_matches else 'Too few to judge')

    fig = px.bar(grounds, x='matches', y='ground', orientation='h', text='matches', color='enough',
                 color_discrete_map={'Enough to judge': TEAL, 'Too few to judge': GREY})
    fig.add_vline(x=min_matches, line_dash='dash', line_color=ORANGE, annotation_text=f'cut-off {min_matches}')
    fig.update_traces(textposition='outside')
    fig.update_yaxes(categoryorder='total ascending')
    look(fig, 'Matches held', 'Ground', height=max(450, 24 * len(grounds)), legend=True)

    n_enough = int((grounds['matches'] >= min_matches).sum())
    st.subheader(f'Only {n_enough} of {len(grounds)} grounds have {min_matches} or more matches')
    st.plotly_chart(fig, use_container_width=True)
    st.caption('Each bar is one ground (cleaned names). Green bars are past the cut-off line: enough matches to say something. Grey bars are too few.')

    # ---- chart 6: how often batting first wins, grounds above the cut-off
    bat = q('''
        SELECT venue_clean AS ground,
               COUNT(*) AS decided,
               ROUND(100.0 * SUM(1 - chase_won) / COUNT(*), 1) AS bat_pct
        FROM v_match_totals
        WHERE venue_clean IN (SELECT venue_clean FROM matches_clean GROUP BY venue_clean HAVING COUNT(*) >= ?)
        GROUP BY venue_clean
        ORDER BY bat_pct DESC
    ''', (min_matches,))
    league_bat = float(q('SELECT ROUND(100.0 * SUM(1 - chase_won) / COUNT(*), 1) AS pct FROM v_match_totals').iloc[0]['pct'])

    if bat.empty:
        st.info('No ground has that many matches. Lower the cut-off.')
    else:
        bat['vs league'] = bat['bat_pct'].apply(lambda x: 'Above league' if x > league_bat else 'At or below league')
        bat['label'] = bat['bat_pct'].astype(str) + '%<br>n=' + bat['decided'].astype(str)

        fig = px.bar(bat, x='ground', y='bat_pct', text='label', color='vs league',
                     color_discrete_map={'Above league': ORANGE, 'At or below league': BLUE})
        fig.add_hline(y=league_bat, line_dash='dash', line_color='black', annotation_text=f'league {league_bat}%')
        fig.update_traces(textposition='outside')
        fig.update_yaxes(range=[0, 100])
        fig.update_xaxes(tickangle=-40)
        look(fig, 'Ground', 'Batting-first win (%)', height=550, legend=True)

        st.subheader(f'Batting first works best at {bat.iloc[0]["ground"]} and worst at {bat.iloc[-1]["ground"]}')
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f'Only grounds with {min_matches}+ matches. Orange bars beat the dashed league line: batting first works better there '
                   'than in the IPL overall. n = decided matches.')

    # ---- own chart 1: sixes by team (question: which teams lean on big hitting?)
    sixes = q('''
        SELECT batting_team AS team, SUM(CASE WHEN batter_runs = 6 THEN 1 ELSE 0 END) AS sixes
        FROM v_ball
        GROUP BY batting_team
        ORDER BY sixes DESC
    ''')
    fig = px.bar(sixes, x='sixes', y='team', orientation='h', text='sixes', color_discrete_sequence=[BLUE])
    fig.update_traces(textposition='outside')
    fig.update_yaxes(categoryorder='total ascending')
    look(fig, 'Total sixes', 'Team', height=max(400, 35 * len(sixes)))

    st.subheader(f'{sixes.iloc[0]["team"]} have hit the most sixes: {int(sixes.iloc[0]["sixes"])}')
    st.plotly_chart(fig, use_container_width=True)
    st.caption('Total sixes over all seasons. Teams that played more matches have had more chances.')

    # ---- own chart 2 (a table): grounds used each season (question: has the tournament spread out?)
    gs = q('''
        SELECT season_year AS season, COUNT(DISTINCT venue_clean) AS grounds
        FROM matches_clean
        GROUP BY season_year
        ORDER BY season_year
    ''')
    shade = (gs['grounds'] - gs['grounds'].min()) / max(1, gs['grounds'].max() - gs['grounds'].min())   # 0 = fewest, 1 = most
    fills = px.colors.sample_colorscale('Blues', list(shade * 0.85 + 0.1))                       # light blue to dark blue
    fig = go.Figure(go.Table(
        header=dict(values=['Season'] + gs['season'].astype(str).tolist(),
                    fill_color=BLUE, font=dict(color='white', size=15), align='center', height=36),
        cells=dict(values=[['Grounds used']] + [[int(v)] for v in gs['grounds']],
                   fill_color=[['#e3e7ed']] + [[c] for c in fills],
                   font=dict(color=[[INK]] + [['white' if s > 0.5 else INK] for s in shade], size=18),
                   align='center', height=44)))
    fig.update_layout(height=140, margin=dict(t=5, b=5, l=5, r=5))

    most = int(gs['grounds'].max())
    most_years = ', '.join(gs[gs['grounds'] == most]['season'].astype(str))
    st.subheader(f'{int(gs.iloc[0]["grounds"])} grounds in {gs.iloc[0]["season"]}, {int(gs.iloc[-1]["grounds"])} in {gs.iloc[-1]["season"]}; '
                 f'the most was {most} ({most_years})')
    st.plotly_chart(fig, use_container_width=True)
    st.caption('Each column is one season; the number is how many different grounds hosted matches. The darker the blue, the more grounds.')


# ============================================================
# TAB 2 : VENUE (one or more grounds)
# ============================================================
with tab2:

    # ---- picker: built from venue_clean, most matches first
    chosen = st.multiselect('Select one or more grounds (most matches first)', venues['ground'].tolist(),
                            default=[venues.iloc[0]['ground']])         # starts with the busiest ground
    if not chosen:                                                      # an empty picker would give empty charts
        chosen = [venues.iloc[0]['ground']]
        st.info(f'No ground selected, so showing {chosen[0]}.')
    marks = ','.join('?' * len(chosen))                                 # one ? per ground, for SQL IN (...)

    # ---- card 1 (mini table): matches held at each selected ground, every column left-aligned
    held = venues[venues['ground'].isin(chosen)].copy()
    held['Enough to judge?'] = held['matches'].apply(lambda x: 'Yes' if x >= min_matches else 'No - too few')
    held.columns = ['Ground', 'Matches held', 'Enough to judge?']
    few = held[held['Matches held'] < min_matches]['Ground'].tolist()
    st.subheader('Matches held at the selected grounds')
    held_view = held.copy()
    held_view['Matches held'] = held_view['Matches held'].astype(str)        # text, so it is left-aligned like the other columns
    st.dataframe(held_view, hide_index=True, use_container_width=True,       # no 0, 3, 5... index column
                 column_config={'Ground': st.column_config.TextColumn('Ground'),
                                'Matches held': st.column_config.TextColumn('Matches held'),
                                'Enough to judge?': st.column_config.TextColumn('Enough to judge?')})
    if few:
        st.warning(f'Fewer than {min_matches} matches at: {", ".join(few)}. Do not trust the numbers below for these grounds.')

    # ---- chart 2 (hero): average first-innings score against the league average
    score = q(f'''
        SELECT mc.venue_clean AS ground, ROUND(AVG(i.runs), 1) AS avg_runs
        FROM v_innings i
        JOIN matches_clean mc ON mc.match_id = i.match_id
        WHERE i.innings = 1 AND mc.venue_clean IN ({marks})
        GROUP BY mc.venue_clean
        ORDER BY avg_runs DESC
    ''', tuple(chosen))
    league_avg = float(q('SELECT ROUND(AVG(runs), 1) AS a FROM v_innings WHERE innings = 1').iloc[0]['a'])

    fig = px.bar(score, x='ground', y='avg_runs', text='avg_runs', color='ground', color_discrete_map=GROUND_COLORS)
    fig.add_hline(y=league_avg, line_dash='dash', line_color='black', annotation_text=f'league average {league_avg} (all grounds)')
    fig.update_traces(textposition='outside')
    fig.update_yaxes(range=[0, max(score['avg_runs'].max(), league_avg) * 1.25])
    fig.update_xaxes(tickangle=-30)
    look(fig, 'Ground (selected above)', 'Average first-innings score (runs)', height=480)

    top = score.iloc[0]
    gap = top['avg_runs'] - league_avg
    st.subheader(f'{top["ground"]} scores highest: {top["avg_runs"]} runs, {abs(gap):.1f} {"above" if gap >= 0 else "below"} the league average of {league_avg}')
    st.plotly_chart(fig, use_container_width=True)
    st.caption('Each bar is the average first-innings score at one selected ground (name under the bar). A bar above the dashed line is a '
               'higher-scoring ground than the IPL overall; below the line, lower-scoring.')

    # ---- chart 3: batting first against chasing at each ground, with the match count
    vc = q(f'''
        SELECT venue_clean AS ground, COUNT(*) AS decided, SUM(chase_won) AS chase_wins
        FROM v_match_totals
        WHERE venue_clean IN ({marks})
        GROUP BY venue_clean
        ORDER BY decided DESC
    ''', tuple(chosen))

    if vc.empty:
        st.info('No decided matches at the selected grounds.')
    else:
        vc['axis'] = vc['ground'] + '<br>(' + vc['decided'].astype(str) + ' decided matches)'     # match count under each ground
        vc['Batting first won'] = 100 * (vc['decided'] - vc['chase_wins']) / vc['decided']
        vc['Chasing won'] = 100 * vc['chase_wins'] / vc['decided']
        outcome = vc.melt(id_vars='axis', value_vars=['Batting first won', 'Chasing won'], var_name='Result', value_name='Share')

        fig = px.bar(outcome, x='axis', y='Share', color='Result', barmode='group', text='Share',
                     color_discrete_map={'Batting first won': ORANGE, 'Chasing won': BLUE})
        fig.add_hline(y=50, line_dash='dash', line_color='black', annotation_text='50% (equal)')
        fig.update_traces(texttemplate='%{y:.0f}%', textposition='outside')
        fig.update_yaxes(range=[0, 110])
        fig.update_xaxes(tickangle=-30)
        look(fig, 'Ground (number of decided matches in brackets)', 'Share of decided matches won (%)',
             height=480, legend=True, legend_title='Which side won')

        bat_better = int((vc['Batting first won'] > vc['Chasing won']).sum())
        chase_better = int((vc['Chasing won'] > vc['Batting first won']).sum())
        if len(vc) == 1:                                                # one ground: say it directly
            who = 'Batting first' if bat_better else ('Chasing' if chase_better else 'Neither side')
            st.subheader(f'{who} wins more often at {vc.iloc[0]["ground"]}')
        else:
            st.subheader(f'Batting first wins more often at {bat_better} of the {len(vc)} selected grounds, chasing at {chase_better}')
        st.plotly_chart(fig, use_container_width=True)
        st.caption('Each pair of bars is one ground: the share of its decided matches won by the side batting first (orange) and by the side chasing (blue). '
                   'The match count is under the ground name; the dashed line is 50%.')

    # ---- own chart: first-innings score by season (question: are these grounds getting higher scoring?)
    vs = q(f'''
        SELECT mc.venue_clean AS ground, mc.season_year AS season, COUNT(*) AS matches, ROUND(AVG(i.runs), 1) AS avg_runs
        FROM v_innings i
        JOIN matches_clean mc ON mc.match_id = i.match_id
        WHERE i.innings = 1 AND mc.venue_clean IN ({marks})
        GROUP BY mc.venue_clean, mc.season_year
        ORDER BY mc.season_year
    ''', tuple(chosen))
    vs['season'] = vs['season'].astype(str)                             # plain years on the axis

    fig = px.line(vs, x='season', y='avg_runs', color='ground', markers=True, hover_data=['matches'],
                  color_discrete_map=GROUND_COLORS)
    fig.add_hline(y=league_avg, line_dash='dash', line_color='black', annotation_text=f'league average {league_avg} (all grounds)')
    fig.update_traces(line_width=3)
    fig.update_xaxes(type='category', categoryorder='array', categoryarray=sorted(vs['season'].unique()))
    look(fig, 'Season (year)', 'Average first-innings score (runs)', height=480, legend=True, legend_title='Ground')

    st.subheader('Is scoring going up or down? One line for each selected ground')
    st.plotly_chart(fig, use_container_width=True)
    st.caption('Each point is one season at a ground: the average first-innings score. The legend on the right names each line. '
               'Hover a point to see how many matches it is built on; a season with only 1 or 2 matches can swing a lot.')


# ============================================================
# TAB 3 : TEAM (one side at a time)
# ============================================================
with tab3:

    # ---- picker: team1 and team2 together, so no team is missed
    team = st.selectbox('Select a team', teams)
    st.caption(f'The list has {len(teams)} teams. The Overview tab counts {n_teams}.')           # must match

    # ---- season filter: every card and chart on this tab follows it
    seasons = [int(x) for x in q('SELECT DISTINCT season_year AS s FROM matches_clean ORDER BY s')['s']]
    lo, hi = st.select_slider('Seasons to include', options=seasons, value=(seasons[0], seasons[-1]))
    st.caption(f'Everything on this tab covers {lo} to {hi}. Move the ends of the slider to compare periods.')

    # ---- card 1: played, won, win rate
    rec = q('''
        SELECT COUNT(*) AS played, SUM(CASE WHEN match_winner = ? THEN 1 ELSE 0 END) AS won
        FROM matches_clean
        WHERE match_id IN (SELECT match_id FROM matches WHERE team1 = ? OR team2 = ?)
          AND season_year BETWEEN ? AND ?
    ''', (team, team, team, lo, hi))
    played = int(rec.iloc[0]['played'])
    if played == 0:                                                      # nothing to show for this team in these seasons
        st.warning(f'{team} played no matches between {lo} and {hi}. Widen the season slider.')
        st.stop()
    won = int(rec.iloc[0]['won'])

    c1, c2, c3 = st.columns(3)
    c1.metric('Matches played', played)
    c2.metric('Matches won', won)
    c3.metric('Win rate', f'{100 * won / played:.1f}%')
    st.caption(f'Seasons {lo} to {hi}. Read the three together: a high win rate from very few matches does not mean much.')

    # ---- chart 2 (hero): win rate by season, with the 50% line
    ts = q('''
        SELECT mc.season_year AS season, COUNT(*) AS played,
               ROUND(100.0 * SUM(CASE WHEN mc.match_winner = ? THEN 1 ELSE 0 END) / COUNT(*), 1) AS win_pct
        FROM matches_clean mc
        WHERE mc.match_id IN (SELECT match_id FROM matches WHERE team1 = ? OR team2 = ?)
          AND mc.season_year BETWEEN ? AND ?
        GROUP BY mc.season_year
        ORDER BY mc.season_year
    ''', (team, team, team, lo, hi))
    ts['season'] = ts['season'].astype(str)                              # plain years on the axis
    ts['label'] = ts['win_pct'].round(0).astype(int).astype(str) + '% (n=' + ts['played'].astype(str) + ')'

    fig = px.line(ts, x='season', y='win_pct', markers=True, text='label', color_discrete_sequence=[TEAM_COLORS[team]])
    fig.add_hline(y=50, line_dash='dash', line_color='black', annotation_text='50%')
    fig.update_traces(textposition='top center', line_width=4, marker_size=10)
    fig.update_xaxes(type='category')
    fig.update_yaxes(range=[0, 110])
    look(fig, 'Season', 'Win rate (%)', height=450)

    best = ts.sort_values('win_pct').iloc[-1]
    worst = ts.sort_values('win_pct').iloc[0]
    st.subheader(f'{team}: best season {best["season"]} ({best["win_pct"]}%), weakest {worst["season"]} ({worst["win_pct"]}%)')
    st.plotly_chart(fig, use_container_width=True)
    st.caption('Each point is one season: the % of matches won. n = matches that season. Above the dashed 50% line the team won more than it lost.')

    # ---- chart 3: record against each opponent, sorted, with matches played
    opp = q('''
        SELECT CASE WHEN m.team1 = ? THEN m.team2 ELSE m.team1 END AS opponent,
               COUNT(*) AS played,
               SUM(CASE WHEN mc.match_winner = ? THEN 1 ELSE 0 END) AS won,
               ROUND(100.0 * SUM(CASE WHEN mc.match_winner = ? THEN 1 ELSE 0 END) / COUNT(*), 1) AS win_pct
        FROM matches m
        JOIN matches_clean mc ON mc.match_id = m.match_id
        WHERE (m.team1 = ? OR m.team2 = ?) AND mc.season_year BETWEEN ? AND ?
        GROUP BY opponent
        ORDER BY win_pct DESC, played DESC
    ''', (team, team, team, team, team, lo, hi))
    opp['label'] = opp['win_pct'].astype(str) + '% (' + opp['won'].astype(int).astype(str) + ' won of ' + opp['played'].astype(str) + ')'

    fig = px.bar(opp, x='win_pct', y='opponent', orientation='h', text='label',
                 color='win_pct', color_continuous_scale=['#b85c5c', '#e9e4d6', '#3f7f6e'], range_color=[0, 100])   # muted red = loses, green = wins
    fig.add_vline(x=50, line_dash='dash', line_color='black', annotation_text='50%')
    fig.update_traces(textposition='outside')
    fig.update_yaxes(categoryorder='total ascending')
    fig.update_xaxes(range=[0, 135])
    look(fig, 'Win rate against them (%)', 'Opponent', height=max(400, 40 * len(opp)))

    st.subheader(f'{team} do best against {opp.iloc[0]["opponent"]} ({opp.iloc[0]["win_pct"]}%) and worst against {opp.iloc[-1]["opponent"]} ({opp.iloc[-1]["win_pct"]}%)')
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f'Seasons {lo} to {hi}. Each bar is the % of matches won against one opponent; the label shows how many matches. '
               'Green = we usually win, red = we usually lose; past the dashed 50% line we win more often than not.')

    # ---- own chart: batting first against chasing (question: do they do better setting or chasing?)
    tb = q('''
        SELECT CASE WHEN vt.bat_first_team = ? THEN 'Batting first' ELSE 'Chasing' END AS batting_order,
               COUNT(*) AS played,
               SUM(CASE WHEN vt.match_winner = ? THEN 1 ELSE 0 END) AS won
        FROM v_match_totals vt
        JOIN matches m ON m.match_id = vt.match_id
        WHERE (m.team1 = ? OR m.team2 = ?) AND vt.season_year BETWEEN ? AND ?
        GROUP BY batting_order
    ''', (team, team, team, team, lo, hi))
    tb['win_pct'] = (100 * tb['won'] / tb['played']).round(1)
    tb['label'] = tb['win_pct'].astype(str) + '% (' + tb['won'].astype(int).astype(str) + ' won of ' + tb['played'].astype(str) + ')'

    fig = px.bar(tb, x='batting_order', y='win_pct', text='label', color='batting_order',
                 color_discrete_map={'Batting first': ORANGE, 'Chasing': BLUE})
    fig.add_hline(y=50, line_dash='dash', line_color='black', annotation_text='50%')
    fig.update_traces(textposition='outside')
    fig.update_yaxes(range=[0, 110])
    look(fig, 'When the team', 'Win rate (%)')

    better = tb.sort_values('win_pct').iloc[-1]
    st.subheader(f'{team} win more often when {better["batting_order"].lower()} ({better["win_pct"]}%)')
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f'Seasons {lo} to {hi}. Each bar is the % of matches won when the team batted first, and when it chased. The label shows the number of matches.')