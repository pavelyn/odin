import logging
import time
import traceback


from tinkoff.invest import RequestError

from src.py.logic.fileWorker import return_true_if_file_empty_or_not_exists, write_wallet_to_memory, \
    read_shares_from_file, write_wallet_to_memory_as_json
from src.py.logic.telegram import telegram_bot_sendtext
from src.py.logic.tinkoffMethods import get_list_of_shares, get_candle, get_steam_limits
from src.py.odin.tinkoffSocketOdinScanner import run
from docopt import docopt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

STOCKS_FOR_TRADE = {'SFIN'}
STOCKS_FOR_IGNORE = {'DIAS', 'KZIZ', 'TRNFP', 'TCSG', 'QIWI', 'UDMN', 'SFTL', 'NOMP', 'NOMPP', 'NTZL', 'KZIZP', 'OBNE',
                     'OBNEP', 'UFOSP', 'TGKJ', 'UDMN', 'ORUP', 'GRNT', 'ZILLP', 'SLAV', 'VEON-RX', 'DSKY', 'LEAS', 'FIVE', 'GMKN', 'ZAYM', 'YNDX'}

def calculate_average_volumes(parts):
    average_volumes = []
    for part in parts:
        total_volume = sum(stock['volume'] for stock in part.values())
        average_volume = total_volume / len(part) if part else 0
        average_volumes.append(average_volume)
    return average_volumes

#Функция для разделения списка на n частей с сбалансированным объемом
def split_into_n_parts(stocks, n):
    sorted_stocks = sorted(stocks.items(), key=lambda x: x[1]['volume'], reverse=True)
    parts = [{} for _ in range(n)]  # Инициализация списка словарей для частей
    volumes = [0 for _ in range(n)]

    for ticker, stock_data in sorted_stocks:
        index = volumes.index(min(volumes))
        parts[index][ticker] = stock_data  # Добавление словаря с данными акции в часть
        volumes[index] += stock_data['volume']

    return parts


def main(stock_run):
    shares = get_list_of_shares()

    logging.info("%d amount of shares", len(shares))

    if shares is None:
        print("No shares returned by get_list_of_shares")
        return

    shares = [share for share in shares if share.get('ticker') not in STOCKS_FOR_IGNORE]

    #shares = [share for share in shares if share.get('ticker') in STOCKS_FOR_TRADE]

    logging.info("%d amount of shares after filter", len(shares))

    parallel_amount = 4 #количество потоков
    available_number_of_threads = get_steam_limits()

    if available_number_of_threads != parallel_amount:
        print(available_number_of_threads)
        raise ValueError('==========Stream limit is not correct==========')

    file_name = f'AAB_closeDate_{stock_run}'

    if return_true_if_file_empty_or_not_exists(file_name):
        data = {}

        for share in shares:
            high_price, close_price, open_today_price, volume, today_low_price = get_candle(share.get('figi'))
            data[share.get('ticker')] = {
                "figi": share.get('figi'),
                "high_price": high_price,
                "close_price": close_price,
                "open_today_price": open_today_price,
                "today_low_price": today_low_price,
                "volume": volume,
                "was_buy": False,
                "number_of_purchases": 0,
                "start_ask_price": 0.0,
                "start_ask_date": 0,
                "proliv_happened": False,
                "proliv_count": 0,
                "trade_sum": 0.0
            }

        n_parts = parallel_amount
        result = split_into_n_parts(data, n_parts)
        average_volumes = calculate_average_volumes(result)
        for i, avg_volume in enumerate(average_volumes, 1):
            print(f"Средний объем для части {i}: {avg_volume}")

        for i, part in enumerate(result, 1):
            print(f"Часть {i}: {part}")
            write_wallet_to_memory_as_json(part, f'AAB_closeDate_{i}')

    selected_shares = read_shares_from_file(shares, stock_run)

    while True:
        try:
            logging.critical("Script started")
            logging.critical("Shares %s \n stock run %s", selected_shares, stock_run)
            run(selected_shares, stock_run)
        except (RequestError, ConnectionAbortedError, ConnectionError) as e:
            logging.error("Stream disconnected. %s", str(e))
            logging.error("Attempting to reconnect...")
            time.sleep(1)  # Wait before attempting to reconnect


if __name__ == "__main__":
    doc = """
    Usage:
      runMainOdinScanner.py [--stock_run=<stock_run>]
    
    Options:
      --stock_run=<stock_run>  Stock run flag [default: 1].
    """
    args = docopt(doc)
    stock_run = args["--stock_run"]

    try:
        main(stock_run)
    except Exception as e:
        print('ERROR:', str(e))
        print(traceback.format_exc())
        telegram_bot_sendtext("Odin stopped due to error")
        telegram_bot_sendtext(str(e))