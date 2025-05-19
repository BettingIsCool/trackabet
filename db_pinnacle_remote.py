# The module 'db_pinnacle_remote.py' uses sqlalchemy as the database connector which is the preferred way for streamlit
# The module 'db_pinnacle_remote2.py' uses mysql-connector-python

import time
import streamlit as st
from sqlalchemy import text
from datetime import datetime
from config import TABLE_LEAGUES, TABLE_FIXTURES, TABLE_ODDS, TABLE_BETS, TABLE_USERS

conn = st.connection('pinnacle', type='sql')


@st.cache_data()
def get_leagues(sport_id: int):
    """
    Fetches leagues associated with a specific sport from the database.

    This function utilizes the Streamlit caching mechanism to store
    the query results persistently, optimizing performance for recurring
    requests. The function retrieves league IDs and league names matching
    the provided sport ID.

    :param sport_id: The identifier of the sport for which leagues data
        should be fetched.
    :type sport_id: int
    :return: A list of tuples where each tuple contains league ID and league
        name for leagues associated with the given sport.
    :rtype: list[tuple[int, str]]
    """
    return conn.query(f"SELECT league_id, league_name FROM {TABLE_LEAGUES} WHERE sport_id = {sport_id}")


@st.cache_data()
def get_fixtures(sport_id: int, date_from: datetime, date_to: datetime):
    """
    Fetches distinct fixtures for a specific sport within a given date range, optionally filtering
    for the availability of odds. The fixtures are retrieved from the database and include
    details such as the event ID, league ID, league name, start time, and runners (home and away teams).
    The results are ordered by the event start time.

    :param sport_id: The ID of the sport for which to fetch fixtures.
    :type sport_id: int
    :param date_from: The start date and time for the range within which to fetch the fixtures.
    :param date_to: The end date and time for the range within which to fetch the fixtures.
    :return: Query results containing the details of fixtures (event ID, league details, start time,
             and team runners).
    :rtype: Any
    """
    # This query returns the fixtures including if odds and results are actually available
    #return conn.query(f"SELECT DISTINCT(f.event_id), f.league_id, f.league_name, f.starts, f.runner_home, f.runner_away FROM {TABLE_FIXTURES} f, {TABLE_ODDS} o, {TABLE_RESULTS} r WHERE o.event_id = f.event_id AND r.event_id = f.event_id AND f.sport_id = {sport_id} AND f.starts >= '{date_from.strftime('%Y-%m-%d %H:%M:%S')}' AND f.starts < DATE_ADD('{date_to.strftime('%Y-%m-%d %H:%M:%S')}', INTERVAL 1 DAY) ORDER BY f.starts")
    return conn.query(f"SELECT DISTINCT(f.event_id), f.league_id, f.league_name, f.starts, f.runner_home, f.runner_away FROM {TABLE_FIXTURES} f, {TABLE_ODDS} o WHERE o.event_id = f.event_id AND f.sport_id = {sport_id} AND f.starts >= '{date_from.strftime('%Y-%m-%d %H:%M:%S')}' AND f.starts < DATE_ADD('{date_to.strftime('%Y-%m-%d %H:%M:%S')}', INTERVAL 1 DAY) ORDER BY f.starts")

    # This query returns the fixtures without checking for odds and results availability
    # return conn.query(f"SELECT DISTINCT(f.event_id), f.league_id, f.league_name, f.starts, f.runner_home, f.runner_away FROM {TABLE_FIXTURES} f, {TABLE_ODDS} o, {TABLE_RESULTS} r WHERE f.sport_id = {sport_id} AND DATE(f.starts) >= '{date_from.strftime('%Y-%m-%d')}' AND DATE(f.starts) <= '{date_to.strftime('%Y-%m-%d')}' AND o.event_id = f.event_id AND r.event_id = f.event_id ORDER BY f.starts")


