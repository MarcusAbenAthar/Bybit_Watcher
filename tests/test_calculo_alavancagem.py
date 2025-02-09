import unittest
from unittest.mock import Mock, patch
import numpy as np
from plugins.calculo_alavancagem import CalculoAlavancagem


class TestCalculoAlavancagem(unittest.TestCase):

    def setUp(self):
        """Configuração inicial para cada teste."""
        self.plugin = CalculoAlavancagem()
        # Mock GerentePlugin
        self.plugin.gerente = Mock()
        self.plugin.gerente._singleton_plugins = {"conexao": Mock()}

    def test_singleton(self):
        """Testa se o padrão singleton está funcionando."""
        plugin1 = CalculoAlavancagem()
        plugin2 = CalculoAlavancagem()
        self.assertIs(plugin1, plugin2, "As instâncias devem ser as mesmas (singleton)")

    def test_calculo_alavancagem_basico(self):
        """Testa o cálculo básico de alavancagem."""
        # Setup
        dados = np.array(
            [[0, 0, 100.0, 90.0, 95.0, 1000.0] for _ in range(20)], dtype=np.float64
        )
        symbol = "BTC/USDT"
        timeframe = "1h"
        config = Mock()
        config.getint.return_value = 20

        # Mock exchange
        mock_exchange = Mock()
        mock_exchange.fetch_ohlcv.return_value = dados
        self.plugin.gerente._singleton_plugins["conexao"].exchange = mock_exchange

        # Test
        alavancagem = self.plugin.calcular_alavancagem(dados, symbol, timeframe, config)
        self.assertIsInstance(alavancagem, (int, float))
        self.assertGreaterEqual(alavancagem, 1)
        self.assertLessEqual(alavancagem, 20)

    def test_calculo_atr(self):
        """Testa o cálculo do ATR."""
        # Criar dados como numpy array
        dados = np.array(
            [[0, 0, 100.0, 90.0, 95.0, 1000.0] for _ in range(20)], dtype=np.float64
        )
        atr = self.plugin.calcular_atr(dados)

        self.assertIsNotNone(atr)
        self.assertTrue(isinstance(atr, np.ndarray))


if __name__ == "__main__":
    unittest.main()
