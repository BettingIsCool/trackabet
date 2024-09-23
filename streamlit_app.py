


# TODO explain header columns (either as a legend or as a tooltip)
# TODO check if bet_status filter works for 'na' & 'HL'
# TODO import @pyckio picks (complete database) + compare if results match
# TODO private github repo (streamlit teams)
# TODO streamlit-extras lib
# TODO check database indexes
# TODO track-a-ber by bettingiscool + version number (itslic) upper/lower sidebar
# TODO introduce luck factor/rating/comment (rated by standard deviations away from mean)
# TODO add 'sort rows by clicking on the column header'
# TODO add average odds
# TODO Don't allow writing/searching in timezone selectbox (this could lead to error)
# TODO doublecheck error when switching decimal/american (maybe multiple tabs open)

import streamlit as st

# set_page_config() can only be called once per app page, and must be called as the first Streamlit command in your script.
st.set_page_config(page_title="Track-A-Bet by BettingIsCool", page_icon="🦈", layout="wide", initial_sidebar_state="expanded")

import pytz
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
    tools.refresh_table()
    if username not in set(db.get_users()):
        db.append_user(data={'username': username})
    st.session_state.users_fetched = True

# Set odds format
if 'odds_display' not in st.session_state:
    st.session_state.odds_display = db.get_user_odds_display(username=username)[0]
if 'timezone' not in st.session_state:
    st.session_state.timezone = db.get_user_timezone(username=username)[0]

# Initialize bets_to_be_deleted & dataframe
bets_to_be_deleted, df = set(), set()

# Welcome message in the sidebar
st.sidebar.markdown("Track-A-Bet by BettingIsCool v1.0.0")
st.sidebar.title(f"Welcome {username}")

# Create a radio button for Decimal/American odds format
odds_display_options = ['Decimal', 'American']
selected_odds_display = st.sidebar.radio(label="Select odds format", options=odds_display_options, index=odds_display_options.index(st.session_state.odds_display))
if st.session_state.odds_display != selected_odds_display:
    db.update_user_odds_display(username=username, odds_display=selected_odds_display)
    st.session_state.odds_display = selected_odds_display

timezone_options = pytz.common_timezones
selected_timezone = st.sidebar.selectbox(label='Select timezone', options=timezone_options, index=timezone_options.index(st.session_state.timezone))
if st.session_state.timezone != selected_timezone:
    db.update_user_timezone(username=username, timezone=selected_timezone)
    st.session_state.odds_display = selected_timezone

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
            events = db.get_fixtures(sport_id=SPORTS[selected_sport], date_from=selected_from_date, date_to=selected_to_date)

            event_options, event_details = dict(), dict()
            for index, row in events.iterrows():
                if row['event_id'] not in event_options.keys():
                    event_options.update({row['event_id']: f"{row['starts']} {row['league_name'].upper()} {row['runner_home']} - {row['runner_away']}"})
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
                                    odds = st.sidebar.number_input("Enter odds", min_value=-10000, value=100, step=1)
                                else:
                                    american_odds = st.sidebar.number_input("Enter odds", min_value=1.001, value=2.000, step=0.01, format="%0.3f")
                                    odds = tools.get_decimal_odds(american_odds=american_odds)

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
                                                st.cache_data.clear()

col1, col2, col3, col4, col5, col6 = st.columns([4, 4, 5, 4, 2, 2])

# Apply filter to recorded bets
user_unique_sports = db.get_user_unique_sports(username=username)
with col1:
    selected_sports = st.multiselect(label='Sports', options=sorted(user_unique_sports), default=user_unique_sports)
