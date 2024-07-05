import uuid
from datetime import datetime, timedelta

import backoff
import requests

from src.py.logic.other import price_converter, short_price_converter_ai
from src.py.logic.propParser import get_tinkoff_config

api_url_base_new = 'https://invest-public-api.tinkoff.ru/rest/tinkoff.public.invest.api.contract.v1.OrdersService'
api_url_base_instrument_service = 'https://invest-public-api.tinkoff.ru/rest/tinkoff.public.invest.api.contract.v1.InstrumentsService'
api_url_base_market_data_service = 'https://invest-public-api.tinkoff.ru/rest/tinkoff.public.invest.api.contract.v1.MarketDataService'
api_url_base_stop_orders_service = 'https://invest-public-api.tinkoff.ru/rest/tinkoff.public.invest.api.contract.v1.StopOrdersService'
api_url_base_operations_servicee = 'https://invest-public-api.tinkoff.ru/rest/tinkoff.public.invest.api.contract.v1.OperationsService'
api_url_base_users_service = 'https://invest-public-api.tinkoff.ru/rest/tinkoff.public.invest.api.contract.v1.UsersService'


def get_list_of_shares():
    api = '{0}/Shares'
    api_url = api.format(api_url_base_instrument_service)
    api_token, account_id = get_tinkoff_config('config.properties')
    api_headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {0}'.format(api_token)}

    params = {
        "instrumentStatus": "INSTRUMENT_STATUS_BASE",
    }

    result = requests.post(api_url, json=params, headers=api_headers)

    instruments = result.json().get('instruments')

    shares = []

    for instrument in instruments:
        if instrument.get('currency') == 'rub':
            sector = instrument.get('sector')

            if sector == 'health_care':
                sector = 'healthCare'
            if sector == 'real_estate':
                sector = 'realEstate'

            shares.append({
                'figi': instrument.get('figi'),
                'ticker': instrument.get('ticker'),
                'instrumentId': instrument.get('figi'),
                'lot': instrument.get('lot'),
                'sector': sector,
            })

    return shares


def get_min_price_increment(figi):
    api = '{0}/ShareBy'
    api_url = api.format(api_url_base_instrument_service)
    api_token, account_id = get_tinkoff_config('config.properties')
    api_headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {0}'.format(api_token)}

    params = {
        "idType": "INSTRUMENT_ID_TYPE_FIGI",
        "id": figi
    }

    result = requests.post(api_url, json=params, headers=api_headers)

    instruments = result.json().get('instrument')
    min_price_increment_raw = instruments.get('minPriceIncrement')

    units = int(min_price_increment_raw.get('units'))
    nano = int(min_price_increment_raw.get('nano'))

    min_price_increment = short_price_converter_ai(units, nano)

    return min_price_increment


def create_a_limit_order(figi_name, priceNano, priceUnits, action, lots, order_type):
    order_id = uuid.uuid4().hex[:15].upper()
    api = '{0}/PostOrder'
    api_url = api.format(api_url_base_new)
    api_token, account_id = get_tinkoff_config('config.properties')
    api_headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {0}'.format(api_token)}

    params = {
        "figi": figi_name,
        "quantity": lots,
        "price": {
            "nano": priceNano,
            "units": priceUnits
        },
        "direction": action,
        "accountId": account_id,
        "orderType": order_type,
        "orderId": order_id,
        "instrumentId": figi_name
    }

    result = requests.post(api_url, json=params, headers=api_headers)

    status = result.json().get('executionReportStatus')
    order_id_response = result.json().get('orderId')

    if status is None:
        print(result.content)
        raise ValueError('==========Status bad!==========')

    print('Создаеться лимитка', figi_name, priceNano, priceUnits, action, lots, order_type)

    priceSum = result.json().get('initialOrderPrice')
    priceSumUnits = priceSum.get('units')
    priceSumNano = priceSum.get('nano')

    price_sum = price_converter(priceSumUnits, priceSumNano)

    if status != 'EXECUTION_REPORT_STATUS_NEW':
        raise ValueError('==========Limit order request return error!==========')
    else:
        print('Order', action, 'created with price', price_converter(priceUnits, priceNano), '| price sum', price_sum)

    return order_id_response, price_sum


