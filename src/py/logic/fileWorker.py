import json
import os
import ast
import msvcrt
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_file_path(ticket_name):
    script_dir = os.path.dirname(os.path.abspath(__file__))  # get the directory of the current script
    file_path = os.path.join(script_dir, 'memory_files', f'{ticket_name}.json')  # create the path to the file
    return os.path.normpath(file_path)  # normalize the path


def return_true_if_file_empty_or_not_exists(ticket_name):
    file_path = get_file_path(ticket_name)
    if os.path.isfile(file_path):
        if os.stat(file_path).st_size == 0:
            return True
        else:
            return False
    else:
        return True


def write_wallet_to_memory(stock, ticket_name):
    file_path = get_file_path(ticket_name)
    with open(file_path, "a") as file_object:
        file_object.write(str(stock))


def write_wallet_to_memory_as_json(stock, ticket_name):
    file_path = get_file_path(ticket_name)
    try:
        # Читаем текущее содержимое файла
        with open(file_path, "r", encoding="utf-8") as file_object:
            current_data = json.load(file_object)
    except FileNotFoundError:
        # Если файла не существует, создаем новый со стандартным содержимым
        current_data = {}
    except json.JSONDecodeError:
        # Если существующий файл не является валидным JSON, используем пустой словарь
        current_data = {}

    # Обновляем данные
    current_data.update(stock)

    # Записываем обновленные данные обратно в файл
    with open(file_path, "w", encoding="utf-8") as file_object:
        json.dump(current_data, file_object, ensure_ascii=False, indent=4)


def add_stock_name_to_file(name_of_file, stock_name):
    file_path = get_file_path(name_of_file)
    with open(file_path, 'r+') as file:
        lines = file.read().splitlines()
        if stock_name not in lines:
            file.write(f'{stock_name}\n')


def write_wallet_to_memory_with_clean(stock, ticket_name):
    file_path = get_file_path(ticket_name)

    existing_data = {}
    try:
        with open(file_path, "r") as file_object:
            existing_data = json.load(file_object)
    except FileNotFoundError:
        pass

    existing_data.update(stock)

    with open(file_path, "w") as file_object:
        file_object.write(json.dumps(existing_data))



def write_file_with_new_line(stock, ticket_name):
    file_path = get_file_path(ticket_name)
    with open(file_path, "a") as file_object:
        file_object.write(str(stock) + '\n')


def clear_memory_file(ticket_name):
    file_path = get_file_path(ticket_name)
    with open(file_path, 'w') as file_object:
        pass


def read_wallet_from_memory(ticket_name):
    file_path = get_file_path(ticket_name)
    if os.path.isfile(file_path):
        with open(file_path, "r") as f:
            content = f.read()
            try:
                mylist = ast.literal_eval(content)
            except ValueError:
                print('Decoding JSON has failed')
                return None
            return mylist
    else:
        print('File does not exist')
        return None


def read_ai_scanner_signals(ticket_name):
    file_path = get_file_path(ticket_name)
    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            return file.readlines()

    else:
        print('File does not exist')
        return None


def search_ticker(ticker, figi, name_of_file):
    file_path = get_file_path(name_of_file)
    with open(file_path, "r") as file:
        data = file.read()
        data = ast.literal_eval(data.replace("false", "False").replace("true", "True"))

    stock_data = data.get(ticker)
    if stock_data and stock_data['figi'] == figi:
        return stock_data['high_price'], stock_data['close_price'], stock_data['open_today_price'], stock_data['today_low_price'],\
            stock_data['volume'], stock_data['was_buy'], stock_data['number_of_purchases'], stock_data['start_ask_price'], stock_data['start_ask_date'], stock_data['proliv_happened'], stock_data['proliv_count'], stock_data['trade_sum']
    else:
        raise ValueError('==========search_ticker cannot find ticker or figi==========')


def search_ticker_soplya(ticker, figi):
    file_path = get_file_path("AAB_soplya")
    with open(file_path, "r") as file:
        data = file.read()
        data = ast.literal_eval(data.replace("false", "False").replace("true", "True"))

    stock_data = data.get(ticker)
    if stock_data and stock_data['figi'] == figi:
        return stock_data['today_high_price'], stock_data['previous_close_price'], stock_data['today_volume_price'], stock_data['previous_volume_price'], stock_data['was_buy'], stock_data['number_of_purchases']
    else:
        raise ValueError('==========search_ticker cannot find ticker or figi==========')


