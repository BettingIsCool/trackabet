# TODO set up test environment
# TODO tag update not working (only after 2nd try)
# TODO add tennis sets/games explanation
# TODO color status / pl green-red
# TODO new layout / styled button -> https://www.youtube.com/watch?v=jbJpAdGlKVY
# TODO get rid of rerun (on_change function)
# TODO Re-arrange 'add a abet', collapse sidebar
# TODO Improvement idea: filters for leagues and markets.
# TODO Improvement idea: Have a auto complete on tags too so you can start entering the word like you do with bookmarkers. And maybe add the most recents tags under the form box so you can choose it.
# TODO session expired after a few minutes
# TODO refactoring / gold-plating
# TODO private github repo (streamlit teams)
# TODO streamlit-extras lib
# TODO bet size filter / clv filter
# TODO video covering sorting, exporting, tennis markets (games), future bets,...

import streamlit as st

# set_page_config() can only be called once per app page, and must be called as the first Streamlit command in your script.
st.set_page_config(page_title="Track-A-Bet by BettingIsCool", page_icon="🦈", layout="wide", initial_sidebar_state="expanded")

import time
import pytz
import math
import tools
import datetime
import pandas as pd
import db_pinnacle_remote as db

from config import SPORTS, PERIODS, BOOKS, TEXT_LANDING_PAGE

placeholder1 = st.empty()

if 'display_landing_page_text' not in st.session_state:

    # Display landing page (pre login)
    placeholder1.markdown(TEXT_LANDING_PAGE)
    st.session_state.display_landing_page_text = True

# Add google authentication (only users with a valid stripe subscription can log in
# Username must match the registered email-address at stripe
# IMPORTANT: st_paywall is a forked library. This fork supports additional verification, i.e. if the user has a valid subscription for the product
# The original st_paywall just looks into the stripe account for ANY valid subscription for that particular user, but doesn't care if this subscription is actually valid for a specific app.
# See also https://github.com/tylerjrichards/st-paywall/issues/75
# Importing this fork can be done with 'git+https://github.com/bettingiscool/st-paywall_fork.git@main' in the requirements.txt file

from st_paywall import add_auth
add_auth(required=True)

username = st.session_state.email

placeholder1.empty()

# Check if username is in database, otherwise append the user
if 'users_fetched' not in st.session_state:
    tools.clear_cache()
    if username not in set(db.get_users()):
        db.append_user(data={'username': username})

    # Create session token
    else:
        st.session_state.session_id = username + '_' + str(datetime.datetime.now())
        tools.get_active_session.clear()

    st.session_state.users_fetched = True

# Allow only ONE session per user
# See https://discuss.streamlit.io/t/right-way-to-manage-same-user-opening-multiple-sessions/25608