def create_a_limit_order_temp(figi_name, priceNano, priceUnits, action, lots, order_type):
    order_id = uuid.uuid4().hex[:15].upper()
    api = '{0}/PostOrder'
    api_url = api.format(api_url_base_new)
    api_token, account_id = get_tinkoff_config('config.properties')
    api_headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {0}'.format(api_token)}

    params = {
        "figi": figi_name,
        "quantity": lots,
        "price": {
            "nano": priceNano,
            "units": priceUnits
        },
        "direction": action,
        "accountId": account_id,
        "orderType": order_type,
        "orderId": order_id,
        "instrumentId": figi_name
    }

    result = requests.post(api_url, json=params, headers=api_headers)

    status = result.json().get('executionReportStatus')

    return status


def create_a_limit_stop_order(figi_name, priceNano, priceUnits, action, lots, stopPriceNano, stopPriceUnits):
    api = '{0}/PostStopOrder'
    api_url = api.format(api_url_base_stop_orders_service)
    api_token, account_id = get_tinkoff_config('config.properties')
    api_headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {0}'.format(api_token)}

    params = {
        "figi": figi_name,
        "quantity": lots,
        "price": {
            "nano": priceNano,
            "units": priceUnits
        },
        "stopPrice": {
            "nano": stopPriceNano,
            "units": stopPriceUnits
        },
        "direction": action,
        "accountId": account_id,
        "stopOrderType": "STOP_ORDER_TYPE_STOP_LOSS",
        "expirationType": "STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL",
        "instrumentId": figi_name
    }

    result = requests.post(api_url, json=params, headers=api_headers)

    if result.status_code != 200:
        print(result.content)
        raise ValueError('==========Status bad!==========')


def order_executed(order_id, stock_name):
    api = '{0}/GetOrders'
    api_url = api.format(api_url_base_new)
    api_token, account_id = get_tinkoff_config('config.properties')
    api_headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {0}'.format(api_token)}

    params = {
        "accountId": account_id,
    }

    result = requests.post(api_url, json=params, headers=api_headers)

    orders = result.json().get('orders')

    lots_executed = 0
    executed_order_price = 0.0

    order_status = True

    coin = True

    for order in orders:
        if order.get('orderId') == order_id:
            print('Stock', stock_name, 'with order id', order_id, 'still executing')
            order_status = False
            coin = False
            lots_executed = order.get('lotsExecuted')
            executed_order_price = order.get('executed_order_price')
            break

    if orders is None or coin:
        print('Stock', stock_name, 'with order id', order_id, 'done or missing')

    return order_status, int(lots_executed), 0


def order_state(order_id):
    api = '{0}/GetOrderState'
    api_url = api.format(api_url_base_new)
    api_token, account_id = get_tinkoff_config('config.properties')
    api_headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {0}'.format(api_token)}

    params = {
        "accountId": account_id,
        "orderId": order_id,
    }

    result = requests.post(api_url, json=params, headers=api_headers)

    execution_report_status = result.json().get('executionReportStatus')
    lots_executed = result.json().get('lotsExecuted')
    executed_order_price_temp = result.json().get('averagePositionPrice')
    price_sum_temp = result.json().get('executedOrderPrice')
    executed_order_price = short_price_converter_ai(int(executed_order_price_temp.get('units')), executed_order_price_temp.get('nano'))
    price_sum = short_price_converter_ai(int(price_sum_temp.get('units')), price_sum_temp.get('nano'))

    order_status = True

    if execution_report_status != 'EXECUTION_REPORT_STATUS_FILL':
        order_status = False

    return order_status, int(lots_executed), executed_order_price, price_sum