def search_candidates_to_buy(ticker, figi):
    file_path = get_file_path("AAB_candidates_to_buy")
    with open(file_path, "r") as file:
        data = file.read()
        data = ast.literal_eval(data.replace("false", "False").replace("true", "True"))

    stock_data = data.get(ticker)
    if stock_data and stock_data['figi'] == figi:
        return stock_data['price_to_sell'], stock_data['price_to_buy'], stock_data['price_to_stop'], stock_data['change_percent'], stock_data['today_volume_price'], stock_data['order_id'], stock_data['execution_report_status'],\
            stock_data['was_buy'], stock_data['lots_executed'], stock_data['executed_order_price'], stock_data['executed_commission']
    else:
        raise ValueError('==========search_ticker cannot find ticker or figi==========')


def update_candidates_to_buy(stock_name, get_figi, price_to_sell=None, price_to_buy=None, price_to_stop=None, change_percent=None, today_volume_price=None, order_id=None,
                             execution_report_status=None, was_buy=None, lots_executed=None, executed_order_price=None, executed_commission=None):
    file_path = get_file_path("AAB_candidates_to_buy")
    with open(file_path, "r") as file:
        data = file.read()
        data = ast.literal_eval(data.replace("false", "False").replace("true", "True"))

    if stock_name in data and data[stock_name]['figi'] == get_figi:
        if price_to_sell is not None:
            data[stock_name]['price_to_sell'] = price_to_sell
        if price_to_buy is not None:
            data[stock_name]['price_to_buy'] = price_to_buy
        if price_to_stop is not None:
            data[stock_name]['price_to_stop'] = price_to_stop
        if change_percent is not None:
            data[stock_name]['change_percent'] = change_percent
        if today_volume_price is not None:
            data[stock_name]['today_volume_price'] = today_volume_price
        if order_id is not None:
            data[stock_name]['order_id'] = order_id
        if execution_report_status is not None:
            data[stock_name]['execution_report_status'] = execution_report_status
        if was_buy is not None:
            data[stock_name]['was_buy'] = was_buy
        if lots_executed is not None:
            data[stock_name]['lots_executed'] = lots_executed
        if executed_order_price is not None:
            data[stock_name]['executed_order_price'] = executed_order_price
        if executed_commission is not None:
            data[stock_name]['executed_commission'] = executed_commission
    else:
        raise ValueError('==========update_ticker cannot find ticker or figi==========')

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


def update_ticker(name_of_file, stock_name, get_figi, high_price=None, close_price=None, open_today_price=None, today_low_price=None, volume=None, was_buy=None, number_of_purchases=None, start_ask_price=None, start_ask_date=None, proliv_happened=None, proliv_count=None, trade_sum=None):
    file_path = get_file_path(name_of_file)
    with open(file_path, "r") as file:
        data = file.read()
        data = ast.literal_eval(data.replace("false", "False").replace("true", "True"))

    if stock_name in data and data[stock_name]['figi'] == get_figi:
        if high_price is not None:
            data[stock_name]['high_price'] = high_price
        if close_price is not None:
            data[stock_name]['close_price'] = close_price
        if open_today_price is not None:
            data[stock_name]['open_today_price'] = open_today_price
        if today_low_price is not None:
            data[stock_name]['today_low_price'] = today_low_price
        if volume is not None:
            data[stock_name]['volume'] = volume
        if was_buy is not None:
            data[stock_name]['was_buy'] = was_buy
        if number_of_purchases is not None:
            data[stock_name]['number_of_purchases'] = number_of_purchases
        if start_ask_price is not None:
            data[stock_name]['start_ask_price'] = start_ask_price
        if start_ask_date is not None:
            data[stock_name]['start_ask_date'] = start_ask_date
        if proliv_happened is not None:
            data[stock_name]['proliv_happened'] = proliv_happened
        if proliv_count is not None:
            data[stock_name]['proliv_count'] = proliv_count
        if trade_sum is not None:
            data[stock_name]['trade_sum'] = trade_sum
    else:
        raise ValueError('==========update_ticker cannot find ticker or figi==========')

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


def search_lenta(ticker, figi):
    file_path = get_file_path("AAA_lenta")
    with open(file_path, "r") as file:
        data = file.read()
        data = ast.literal_eval(data.replace("false", "False").replace("true", "True"))

    stock_data = data.get(ticker)
    if stock_data and stock_data['figi'] == figi:
        return stock_data['price_lenta'], stock_data['quantity_lenta'], stock_data['time_deal_lenta'], stock_data['direction']
    else:
        return 0, 0, 0, 0


