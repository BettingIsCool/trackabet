import streamlit as st
from sqlalchemy import text
from datetime import datetime
from config import TABLE_LEAGUES, TABLE_FIXTURES, TABLE_ODDS, TABLE_RESULTS, TABLE_BETS, TABLE_USERS

conn = st.connection('pinnacle', type='sql')

@st.cache_data(ttl=10)
def get_leagues(sport_id: int):
    """
    :param sport_id: The ID of the sport for which leagues are to be retrieved.
    :return: A list of tuples containing league IDs and league names for the given sport.
    """
    return conn.query(f"SELECT league_id, league_name FROM {TABLE_LEAGUES} WHERE sport_id = {sport_id}", ttl=600)


@st.cache_data(ttl=10)
def get_fixtures(sport_id: int, date_from: datetime, date_to: datetime):
    """
    :param sport_id: The ID of the sport for which fixtures are to be retrieved.
    :param date_from: The start date for filtering fixtures.
    :param date_to: The end date for filtering fixtures.
    :return: A query result containing the distinct fixtures, including their event ID, league ID, league name, start time, home runner, and away runner.
    """
    return conn.query(f"SELECT DISTINCT(f.event_id), f.league_id, f.league_name, f.starts, f.runner_home, f.runner_away FROM {TABLE_FIXTURES} f, {TABLE_ODDS} o, {TABLE_RESULTS} r WHERE f.sport_id = {sport_id} AND DATE(f.starts) >= '{date_from.strftime('%Y-%m-%d')}' AND DATE(f.starts) <= '{date_to.strftime('%Y-%m-%d')}' AND o.event_id = f.event_id AND r.event_id = f.event_id ORDER BY f.starts", ttl=600)


@st.cache_data(ttl=10)
def get_odds(event_id: int):
    """
    :param event_id: Identifier for the event to fetch odds for
    :return: Query result containing period, market, line, odds1, odds0, and odds2 for the specified event
    """
    return conn.query(f"SELECT period, market, line, odds1, odds0, odds2 FROM {TABLE_ODDS} WHERE event_id = {event_id}", ttl=600)


def get_users():
    """
    :return: List of usernames retrieved from the database TABLE_USERS.
    :rtype: list
    """
    return conn.query(f"SELECT username FROM {TABLE_USERS}")['username'].tolist()


@st.cache_data(ttl=10)
def get_bets(username: str, sports: str, bookmakers: str, tags: str, date_from: datetime, date_to: datetime):
    """
    :param username: The username of the individual placing the bets.
    :param sports: A string specifying which sports to include in the query.
    :param bookmakers: A string specifying which bookmakers to include in the query.
    :param tags: A string specifying which tags to include in the query.
    :param date_from: The start date for filtering bets.
    :param date_to: The end date for filtering bets.
    :return: A list of dictionaries containing bet details filtered by the given criteria.
    """
    return conn.query(f"SELECT delete_bet, id, tag, starts, sport_name, league_name, runner_home, runner_away, market, period_name, side_name, line, odds, stake, bookmaker, bet_status, score_home, score_away, profit, cls_odds, true_cls, cls_limit, ev, clv, bet_added FROM {TABLE_BETS} WHERE user = '{username}' AND sport_name IN {sports} AND bookmaker IN {bookmakers} AND tag in {tags} AND DATE(starts) >= '{date_from.strftime('%Y-%m-%d')}' AND DATE(starts) <= '{date_to.strftime('%Y-%m-%d')}' ORDER BY starts", ttl=600).to_dict('records')


@st.cache_data(ttl=10)
def get_user_unique_sports(username: str):
    """
    :param username: The username for whom unique sports are to be fetched.
    :return: A list of unique sport names that the user has placed bets on.
    """
    return conn.query(f"SELECT DISTINCT(sport_name) FROM {TABLE_BETS} WHERE user = '{username}'", ttl=600)['sport_name'].tolist()


@st.cache_data(ttl=10)
def get_user_unique_leagues(username: str, sports: str):
    """
    :param username: The username of the user whose unique leagues are to be fetched.
    :param sports: A string representing the sports categories to filter the leagues.
    :return: A list of unique league names associated with the user and filtered by the specified sports.
    """
    return conn.query(f"SELECT DISTINCT(league_name) FROM {TABLE_BETS} WHERE user = '{username}' AND sport_name IN {sports}", ttl=600)['league_name'].tolist()