def order_executed_extended(order_id, stock_name):
    api = '{0}/GetOrders'
    api_url = api.format(api_url_base_new)
    api_token, account_id = get_tinkoff_config('config.properties')
    api_headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {0}'.format(api_token)}

    params = {
        "accountId": account_id,
    }

    result = requests.post(api_url, json=params, headers=api_headers)

    orders = result.json().get('orders')

    lots_executed = 0


    execution_report_status = None

    for order in orders:
        if order.get('orderId') == order_id:
            print('Stock', stock_name, 'with order id', order_id, 'still executing')
            execution_report_status = order.get('executionReportStatus')
            lots_executed = order.get('lotsExecuted')
            break

    return execution_report_status, lots_executed, None, None

def cancel_order_by_id(order_id, stock_name):
    api = '{0}/CancelOrder'
    api_url = api.format(api_url_base_new)
    api_token, account_id = get_tinkoff_config('config.properties')
    api_headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {0}'.format(api_token)}

    params = {
        "accountId": account_id,
        "orderId": order_id,
    }

    status = requests.post(api_url, json=params, headers=api_headers)

    if status.status_code != 200:
        print("Cancel order request return error")
    else:
        print('Order was canceled, order id', order_id, 'stock name', stock_name)


def get_current_stock_price(figi, direction = 'ask'):
    api = '{0}/GetOrderBook'
    api_url = api.format(api_url_base_market_data_service)
    api_token, account_id = get_tinkoff_config('config.properties')
    api_headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {0}'.format(api_token)}

    params = {
        "figi": figi,
        "depth": 1,
        "instrumentId": figi,
    }

    result = requests.post(api_url, json=params, headers=api_headers)

    if direction == 'ask':
        asks_raw = result.json().get('asks')
        price = asks_raw[0].get('price')
        units = int(price.get('units'))
        nano = int(price.get('nano'))
        converted_price = short_price_converter_ai(units, nano)
    else:
        asks_raw = result.json().get('bids')
        price = asks_raw[0].get('price')
        units = int(price.get('units'))
        nano = int(price.get('nano'))
        converted_price = short_price_converter_ai(units, nano)

    return converted_price


@backoff.on_exception(backoff.expo,
                      requests.exceptions.RequestException,
                      max_time=150)
def get_candle(figi):
    api = '{0}/GetCandles'
    api_url = api.format(api_url_base_market_data_service)
    api_token, account_id = get_tinkoff_config('config.properties')
    api_headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {0}'.format(api_token)}

    today = datetime.now()
    from_date = get_previous_workday(today)
    to_date = today + timedelta(days=1)

    params = {
        "figi": figi,
        "from": from_date.strftime("%Y-%m-%dT00:00:00.000Z"),
        "to": to_date.strftime("%Y-%m-%dT00:00:00.000Z"),
        "interval": "CANDLE_INTERVAL_DAY",
        "instrumentId": figi,
    }

    result = requests.post(api_url, json=params, headers=api_headers)

    if result.status_code != 200:
        print(figi)
        print(get_ticket_by_figi(figi))
        print(result.content)
        print(result.status_code)
        print(result.reason)
        raise ValueError('==========Status bad!==========')

    candles = result.json().get('candles')

    try:
        today_high_price = short_price_converter_ai(int(candles[-1].get('high').get("units")), int(candles[-1].get('high').get("nano")))
    except IndexError as e:
        print(figi)
        print(get_ticket_by_figi(figi))
        print('ERROR:', str(e))
        raise ValueError('IndexError: list index out of range')

    today_open_price = short_price_converter_ai(int(candles[-1].get('open').get("units")), int(candles[-1].get('open').get("nano")))

    today_low_price = short_price_converter_ai(int(candles[-1].get('low').get("units")), int(candles[-1].get('low').get("nano")))

    today_volume_price = int(candles[-1].get('volume'))

    previous_close_price = short_price_converter_ai(int(candles[0].get('close').get("units")), int(candles[0].get('close').get("nano")))

    return today_high_price, previous_close_price, today_open_price, today_volume_price, today_low_price