#if st.session_state.session_id == tools.get_active_session():
if True:

    # Set odds format
    if 'odds_display' not in st.session_state:
        st.session_state.odds_display = db.get_user_odds_display(username=username)[0]
    if 'timezone' not in st.session_state:
        st.session_state.timezone = db.get_user_timezone(username=username)[0]

    # Initialize bets_to_be_deleted & dataframes
    bets_to_be_deleted, df = set(), set()

    # Welcome message in the sidebar
    st.sidebar.markdown("Track-A-Bet by BettingIsCool v1.5.28")
    st.sidebar.title(f"Welcome {username}")

    st.sidebar.subheader('Add a bet')

    # User needs to select sport & date range before fixtures are being fetched from the database
    selected_sport = st.sidebar.selectbox(label='Select sport', options=SPORTS.keys(), index=None, placeholder='Start typing...', help='41 unique sports supported.')

    if selected_sport is not None:
        selected_from_date = st.sidebar.date_input(label='Select start date', value='today', min_value=datetime.date(year=2021, month=1, day=1), help='Specify what date you want to start searching for fixtures. You can either use the calendar or manually enter the date, i.e. 2024/08/19.')

        if selected_from_date:
            selected_to_date = st.sidebar.date_input(label='Select end date', value=selected_from_date + datetime.timedelta(days=0), min_value=selected_from_date + datetime.timedelta(days=0), max_value=selected_from_date + datetime.timedelta(days=3), help='Specify what date you want to end your search. Please note that a maximum range of 3 days is allowed to avoid excess server load.')

            # The event_options dictionary represents the event as a concatenated string (starts - league_name - runner_home - runner_away) with the event_id as key
            # This string is what users see in the dropdown menu
            if selected_to_date:
                # runtime_start = time.time()

                offset = tools.tz_diff(home='Europe/Vienna', away=st.session_state.timezone, on=None)
                events = db.get_fixtures(sport_id=SPORTS[selected_sport], date_from=datetime.datetime.combine(selected_from_date, datetime.datetime.min.time()) - datetime.timedelta(hours=int(offset)), date_to=datetime.datetime.combine(selected_to_date, datetime.datetime.min.time()) - datetime.timedelta(hours=int(offset)))

                # st.write(f"Runtime get_fixtures: {round(time.time() - runtime_start, 3)} seconds.")

                event_options, event_details = dict(), dict()
                for index, row in events.iterrows():
                    if row['event_id'] not in event_options.keys():
                        starts_converted_to_timezone = pytz.timezone('Europe/Vienna').localize(row['starts']).astimezone(pytz.timezone(st.session_state.timezone)).replace(tzinfo=None).strftime('%Y-%m-%d %H:%M')
                        event_options.update({row['event_id']: f"{starts_converted_to_timezone} {row['league_name'].upper()} {row['runner_home']} - {row['runner_away']}"})
                        event_details.update({row['event_id']: {'starts': row['starts'], 'league_id': row['league_id'], 'league_name': row['league_name'], 'runner_home': row['runner_home'], 'runner_away': row['runner_away']}})
                selected_event_id = st.sidebar.selectbox(label='Select event', options=event_options.keys(), index=None, format_func=lambda x: event_options.get(x), placeholder='Start typing...', help='Start searching your fixture by typing any league, home team, away team. Only fixtures with available odds are listed.')

                if selected_event_id is not None:
                    odds = db.get_odds(event_id=selected_event_id)
                    selected_market = st.sidebar.selectbox(label='Select market', options=odds.market.unique(), index=None, help='Only markets with available odds are listed.')

                    if selected_market is not None:
                        period_options = dict()
                        for index, row in odds.iterrows():
                            if row['market'] == selected_market and row['period'] not in period_options.keys():
                                period_options.update({row['period']: PERIODS[(SPORTS[selected_sport], row['period'])]})
                        selected_period = st.sidebar.selectbox(label='Select period', options=period_options.keys(), index=None, format_func=lambda x: period_options.get(x), help='Only periods with available closing odds are listed.')

                        if selected_period is not None:
                            side_options = dict()
                            for index, row in odds.iterrows():
                                if selected_market == 'moneyline':
                                    if row['market'] == selected_market and row['period'] == selected_period:
                                        if row['odds1'] is not None:
                                            side_options.update({'odds1': event_details[selected_event_id]['runner_home']})
                                        if row['odds0'] is not None:
                                            side_options.update({'odds0': 'Draw'})
                                        if row['odds2'] is not None:
                                            side_options.update({'odds2': event_details[selected_event_id]['runner_away']})

                                elif selected_market == 'spread':
                                    if row['market'] == selected_market and row['period'] == selected_period:
                                        if row['odds1'] is not None:
                                            side_options.update({'odds1': event_details[selected_event_id]['runner_home']})
                                        if row['odds2'] is not None:
                                            side_options.update({'odds2': event_details[selected_event_id]['runner_away']})

                                elif selected_market in ('totals', 'home_totals', 'away_totals'):
                                    if row['market'] == selected_market and row['period'] == selected_period:
                                        if row['odds1'] is not None:
                                            side_options.update({'odds1': 'Over'})
                                        if row['odds2'] is not None:
                                            side_options.update({'odds2': 'Under'})
                            selected_side = st.sidebar.selectbox(label='Select side', options=side_options.keys(), index=None, format_func=lambda x: side_options.get(x))

                            if selected_side is not None:
                                selected_line, line_options = None, dict()

                                # User has to select a line for all markets except moneyline
                                if selected_market != 'moneyline':

                                    # Please note that the selected home line is returned even if the selection is 'away' (raw_line in the database)
                                    for index, row in odds.iterrows():
                                        if row['market'] == selected_market and row['period'] == selected_period and row[selected_side] is not None:
                                            if row['market'] == 'spread' and selected_side == 'odds2':
                                                line_options.update({row['line']: -row['line']})
                                            else:
                                                line_options.update({row['line']: row['line']})
                                    selected_line = st.sidebar.selectbox(label='Select line', options=line_options.keys(), index=None, format_func=lambda x: line_options.get(x), help='Only lines with available closing odds are listed.')

                                if (selected_line is None and selected_market == 'moneyline') or (selected_line is not None and selected_market != 'moneyline'):
                                    if st.session_state.odds_display == 'American':
                                        american_odds = st.sidebar.number_input("Enter odds", min_value=-10000, value=100, step=1)
                                        odds = tools.get_decimal_odds(american_odds=american_odds)
                                    else:
                                        odds = st.sidebar.number_input("Enter odds", min_value=1.001, value=2.000, step=0.01, format="%0.3f")

                                    if odds:
                                        stake = st.sidebar.number_input("Enter stake", min_value=0.01, value=1.00, step=1.00, format="%0.2f")

                                        if stake:
                                            book = st.sidebar.selectbox("Select bookmaker", options=sorted(BOOKS))

                                            if book:
                                                tag = st.sidebar.text_input("Enter tag", max_chars=25, help='You can add a custom string to classify this bet as something that you may want to research in a future analysis. This could be a particular strategy, model or a tipster, etc.')

                                                data = dict()
                                                data.update({'user': username})
                                                data.update({'tag': tag})
                                                data.update({'starts': event_details[selected_event_id]['starts']})
                                                data.update({'sport_id': SPORTS[selected_sport]})
                                                data.update({'sport_name': selected_sport})
                                                data.update({'league_id': event_details[selected_event_id]['league_id']})
                                                data.update({'league_name': event_details[selected_event_id]['league_name']})
                                                data.update({'event_id': selected_event_id})
                                                data.update({'runner_home': event_details[selected_event_id]['runner_home']})
                                                data.update({'runner_away': event_details[selected_event_id]['runner_away']})
                                                data.update({'market': selected_market})
                                                data.update({'period': selected_period})
                                                data.update({'period_name': period_options[selected_period]})
                                                data.update({'side_name': side_options[selected_side]})
                                                data.update({'side': selected_side})
                                                data.update({'bet_status': 'na'})
                                                data.update({'score_home': 0})
                                                data.update({'score_away': 0})
                                                data.update({'profit': 0.00})
                                                data.update({'cls_odds': 0.00})
                                                data.update({'true_cls': 0.00})
                                                data.update({'cls_limit': 0.00})
                                                data.update({'ev': 0.00})
                                                data.update({'clv': 0.00})
                                                data.update({'odds': odds})
                                                data.update({'stake': stake})
                                                data.update({'bookmaker': book})
                                                data.update({'bet_added': datetime.datetime.now()})

                                                if selected_line is not None:
                                                    data.update({'raw_line': selected_line})
                                                    data.update({'line': line_options[selected_line]})
                                                else:
                                                    data.update({'raw_line': 0})
                                                    data.update({'line': 0})

                                                bet_added = st.sidebar.button('Add bet')

                                                if bet_added:
                                                    db.append_bet(data=data)
                                                    placeholder1.success('Bet added successfully!')
                                                    st.cache_data.clear()
                                                    time.sleep(1.5)
                                                    placeholder1.empty()

    col1, col2, col3, col4, col5, col6 = st.columns([4, 4, 5, 4, 2, 2])

    # Apply filter to recorded bets
    user_unique_sports = db.get_user_unique_sports(username=username)
    with col1:
        selected_sports = st.multiselect(label='Sports', options=sorted(user_unique_sports), default=user_unique_sports)
    selected_sports = [f"'{s}'" for s in selected_sports]
    selected_sports = f"({','.join(selected_sports)})"

    weighted_average_odds = 1.00
    if selected_sports != '()':
        user_unique_bookmakers = db.get_user_unique_bookmakers(username=username, sports=selected_sports)
        with col2:
            selected_bookmakers = st.multiselect(label='Bookmakers', options=sorted(user_unique_bookmakers), default=user_unique_bookmakers)
        selected_bookmakers = [f"'{s}'" for s in selected_bookmakers]
        selected_bookmakers = f"({','.join(selected_bookmakers)})"

        if selected_bookmakers != '()':
            user_unique_tags = db.get_user_unique_tags(username=username, sports=selected_sports, bookmakers=selected_bookmakers)
            with col3:
                selected_tags = st.multiselect(label='Tags', options=sorted(user_unique_tags), default=user_unique_tags)
            selected_tags = [f"'{s}'" for s in selected_tags]
            selected_tags = f"({','.join(selected_tags)})"

            if selected_tags != '()':
                user_unique_bet_status = db.get_user_unique_bet_status(username=username, sports=selected_sports, bookmakers=selected_bookmakers, tags=selected_tags)
                with col4:
                    selected_bet_status = st.multiselect(label='Status', options=sorted(user_unique_bet_status), default=user_unique_bet_status, help='Select the bet status. W = Won, HW = Half Won, L = Lost, HL = Half Lost, P = Push, V = Void, na = ungraded')
                selected_bet_status = [f"'{s}'" for s in selected_bet_status]
                selected_bet_status = f"({','.join(selected_bet_status)})"

                if selected_bet_status != '()':
                    user_unique_starts = db.get_user_unique_starts(username=username, sports=selected_sports, bookmakers=selected_bookmakers, tags=selected_tags, bet_status=selected_bet_status)

                    if user_unique_starts is not None:
                        with col5:
                            selected_date_from = st.date_input(label='Start', value=min(user_unique_starts), min_value=min(user_unique_starts), max_value=max(user_unique_starts), help='Specify the start date for analysis. You can either use the calendar or manually enter the date, i.e. 2024/08/19.')
                        with col6:
                            selected_date_to = st.date_input(label='End', value=max(user_unique_starts), min_value=min(user_unique_starts), max_value=max(user_unique_starts), help='Specify the end date for analysis. You can either use the calendar or manually enter the date, i.e. 2024/08/19.')

                        bets = db.get_bets(username=username, sports=selected_sports, bookmakers=selected_bookmakers, tags=selected_tags, bet_status=selected_bet_status, date_from=selected_date_from, date_to=selected_date_to)
                        bets_df = pd.DataFrame(data=bets)

                        # Convert datetimes to user timezone
                        # There is a possibility that the conversion fails if the timestamp falls into a time change
                        # See https://github.com/streamlit/streamlit/issues/1288
                        try:
                            bets_df.starts = bets_df.starts.dt.tz_localize('Europe/Vienna').dt.tz_convert(st.session_state.timezone).dt.tz_localize(None)
                        except Exception as ex:
                            pass

                        try:
                            bets_df.bet_added = bets_df.bet_added.dt.tz_localize('Europe/Vienna').dt.tz_convert(st.session_state.timezone).dt.tz_localize(None)
                        except Exception as ex:
                            pass

                        bets_df = bets_df.rename(columns={'delete_bet': 'DEL', 'id': 'ID', 'tag': 'TAG', 'starts': 'STARTS', 'sport_name': 'SPORT', 'league_name': 'LEAGUE', 'runner_home': 'RUNNER_HOME', 'runner_away': 'RUNNER_AWAY', 'market': 'MARKET', 'period_name': 'PERIOD', 'side_name': 'SIDE', 'line': 'LINE', 'odds': 'ODDS', 'stake': 'STAKE', 'bookmaker': 'BOOK', 'bet_status': 'ST', 'score_home': 'SH', 'score_away': 'SA', 'profit': 'P/L', 'cls_odds': 'CLS', 'true_cls': 'CLS_TRUE', 'cls_limit': 'CLS_LIMIT', 'ev': 'EXP_WIN', 'clv': 'CLV', 'bet_added': 'BET_ADDED'})
                        bets_df = bets_df[['DEL', 'TAG', 'STARTS', 'SPORT', 'LEAGUE', 'RUNNER_HOME', 'RUNNER_AWAY', 'MARKET', 'PERIOD', 'SIDE', 'LINE', 'ODDS', 'STAKE', 'BOOK', 'ST', 'SH', 'SA', 'P/L', 'CLS', 'CLS_TRUE', 'CLS_LIMIT', 'EXP_WIN', 'CLV', 'BET_ADDED', 'ID']]

                        # Calculate weighhted average odds (using decimal odds)
                        sumprod_odds_stake = 0.00
                        for index, row in bets_df.iterrows():
                            sumprod_odds_stake += row['ODDS'] * row['STAKE']
                        weighted_average_odds = sumprod_odds_stake / bets_df['STAKE'].sum()

                        # Apply font & background colors to cells, apply number formatting
                        if st.session_state.odds_display == 'American':
                            bets_df.ODDS = bets_df.ODDS.apply(tools.get_american_odds)
                            bets_df.CLS = bets_df.CLS.apply(tools.get_american_odds)
                            bets_df.CLS_TRUE = bets_df.CLS_TRUE.apply(tools.get_american_odds)
                            styled_df = bets_df.style.applymap(tools.color_cells, subset=['ST', 'P/L', 'EXP_WIN', 'CLV']).format({'LINE': '{:g}'.format, 'ODDS': '{0:g}'.format, 'STAKE': '{:,.2f}'.format, 'P/L': '{:,.2f}'.format, 'CLS': '{0:g}'.format, 'CLS_TRUE': '{0:g}'.format, 'CLS_LIMIT': '{:,.0f}'.format, 'EXP_WIN': '{:,.2f}'.format, 'CLV': '{:,.2%}'.format, 'SH': '{0:g}'.format, 'SA': '{0:g}'.format})
                        else:
                            styled_df = bets_df.style.applymap(tools.color_cells, subset=['ST', 'P/L', 'EXP_WIN', 'CLV']).format({'LINE': '{:g}'.format, 'ODDS': '{:,.3f}'.format, 'STAKE': '{:,.2f}'.format, 'P/L': '{:,.2f}'.format, 'CLS': '{:,.3f}'.format, 'CLS_TRUE': '{:,.3f}'.format, 'CLS_LIMIT': '{:,.0f}'.format, 'EXP_WIN': '{:,.2f}'.format, 'CLV': '{:,.2%}'.format, 'SH': '{0:g}'.format, 'SA': '{0:g}'.format})
                            pd.set_option("styler.render.max_elements", 33333333)

                        # Option without editable dataframe
                        #df = st.data_editor(styled_df, column_config={"DEL": st.column_config.CheckboxColumn("DEL", help="Select if you want to delete this bet.", default=False), "ST": st.column_config.TextColumn("ST", help="Bet Status. W = Won, HW = Half Won, L = Lost, HL = Half Lost, P = Push, V = Void, na = ungraded"), "TAG": st.column_config.Column("TAG", help="Tag your bets to classify them for future research, i.e. apply a tag filter. This could be a particular strategy, model or a tipster, etc."), "SH": st.column_config.Column("SH", help="Score Home"), "SA": st.column_config.Column("SA", help="Score Away"), "STARTS": st.column_config.Column("STARTS", help="Event starting time"), "SPORT": st.column_config.Column("SPORT", help="Sport"), "LEAGUE": st.column_config.Column("LEAGUE", help="League"), "RUNNER_HOME": st.column_config.Column("RUNNER_HOME", help="Home Team/Player 1"), "RUNNER_AWAY": st.column_config.Column("RUNNER_AWAY", help="Away Team/Player 2"), "MARKET": st.column_config.Column("MARKET", help="Market. This can be one of the following: MONEYLINE, SPREAD, TOTALS, HOME_TOTALS, AWAY_TOTALS"), "PERIOD": st.column_config.Column("PERIOD", help="Period. This refers to the game section of the bet, i.e. fulltime, halftime, 1st quarter, etc."), "SIDE": st.column_config.Column("SIDE", help="Selection"), "LINE": st.column_config.Column("LINE", help="Line refers to the handicap for spread & totals markets."), "ODDS": st.column_config.Column("ODDS", help="Obtained price"), "STAKE": st.column_config.Column("STAKE", help="Risk amount"), "BOOK": st.column_config.Column("BOOK", help="Bookmaker"), "P/L": st.column_config.Column("P/L", help="Actual profit"), "CLS": st.column_config.Column("CLS", help="Closing price"), "CLS_TRUE": st.column_config.Column("CLS_TRUE", help="Closing price with bookmaker margin removed (= no-vig closing odds)"), "CLS_LIMIT": st.column_config.Column("CLS_LIMIT", help="Maximum bet size at closing"), "EXP_WIN": st.column_config.Column("EXP_WIN", help="Expected Win. This is the expected value of your bet. This figure compares obtained odds with no-vig closing odds and takes into account the stake. Quality bets will typically have an exp_win > 0."), "CLV": st.column_config.Column("CLV", help="Closing line value. This is the expected roi of your bet. This figure compares obtained odds with no-vig closing odds. Quality bets will typically have a clv > 0."), "BET_ADDED": st.column_config.Column("BET_ADDED", help="Timestamp of the recorded bet.")}, disabled=['STARTS', 'SPORT', 'LEAGUE', 'RUNNER_HOME', 'RUNNER_AWAY', 'MARKET', 'PERIOD', 'SIDE', 'LINE', 'ODDS', 'CLS', 'CLS_TRUE', 'CLS_LIMIT', 'EXP_WIN', 'CLV', 'BET_ADDED', 'ID', 'TAG', 'STAKE', 'BOOK', 'ST', 'SH', 'SA', 'P/L'], key='initial_df_key', hide_index=True)

                        # START - Option with editable dataframe
                        if 'initial_df' not in st.session_state:
                            st.session_state['initial_df'] = placeholder1.data_editor(styled_df, column_config={"DEL": st.column_config.CheckboxColumn("DEL", help="Select if you want to delete this bet.", default=False), "ST": st.column_config.TextColumn("ST", help="Bet Status. W = Won, HW = Half Won, L = Lost, HL = Half Lost, P = Push, V = Void, na = ungraded. This will be settled automatically. Please be patient, this can take up to several hours. On rare occasions it is possible that the payout or grading you received from your sportsbook is different (i.e. due to divergent settlement rules if a match is abandoned or due to a retirement of a player). You can edit the value by double-clicking on the cell.", required=True), "TAG": st.column_config.TextColumn("TAG", help="Tag your bets to classify them for future research, i.e. apply a tag filter. This could be a particular strategy, model or a tipster, etc. You can edit the value with a double-click on the cell."), "SH": st.column_config.NumberColumn("SH", help="Score Home. This will be settled automatically. Please be patient, this can take up to several hours. On rare occasions it is possible that the payout or grading you received from your sportsbook is different (i.e. due to divergent settlement rules if a match is abandoned or due to a retirement of a player). You can edit the value by double-clicking on the cell.", required=True, min_value=0, max_value=1000, step=1), "P/L": st.column_config.NumberColumn("P/L", help="Actual profit. This will be settled automatically. Please be patient, this can take up to several hours. On rare occasions it is possible that the payout or grading you received from your sportsbook is different (i.e. due to divergent settlement rules if a match is abandoned or due to a retirement of a player). You can edit the value by double-clicking on the cell.", required=True, min_value=-1000000, max_value=1000000, step=0.01), "SA": st.column_config.NumberColumn("SA", help="Score Away. This will be settled automatically. Please be patient, this can take up to several hours. On rare occasions it is possible that the payout or grading you received from your sportsbook is different (i.e. due to divergent settlement rules if a match is abandoned or due to a retirement of a player). You can edit the value by double-clicking on the cell.", required=True, min_value=0, max_value=1000, step=1), "STARTS": st.column_config.DatetimeColumn("STARTS", help="Event starting time"), "SPORT": st.column_config.TextColumn("SPORT", help="Sport"), "LEAGUE": st.column_config.TextColumn("LEAGUE", help="League"), "RUNNER_HOME": st.column_config.TextColumn("RUNNER_HOME", help="Home Team/Player 1"), "RUNNER_AWAY": st.column_config.TextColumn("RUNNER_AWAY", help="Away Team/Player 2"), "MARKET": st.column_config.TextColumn("MARKET", help="Market. This can be one of the following: MONEYLINE, SPREAD, TOTALS, HOME_TOTALS, AWAY_TOTALS"), "PERIOD": st.column_config.TextColumn("PERIOD", help="Period. This refers to the game section of the bet, i.e. fulltime, halftime, 1st quarter, etc."), "SIDE": st.column_config.TextColumn("SIDE", help="Selection"), "LINE": st.column_config.NumberColumn("LINE", help="Line refers to the handicap for spread & totals markets."), "ODDS": st.column_config.NumberColumn("ODDS", help="Obtained price"), "STAKE": st.column_config.NumberColumn("STAKE", help="Risk amount"), "BOOK": st.column_config.TextColumn("BOOK", help="Bookmaker. You can edit the value with a double-click on the cell."), "CLS": st.column_config.NumberColumn("CLS", help="Closing price"), "CLS_TRUE": st.column_config.NumberColumn("CLS_TRUE", help="Closing price with bookmaker margin removed (= no-vig closing odds)"), "CLS_LIMIT": st.column_config.NumberColumn("CLS_LIMIT", help="Maximum bet size at closing"), "EXP_WIN": st.column_config.NumberColumn("EXP_WIN", help="Expected Win. This is the expected value of your bet. This figure compares obtained odds with no-vig closing odds and takes into account the stake. Quality bets will typically have an exp_win > 0."), "CLV": st.column_config.NumberColumn("CLV", help="Closing line value. This is the expected roi of your bet. This figure compares obtained odds with no-vig closing odds. Quality bets will typically have a clv > 0."), "BET_ADDED": st.column_config.DatetimeColumn("BET_ADDED", help="Timestamp of the recorded bet.")}, disabled=['STARTS', 'SPORT', 'LEAGUE', 'RUNNER_HOME', 'RUNNER_AWAY', 'MARKET', 'PERIOD', 'SIDE', 'LINE', 'ODDS', 'CLS', 'CLS_TRUE', 'CLS_LIMIT', 'EXP_WIN', 'CLV', 'BET_ADDED', 'ID', 'STAKE'], key='initial_df_key', hide_index=True)
                            placeholder1.empty()

                        st.session_state['edited_df'] = st.data_editor(styled_df, column_config={"DEL": st.column_config.CheckboxColumn("DEL", help="Select if you want to delete this bet.", default=False), "ST": st.column_config.TextColumn("ST", help="Bet Status. W = Won, HW = Half Won, L = Lost, HL = Half Lost, P = Push, V = Void, na = ungraded. This will be settled automatically. Please be patient, this can take up to several hours. On rare occasions it is possible that the payout or grading you received from your sportsbook is different (i.e. due to divergent settlement rules if a match is abandoned or due to a retirement of a player). You can edit the value by double-clicking on the cell.", required=True), "TAG": st.column_config.TextColumn("TAG", help="Tag your bets to classify them for future research, i.e. apply a tag filter. This could be a particular strategy, model or a tipster, etc. You can edit the value with a double-click on the cell."), "SH": st.column_config.NumberColumn("SH", help="Score Home. This will be settled automatically. Please be patient, this can take up to several hours. On rare occasions it is possible that the payout or grading you received from your sportsbook is different (i.e. due to divergent settlement rules if a match is abandoned or due to a retirement of a player). You can edit the value by double-clicking on the cell.", required=True, min_value=0, max_value=1000, step=1), "P/L": st.column_config.NumberColumn("P/L", help="Actual profit. This will be settled automatically. Please be patient, this can take up to several hours. On rare occasions it is possible that the payout or grading you received from your sportsbook is different (i.e. due to divergent settlement rules if a match is abandoned or due to a retirement of a player). You can edit the value by double-clicking on the cell.", required=True, min_value=-1000000, max_value=1000000, step=0.01), "SA": st.column_config.NumberColumn("SA", help="Score Away. This will be settled automatically. Please be patient, this can take up to several hours. On rare occasions it is possible that the payout or grading you received from your sportsbook is different (i.e. due to divergent settlement rules if a match is abandoned or due to a retirement of a player). You can edit the value by double-clicking on the cell.", required=True, min_value=0, max_value=1000, step=1), "STARTS": st.column_config.DatetimeColumn("STARTS", help="Event starting time"), "SPORT": st.column_config.TextColumn("SPORT", help="Sport"), "LEAGUE": st.column_config.TextColumn("LEAGUE", help="League"), "RUNNER_HOME": st.column_config.TextColumn("RUNNER_HOME", help="Home Team/Player 1"), "RUNNER_AWAY": st.column_config.TextColumn("RUNNER_AWAY", help="Away Team/Player 2"), "MARKET": st.column_config.TextColumn("MARKET", help="Market. This can be one of the following: MONEYLINE, SPREAD, TOTALS, HOME_TOTALS, AWAY_TOTALS"), "PERIOD": st.column_config.TextColumn("PERIOD", help="Period. This refers to the game section of the bet, i.e. fulltime, halftime, 1st quarter, etc."), "SIDE": st.column_config.TextColumn("SIDE", help="Selection"), "LINE": st.column_config.NumberColumn("LINE", help="Line refers to the handicap for spread & totals markets."), "ODDS": st.column_config.NumberColumn("ODDS", help="Obtained price"), "STAKE": st.column_config.NumberColumn("STAKE", help="Risk amount"), "BOOK": st.column_config.TextColumn("BOOK", help="Bookmaker. You can edit the value with a double-click on the cell."), "CLS": st.column_config.NumberColumn("CLS", help="Closing price"), "CLS_TRUE": st.column_config.NumberColumn("CLS_TRUE", help="Closing price with bookmaker margin removed (= no-vig closing odds)"), "CLS_LIMIT": st.column_config.NumberColumn("CLS_LIMIT", help="Maximum bet size at closing"), "EXP_WIN": st.column_config.NumberColumn("EXP_WIN", help="Expected Win. This is the expected value of your bet. This figure compares obtained odds with no-vig closing odds and takes into account the stake. Quality bets will typically have an exp_win > 0."), "CLV": st.column_config.NumberColumn("CLV", help="Closing line value. This is the expected roi of your bet. This figure compares obtained odds with no-vig closing odds. Quality bets will typically have a clv > 0."), "BET_ADDED": st.column_config.DatetimeColumn("BET_ADDED", help="Timestamp of the recorded bet.")}, disabled=['STARTS', 'SPORT', 'LEAGUE', 'RUNNER_HOME', 'RUNNER_AWAY', 'MARKET', 'PERIOD', 'SIDE', 'LINE', 'ODDS', 'CLS', 'CLS_TRUE', 'CLS_LIMIT', 'EXP_WIN', 'CLV', 'BET_ADDED', 'ID', 'STAKE'], key='edited_df_key', hide_index=True)

                        if not st.session_state['initial_df'].equals(st.session_state['edited_df']):

                            tools.update_bet(initial_df=st.session_state['initial_df'], edited_df=st.session_state['edited_df'], placeholder=placeholder1)
                            st.session_state['initial_df'] = st.session_state['edited_df']
                            st.rerun()

                        df = st.session_state['edited_df']
                        # END - Option with editable dataframe

                        bets_to_be_deleted = df.loc[(df['DEL'] == True), 'ID'].tolist()

    # Place Refresh & Delete button below dataframe
    # Delete button will only be visible if at least one event is selected
    st.button('Refresh', on_click=tools.clear_cache)
    if bets_to_be_deleted:
        st.button('Delete selected bet(s)', on_click=tools.delete_bets, args=(bets_to_be_deleted,), type="primary")

    # Display stats
    if len(df) > 0:

        bet_count = len(df[df['ST'] != 'na'])
        turnover = df.loc[df['ST'] != 'na', 'STAKE'].sum()
        sum_profit = df['P/L'].sum()
        sum_ev = df['EXP_WIN'].sum()
        act_roi = sum_profit / turnover
        clv = sum_ev / turnover

        implied_win_percentage = (clv + 1) / weighted_average_odds
        if implied_win_percentage > 0:
            yield_standard_deviation = weighted_average_odds * math.sqrt(implied_win_percentage - implied_win_percentage ** 2) / math.sqrt(bet_count)
            luck_factor, comment_luck_factor, color_luck_factor = tools.get_luck_factor(std_dev=yield_standard_deviation, act_roi=act_roi, clv=clv)
            format_luck_factor = 'g' if luck_factor == 0 else '+g'

            rating, comment_rating, color_rating = tools.get_rating(clv=clv)

            color_profit, color_clv, color_ev = tools.get_text_colouring(sum_profit=sum_profit, sum_ev=sum_ev)

            if st.session_state.odds_display == 'Decimal':
                st.title(f"BETS: :gray[{bet_count}] - TURNOVER: :gray[{int(turnover)}] - Ø-ODDS: :gray[{round(weighted_average_odds, 2):g}] - P/L: {color_profit}[{round(sum_profit, 2):+g}] - ROI: {color_profit}[{round(100 * act_roi, 2):+g}%]", help='Ø-ODDS are the average odds weighted by stake, i.e. if you have a bet at 2.0 with stake €200 and another bet at 3.0 with stake €100 then your weighted average odds are 2.33')
            else:
                st.title(f"BETS: :gray[{bet_count}] - TURNOVER: :gray[{int(turnover)}] - Ø-ODDS: :gray[{int(tools.get_american_odds(decimal_odds=weighted_average_odds))}] - P/L: {color_profit}[{round(sum_profit, 2):+g}] - ROI: {color_profit}[{round(100 * sum_profit / turnover, 2):+g}%]", help='Ø-ODDS are the average odds weighted by stake, i.e. if you have a bet at 2.0 with stake €200 and another bet at 3.0 with stake €100 then your weighted average odds are 2.33')

            st.subheader(f"EXP P/L: {color_ev}[{round(sum_ev, 2):+g}] - EXP ROI (CLV): {color_clv}[{round(100 * clv, 2):+g}%] - LUCK FACTOR: :{color_luck_factor}[{luck_factor:{format_luck_factor}}] :{color_luck_factor}[({comment_luck_factor})] - RATING: :{color_rating}[{rating}] :{color_rating}[({comment_rating})]", help='LUCK FACTOR gives you an idea of how lucky/unlucky you were with the results of your bets. This figure ranges from -3 (extremely unlucky) to +3 (extremely lucky) and is measured by how many standard deviations your actual roi is away from the mean. RATING indicates the quality of your bets, i.e. if they are +ev on average or not. This figure ranges from A (excellent) to F (terrible) and is based on the expected roi. This is the most important figure and should be monitored closely.')

            cum_profit, cum_clv, cum_bets, cur_profit, cur_clv, cur_bets = list(), list(), list(), 0.00, 0.00, 0
            for index, row in df.iterrows():
                if row['ST'] != 'na':
                    cur_profit += row['P/L']
                    cur_clv += row['EXP_WIN']
                    cur_bets += 1

                    cum_profit.append(cur_profit)
                    cum_clv.append(cur_clv)
                    cum_bets.append(cur_bets)

            chart_data = pd.DataFrame({"bet_no": cum_bets, "Actual P/L": cum_profit, "Expected P/L": cum_clv}, columns=["bet_no", "Actual P/L", "Expected P/L"])
            st.line_chart(chart_data, x="bet_no", y=["Actual P/L", "Expected P/L"], x_label='Bet no', y_label='Actual vs expected profit', color=["#FF0000", "#FFA500"], height=800)

    st.sidebar.image(image="media/logo_sbic.png", use_column_width='auto')

    # Create a radio button for Decimal/American odds format
    odds_display_options = ['Decimal', 'American']
    st.session_state.odds_display = st.sidebar.radio(label="Select odds format", options=odds_display_options, index=odds_display_options.index(st.session_state.odds_display), horizontal=True, on_change=db.set_user_odds_display, args=(username, placeholder1), key='odds_display_key')

    # Create selectbox for timezone
    timezone_options = pytz.common_timezones
    st.session_state.timezone = st.sidebar.selectbox(label="Select timezone", options=timezone_options, index=timezone_options.index(st.session_state.timezone), on_change=db.set_user_timezone, args=(username, placeholder1), key='timezone_key')

else:
    st.info('Your session has expired')
    for key in st.session_state.keys():
        del st.session_state[key]
