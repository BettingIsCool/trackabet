import time
import pandas as pd
import pendulum
import streamlit as st
import db_pinnacle_remote as db


def delete_bets(bets_to_be_deleted: set):
    """
    :param bets_to_be_deleted: Set containing IDs of bets to be deleted
    :return: None
    """
    for key in bets_to_be_deleted:
        db.delete_bet(id=key)
    st.cache_data.clear()


def clear_cache():
    """
    Clears the cached data for Streamlit application.

    :return: None
    """
    st.cache_data.clear()


def color_cells(val: (str, int, float)):
    """
    :param val: The value to determine the cell color. Can be a string, integer, or float. If the value is a string, 'HW' and 'W' result in a green color, while 'HL' and 'L' result in a red color. If the value is a number, any positive value results in a green color, and any negative value results in a red color.
    :return: The style string for coloring the cell. Defaults to 'white' if val is None or does not meet other conditions.
    """
    color = 'white'
    if val is not None:

        if isinstance(val, str):
            if val in ('HW', 'W'):
                color = 'green'
            elif val in ('HL', 'L'):
                color = 'red'
            elif val == 'na':
                color = 'gray'

        else:
            if val > 0:
                color = 'green'
            elif val < 0:
                color = 'red'

    return f'color: {color}'


def get_text_colouring(sum_profit: float, sum_ev: float):
    """
    :param sum_profit: The total profit value used to determine the color of profit
    :param sum_ev: The expected value used to determine the color of EV and CLV
    :return: A tuple containing the colors for profit, CLV (Customer Lifetime Value), and EV (Expected Value)
    """
    color_profit, color_clv, color_ev = ':gray', ':gray', ':gray'

    if sum_profit > 0:
        color_profit = ':green'
    elif sum_profit < 0:
        color_profit = ':red'

    if sum_ev > 0:
        color_clv = ':green'
        color_ev = ':green'
    elif sum_ev < 0:
        color_clv = ':red'
        color_ev = ':red'

    return color_profit, color_clv, color_ev


def get_american_odds(decimal_odds: float):
    """
    :param decimal_odds: The decimal odds value to be converted to American odds format.
    :return: The corresponding American odds value.
    """
    return int((decimal_odds - 1) * 100) if decimal_odds >= 2.00 else int(-100 / (decimal_odds - 1))


def get_decimal_odds(american_odds: int):
    """
    :param american_odds: American odds value for which the decimal odds are to be calculated.
    :type american_odds: int
    :return: Decimal odds corresponding to the given American odds.
    :rtype: float
    """
    return american_odds / 100 + 1 if american_odds >= 0 else - 100 / american_odds + 1


def get_luck_factor(std_dev: float, act_roi: float, clv: float):
    """
    :param std_dev: The standard deviation of the return on investment (ROI).
    :param act_roi: The actual return on investment.
    :param clv: The expected customer lifetime value.
    :return: A tuple containing the luck factor (int), a describing string (str), and a color indicator (str).
    """
    if act_roi < clv - 3 * std_dev:
        return -3, 'extremely unlucky', 'red'
    elif act_roi < clv - 2 * std_dev:
        return -2, 'very unlucky', 'red'
    elif act_roi < clv - std_dev:
        return -1, 'unlucky', 'red'
    elif act_roi > clv + 3 * std_dev:
        return 3, 'extremely lucky', 'green'
    elif act_roi > clv + 2 * std_dev:
        return 2, 'very lucky', 'green'
    elif act_roi > clv + std_dev:
        return 1, 'lucky', 'green'
    else:
        return 0, 'normal', 'gray'


def get_rating(clv: float):
    """
    :param clv: Customer lifetime value as a floating-point number.
    :return: A tuple containing the rating (str), description (str), and color (str).
    """
    if clv >= 0.1:
        return 'A', 'excellent', 'green'
    elif clv >= 0.025:
        return 'B', 'very good', 'green'
    elif clv > 0:
        return 'C', 'solid', 'green'
    elif clv < -0.1:
        return 'F', 'terrible', 'red'
    elif clv < -0.025:
        return 'E', 'very poor', 'red'
    else:
        return 'D', 'poor', 'red'


@st.cache_resource()
def get_active_session(username: str):
    """
    :return: The session ID of the active session for the specified user.
    """
    return st.session_state.session_id