def get_candle_two_day_before(figi):
    api = '{0}/GetCandles'
    api_url = api.format(api_url_base_market_data_service)
    api_token, account_id = get_tinkoff_config('config.properties')
    api_headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {0}'.format(api_token)}

    today = datetime.now()
    to_date = get_previous_workday(today)  # Получаем вчерашний рабочий день как конечную дату
    from_date = get_previous_workday(to_date)  # Получаем позавчерашний рабочий день как начальную дату


    params = {
        "figi": figi,
        "from": from_date.strftime("%Y-%m-%dT00:00:00.000Z"),
        "to": to_date.strftime("%Y-%m-%dT00:00:00.000Z"),
        "interval": "CANDLE_INTERVAL_DAY",
        "instrumentId": figi,
    }

    result = requests.post(api_url, json=params, headers=api_headers)

    if result.status_code != 200:
        print(result.content)
        raise ValueError('==========Status bad!==========')

    candles = result.json().get('candles')

    today_high_price = short_price_converter_ai(int(candles[-1].get('close').get("units")), int(candles[-1].get('close').get("nano")))

    today_volume_price = int(candles[-1].get('volume'))
    previous_volume_price = int(candles[-2].get('volume'))

    previous_close_price = short_price_converter_ai(int(candles[0].get('close').get("units")), int(candles[0].get('close').get("nano")))

    return today_high_price, previous_close_price, today_volume_price, previous_volume_price

@backoff.on_exception(backoff.expo,
                      requests.exceptions.RequestException,
                      max_time=300)
def get_candle_temp(figi):
    api = '{0}/GetCandles'
    api_url = api.format(api_url_base_market_data_service)
    api_token, account_id = get_tinkoff_config('config.properties')
    api_headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {0}'.format(api_token)}

    today = datetime.now()
    from_date = get_previous_workday(today)
    to_date = today + timedelta(days=1)

    params = {
        "figi": figi,
        "from": from_date.strftime("%Y-%m-%dT00:00:00.000Z"),
        "to": to_date.strftime("%Y-%m-%dT00:00:00.000Z"),
        "interval": "CANDLE_INTERVAL_DAY",
        "instrumentId": figi,
    }

    result = requests.post(api_url, json=params, headers=api_headers)

    if result.status_code != 200:
        print(figi)
        print(result.content)
        print(result.status_code)
        print(result.reason)
        raise ValueError('==========Status bad!==========')

    candles = result.json().get('candles')

    try:
        today_high_price = short_price_converter_ai(int(candles[-1].get('high').get("units")), int(candles[-1].get('high').get("nano")))
    except IndexError as e:
        print(figi)
        print('ERROR:', str(e))
        raise ValueError('IndexError: list index out of range')

    today_open_price = short_price_converter_ai(int(candles[-1].get('open').get("units")), int(candles[-1].get('open').get("nano")))
    today_low_price = short_price_converter_ai(int(candles[-1].get('low').get("units")), int(candles[-1].get('low').get("nano")))
    today_volume_price = int(candles[-1].get('volume'))
    previous_close_price = short_price_converter_ai(int(candles[0].get('close').get("units")), int(candles[0].get('close').get("nano")))

    return today_high_price, previous_close_price, today_open_price, today_volume_price, today_low_price

def get_amount_of_stocks_in_portfolio(figi):
    api = '{0}/GetPortfolio'
    api_url = api.format(api_url_base_operations_servicee)
    api_token, account_id = get_tinkoff_config('config.properties')
    api_headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {0}'.format(api_token)}

    params = {
        "accountId": "2010921845",
        "currency": "RUB",
    }

    result = requests.post(api_url, json=params, headers=api_headers)

    if result.status_code != 200:
        print(result.content)
        raise ValueError('==========Status bad!==========')

    positions = result.json().get('positions')

    quantity = 0

    for position in positions:
        if position.get('figi') == figi:
            quantity_raw = position.get('quantity')
            quantity = short_price_converter_ai(int(quantity_raw.get("units")), int(quantity_raw.get("nano")))
            break

    return quantity


