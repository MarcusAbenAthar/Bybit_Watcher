# app_module.py

from injector import Module
from plugins.analise_candles import AnaliseCandles
from plugins.armazenamento import Armazenamento
from plugins.banco_dados import BancoDados
from plugins.calculo_alavancagem import CalculoAlavancagem
from plugins.conexao import Conexao
from plugins.execucao_ordens import ExecucaoOrdens
from plugins.medias_moveis import MediasMoveis
from plugins.price_action import PriceAction


class AppModule(Module):
    def configure(self, binder):
        binder.bind(AnaliseCandles)
        binder.bind(Armazenamento)
        binder.bind(BancoDados)
        binder.bind(CalculoAlavancagem)
        binder.bind(Conexao)
        binder.bind(ExecucaoOrdens)
        binder.bind(MediasMoveis)
        binder.bind(PriceAction)
