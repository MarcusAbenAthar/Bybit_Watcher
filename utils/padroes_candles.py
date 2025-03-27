# padroes_candles.py
# Descrição: Dicionário com os padrões de candles e suas respectivas funções de stop loss e take profit.

PADROES_CANDLES = {
    "2crows_alta": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "2crows_baixa": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "3blackcrows_alta": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "3blackcrows_baixa": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "3inside_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "3inside_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "3linestrike_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "3linestrike_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "3outside_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "3outside_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "3starsinsouth_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "3starsinsouth_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "3whitesoldiers_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "3whitesoldiers_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "abandonedbaby_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "abandonedbaby_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "advanceblock_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "advanceblock_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "belthold_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "belthold_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "breakaway_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "breakaway_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "closingmarubozu_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "closingmarubozu_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "concealbabyswall_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "concealbabyswall_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "counterattack_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "counterattack_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "darkcloudcover_alta": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "darkcloudcover_baixa": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "doji_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "doji_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "dojistar_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "dojistar_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "dragonflydoji_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "dragonflydoji_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "engulfing_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "engulfing_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "eveningdojistar_alta": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "eveningdojistar_baixa": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "eveningstar_alta": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "eveningstar_baixa": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "gapsidesidewhite_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "gapsidesidewhite_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "gravestonedoji_alta": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "gravestonedoji_baixa": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "hammer_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "hammer_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "hangingman_alta": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "hangingman_baixa": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "harami_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "harami_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "haramicross_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "haramicross_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "highwave_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "highwave_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "hikkake_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "hikkake_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "hikkakemod_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "hikkakemod_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "homingpigeon_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "homingpigeon_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "identical3crows_alta": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "identical3crows_baixa": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "inneck_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "inneck_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "invertedhammer_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "invertedhammer_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "kicking_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "kicking_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "kickingbylength_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "kickingbylength_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "ladderbottom_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "ladderbottom_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "longleggeddoji_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "longleggeddoji_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "longline_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "longline_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "marubozu_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "marubozu_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "matchinglow_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "matchinglow_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "mathold_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "mathold_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "morningdojistar_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "morningdojistar_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "morningstar_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "morningstar_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "onneck_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "onneck_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "piercing_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "piercing_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "rickshawman_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "rickshawman_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "risefall3methods_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "risefall3methods_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "separatinglines_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "separatinglines_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "shootingstar_alta": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "shootingstar_baixa": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "shortline_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "shortline_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "spinningtop_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "spinningtop_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "stalledpattern_alta": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "stalledpattern_baixa": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "sticksandwich_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "sticksandwich_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "takuri_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "takuri_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "tasukigap_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "tasukigap_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "thrusting_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "thrusting_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "tristar_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "tristar_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "unique3river_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "unique3river_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "upsidegap2crows_alta": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (2 / alavancagem),
    },
    "upsidegap2crows_baixa": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (2 / alavancagem),
    },
    "xsidegap3methods_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "xsidegap3methods_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2] + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3] - (data[2] - data[3]) * (1.5 / alavancagem),
    },
}