selected_sports = [f"'{s}'" for s in selected_sports]
selected_sports = f"({','.join(selected_sports)})"

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

                    bets = db.get_bets(username=username, sports=selected_sports, bookmakers=selected_bookmakers, tags=selected_tags, date_from=selected_date_from, date_to=selected_date_to)
                    bets_df = pd.DataFrame(data=bets)

                    # Convert datetimes to user timezone
                    bets_df.starts = bets_df.starts.dt.tz_localize('Europe/Vienna').dt.tz_convert(selected_timezone).dt.tz_localize(None)
                    bets_df.bet_added = bets_df.bet_added.dt.tz_localize('Europe/Vienna').dt.tz_convert(selected_timezone).dt.tz_localize(None)

                    bets_df = bets_df.rename(columns={'delete_bet': 'DEL', 'id': 'ID', 'tag': 'TAG', 'starts': 'STARTS', 'sport_name': 'SPORT', 'league_name': 'LEAGUE', 'runner_home': 'RUNNER_HOME', 'runner_away': 'RUNNER_AWAY', 'market': 'MARKET', 'period_name': 'PERIOD', 'side_name': 'SIDE', 'line': 'LINE', 'odds': 'ODDS', 'stake': 'STAKE', 'bookmaker': 'BOOK', 'bet_status': 'ST', 'score_home': 'SH', 'score_away': 'SA', 'profit': 'P/L', 'cls_odds': 'CLS', 'true_cls': 'CLS_TRUE', 'cls_limit': 'CLS_LIMIT', 'ev': 'EXP_WIN', 'clv': 'CLV', 'bet_added': 'BET_ADDED'})
                    bets_df = bets_df[['DEL', 'TAG', 'STARTS', 'SPORT', 'LEAGUE', 'RUNNER_HOME', 'RUNNER_AWAY', 'MARKET', 'PERIOD', 'SIDE', 'LINE', 'ODDS', 'STAKE', 'BOOK', 'ST', 'SH', 'SA', 'P/L', 'CLS', 'CLS_TRUE', 'CLS_LIMIT', 'EXP_WIN', 'CLV', 'BET_ADDED', 'ID']]

                    # Apply font & background colors to cells, apply number formatting
                    if st.session_state.odds_display == 'American':
                        bets_df.ODDS = bets_df.ODDS.apply(tools.get_american_odds)
                        bets_df.CLS = bets_df.CLS.apply(tools.get_american_odds)
                        bets_df.CLS_TRUE = bets_df.CLS_TRUE.apply(tools.get_american_odds)
                        styled_df = bets_df.style.applymap(tools.color_cells, subset=['ST', 'P/L', 'EXP_WIN', 'CLV']).format({'LINE': '{:g}'.format, 'ODDS': '{0:g}'.format, 'STAKE': '{:,.2f}'.format, 'P/L': '{:,.2f}'.format, 'CLS': '{0:g}'.format, 'CLS_TRUE': '{0:g}'.format, 'CLS_LIMIT': '{:,.0f}'.format, 'EXP_WIN': '{:,.2f}'.format, 'CLV': '{:,.2%}'.format, 'SH': '{0:g}'.format, 'SA': '{0:g}'.format})
                    else:
                        styled_df = bets_df.style.applymap(tools.color_cells, subset=['ST', 'P/L', 'EXP_WIN', 'CLV']).format({'LINE': '{:g}'.format, 'ODDS': '{:,.3f}'.format, 'STAKE': '{:,.2f}'.format, 'P/L': '{:,.2f}'.format, 'CLS': '{:,.3f}'.format, 'CLS_TRUE': '{:,.3f}'.format, 'CLS_LIMIT': '{:,.0f}'.format, 'EXP_WIN': '{:,.2f}'.format, 'CLV': '{:,.2%}'.format, 'SH': '{0:g}'.format, 'SA': '{0:g}'.format})
                    df = st.data_editor(styled_df, column_config={"DEL": st.column_config.CheckboxColumn("DEL", help="Select if you want to delete this bet.", default=False)}, disabled=['TAG', 'STARTS', 'SPORT', 'LEAGUE', 'RUNNER_HOME', 'RUNNER_AWAY', 'MARKET', 'PERIOD', 'SIDE', 'LINE', 'ODDS', 'STAKE', 'BOOK', 'ST', 'SH', 'SA', 'P/L', 'CLS', 'CLS_TRUE', 'CLS_LIMIT', 'EXP_WIN', 'CLV', 'BET_ADDED', 'ID'], hide_index=True)

                    bets_to_be_deleted = df.loc[(df['DEL'] == True), 'ID'].tolist()

# Place Refresh & Delete button below dataframe
# Delete button will only be visible if at least one event is selected
st.button('Refresh dashboard', on_click=tools.refresh_table)
if bets_to_be_deleted:
    st.button('Delete selected bet(s)', on_click=tools.delete_bets, args=(bets_to_be_deleted,), type="primary")

if len(df) > 0:

    # Display cumulative stats
    bet_count = len(df[df['ST'] != 'na'])
    turnover = df.loc[df['ST'] != 'na', 'STAKE'].sum()
    sum_profit = df['P/L'].sum()
    sum_ev = df['EXP_WIN'].sum()
    clv = sum_ev / turnover

    color_profit, color_clv, color_ev = tools.get_text_colouring(sum_profit=sum_profit, sum_ev=sum_ev)

    st.header(f"BETS: :gray[{bet_count}] - TURNOVER: :gray[{int(turnover)}] - P/L: {color_profit}[{round(sum_profit, 2):+g}] - ROI: {color_profit}[{round(100 * sum_profit / turnover, 2):+g}%] - EXP_WIN: {color_ev}[{round(sum_ev, 2):+g}] - CLV: {color_clv}[{round(100 * clv, 2):+g}%]")

    cum_profit, cum_clv, cum_bets, cur_profit, cur_clv, cur_bets = list(), list(), list(), 0.00, 0.00, 0
    for index, row in df.iterrows():
        if row['ST'] != 'na':
            cur_profit += row['P/L']
            cur_clv += row['EXP_WIN']
            cur_bets += 1

            cum_profit.append(cur_profit)
            cum_clv.append(cur_clv)
            cum_bets.append(cur_bets)

    chart_data = pd.DataFrame({"bet_no": cum_bets, "Actual P/L": cum_profit, "CLV": cum_clv}, columns=["bet_no", "Actual P/L", "CLV"])
    st.line_chart(chart_data, x="bet_no", y=["Actual P/L", "CLV"], x_label='Bet no', y_label='Actual vs expected profit', color=["#FF0000", "#FFA500"], height=800)


st.sidebar.image(image="logo_sbic_round.png", use_column_width='auto')
