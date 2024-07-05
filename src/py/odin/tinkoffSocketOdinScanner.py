import logging
import time

from tinkoff.invest import (
    Client,
    MarketDataRequest,
    SubscriptionAction,
    SubscribeOrderBookRequest, SubscribeTradesRequest, OrderBookInstrument, SubscribeLastPriceRequest, LastPriceInstrument,
    SubscribeCandlesRequest, CandleInstrument, TradeInstrument)
from tinkoff.invest.grpc.marketdata_pb2 import SUBSCRIPTION_INTERVAL_ONE_DAY, TRADE_SOURCE_ALL

from src.py.logic.fileWorker import search_ticker
from src.py.logic.other import short_price_converter
from src.py.logic.propParser import get_tinkoff_config
from src.py.odin.streamOdinScanner import eventHandler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def run(orderbook_subs, stock_run):
    api_token, account_id = get_tinkoff_config('config.properties')

    def request_iterator():
        for x in orderbook_subs:
            yield MarketDataRequest(
                subscribe_order_book_request=SubscribeOrderBookRequest(
                    subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
                    instruments=[
                        OrderBookInstrument(
                            figi=x.get('figi'),
                            depth=20,
                            instrument_id=x.get('instrumentId')
                        )
                    ],
                ),
            )
            yield MarketDataRequest(
                subscribe_last_price_request=SubscribeLastPriceRequest(
                    subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
                    instruments=[
                        LastPriceInstrument(
                            figi=x.get('figi'),
                            instrument_id=x.get('instrumentId')
                        )
                    ],
                ),
            )
            yield MarketDataRequest(
                subscribe_candles_request=SubscribeCandlesRequest(
                    subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
                    instruments=[
                        CandleInstrument(
                            figi=x.get('figi'),
                            interval=SUBSCRIPTION_INTERVAL_ONE_DAY,
                            instrument_id=x.get('instrumentId')
                        )
                    ],
                    waiting_close=False
                ),
            )
            # yield MarketDataRequest(
            #     subscribe_trades_request=SubscribeTradesRequest(
            #         subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
            #         instruments=[
            #             TradeInstrument(
            #                 figi=x.get('figi'),
            #                 instrument_id=x.get('instrumentId')
            #             )
            #         ],
            #         trade_type = TRADE_SOURCE_ALL
            #     ),
            # )
        while True:
            time.sleep(0.5)

    figi_mapping = {x.get('figi'): x for x in orderbook_subs}
    logging.critical("Figi mapped")

    last_prices = {}
    candles = {}
    #trades = {} ###### Сканер объемов на основе ленты принтов

    with Client(api_token) as client:
        for marketdata in client.market_data_stream.market_data_stream(
                request_iterator()
        ):
            last_price = marketdata.last_price
            candle = marketdata.candle
            #trade = marketdata.trade
            orderbook_data = marketdata.orderbook

            if last_price is not None:
                stock_figi = last_price.figi
                last_prices[stock_figi] = last_price

            if candle is not None:
                stock_figi = candle.figi
                candles[stock_figi] = candle

            # if trade is not None:
            #     stock_figi = trade.figi
            #     trades[stock_figi] = trade

            if orderbook_data is not None:
                event = []

                stock_figi = orderbook_data.figi
                stock_info = figi_mapping.get(stock_figi)

                if stock_info is None:
                    continue

                last_price_info = last_prices.get(stock_figi)

                if last_price_info is not None:
                    last_price = short_price_converter(last_price_info.price)
                else:
                    continue

                # trades_info = trades.get(stock_figi)
                #
                # if trades_info is not None:
                #     trade_direction = int(trades_info.direction)
                #     trade_price = short_price_converter(trades_info.price)
                #     trade_quantity = trades_info.quantity
                #     trade_time = trades_info.time
                # else:
                #     continue

                stock_name = stock_info.get('ticker')
                lot = stock_info.get('lot')
                sector = stock_info.get('sector')

                asks_raw = orderbook_data.asks
                bids_raw = orderbook_data.bids

                file_name = f'AAB_closeDate_{stock_run}'

                high_price, close_price, open_today_price, today_low_price, volume, was_buy, number_of_purchases, start_ask_price, start_ask_date, proliv_happened, proliv_count, trade_sum = search_ticker(
                    stock_name, stock_figi, file_name)

                candles_info = candles.get(stock_figi)

                if candles_info is not None:
                    high_price = short_price_converter(candles_info.high)
                    open_today_price = short_price_converter(candles_info.open)
                    today_low_price = short_price_converter(candles_info.low)
                    volume = candles_info.volume
                else:
                    continue

                if len(asks_raw) > 0 and len(bids_raw) > 0:
                    ask_price = short_price_converter(asks_raw[0].price)
                    bid_price = short_price_converter(bids_raw[0].price)
                    ask_amount = asks_raw[0].quantity
                    bid_amount = bids_raw[0].quantity

                    event.append({
                        'figi': stock_figi,
                        'lot': lot,
                        'asks': ask_price,
                        'bids': bid_price,
                        'stock_name': stock_name,
                        'ask_amount': ask_amount,
                        'bid_amount': bid_amount,
                        'nano_value_asks': asks_raw[0].price.nano,
                        'units_value_asks': asks_raw[0].price.units,
                        'nano_value_bids': bids_raw[0].price.nano,
                        'units_value_bids': bids_raw[0].price.units,
                        'sector': sector,
                        'high_price': high_price,
                        'close_price': close_price,
                        'open_today_price': open_today_price,
                        'today_low_price': today_low_price,
                        'volume': volume,
                        'was_buy': was_buy,
                        'number_of_purchases': number_of_purchases,
                        'start_ask_price': start_ask_price,
                        'asks_raw': asks_raw,
                        'bids_raw': bids_raw,
                        'start_ask_date': start_ask_date,
                        'last_price': last_price,
                        'proliv_happened': proliv_happened,
                        'proliv_count': proliv_count,
                        # 'trade_direction': trade_direction,
                        # 'trade_price': trade_price,
                        # 'trade_quantity': trade_quantity,
                        # 'trade_time': trade_time,
                        # 'trade_sum': trade_sum,
                    })

                    eventHandler(event, stock_run)
