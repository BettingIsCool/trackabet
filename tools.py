import pytz
from datetime import datetime

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


def refresh_table():
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
        color_ev = ':green'

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