@st.cache_data()
def get_odds(event_id: int):
    """
    Fetches odds information from the database for a specific event.

    This function retrieves period, market, line, and related odds data
    from the specified table within the database using the given event ID.
    It uses caching to improve performance by storing query results.

    :param event_id: The identifier of the event for which odds information
        is to be fetched.
    :type event_id: int
    :return: A query result containing columns - period, market, line, odds1,
        odds0, and odds2 for the specified event.
    :rtype: Any
    """
    return conn.query(f"SELECT period, market, line, odds1, odds0, odds2 FROM {TABLE_ODDS} WHERE event_id = {event_id}")


@st.cache_data()
def get_bets(username: str, sports: str, bookmakers: str, tags: str, bet_status: str, date_from: datetime, date_to: datetime):
    """
    Fetches a filtered list of bets from the database based on specified parameters.

    This function queries the database for bets associated with a given username that
    meet specified filtering criteria such as sports, bookmakers, tags, bet status,
    and a date range. The results are returned as a list of dictionaries containing
    various bet details.

    :param username: The username of the user whose bets are being queried.
    :type username: str
    :param sports: A comma-separated string of sports to filter bets.
    :type sports: str
    :param bookmakers: A comma-separated string of bookmakers to filter bets.
    :type bookmakers: str
    :param tags: A comma-separated string of tags to filter bets.
    :type tags: str
    :param bet_status: A comma-separated string of bet statuses to filter bets.
    :type bet_status: str
    :param date_from: The start date of the date range for filtering bets.
    :type date_from: datetime
    :param date_to: The end date of the date range for filtering bets.
    :type date_to: datetime
    :return: A list of dictionaries where each dictionary represents a bet record.
    :rtype: list
    """
    return conn.query(f"SELECT delete_bet, id, tag, starts, sport_name, league_name, runner_home, runner_away, market, period_name, side_name, line, odds, stake, bookmaker, bet_status, score_home, score_away, profit, cls_odds, true_cls, cls_limit, ev, clv, bet_added FROM {TABLE_BETS} WHERE user = '{username}' AND sport_name IN {sports} AND bookmaker IN {bookmakers} AND tag in {tags} AND bet_status in {bet_status} AND DATE(starts) >= '{date_from.strftime('%Y-%m-%d')}' AND DATE(starts) <= '{date_to.strftime('%Y-%m-%d')}' ORDER BY starts").to_dict('records')


@st.cache_data()
def get_user_unique_sports(username: str):
    """
    Fetches a list of unique sports associated with a given user's betting data.
    This function interacts with a database to retrieve distinct sports where the
    user has placed bets. The results are cached to improve performance and reduce
    unnecessary database queries.

    .. note::
        Ensure the connection to the database is valid and the table referenced
        by `TABLE_BETS` exists and contains the required schema.

    :param username: The username of the user for whom the unique sports are retrieved.
    :type username: str
    :return: A list of unique sports associated with the user's bets.
    :rtype: list[str]
    """
    return conn.query(f"SELECT DISTINCT(sport_name) FROM {TABLE_BETS} WHERE user = '{username}'")['sport_name'].tolist()


@st.cache_data()
def get_user_unique_leagues(username: str, sports: str):
    """
    Fetches a distinct list of league names based on the specified user and sports.
    This function utilizes caching to improve performance for repetitive queries.

    :param username: The username of the user whose league data needs to be fetched.
    :type username: str
    :param sports: A string representing the sports categories to filter leagues.
    :type sports: str
    :return: A list containing unique league names associated with the user and sports.
    :rtype: list
    """
    return conn.query(f"SELECT DISTINCT(league_name) FROM {TABLE_BETS} WHERE user = '{username}' AND sport_name IN {sports}")['league_name'].tolist()


@st.cache_data()
def get_user_unique_bookmakers(username: str, sports: str):
    """
    Retrieve a list of unique bookmakers associated with a specific user and sports.

    This function interacts with a database to fetch distinct bookmaker names
    that are linked to bets placed by the user for the given sports.

    :param username: The username of the user for whom the bookmakers are being queried.
    :type username: str
    :param sports: A comma-separated string of sports names for which the query is performed.
    :type sports: str
    :return: A list of unique bookmaker names for the specified user and sports.
    :rtype: list
    """
    return conn.query(f"SELECT DISTINCT(bookmaker) FROM {TABLE_BETS} WHERE user = '{username}' AND sport_name IN {sports}")['bookmaker'].tolist()


