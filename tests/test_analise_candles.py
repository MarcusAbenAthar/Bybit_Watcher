import unittest
from plugins.analise_candles import AnaliseCandles
from unittest.mock import Mock
from utils.padroes_candles import PADROES_CANDLES


class TestAnaliseCandles(unittest.TestCase):
    """
    Testes unitários para o plugin AnaliseCandles.
    """

    def setUp(self):
        self.plugin = AnaliseCandles()
        self.plugin.calculo_alavancagem = Mock()
        self.plugin.calculo_alavancagem.calcular_alavancagem.return_value = 1.0
        self.candle_doji = [100.0, 100.5, 105.0, 95.0]
        self.candle_martelo = [100.0, 110.0, 112.0, 90.0]
        self.candle_estrela = [110.0, 100.0, 115.0, 98.0]

    def test_identificar_padrao(self):
        padrao = self.plugin.identificar_padrao(self.candle_doji)
        self.assertIsNotNone(padrao)

    def test_calcular_forca_padrao(self):
        forca = self.plugin.calcular_forca_padrao(self.candle_martelo, "martelo")
        self.assertIsInstance(forca, float)
        self.assertTrue(0 <= forca <= 100)

    def test_calcular_confianca(self):
        confianca = self.plugin.calcular_confianca(self.candle_martelo, "martelo")
        self.assertIsInstance(confianca, float)
        self.assertTrue(0 <= confianca <= 100)

    def test_gerar_sinal(self):
        for padrao in PADROES_CANDLES.keys():
            sinal = self.plugin.gerar_sinal(
                self.candle_martelo, padrao, "alta", "BTCUSDT", "1h", {}
            )
            self.assertIsInstance(sinal, dict)
            self.assertIn("sinal", sinal)
            self.assertIn("stop_loss", sinal)
            self.assertIn("take_profit", sinal)
            self.assertIn("forca", sinal)
            self.assertIn("confianca", sinal)

    def test_tratamento_erros(self):
        self.assertEqual(self.plugin.calcular_forca_padrao([], "martelo"), 0)
        self.assertEqual(self.plugin.calcular_confianca([], "martelo"), 0)


if __name__ == "__main__":
    unittest.main()
