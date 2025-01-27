PADROES_CANDLES = {
    # Padrões 1-10
    "dois_corvos_alta": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "dois_corvos_baixa": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "tres_corvos_negros_alta": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (2 / alavancagem),
    },
    "tres_corvos_negros_baixa": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (2 / alavancagem),
    },
    "tres_dentro_cima_baixo_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "tres_dentro_cima_baixo_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "golpe_de_tres_linhas_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (2 / alavancagem),
    },
    "golpe_de_tres_linhas_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (2 / alavancagem),
    },
    "tres_fora_cima_baixo_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "tres_fora_cima_baixo_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    # Padrões 11-20
    "tres_estrelas_no_sul_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (2 / alavancagem),
    },
    "tres_estrelas_no_sul_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (2 / alavancagem),
    },
    "tres_soldados_brancos_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "tres_soldados_brancos_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "bebe_abandonado_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (2 / alavancagem),
    },
    "bebe_abandonado_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (2 / alavancagem),
    },
    "avanco_de_bloco_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "avanco_de_bloco_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "cinturao_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (2 / alavancagem),
    },
    "cinturao_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (2 / alavancagem),
    },
    # Padrões 21-30
    "rompimento_de_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "rompimento_de_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "fechamento_marubozu_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (2 / alavancagem),
    },
    "fechamento_marubozu_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (2 / alavancagem),
    },
    "engolimento_de_bebe_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "engolimento_de_bebe_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "contra_ataque_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (2 / alavancagem),
    },
    "contra_ataque_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (2 / alavancagem),
    },
    "cobertura_de_nuvem_escura_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "cobertura_de_nuvem_escura_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    # Padrões 31-40
    "doji_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (2 / alavancagem),
    },
    "doji_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (2 / alavancagem),
    },
    "doji_estrela_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "doji_estrela_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "libelula_doji_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (2 / alavancagem),
    },
    "libelula_doji_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (2 / alavancagem),
    },
    "engolfo_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    # Padrões 31-40
    "estrela_da_manha_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (2 / alavancagem),
    },
    "estrela_da_manha_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (2 / alavancagem),
    },
    "estrela_da_noite_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "estrela_da_noite_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "lacuna_lateral_lado_branco_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (2 / alavancagem),
    },
    "lacuna_lateral_lado_branco_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (2 / alavancagem),
    },
    "lapide_doji_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "lapide_doji_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "martelo_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (2 / alavancagem),
    },
    "martelo_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (2 / alavancagem),
    },
    # Padrões 41-50
    "enforcado_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "enforcado_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "harami_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (2 / alavancagem),
    },
    "harami_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (2 / alavancagem),
    },
    "harami_cruzado_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "harami_cruzado_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "onda_alta_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (2 / alavancagem),
    },
    "onda_alta_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (2 / alavancagem),
    },
    "hikkake_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (1.5 / alavancagem),
    },
    "hikkake_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.05 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (1.5 / alavancagem),
    },
    # Padrões 51-52
    "hikkake_modificado_alta": {
        "sinal": "compra",
        "stop_loss": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (2 / alavancagem),
    },
    "hikkake_modificado_baixa": {
        "sinal": "venda",
        "stop_loss": lambda data, alavancagem: data[2]
        + (data[2] - data[3]) * (0.1 / alavancagem),
        "take_profit": lambda data, alavancagem: data[3]
        - (data[2] - data[3]) * (2 / alavancagem),
    },
}