@st.cache_data()
def get_user_unique_tags(username: str, sports: str, bookmakers: str):
    """
    Fetches a list of unique tags associated with a specific user based on their bets. The tags are filtered
    by the username, selected sports, and bookmakers provided as parameters. Results are cached for efficiency.

    :param username: The username of the user whose unique tags need to be retrieved.
    :type username: str
    :param sports: A string representing the sports to filter bets by. Expected to be a list-like string
                   representation compatible with the query requirements.
    :type sports: str
    :param bookmakers: A string representing the bookmakers to filter bets by. Expected to be a list-like
                       string representation compatible with the query requirements.
    :type bookmakers: str
    :return: A list of unique tags associated with the user's filtered bets.
    :rtype: list
    """
    return conn.query(f"SELECT DISTINCT(tag) FROM {TABLE_BETS} WHERE user = '{username}' AND sport_name IN {sports} AND bookmaker IN {bookmakers}")['tag'].tolist()


@st.cache_data()
def get_user_unique_bet_status(username: str, sports: str, bookmakers: str, tags: str):
    """
    Retrieves the unique bet statuses for a user based on specific criteria including sports,
    bookmakers, and tags. The function performs a query to obtain distinct bet statuses
    from the bets table filtered by the provided user and other criteria. The result is
    then returned as a list of distinct bet statuses.

    :param username: The username of the user for whom bet statuses are to be retrieved.
    :type username: str
    :param sports: Comma-separated sports names to filter bets.
    :type sports: str
    :param bookmakers: Comma-separated bookmakers to filter bets.
    :type bookmakers: str
    :param tags: Comma-separated tags to filter bets.
    :type tags: str
    :return: A list of unique bet statuses for the user filtered by the specified criteria.
    :rtype: list
    """
    return conn.query(f"SELECT DISTINCT(bet_status) FROM {TABLE_BETS} WHERE user = '{username}' AND sport_name IN {sports} AND bookmaker IN {bookmakers} AND tag IN {tags}")['bet_status'].tolist()


@st.cache_data()
def get_user_unique_starts(username: str, sports: str, bookmakers: str, tags: str, bet_status: str):
    """
    Fetches unique start dates for bets placed by a specific user based on the given filters.

    This function queries the database to retrieve distinct starting dates for bets that match
    the provided filters including sports, bookmakers, tags, and bet status. It leverages
    caching to optimize performance for repeated queries with the same parameters.

    :param username: The username of the user whose bet starts are to be retrieved
    :param sports: A string containing the filtered sports names
    :param bookmakers: A string indicating the filtered bookmaker names
    :param tags: A string of tags to filter bets
    :param bet_status: A string indicating the status of bets to include in the query
    :return: A list of distinct start dates for bets matching the filters
    """
    return conn.query(f"SELECT DISTINCT(starts) FROM {TABLE_BETS} WHERE user = '{username}' AND sport_name IN {sports} AND bookmaker IN {bookmakers} AND tag IN {tags} AND bet_status IN {bet_status}")['starts'].tolist()


