# The module 'db_pinnacle_remote.py' uses sqlalchemy as the database connector which is the preferred way for streamlit
# The module 'db_pinnacle_remote2.py' uses mysql-connector-python

import time
import streamlit as st
from sqlalchemy import text
from datetime import datetime
from config import TABLE_LEAGUES, TABLE_FIXTURES, TABLE_ODDS, TABLE_RESULTS, TABLE_BETS, TABLE_USERS

conn = st.connection('pinnacle', type='sql')


@st.cache_data()
def get_leagues(sport_id: int):
    """
    :param sport_id: The ID of the sport for which leagues are to be retrieved.
    :return: A list of tuples containing league IDs and league names for the given sport.
    """
    return conn.query(f"SELECT league_id, league_name FROM {TABLE_LEAGUES} WHERE sport_id = {sport_id}")


@st.cache_data()
def get_fixtures(sport_id: int, date_from: datetime, date_to: datetime):
    """
    :param sport_id: The ID of the sport for which fixtures are to be retrieved.
    :param date_from: The start date for filtering fixtures.
    :param date_to: The end date for filtering fixtures.
    :return: A query result containing the distinct fixtures, including their event ID, league ID, league name, start time, home runner, and away runner.
    """

    # This query returns the fixtures including if odds & results are actually available
    #return conn.query(f"SELECT DISTINCT(f.event_id), f.league_id, f.league_name, f.starts, f.runner_home, f.runner_away FROM {TABLE_FIXTURES} f, {TABLE_ODDS} o, {TABLE_RESULTS} r WHERE o.event_id = f.event_id AND r.event_id = f.event_id AND f.sport_id = {sport_id} AND f.starts >= '{date_from.strftime('%Y-%m-%d %H:%M:%S')}' AND f.starts < DATE_ADD('{date_to.strftime('%Y-%m-%d %H:%M:%S')}', INTERVAL 1 DAY) ORDER BY f.starts")
    return conn.query(f"SELECT DISTINCT(f.event_id), f.league_id, f.league_name, f.starts, f.runner_home, f.runner_away FROM {TABLE_FIXTURES} f, {TABLE_ODDS} o WHERE o.event_id = f.event_id AND f.sport_id = {sport_id} AND f.starts >= '{date_from.strftime('%Y-%m-%d %H:%M:%S')}' AND f.starts < DATE_ADD('{date_to.strftime('%Y-%m-%d %H:%M:%S')}', INTERVAL 1 DAY) ORDER BY f.starts")

    # This query returns the fixtures without checking for odds & results availability
    # return conn.query(f"SELECT DISTINCT(f.event_id), f.league_id, f.league_name, f.starts, f.runner_home, f.runner_away FROM {TABLE_FIXTURES} f, {TABLE_ODDS} o, {TABLE_RESULTS} r WHERE f.sport_id = {sport_id} AND DATE(f.starts) >= '{date_from.strftime('%Y-%m-%d')}' AND DATE(f.starts) <= '{date_to.strftime('%Y-%m-%d')}' AND o.event_id = f.event_id AND r.event_id = f.event_id ORDER BY f.starts")


@st.cache_data()
def get_odds(event_id: int):
    """
    :param event_id: Identifier for the event to fetch odds for
    :return: Query result containing period, market, line, odds1, odds0, and odds2 for the specified event
    """
    return conn.query(f"SELECT period, market, line, odds1, odds0, odds2 FROM {TABLE_ODDS} WHERE event_id = {event_id}")


@st.cache_data()
def get_bets(username: str, sports: str, bookmakers: str, tags: str, bet_status: str, date_from: datetime, date_to: datetime):
    """
    :param username: The username of the individual placing the bets.
    :param sports: A string specifying which sports to include in the query.
    :param bookmakers: A string specifying which bookmakers to include in the query.
    :param tags: A string specifying which tags to include in the query.
    :param date_from: The start date for filtering bets.
    :param date_to: The end date for filtering bets.
    :return: A list of dictionaries containing bet details filtered by the given criteria.
    """
    return conn.query(f"SELECT delete_bet, id, tag, starts, sport_name, league_name, runner_home, runner_away, market, period_name, side_name, line, odds, stake, bookmaker, bet_status, score_home, score_away, profit, cls_odds, true_cls, cls_limit, ev, clv, bet_added FROM {TABLE_BETS} WHERE user = '{username}' AND sport_name IN {sports} AND bookmaker IN {bookmakers} AND tag in {tags} AND bet_status in {bet_status} AND DATE(starts) >= '{date_from.strftime('%Y-%m-%d')}' AND DATE(starts) <= '{date_to.strftime('%Y-%m-%d')}' ORDER BY starts").to_dict('records')


