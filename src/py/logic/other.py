import datetime
from decimal import Decimal


def get_change(current, previous):
    if current == previous:
        return 100.0000
    try:
        if previous is not None:
            return previous / current * 100.0000 - 100.0000
        else:
            return 0
    except ZeroDivisionError:
        return 0


def get_percent_diff(ask_sum, bid_sum):
    percentage_change = ((bid_sum - ask_sum) / ask_sum) * 100
    return percentage_change


def percent_difference(value1, value2):
    return ((value1 / value2) * 100) - 100


def price_converter(units, nano):
    nanoValueAsks = int(nano)
    unitsValueAsks = int(units)
    price = unitsValueAsks + nanoValueAsks / 1e9
    return price


def short_price_converter(price):
    return price.units + price.nano / 1e9


def short_price_converter_temp(price):
    return price["units"] + price["nano"] / 1e9


def short_price_converter_ai(units, nano):
    return units + nano / 1e9


def short_price_deconverter(price):
    units = int(price)
    nano = int((price - units) * 1e9)
    return nano, units

def price_deconverter(price):
   value = Decimal(price)
   units = int(value) if value is not None else 0
   nano = int((value - units) * Decimal(1_000_000_000)) if value is not None else 0
   return nano, units


def calculate_max_money_limit(turnover, percentage, max_fixed_price):
    max_money_limit = turnover * percentage
    return min(max_money_limit, max_fixed_price)


def calculate_amount_of_stocks(ask_price_current, lot, max_money_limit_for_single_stock):
    amount_of_stocks = 0
    ask_price_current_temp = ask_price_current * lot

    while ask_price_current_temp <= max_money_limit_for_single_stock:
        ask_price_current_temp += ask_price_current * lot
        amount_of_stocks += 1
    return amount_of_stocks


def calculate_shares(initial_shares, multiplier, iteration):
    #multiplier # Удваиваем количество акций при каждой покупке
    return initial_shares * (multiplier ** iteration)


def calculate_trend(bids, asks):
    # Calculate weighted sums giving higher priority to better prices
    weighted_bid_sum = sum((len(bids) - i) * order.quantity for i, order in enumerate(bids))
    weighted_ask_sum = sum((len(asks) - i) * order.quantity for i, order in enumerate(asks))

    # Determine trend: True for ascending, False for descending (or stable)
    trend = weighted_bid_sum >= weighted_ask_sum

    return trend


def convert_date(timestamp):
    dt_object = datetime.datetime.fromtimestamp(timestamp)

    formatted_time = dt_object.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_time