def append_bet(data: dict):
    """
    Appends a new bet record to the database. This function executes an SQL insert statement
    to add a record to the bets table using the given dictionary. It ensures that the session
    is properly managed and the data is committed to the database.

    :param data: A dictionary containing all the required fields for the bet record. The keys
        correspond to columns in the bets table. It must include:
        - "user": User ID
        - "tag": A tag associated with the bet
        - "starts": The start time of the event
        - "sport_id": ID of the sport
        - "sport_name": Name of the sport
        - "league_id": ID of the league
        - "league_name": Name of the league
        - "event_id": ID of the event
        - "runner_home": Name of the home runner
        - "runner_away": Name of the away runner
        - "market": The market type for the bet
        - "period": The period code of the event
        - "period_name": Name or description of the period
        - "side": The side of the bet
        - "side_name": Name or description of the side
        - "raw_line": Raw line for the bet
        - "line": Adjusted line for the bet
        - "odds": Odds for the bet
        - "stake": Stake amount of the bet
        - "bookmaker": Bookmaker offering the bet
        - "bet_status": Status of the bet
        - "score_home": Current or final home score
        - "score_away": Current or final away score
        - "profit": Calculated profit of the bet
        - "cls_odds": Closing odds at bet placement
        - "true_cls": True closing line at bet placement
        - "cls_limit": Closing line limit
        - "ev": Expected value of the bet
        - "clv": Closing line value
        - "bet_added": Timestamp for when the bet was added

    :return: None
    """
    query = f"INSERT INTO {TABLE_BETS} (user, tag, starts, sport_id, sport_name, league_id, league_name, event_id, runner_home, runner_away, market, period, period_name, side, side_name, raw_line, line, odds, stake, bookmaker, bet_status, score_home, score_away, profit, cls_odds, true_cls, cls_limit, ev, clv, bet_added) VALUES(:user, :tag, :starts, :sport_id, :sport_name, :league_id, :league_name, :event_id, :runner_home, :runner_away, :market, :period, :period_name, :side, :side_name, :raw_line, :line, :odds, :stake, :bookmaker, :bet_status, :score_home, :score_away, :profit, :cls_odds, :true_cls, :cls_limit, :ev, :clv, :bet_added)"

    with conn.session as session:
        session.execute(text(query), params=dict(user=data['user'], tag=data['tag'], starts=data['starts'], sport_id=data['sport_id'], sport_name=data['sport_name'], league_id=data['league_id'], league_name=data['league_name'], event_id=data['event_id'], runner_home=data['runner_home'], runner_away=data['runner_away'], market=data['market'], period=data['period'], period_name=data['period_name'], side=data['side'], side_name=data['side_name'], raw_line=data['raw_line'], line=data['line'], odds=data['odds'], stake=data['stake'], bookmaker=data['bookmaker'], bet_status=data['bet_status'], score_home=data['score_home'], score_away=data['score_away'], profit=data['profit'], cls_odds=data['cls_odds'], true_cls=data['true_cls'], cls_limit=data['cls_limit'], ev=data['ev'], clv=data['clv'], bet_added=data['bet_added']))
        session.commit()


def delete_bet(key: int):
    """
    Deletes a bet record from the database identified by its key.

    This function constructs and executes an SQL DELETE statement to remove the
    record associated with the provided key from the bets table. The deletion is
    made within a session, and the changes are committed to the database.

    :param key: The unique identifier of the bet record to be deleted.
    :type key: int
    :return: None
    """
    query = f"DELETE FROM {TABLE_BETS} WHERE id = {key}"

    with conn.session as session:
        session.execute(text(query))
        session.commit()