@st.cache_data()
def get_user_unique_sports(username: str):
    """
    :param username: The username for whom unique sports are to be fetched.
    :return: A list of unique sport names that the user has placed bets on.
    """
    return conn.query(f"SELECT DISTINCT(sport_name) FROM {TABLE_BETS} WHERE user = '{username}'")['sport_name'].tolist()


@st.cache_data()
def get_user_unique_leagues(username: str, sports: str):
    """
    :param username: The username of the user whose unique leagues are to be fetched.
    :param sports: A string representing the sports categories to filter the leagues.
    :return: A list of unique league names associated with the user and filtered by the specified sports.
    """
    return conn.query(f"SELECT DISTINCT(league_name) FROM {TABLE_BETS} WHERE user = '{username}' AND sport_name IN {sports}")['league_name'].tolist()


@st.cache_data()
def get_user_unique_bookmakers(username: str, sports: str):
    """
    :param username: The username of the user whose unique bookmakers are being retrieved.
    :param sports: A string representing the sports categories to filter bets by.
    :return: A list of unique bookmakers that the specified user has placed bets with in the given sports categories.
    """
    return conn.query(f"SELECT DISTINCT(bookmaker) FROM {TABLE_BETS} WHERE user = '{username}' AND sport_name IN {sports}")['bookmaker'].tolist()


@st.cache_data()
def get_user_unique_tags(username: str, sports: str, bookmakers: str):
    """
    :param username: The username of the user whose unique tags are being queried.
    :param sports: A string containing the sports names to filter the query.
    :param bookmakers: A string containing the bookmaker names to filter the query.
    :return: A list of unique tags associated with the provided username, filtered by the specified sports and bookmakers.
    """
    return conn.query(f"SELECT DISTINCT(tag) FROM {TABLE_BETS} WHERE user = '{username}' AND sport_name IN {sports} AND bookmaker IN {bookmakers}")['tag'].tolist()


@st.cache_data()
def get_user_unique_bet_status(username: str, sports: str, bookmakers: str, tags: str):
    """
    :param username: The username of the individual for whom the unique bet status is being queried.
    :param sports: The specific sports that are being considered for the bet status.
    :param bookmakers: The bookmakers associated with the bets that are being queried.
    :param tags: The tags that categorize the bets for which the status is being requested.
    :return: A list of unique bet statuses for the given user, filtered by sports, bookmakers, and tags.
    """
    return conn.query(f"SELECT DISTINCT(bet_status) FROM {TABLE_BETS} WHERE user = '{username}' AND sport_name IN {sports} AND bookmaker IN {bookmakers} AND tag IN {tags}")['bet_status'].tolist()


@st.cache_data()
def get_user_unique_starts(username: str, sports: str, bookmakers: str, tags: str, bet_status: str):
    """
    :param username: User's name for which unique starts are to be retrieved
    :param sports: Comma separated string of sport names
    :param bookmakers: Comma separated string of bookmaker names
    :param tags: Comma separated string of tags
    :param bet_status: Comma separated string of bet statuses
    :return: List of distinct starts associated with the given user and filters
    """
    return conn.query(f"SELECT DISTINCT(starts) FROM {TABLE_BETS} WHERE user = '{username}' AND sport_name IN {sports} AND bookmaker IN {bookmakers} AND tag IN {tags} AND bet_status IN {bet_status}")['starts'].tolist()


def append_bet(data: dict):
    """
    :param data: A dictionary containing the betting information to be inserted into the database. The keys in the dictionary should include 'user', 'tag', 'starts', 'sport_id', 'sport_name', 'league_id', 'league_name', 'event_id', 'runner_home', 'runner_away', 'market', 'period', 'period_name', 'side', 'side_name', 'raw_line', 'line', 'odds', 'stake', 'bookmaker', 'bet_status', 'score_home', 'score_away', 'profit', 'cls_odds', 'true_cls', 'cls_limit', 'ev', 'clv', and 'bet_added'.
    :return: None. The function commits the transaction to the database without returning any value.
    """
    query = f"INSERT INTO {TABLE_BETS} (user, tag, starts, sport_id, sport_name, league_id, league_name, event_id, runner_home, runner_away, market, period, period_name, side, side_name, raw_line, line, odds, stake, bookmaker, bet_status, score_home, score_away, profit, cls_odds, true_cls, cls_limit, ev, clv, bet_added) VALUES(:user, :tag, :starts, :sport_id, :sport_name, :league_id, :league_name, :event_id, :runner_home, :runner_away, :market, :period, :period_name, :side, :side_name, :raw_line, :line, :odds, :stake, :bookmaker, :bet_status, :score_home, :score_away, :profit, :cls_odds, :true_cls, :cls_limit, :ev, :clv, :bet_added)"

    with conn.session as session:
        session.execute(text(query), params=dict(user=data['user'], tag=data['tag'], starts=data['starts'], sport_id=data['sport_id'], sport_name=data['sport_name'], league_id=data['league_id'], league_name=data['league_name'], event_id=data['event_id'], runner_home=data['runner_home'], runner_away=data['runner_away'], market=data['market'], period=data['period'], period_name=data['period_name'], side=data['side'], side_name=data['side_name'], raw_line=data['raw_line'], line=data['line'], odds=data['odds'], stake=data['stake'], bookmaker=data['bookmaker'], bet_status=data['bet_status'], score_home=data['score_home'], score_away=data['score_away'], profit=data['profit'], cls_odds=data['cls_odds'], true_cls=data['true_cls'], cls_limit=data['cls_limit'], ev=data['ev'], clv=data['clv'], bet_added=data['bet_added']))
        session.commit()


