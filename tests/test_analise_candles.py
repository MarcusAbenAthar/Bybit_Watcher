from unittest import TestCase
import unittest
from unittest.mock import patch, Mock
import numpy as np
from plugins.analise_candles import AnaliseCandles
from configparser import ConfigParser


class TestAnaliseCandles(TestCase):
    """
    Testes unitários para o plugin AnaliseCandles.
    """

    def setUp(self):
        """Configura o ambiente para cada teste."""
        self.plugin = AnaliseCandles()
        # Mock do banco de dados
        self.plugin.banco_dados = Mock()

        # Dados de teste em formato numpy array (OHLC)
        self.dados_teste = np.array(
            [
                [100.0, 105.0, 95.0, 102.0],
                [102.0, 107.0, 97.0, 104.0],
                [104.0, 109.0, 99.0, 106.0],
            ]
        )

    @patch("talib.CDL2CROWS")
    def test_identificar_padrao_deve_chamar_talib(self, mock_cdl):
        """Testa se identificar_padrao chama corretamente o TALib."""
        mock_cdl.return_value = np.array([0, 0, 100])

        open_prices = self.dados_teste[:, 0]
        high_prices = self.dados_teste[:, 1]
        low_prices = self.dados_teste[:, 2]
        close_prices = self.dados_teste[:, 3]

        self.plugin.identificar_padrao(self.dados_teste)
        mock_cdl.assert_called_once_with(
            open_prices, high_prices, low_prices, close_prices
        )

    def test_calcular_confianca(self):
        """Testa o cálculo de confiança."""
        confianca = self.plugin.calcular_confianca(self.dados_teste, "CDL2CROWS")
        self.assertIsInstance(confianca, float)
        self.assertTrue(0 <= confianca <= 100)

    def test_calcular_forca_padrao(self):
        """Testa o cálculo de força do padrão."""
        forca = self.plugin.calcular_forca_padrao(self.dados_teste, "CDL2CROWS")
        self.assertIsInstance(forca, float)

    def test_gerar_sinal_deve_retornar_dict(self):
        """Testa se gerar_sinal retorna um dicionário com os campos corretos."""
        # Mock da configuração
        mock_config = Mock()

        sinal = self.plugin.gerar_sinal(
            self.dados_teste, "CDL2CROWS", "FORTE", "BTCUSDT", "1h", mock_config
        )
        self.assertIsInstance(sinal, dict)
        self.assertIn("padrao", sinal)
        self.assertIn("forca", sinal)

    def test_identificar_padrao_com_dados_invalidos(self):
        """Testa se identificar_padrao trata corretamente dados inválidos."""
        resultado = self.plugin.identificar_padrao(None)
        self.assertIsNone(resultado)


if __name__ == "__main__":
    unittest.main()