def set_user_odds_display(username: str, placeholder: st.delta_generator.DeltaGenerator):
    """
    Updates the odds display format for a user and reflects changes persistently in the database.

    This function modifies the current odds display format session state based on the input
    parameters. An SQL query is executed to update the corresponding user's odds display format
    in the database, ensuring that the changes are saved. A confirmation message is
    displayed in a Streamlit placeholder, which is then cleared after a short delay.

    :param username: The username of the user whose odds display format is being updated.
    :param placeholder: A Streamlit DeltaGenerator object used to display messages to the user.
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
    Sets the user's timezone in the application's database and provides user feedback.

    This function updates the timezone for the specified username in the database
    and uses a `placeholder` to notify the user of a successful operation. It retrieves
    the timezone value from the application's session state and commits the change
    to a database. After successfully updating, it provides a success message through
    a `placeholder` object and automatically clears out the placeholder after a brief delay.

    :param username: The username of the user whose timezone will be updated.
    :type username: str
    :param placeholder: An element used to temporarily display success notifications to the user.
    :type placeholder: st.delta_generator.DeltaGenerator
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


def set_user_default_sport(username: str, placeholder: st.delta_generator.DeltaGenerator):
    """
    Sets the default sport for a user in the session state and updates the database
    accordingly. After updating, a success message is displayed temporarily.

    :param username: The username of the user whose default sport needs to be updated.
    :type username: str
    :param placeholder: A Streamlit DeltaGenerator object to render messages in the UI.
    :type placeholder: st.delta_generator.DeltaGenerator
    :return: None
    """
    st.session_state.default_sport = st.session_state.default_sport_key

    query = f"UPDATE {TABLE_USERS} SET default_sport = '{st.session_state.default_sport}' WHERE username = '{username}'"

    with conn.session as session:
        session.execute(text(query))
        session.commit()

    placeholder.success('Default sport changed successfully!')
    time.sleep(2)
    placeholder.empty()


def set_user_default_book(username: str, placeholder: st.delta_generator.DeltaGenerator):
    """
    Set the default bookmaker for a specific user and update the related database record.

    This function assigns a default bookmaker to a user in the session state and updates
    the corresponding record in the database. It also provides feedback to the user through
    a placeholder element and temporarily displays a success message before clearing it.

    :param username: The unique identifier of the user whose default bookmaker is being set.
    :type username: str
    :param placeholder: A Streamlit delta generator object for displaying temporary messages.
    :type placeholder: st.delta_generator.DeltaGenerator
    :return: None
    """
    st.session_state.default_book = st.session_state.default_book_key

    query = f"UPDATE {TABLE_USERS} SET default_book = '{st.session_state.default_book}' WHERE username = '{username}'"

    with conn.session as session:
        session.execute(text(query))
        session.commit()

    placeholder.success('Default bookmaker changed successfully!')
    time.sleep(2)
    placeholder.empty()


def set_user_default_tag(username: str, placeholder: st.delta_generator.DeltaGenerator):
    """
    Updates the default tag for a user in the system and provides user feedback.

    This function sets the user's default tag in the system by updating the
    session state and the database. It also provides a visual confirmation of
    the update using the provided placeholder.

    :param username: The username of the target user whose default tag will
        be updated.
    :type username: str
    :param placeholder: A Streamlit DeltaGenerator object used for displaying
        feedback to the user.
    :type placeholder: st.delta_generator.DeltaGenerator
    :return: None
    """
    st.session_state.default_tag = st.session_state.default_tag_key

    query = f"UPDATE {TABLE_USERS} SET default_tag = '{st.session_state.default_tag}' WHERE username = '{username}'"

    with conn.session as session:
        session.execute(text(query))
        session.commit()

    placeholder.success('Default tag changed successfully!')
    time.sleep(2)
    placeholder.empty()


def get_user_odds_display(username: str):
    """
    Retrieves the odds display setting for a specific user from the database.

    The function interacts with the database to fetch the odds display value
    associated with a given username. It queries the database using the
    username and returns the odds display setting as a list.

    :param username: The username of the user whose odds display setting
        is to be retrieved.
    :type username: str

    :return: A list containing the odds display setting for the specified
        user.
    :rtype: list

    :raises KeyError: If the queried result from the database does not
        contain the expected 'odds_display' key.
    :raises DatabaseError: If there is an issue with the database
        connection or query execution.
    """
    return conn.query(f"SELECT odds_display FROM {TABLE_USERS} WHERE username = '{username}'")['odds_display'].tolist()


def get_user_timezone(username: str):
    """
    Fetches the timezone associated with a specific username from the users table in the database.

    This function queries the `TABLE_USERS` table to retrieve the timezone value linked to
    the provided username. It utilizes the database connection `conn` for executing the query,
    and the resulting timezone is returned as a list.

    :param username: The username whose timezone is to be retrieved.
    :type username: str
    :return: A list containing the timezone(s) associated with the provided username.
    :rtype: list
    """
    return conn.query(f"SELECT timezone FROM {TABLE_USERS} WHERE username = '{username}'")['timezone'].tolist()


def get_user_default_sport(username: str):
    """
    Fetches the default sport of a given user from the database.

    This function queries the database to retrieve the default sport
    associated with the provided username. The default sport is stored
    in the corresponding user record and is returned as part of the
    query result. The result is expected to be in list format.

    :param username: The username whose default sport is to be retrieved.
    :type username: str
    :return: A list containing the user's default sport.
    :rtype: list
    """
    return conn.query(f"SELECT default_sport FROM {TABLE_USERS} WHERE username = '{username}'")['default_sport'].tolist()


def get_user_default_book(username: str):
    """
    Fetches the default book assigned to a given user from the database.

    This function retrieves the default book associated with the provided
    username by querying the respective user data table in the database.

    :param username: The username of the user whose default book is to be retrieved.
    :type username: str
    :return: A list containing the default book associated with the specified user.
    :rtype: list
    """
    return conn.query(f"SELECT default_book FROM {TABLE_USERS} WHERE username = '{username}'")['default_book'].tolist()


def get_user_default_tag(username: str):
    """
    Retrieve the default tag associated with a specific user from the database.

    This function queries the database table containing user data and extracts
    the default tag corresponding to the given username. The result is subsequently
    converted into a list.

    :param username: The username of the user whose default tag is to be fetched.
    :type username: str
    :return: A list containing the default tag associated with the given username.
    :rtype: list
    """
    return conn.query(f"SELECT default_tag FROM {TABLE_USERS} WHERE username = '{username}'")['default_tag'].tolist()


def append_user(data: dict):
    """
    Adds a new user entry into the database.

    This function inserts a new row into the users table with the provided
    user data. It utilizes the provided data dictionary to extract user
    details such as username, odds display type, timezone, and default
    preferences for sport, book, and tag. The function ensures that the
    changes are committed to the database after the query execution.

    :param data: A dictionary containing the user details to be inserted
        into the database. The dictionary should include the following keys:
        - username: The username of the user.
        - odds_display: Display format of odds (e.g., 'Decimal').
        - timezone: Timezone preference for the user.
        - default_sport: Default preferred sport (e.g., 'Soccer').
        - default_book: Default preferred betting book (e.g., 'Pinnacle').
        - default_tag: Default tag for the user.

    :return: None
    """
    query = f"INSERT INTO {TABLE_USERS} (username, odds_display, timezone, default_sport, default_book, default_tag) VALUES(:username, :odds_display, :timezone, :default_sport, :default_book, :default_tag)"

    with conn.session as session:
        session.execute(text(query), params=dict(username=data['username'], odds_display='Decimal', timezone='Europe/London', default_sport='Soccer', default_book='Pinnacle', default_tag=''))
        session.commit()


def get_users():
    """
    Fetches a list of usernames from the database.

    This function retrieves all usernames stored in the users table in the database.
    It queries the table and returns a list of usernames.

    :return: A list of usernames retrieved from the database
    :rtype: list
    """
    return conn.query(f"SELECT username FROM {TABLE_USERS}")['username'].tolist()


def update_bet(dbid: int, column_name: str, column_value: (str, int, float), placeholder: st.delta_generator.DeltaGenerator):
    """
    Update a specific column of a bet record in the database with the provided value.

    This function modifies a column in the `TABLE_BETS` database table for a given bet ID
    (`dbid`). Depending on the column being updated, the value is processed accordingly to
    ensure proper formatting within the SQL query. After executing the update, a success
    message is displayed via the provided `placeholder`.

    :param dbid: The ID of the bet record to be updated.
    :type dbid: int
    :param column_name: The name of the database column to update. Accepted values include
        'bet_status', 'tag', 'bookmaker', 'score_home', 'score_away', and others.
    :type column_name: str
    :param column_value: The value to update the column with. Can be any of the
        specified types depending on the column being updated.
    :type column_value: str | int | float
    :param placeholder: A Streamlit DeltaGenerator object used for rendering success
        messages after the update operation.
    :type placeholder: st.delta_generator.DeltaGenerator
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