def delete_bet(id: int):
    """
    :param id: The identifier of the bet to be deleted from the database.
    :return: None
    """
    query = f"DELETE FROM {TABLE_BETS} WHERE id = {id}"

    with conn.session as session:
        session.execute(text(query))
        session.commit()


def set_user_odds_display(username: str, placeholder: st.delta_generator.DeltaGenerator):
    """
    :param username: The username of the user whose odds display setting is being updated.
    :param placeholder: A Streamlit DeltaGenerator object used to display success messages.
    :return: None
    """
    st.session_state.odds_display = st.session_state.odds_display_key

    query = f"UPDATE {TABLE_USERS} SET odds_display = '{st.session_state.odds_display}' WHERE username = '{username}'"

    with conn.session as session:
        session.execute(text(query))
        session.commit()

    placeholder.success('Odds format changed successfully!')
    time.sleep(2)
    placeholder.empty()


def set_user_timezone(username: str, placeholder: st.delta_generator.DeltaGenerator):
    """
    :param username: The username of the user whose timezone is being updated.
    :param placeholder: A DeltaGenerator instance used for displaying success messages.
    :return: None
    """
    st.session_state.timezone = st.session_state.timezone_key

    query = f"UPDATE {TABLE_USERS} SET timezone = '{st.session_state.timezone}' WHERE username = '{username}'"

    with conn.session as session:
        session.execute(text(query))
        session.commit()

    placeholder.success('Timezone changed successfully!')
    time.sleep(2)
    placeholder.empty()


def get_user_odds_display(username: str):
    """
    :param username: The username of the user whose odds display is being retrieved.
    :return: A list of odds displays associated with the given username.
    """
    return conn.query(f"SELECT odds_display FROM {TABLE_USERS} WHERE username = '{username}'")['odds_display'].tolist()


def get_user_timezone(username: str):
    """
    :param username: The username of the user whose timezone information is to be retrieved
    :return: The timezone information of the specified user
    """
    return conn.query(f"SELECT timezone FROM {TABLE_USERS} WHERE username = '{username}'")['timezone'].tolist()


def append_user(data: dict):
    """
    :param data: Dictionary containing user data with the key 'username'.
    :return: None
    """
    query = f"INSERT INTO {TABLE_USERS} (username, odds_display, timezone) VALUES(:username, :odds_display, :timezone)"

    with conn.session as session:
        session.execute(text(query), params=dict(username=data['username'], odds_display='Decimal', timezone='Europe/London'))
        session.commit()


def get_users():
    """
    :return: List of usernames retrieved from the database TABLE_USERS.
    :rtype: list
    """
    return conn.query(f"SELECT username FROM {TABLE_USERS}")['username'].tolist()


def update_bet(dbid: int, column_name: str, column_value: (str, int, float), placeholder: st.delta_generator.DeltaGenerator):
    """
    :param dbid: The unique identifier of the bet to be updated.
    :param column_name: The name of the column to be updated (e.g., 'bet_status').
    :param column_value: The new value to be set for the specified column. Can be of type str, int, or float.
    :param placeholder: A Streamlit DeltaGenerator object used for updating the application interface.
    :return: None
    """
    if column_name in ('bet_status', 'tag', 'bookmaker', 'score_home', 'score_away'):
        query = f"UPDATE {TABLE_BETS} SET {column_name} = '{column_value}', user_edit = '{datetime.now()}' WHERE id = {dbid}"

    else:
        query = f"UPDATE {TABLE_BETS} SET {column_name} = {column_value}, user_edit = '{datetime.now()}' WHERE id = {dbid}"

    with conn.session as session:
        session.execute(text(query))
        session.commit()

    placeholder.success(f'{column_name} successfully updated for bet ID {dbid}.')
    time.sleep(0.25)
    placeholder.empty()
