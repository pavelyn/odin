import configparser
import os


def get_file_path(file_name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, '..', '..', 'resource', file_name)
    return os.path.normpath(file_path)


def get_telegram_config(file_name):
    config = configparser.ConfigParser()
    config.read(get_file_path(file_name))
    return config['telegram']['token'], config['telegram']['id']


def get_tinkoff_config(file_name):
    config = configparser.ConfigParser()
    config.read(get_file_path(file_name))
    return config['tinkoff']['api_token'], config['tinkoff']['accountId']


def get_settings(file_name):
    config = configparser.ConfigParser()
    config.read(get_file_path(file_name))
    config_section_name = 'settings'

    number_of_attempt_for_limit_order = int(config[config_section_name]['number_of_attempt_for_limit_order'])
    expected_percent_change_for_buy = float(config[config_section_name]['expected_percent_change_for_buy'])
    percent_for_drop = float(config[config_section_name]['percent_for_drop'])
    expected_percent_change_for_sell = float(config[config_section_name]['expected_percent_change_for_sell'])
    if_buy = bool(config[config_section_name]['if_buy'])
    money_part = int(config[config_section_name]['money_part'])
    depo = int(config[config_section_name]['depo'])
    return number_of_attempt_for_limit_order, expected_percent_change_for_buy, percent_for_drop, expected_percent_change_for_sell, if_buy, money_part, depo