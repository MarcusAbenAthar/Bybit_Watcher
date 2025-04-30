"""
Teste isolado de conexão com Bybit usando ccxt e variáveis do .env.
Salve este arquivo na raiz do projeto e execute para validar as credenciais.
"""
import os
from dotenv import load_dotenv
import ccxt
import argparse
import json
from pprint import pprint

# Carrega variáveis do .env
load_dotenv()

def testar_conexao_bybit(symbol=None):
    testnet = os.getenv("BYBIT_TESTNET", "true").lower() == "true"
    if testnet:
        api_key = os.getenv("TESTNET_BYBIT_API_KEY")
        api_secret = os.getenv("TESTNET_BYBIT_API_SECRET")
        base_url = "https://api-testnet.bybit.com"
    else:
        api_key = os.getenv("BYBIT_API_KEY")
        api_secret = os.getenv("BYBIT_API_SECRET")
        base_url = "https://api.bybit.com"

    print(f"Ambiente: {'TESTNET' if testnet else 'MAINNET'}")
    print(f"API_KEY: {api_key}")
    print(f"API_SECRET: {api_secret}")
    print(f"Base URL: {base_url}\n")

    try:
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'linear',
                'testnet': testnet,
            },
        })
        if testnet:
            exchange.set_sandbox_mode(True)
        # Testa chamada simples
        mercados = exchange.fetch_markets()
        if symbol:
            # Filtra mercados pelo símbolo ou ID
            filtered = [m for m in mercados if m.get('symbol') == symbol or m.get('id') == symbol]
            if not filtered:
                print(f"Símbolo {symbol} não encontrado.")
            else:
                for m in filtered:
                    print(json.dumps(m, indent=2, ensure_ascii=False))
        else:
            print(f"Conexão bem-sucedida! Total de mercados disponíveis: {len(mercados)}")
            # Salva dados completos em JSON para análise
            output_file = 'mercados_bybit.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(mercados, f, ensure_ascii=False, indent=2)
            print(f"Dados completos salvos em: {output_file}")
    except Exception as e:
        print("Erro ao conectar na Bybit:", str(e))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Teste de conexão Bybit com opção de filtro por símbolo")
    parser.add_argument('-s', '--symbol', help="Símbolo para filtrar (ex: BTC/USDT ou BTCUSDT)")
    args = parser.parse_args()
    testar_conexao_bybit(args.symbol)
