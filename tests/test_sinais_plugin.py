import unittest
from plugins.sinais_plugin import SinaisPlugin
from unittest.mock import Mock


class TestSinaisPlugin(unittest.TestCase):
    """
    Testes unitários para o plugin SinaisPlugin.
    """

    def setUp(self):
        self.plugin = SinaisPlugin()
        self.plugin.calculo_alavancagem = Mock()
        self.plugin.calculo_alavancagem.calcular_alavancagem.return_value = 1.0

    def test_gerar_sinal(self):
        sinal = self.plugin.gerar_sinal("BTCUSDT", "1h", {})
        self.assertIsInstance(sinal, dict)
        self.assertIn("sinal", sinal)
        self.assertIn("stop_loss", sinal)
        self.assertIn("take_profit", sinal)

    def test_tratamento_erros(self):
        self.assertEqual(
            self.plugin.gerar_sinal(None, None, {}), self.plugin._sinal_padrao()
        )


if __name__ == "__main__":
    unittest.main()