def update_lenta(stock_name, get_figi, price_lenta=None, quantity_lenta=None, time_deal_lenta=None, direction=None):
    file_path = get_file_path("AAA_lenta")
    with open(file_path, "r") as file:
        data = file.read()
        data = ast.literal_eval(data.replace("false", "False").replace("true", "True"))

    if stock_name in data and data[stock_name]['figi'] == get_figi:
        if price_lenta is not None:
            data[stock_name]['price_lenta'] = price_lenta
        if quantity_lenta is not None:
            data[stock_name]['quantity_lenta'] = quantity_lenta
        if time_deal_lenta is not None:
            data[stock_name]['time_deal_lenta'] = time_deal_lenta.isoformat()
        if direction is not None:
            data[stock_name]['direction'] = direction
    else:
        raise ValueError('==========update_lenta cannot find ticker or figi==========')

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


def search_trailing_stop(ticker, figi):
    file_path = get_file_path("AAA_trailing_stop")
    with open(file_path, "r") as file:
        data = file.read()
        data = ast.literal_eval(data.replace("false", "False").replace("true", "True"))

    stock_data = data.get(ticker)
    if stock_data and stock_data['figi'] == figi:
        return stock_data['amount'], stock_data['price'], stock_data['trailing_stop_price'], stock_data['activation_price_bool']
    else:
        raise ValueError('==========search_ticker cannot find ticker or figi==========')


def get_trailing_stop():
    file_path = get_file_path("AAA_trailing_stop")
    with open(file_path, "r") as file:
        data = file.read()
        data = ast.literal_eval(data.replace("false", "False").replace("true", "True"))

    return data


def update_trailing_stop(stock_name, get_figi, amount=None, price=None, trailing_stop_price=None, activation_price_bool=None):
    file_path = get_file_path("AAA_trailing_stop")
    with open(file_path, "r") as file:
        data = file.read()
        data = ast.literal_eval(data.replace("false", "False").replace("true", "True"))

    if stock_name in data and data[stock_name]['figi'] == get_figi:
        if amount is not None:
            data[stock_name]['amount'] = amount
        if price is not None:
            data[stock_name]['price'] = price
        if trailing_stop_price is not None:
            data[stock_name]['trailing_stop_price'] = trailing_stop_price
        if activation_price_bool is not None:
            data[stock_name]['activation_price_bool'] = activation_price_bool
    else:
        raise ValueError('==========update_lenta cannot find ticker or figi==========')

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


def read_shares_from_file(shares, stock_run):
    file_name = get_file_path("AAB_closeDate_" + stock_run)  # Путь к файлу предполагается верным
    selected_shares = []  # Список для хранения отфильтрованных акций
    try:
        with open(file_name, 'r') as file:
            share_data = json.load(file)  # Чтение и десериализация всего файла сразу
            file_figis = set(share_data.keys())  # Получение ключей (figi) из данных файла

        # Фильтрация shares и сохранение совпадений
        for share in shares:
            if share['ticker'] in file_figis:
                selected_shares.append(share)

        return selected_shares
    except FileNotFoundError:
        print(f"Файл {file_name} не найден.")
        return []
    except json.JSONDecodeError as e:
        print(f"Ошибка при чтении JSON из файла {file_name}: {e}")
        return []
    except Exception as e:
        print(f"Ошибка: {e}")
        return []


def lock_file(file_name, mode='r+', timeout=10):
    """Пытается заблокировать файл для эксклюзивного доступа, повторяя попытки в течение заданного времени."""
    file_path = get_file_path(file_name)
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            file = open(file_path, mode)
            fd = file.fileno()
            msvcrt.locking(fd, msvcrt.LK_NBLCK, os.path.getsize(file_path) or 1)
            logging.info("Файл %s заблокирован", file.name)
            return file
        except OSError as e:
            logging.info("Невозможно заблокировать файл %s, он уже используется. Повторная попытка...", file_name)
            file.close()
            time.sleep(1)  # Задержка перед следующей попыткой
    logging.info("Время ожидания истекло, файл %s так и не был заблокирован.", file_name)
    return None


def unlock_file(file):
    """Разблокирует файл."""
    if file:
        fd = file.fileno()
        try:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, os.path.getsize(file.name) or 1)
        except OSError as e:
            logging.info("Файл %s разблокирован", file.name)
        finally:
            file.close()


def write_list_to_file(file, data_list):
    try:
        file.seek(0)
        file.write(str(data_list))
        file.truncate()
    except Exception as e:
        print(f"Ошибка при записи в файл: {e}")
    finally:
        file.flush()