def get_ticket_by_figi(figi):
    api = '{0}/ShareBy'
    api_url = api.format(api_url_base_instrument_service)
    api_token, account_id = get_tinkoff_config('config.properties')
    api_headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {0}'.format(api_token)}

    params = {
        "id_type": 'INSTRUMENT_ID_TYPE_FIGI',
        "id": figi,
    }

    result = requests.post(api_url, json=params, headers=api_headers)

    if result.status_code != 200:
        print(figi)
        raise ValueError('==========Status code not 200!==========')

    instrument = result.json().get('instrument')
    ticker = instrument.get('ticker')

    return ticker


def get_asset_reports(figi):
    api = '{0}/GetAssetReports'
    api_url = api.format(api_url_base_instrument_service)
    api_token, account_id = get_tinkoff_config('config.properties')
    api_headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {0}'.format(api_token)}

    figi_uuid = get_figi_uuid(figi)

    today = datetime.now()
    to_date = today + timedelta(days=10)

    params = {
        "instrumentId": figi_uuid,
        "from": today.strftime("%Y-%m-%dT00:00:00.000Z"),
        "to": to_date.strftime("%Y-%m-%dT00:00:00.000Z"),
    }

    result = requests.post(api_url, json=params, headers=api_headers)

    if result.status_code != 200:
        print(figi)
        raise ValueError('==========Status code not 200!==========')

    events = result.json().get('events')

    if not events:
        report_date = None
    else:
        report_date = events[0].get('reportDate')

    return report_date


def get_figi_uuid(figi):
    api = '{0}/FindInstrument'
    api_url = api.format(api_url_base_instrument_service)
    api_token, account_id = get_tinkoff_config('config.properties')
    api_headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {0}'.format(api_token)}

    params = {
        "query": figi,
        "instrumentKind": 'INSTRUMENT_TYPE_SHARE',
        "apiTradeAvailableFlag": True,
    }

    result = requests.post(api_url, json=params, headers=api_headers)

    if result.status_code != 200:
        print(figi)
        raise ValueError('==========Status code not 200!==========')

    instruments = result.json().get('instruments')

    uid = instruments[0].get('uid')

    return uid


def get_dividends(figi):
    api = '{0}/GetDividends'
    api_url = api.format(api_url_base_instrument_service)
    api_token, account_id = get_tinkoff_config('config.properties')
    api_headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {0}'.format(api_token)}

    today = datetime.now()
    to_date = today + timedelta(days=10)

    params = {
        "figi": figi,
        "from": today.strftime("%Y-%m-%dT00:00:00.000Z"),
        "to": to_date.strftime("%Y-%m-%dT00:00:00.000Z"),
        "instrumentId": figi,
    }

    result = requests.post(api_url, json=params, headers=api_headers)

    if result.status_code != 200:
        print(figi)
        raise ValueError('==========Status code not 200!==========')

    dividends = result.json().get('dividends')

    if not dividends:
        last_buy_date = None
    else:
        last_buy_date = dividends[0].get('lastBuyDate')

    return last_buy_date


def get_steam_limits():
    api = '{0}/GetUserTariff'
    api_url = api.format(api_url_base_users_service)
    api_token, account_id = get_tinkoff_config('config.properties')
    api_headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {0}'.format(api_token)}

    params = {
    }

    result = requests.post(api_url, json=params, headers=api_headers)

    if result.status_code != 200:
        raise ValueError('==========Status code not 200!==========')

    stream_limits = result.json().get('streamLimits')

    stream_limit = stream_limits[0].get('limit')

    return stream_limit

def get_previous_workday(date):
    if date.weekday() == 0:  # Понедельник
        return date - timedelta(days=3)  # Возвращаем пятницу прошлой недели
    elif date.weekday() == 6:  # Воскресенье
        return date - timedelta(days=2)  # Возвращаем пятницу на этой неделе
    else:
        return date - timedelta(days=1)  # Для других дней недели возвращаем предыдущий рабочий день