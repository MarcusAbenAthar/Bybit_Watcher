import unittest
from plugins.price_action import PriceAction
from unittest.mock import Mock


class TestPriceAction(unittest.TestCase):
    """
    Testes unitários para o plugin PriceAction.
    """

    def setUp(self):
        """
        Configura o ambiente de teste antes de cada método.
        """
        self.plugin = PriceAction()

        # Mock para o cálculo de alavancagem
        self.plugin.calculo_alavancagem = Mock()
        self.plugin.calculo_alavancagem.calcular_alavancagem.return_value = 1.0

        # Dados de exemplo para os testes
        self.candle_doji = [100.0, 100.5, 105.0, 95.0]  # Doji clássico
        self.candle_martelo = [100.0, 110.0, 112.0, 90.0]  # Martelo de alta
        self.candle_estrela = [110.0, 100.0, 115.0, 98.0]  # Estrela cadente

    def test_identificar_tendencia(self):
        tendencia = self.plugin.identificar_tendencia(
            [self.candle_martelo, self.candle_doji]
        )
        self.assertIn(tendencia, ["ALTA", "BAIXA", "LATERAL"])

    def test_calcular_forca_padrao(self):
        """
        Testa o cálculo de força do padrão.
        """
        forca = self.plugin.calcular_forca_padrao(self.candle_martelo, "martelo")
        self.assertIsInstance(forca, float)
        self.assertTrue(0 <= forca <= 100)

    def test_gerar_sinal(self):
        """
        Testa a geração de sinais.
        """
        for padrao in ["martelo", "doji", "estrela"]:
            sinal = self.plugin.gerar_sinal(
                self.candle_martelo, padrao, "alta", "BTCUSDT", "1h", {}
            )
            self.assertIsInstance(sinal, dict)
            self.assertIn("sinal", sinal)
            self.assertIn("stop_loss", sinal)
            self.assertIn("take_profit", sinal)

    def test_tratamento_erros(self):
        """
        Testa o tratamento de erros com dados inválidos.
        """
        self.assertEqual(self.plugin.calcular_forca_padrao([], "martelo"), 0)


if __name__ == "__main__":
    unittest.main()