@st.cache_data(ttl=10)
def get_user_unique_bookmakers(username: str, sports: str):
    """
    :param username: The username of the user whose unique bookmakers are being retrieved.
    :param sports: A string representing the sports categories to filter bets by.
    :return: A list of unique bookmakers that the specified user has placed bets with in the given sports categories.
    """
    return conn.query(f"SELECT DISTINCT(bookmaker) FROM {TABLE_BETS} WHERE user = '{username}' AND sport_name IN {sports}", ttl=600)['bookmaker'].tolist()


@st.cache_data(ttl=10)
def get_user_unique_tags(username: str, sports: str, bookmakers: str):
    """
    :param username: The username of the user whose unique tags are being queried.
    :param sports: A string containing the sports names to filter the query.
    :param bookmakers: A string containing the bookmaker names to filter the query.
    :return: A list of unique tags associated with the provided username, filtered by the specified sports and bookmakers.
    """
    return conn.query(f"SELECT DISTINCT(tag) FROM {TABLE_BETS} WHERE user = '{username}' AND sport_name IN {sports} AND bookmaker IN {bookmakers}", ttl=600)['tag'].tolist()


@st.cache_data(ttl=10)
def get_user_unique_starts(username: str, sports: str, bookmakers: str, tags: str):
    """
    :param username: The username of the user whose unique starts are being queried.
    :param sports: A comma-separated string of sports to filter the starts.
    :param bookmakers: A comma-separated string of bookmakers to filter the starts.
    :param tags: A comma-separated string of tags to filter the starts.
    :return: A list of unique start times that match the given filters.
    """
    return conn.query(f"SELECT DISTINCT(starts) FROM {TABLE_BETS} WHERE user = '{username}' AND sport_name IN {sports} AND bookmaker IN {bookmakers} AND tag IN {tags}", ttl=600)['starts'].tolist()


def append_user(data: dict):
    """
    :param data: Dictionary containing user data with the key 'username'.
    :return: None
    """
    query = f"INSERT INTO {TABLE_USERS} (username) VALUES(:username)"

    with conn.session as session:
        session.execute(text(query), params=dict(username = data['username']))
        session.commit()


def append_bet(data: dict):
    """
    :param data: A dictionary containing the betting information to be inserted into the database. The keys in the dictionary should include 'user', 'tag', 'starts', 'sport_id', 'sport_name', 'league_id', 'league_name', 'event_id', 'runner_home', 'runner_away', 'market', 'period', 'period_name', 'side', 'side_name', 'raw_line', 'line', 'odds', 'stake', 'bookmaker', 'bet_status', 'score_home', 'score_away', 'profit', 'cls_odds', 'true_cls', 'cls_limit', 'ev', 'clv', and 'bet_added'.
    :return: None. The function commits the transaction to the database without returning any value.
    """
    query = f"INSERT INTO {TABLE_BETS} (user, tag, starts, sport_id, sport_name, league_id, league_name, event_id, runner_home, runner_away, market, period, period_name, side, side_name, raw_line, line, odds, stake, bookmaker, bet_status, score_home, score_away, profit, cls_odds, true_cls, cls_limit, ev, clv, bet_added) VALUES(:user, :tag, :starts, :sport_id, :sport_name, :league_id, :league_name, :event_id, :runner_home, :runner_away, :market, :period, :period_name, :side, :side_name, :raw_line, :line, :odds, :stake, :bookmaker, :bet_status, :score_home, :score_away, :profit, :cls_odds, :true_cls, :cls_limit, :ev, :clv, :bet_added)"

    with conn.session as session:
        session.execute(text(query), params=dict(user = data['user'], tag = data['tag'], starts = data['starts'], sport_id = data['sport_id'], sport_name = data['sport_name'], league_id = data['league_id'], league_name = data['league_name'], event_id = data['event_id'], runner_home = data['runner_home'], runner_away = data['runner_away'], market = data['market'], period = data['period'], period_name = data['period_name'], side = data['side'], side_name = data['side_name'], raw_line = data['raw_line'], line = data['line'], odds = data['odds'], stake = data['stake'], bookmaker = data['bookmaker'], bet_status = data['bet_status'], score_home = data['score_home'], score_away = data['score_away'], profit = data['profit'], cls_odds = data['cls_odds'], true_cls = data['true_cls'], cls_limit = data['cls_limit'], ev = data['ev'], clv = data['clv'], bet_added = data['bet_added']))
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