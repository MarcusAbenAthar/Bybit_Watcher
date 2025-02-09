import unittest
from unittest.mock import Mock
import numpy as np
from plugins.medias_moveis import MediasMoveis
from plugins.price_action import PriceAction
from plugins.sinais_plugin import SinaisPlugin


class TestIntegracaoPlugins(unittest.TestCase):

    def setUp(self):
        """Configuração para testes de integração."""
        self.medias = MediasMoveis()
        self.price_action = PriceAction()
        self.sinais = SinaisPlugin()

        # Mock do gerente e configurações
        self.mock_config = Mock()
        self.medias.inicializar(self.mock_config)
        self.price_action.inicializar(self.mock_config)
        self.sinais.inicializar(self.mock_config)

    def test_fluxo_analise_completa(self):
        """Testa o fluxo completo de análise."""
        dados = np.array(
            [
                [0, 100.0, 105.0, 95.0, 102.0, 1000.0],
                [0, 102.0, 107.0, 97.0, 104.0, 1100.0],
                [0, 104.0, 109.0, 99.0, 106.0, 1200.0],
            ],
            dtype=np.float64,
        )

        # 1. Calcula médias
        medias = self.medias.calcular_media_movel(dados, 2, "simples")
        self.assertIsNotNone(medias)
        self.assertIsInstance(medias, np.ndarray)
        self.assertTrue(len(medias) > 0)

        # 2. Analisa price action
        padrao = self.price_action.analisar_padrao(dados[-1])
        self.assertIsInstance(padrao, dict)
        self.assertIn("tendencia", padrao)
        self.assertIn("forca", padrao)

        # 3. Gera sinal
        sinal = self.sinais.logar_sinal(
            "BTCUSDT",
            "1h",
            {
                "direcao": "COMPRA" if padrao["tendencia"] == "ALTA" else "VENDA",
                "stop_loss": float(dados[-1][3]),  # low
                "take_profit": float(dados[-1][2]),  # high
            },
        )
        self.assertIsInstance(sinal, dict)
        self.assertIn("symbol", sinal)
        self.assertIn("timeframe", sinal)
        self.assertIn("direcao", sinal)
