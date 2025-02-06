from unittest import TestCase
import unittest
from unittest.mock import patch, Mock
from plugins.sinais_plugin import SinaisPlugin


class TestSinaisPlugin(TestCase):
    """
    Testes unitários para o plugin SinaisPlugin.
    """

    def setUp(self):
        """Configura o ambiente para cada teste."""
        self.plugin = SinaisPlugin()
        self.sinal_teste = {
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "direcao": "COMPRA",
            "stop_loss": 100.0,
            "take_profit": 110.0,
        }

    def test_logar_sinal_deve_retornar_dict(self):
        """Testa se logar_sinal retorna um dicionário quando recebe dados válidos."""
        with patch("plugins.sinais_plugin.logger"):
            resultado = self.plugin.logar_sinal(
                self.sinal_teste["symbol"],
                self.sinal_teste["timeframe"],
                self.sinal_teste,
            )
            self.assertIsInstance(resultado, dict)
            self.assertEqual(resultado["symbol"], "BTCUSDT")
            self.assertEqual(resultado["timeframe"], "1h")
            self.assertEqual(resultado["direcao"], "COMPRA")

    def test_logar_sinal_deve_lancar_erro_com_dados_invalidos(self):
        """Testa se logar_sinal lança erro quando recebe dados inválidos."""
        with patch("plugins.sinais_plugin.logger"):
            with self.assertRaises(Exception):
                self.plugin.logar_sinal(None, None, None)


if __name__ == "__main__":
    unittest.main()
