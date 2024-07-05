#!/usr/bin/python3.6
import ast
import logging
import time
from datetime import timezone, timedelta
from statistics import mean

from src.py.logic.fileWorker import read_wallet_from_memory, return_true_if_file_empty_or_not_exists, \
    write_wallet_to_memory, clear_memory_file, update_ticker, lock_file, unlock_file, \
    write_list_to_file
from src.py.logic.other import get_change, short_price_converter, calculate_max_money_limit, calculate_amount_of_stocks, \
    calculate_trend, percent_difference, price_converter, convert_date
from src.py.logic.propParser import get_settings
from src.py.logic.telegram import telegram_bot_sendtext
from src.py.logic.tinkoffMethods import create_a_limit_order, cancel_order_by_id, get_candle, \
    order_state, get_dividends, get_asset_reports

n_seconds = 60
seconds_to_wait_proliv = 1800
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def eventHandler(event, stock_run):
    get_figi = str(event[0].get('figi'))
    lot = int(event[0].get('lot'))
    stock_name = str(event[0].get('stock_name'))
    ask_price_current = float(event[0].get('asks'))
    bid_price_current = float(event[0].get('bids'))
    nano_value_asks = int(event[0].get('nano_value_asks'))
    units_value_asks = str(event[0].get('units_value_asks'))
    nano_value_bids = int(event[0].get('nano_value_bids'))
    units_value_bids = str(event[0].get('units_value_bids'))
    sector = str(event[0].get('sector'))
    high_price = float(event[0].get('high_price'))
    close_price = float(event[0].get('close_price'))
    last_price = float(event[0].get('last_price'))
    open_today_price = float(event[0].get('open_today_price'))
    today_low_price = float(event[0].get('today_low_price'))
    start_ask_date = float(event[0].get('start_ask_date'))
    volume = int(event[0].get('volume'))
    was_buy = bool(event[0].get('was_buy'))
    was_buy = False #TODO
    proliv_happened = bool(event[0].get('proliv_happened'))
    number_of_purchases = int(event[0].get('number_of_purchases'))
    proliv_count = int(event[0].get('proliv_count'))
    start_last_price = float(event[0].get('start_ask_price'))

    price_diff = 1.5 #Процент от цены с момента открытия до текущей цены
    high_price_diff = 2 #Процент от цены с момента открытия до наивысшей цены за день
    turnover_value = 150000000 #Оборот
    percent_down = 0.5 #Процент на который должна упасть цена для сигнала

    file_name = f'AAB_closeDate_{stock_run}'
    current_time = time.time()

    update_ticker(file_name, stock_name, get_figi, high_price, close_price, open_today_price, today_low_price, volume)

    turnover = (((open_today_price + high_price) / 2) * volume) * lot

    price_difference = last_price - open_today_price
    price_diff_check = round((price_difference / open_today_price) * 100, 2)

    high_price_difference = high_price - open_today_price
    high_price_diff_check = round((high_price_difference / open_today_price) * 100, 2)

    if price_diff_check >= price_diff:
        if high_price_diff_check >= high_price_diff:
            if turnover >= turnover_value:
                ###### START поиск проливов
                if return_true_if_file_empty_or_not_exists(stock_name + '_time_proliv'):
                    write_wallet_to_memory(current_time, stock_name + '_time_proliv')
                    last_clear_time_proliv = current_time
                    update_ticker(file_name, stock_name, get_figi, start_ask_date=current_time)
                else:
                    last_clear_time_proliv = float(read_wallet_from_memory(stock_name + '_time_proliv'))

                proliv_main_logic('start_ask_price', start_last_price, last_price, file_name, stock_name, get_figi, current_time, last_clear_time_proliv, percent_down, bid_price_current, start_ask_date)
                ###### END поиск проливов
            else:
                logging.debug("%s Объем за день ниже ожидаемого turnover=%d", stock_name, turnover)
        else:
            logging.debug("%s Текуший максимальный процент роста за день ниже ожидаемого high_price_diff_check=%f", stock_name, high_price_diff_check)
    else:
        logging.debug("%s Текуший процент роста ниже ожидаемого price_diff_check=%f", stock_name, price_diff_check)

    ###### Сканер объемов на основе ленты принтов
    # sum_signal = 6000000 #Сумма за одну сделку выше которой будет сигнал
    #
    # trade_direction = int(event[0].get('trade_direction'))
    # trade_price = float(event[0].get('trade_price'))
    # trade_quantity = int(event[0].get('trade_quantity'))
    # trade_time = event[0].get('trade_time')
    # trade_sum_from_history = float(event[0].get('trade_sum'))
    #
    # trade_sum = (trade_price * lot) * trade_quantity
    #
    # if trade_sum > sum_signal and trade_sum != trade_sum_from_history:
    #
    #     if trade_direction == 1:
    #         trade_direction_str = "Buy"
    #     else:
    #         trade_direction_str = "Sell"
    #
    #     telegram_bot_sendtext('💸 ' + stock_name + '\nTrade sum: ' + str(trade_sum) + '\nTrade direction: ' + str(trade_direction_str) + '\nTime: ' + str(trade_time)
    #                           + '\nReports: ' + str(get_asset_reports(get_figi)) + '\nDividends: ' + str(get_dividends(get_figi)))
    #     update_ticker(file_name, stock_name, get_figi, trade_sum=trade_sum)


def proliv_main_logic(price_type, start_price, current_price, file_name, stock_name, get_figi, current_time, last_clear_time_proliv, percent_down, bid_price_current, start_ask_date):
    global seconds_to_wait_proliv

    if start_price == 0.0:
        update_ticker(file_name, stock_name, get_figi, **{price_type: current_price})
        start_price = current_price

    if current_price > start_price:
        update_ticker(file_name, stock_name, get_figi, **{price_type: current_price})
        start_price = current_price

    change_percent = round(get_change(current_price, start_price), 4)

    if start_price is not None and current_time - last_clear_time_proliv >= seconds_to_wait_proliv:
        logging.info("%s Время ожидания закончилось сбрасиваем начальную цену %f, аск %f", stock_name, start_price, current_price)
        clear_memory_file(stock_name + '_time_proliv')
        write_wallet_to_memory(current_time, stock_name + '_time_proliv')
        update_ticker(file_name, stock_name, get_figi, **{price_type: 0.0}, start_ask_date=current_time)
        start_price = 0.0

    if change_percent >= percent_down and change_percent != 100.0 and start_price != 0.0:
        clear_memory_file(stock_name + '_time_proliv')
        write_wallet_to_memory(current_time, stock_name + '_time_proliv')
        update_ticker(file_name, stock_name, get_figi, **{price_type: 0.0}, start_ask_date=current_time)
        logging.info("%s Пролив %s произошел на процент %d начальная цена в аске %f, текущая цена %f", stock_name, price_type, change_percent, start_price, current_price)
        telegram_bot_sendtext('🚀 ' + stock_name + '\nLast price current: ' + str(current_price) + '\nStart last price: ' + str(start_price)  + '\nStart ask date: ' + str(convert_date(start_ask_date)) + '\nChange percent: ' + str(change_percent)
                              + '\nBid price current: ' + str(bid_price_current) + '\nReports: ' + str(get_asset_reports(get_figi)) + '\nDividends: ' + str(get_dividends(get_figi)))