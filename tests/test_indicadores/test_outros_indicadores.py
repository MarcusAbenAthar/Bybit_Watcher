import unittest
from unittest.mock import Mock, patch
import numpy as np
from plugins.indicadores.outros_indicadores import OutrosIndicadores


class TestOutrosIndicadores(unittest.TestCase):
    def setUp(self):
        """Configura o ambiente de teste."""
        self.config = {"symbol": "BTCUSDT", "timeframe": "1h", "alavancagem": 1}
        self.outros = OutrosIndicadores(self.config)
        self.outros.calculo_alavancagem = Mock()
        self.outros.banco_dados = Mock()

        self.dados_teste = [
            [1000000000, 100.0, 105.0, 95.0, 102.0, 1000],
            [2000000000, 102.0, 107.0, 97.0, 104.0, 1000],
            [3000000000, 104.0, 109.0, 99.0, 106.0, 1000],
        ]

    def test_calcular_fibonacci_retracement(self):
        """Testa o cálculo dos níveis de Fibonacci."""
        niveis = self.outros.calcular_fibonacci_retracement(self.dados_teste)
        self.assertIsInstance(niveis, dict)
        self.assertIn("0.236", niveis)
        self.assertIn("0.382", niveis)
        self.assertIn("0.5", niveis)
        self.assertIn("0.618", niveis)
        self.assertIn("0.786", niveis)

    @patch("talib.ICHIMOKU")
    def test_calcular_ichimoku(self, mock_ichimoku):
        """Testa o cálculo do Ichimoku Cloud."""
        mock_ichimoku.return_value = (
            np.array([100.0, 102.0, 104.0]),  # tenkan_sen
            np.array([98.0, 100.0, 102.0]),  # kijun_sen
            np.array([105.0, 107.0, 109.0]),  # senkou_span_a
            np.array([95.0, 97.0, 99.0]),  # senkou_span_b
        )
        ichimoku = self.outros.calcular_ichimoku(self.dados_teste)
        self.assertIsInstance(ichimoku, dict)
        self.assertIn("tenkan_sen", ichimoku)
        self.assertIn("kijun_sen", ichimoku)
        self.assertIn("senkou_span_a", ichimoku)
        self.assertIn("senkou_span_b", ichimoku)

    def test_calcular_pivot_points(self):
        """Testa o cálculo dos Pivot Points."""
        pivot_points = self.outros.calcular_pivot_points(self.dados_teste)
        self.assertIsInstance(pivot_points, dict)
        self.assertIn("PP", pivot_points)
        self.assertIn("R1", pivot_points)
        self.assertIn("S1", pivot_points)
        self.assertIn("R2", pivot_points)
        self.assertIn("S2", pivot_points)

    def test_gerar_sinal(self):
        """Testa a geração de sinais."""
        sinal = self.outros.gerar_sinal(
            self.dados_teste,
            "ichimoku",
            "cruzamento_alta",
            "BTCUSDT",
            "1h",
            self.config,
        )
        self.assertIsInstance(sinal, dict)
        self.assertIn("sinal", sinal)
        self.assertIn("stop_loss", sinal)
        self.assertIn("take_profit", sinal)

    def test_executar(self):
        """Testa a execução completa do indicador."""
        self.outros.executar(self.dados_teste, "BTCUSDT", "1h")
        self.outros.banco_dados.conn.cursor.assert_called()