def tz_diff(home, away, on=None):
    """
    Return the difference in hours between the away time zone and home.

    `home` and `away` may be any values which pendulum parses as timezones.
    However, recommended use is to specify the full formal name.
    See https://gist.github.com/pamelafox/986163

    As not all time zones are separated by an integer number of hours, this
    function returns a float.

    As time zones are political entities, their definitions can change over time.
    This is complicated by the fact that daylight savings time does not start
    and end on the same days uniformly across the globe. This means that there are
    certain days of the year when the returned value between `Europe/Berlin` and
    `America/New_York` is _not_ `6.0`.

    By default, this function always assumes that you want the current
    definition. If you prefer to specify, set `on` to the date of your choice.
    It should be a `Pendulum` object.

    This function returns the number of hours which must be added to the home time
    in order to get the away time. For example,
    ```python
    >>> tz_diff('Europe/Berlin', 'America/New_York')
    -6.0
    >>> tz_diff('Europe/Berlin', 'Asia/Kabul')
    2.5
    ```
    """
    if on is None:
        on = pendulum.today()
    diff = (on.set(tz=home) - on.set(tz=away)).total_hours()

    # what about the diff from Tokyo to Honolulu? Right now the result is -19.0
    # it should be 5.0; Honolulu is naturally east of Tokyo, just not so around
    # the date line
    if abs(diff) > 12.0:
        if diff < 0.0:
            diff += 24.0
        else:
            diff -= 24.0

    return diff


def update_bet(initial_df: pd.DataFrame, edited_df: pd.DataFrame, placeholder: st.delta_generator.DeltaGenerator):
    for index, row in initial_df.iterrows():

        # Check & update current vs previous TAG
        initial_value = row['TAG']
        try:
            edited_value = edited_df[edited_df['ID'] == row['ID']]['TAG'].iloc[0]
        except Exception as ex:
            edited_value = initial_value

        if edited_value != initial_value:

            if isinstance(edited_value, str):
                db.update_bet(dbid=row['ID'], column_name='tag', column_value=edited_value, placeholder=placeholder)

            else:
                placeholder.info('Invalid input. Please enter a string')
                time.sleep(2.5)
                placeholder.empty()

        # Check & update current vs previous BOOKMAKER
        initial_value = row['BOOK']
        try:
            edited_value = edited_df[edited_df['ID'] == row['ID']]['BOOK'].iloc[0]
        except Exception as ex:
            edited_value = initial_value

        if edited_value != initial_value:

            if isinstance(edited_value, str):
                db.update_bet(dbid=row['ID'], column_name='bookmaker', column_value=edited_value, placeholder=placeholder)

            else:
                placeholder.info('Invalid input. Please enter a string')
                time.sleep(2.5)
                placeholder.empty()

        # Check & update current vs previous BET_STATUS
        initial_value = row['ST']
        try:
            edited_value = edited_df[edited_df['ID'] == row['ID']]['ST'].iloc[0]
        except Exception as ex:
            edited_value = initial_value

        if edited_value != initial_value:

            if edited_value in ('W', 'HW', 'L', 'HL', 'P', 'V'):
                db.update_bet(dbid=row['ID'], column_name='bet_status', column_value=edited_value, placeholder=placeholder)

            else:
                placeholder.info('Invalid input. Allowed values are: W, HW, L, HL, P, V')
                time.sleep(2.5)
                placeholder.empty()

        # Check & update current vs previous SCORE_HOME
        initial_value = row['SH']
        try:
            edited_value = edited_df[edited_df['ID'] == row['ID']]['SH'].iloc[0]
        except Exception as ex:
            edited_value = initial_value

        if edited_value != initial_value:

            if edited_value is not None and edited_value >= 0:
                db.update_bet(dbid=row['ID'], column_name='score_home', column_value=edited_value, placeholder=placeholder)

            else:
                placeholder.info('Invalid input. Please enter a whole number >= 0')
                time.sleep(2.5)
                placeholder.empty()

        # Check & update current vs previous SCORE_AWAY
        initial_value = row['SA']
        try:
            edited_value = edited_df[edited_df['ID'] == row['ID']]['SA'].iloc[0]
        except Exception as ex:
            edited_value = initial_value

        if edited_value != initial_value:

            if edited_value is not None and edited_value >= 0:
                db.update_bet(dbid=row['ID'], column_name='score_away', column_value=edited_value, placeholder=placeholder)

            else:
                placeholder.info('Invalid input. Please enter a whole number >= 0')
                time.sleep(2.5)
                placeholder.empty()

        # Check & update current vs previous P/L
        initial_value = row['P/L']
        try:
            edited_value = edited_df[edited_df['ID'] == row['ID']]['P/L'].iloc[0]
        except Exception as ex:
            edited_value = initial_value

        if edited_value != initial_value:

            if edited_value is not None and 1000000 > edited_value > -1000000:
                db.update_bet(dbid=row['ID'], column_name='profit', column_value=edited_value, placeholder=placeholder)

            else:
                placeholder.info('Invalid input. Please enter a whole number >= 0')
                time.sleep(2.5)
                placeholder.empty()
