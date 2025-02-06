from unittest import TestCase
from unittest.mock import patch, Mock
import numpy as np
from plugins.indicadores.indicadores_volatilidade import IndicadoresVolatilidade


class TestIndicadoresVolatilidade(TestCase):
    def setUp(self):
        """Configura o ambiente para cada teste."""
        self.plugin = IndicadoresVolatilidade()
        self.plugin.banco_dados = Mock()

        # Dados de teste em formato numpy array (OHLCV)
        self.dados_teste = np.array(
            [
                [100.0, 105.0, 95.0, 102.0, 1000],
                [102.0, 107.0, 97.0, 104.0, 1500],
                [104.0, 109.0, 99.0, 106.0, 2000],
            ]
        )

    @patch("talib.ATR")
    def test_calcular_atr(self, mock_atr):
        """Testa o cálculo do Average True Range."""
        mock_atr.return_value = np.array([8.0, 8.5, 9.0])

        resultado = self.plugin.calcular_atr(self.dados_teste)

        mock_atr.assert_called_once()
        self.assertIsInstance(resultado, np.ndarray)

    @patch("talib.BBANDS")
    def test_calcular_bandas_bollinger(self, mock_bbands):
        """Testa o cálculo das Bandas de Bollinger."""
        mock_bbands.return_value = (
            np.array([110.0, 112.0, 114.0]),  # upper
            np.array([102.0, 104.0, 106.0]),  # middle
            np.array([94.0, 96.0, 98.0]),  # lower
        )

        superior, media, inferior = self.plugin.calcular_bandas_bollinger(
            self.dados_teste
        )

        mock_bbands.assert_called_once()
        self.assertIsInstance(superior, np.ndarray)
        self.assertIsInstance(media, np.ndarray)
        self.assertIsInstance(inferior, np.ndarray)

    def test_gerar_sinal_deve_retornar_dict(self):
        """Testa se gerar_sinal retorna um dicionário com os campos corretos."""
        mock_config = Mock()

        sinal = self.plugin.gerar_sinal(
            self.dados_teste,
            "bandas_bollinger",
            "superior",
            "BTCUSDT",
            "1h",
            mock_config,
        )

        self.assertIsInstance(sinal, dict)
        self.assertIn("sinal", sinal)

    def test_dados_invalidos(self):
        """Testa o comportamento com dados inválidos."""
        with self.assertRaises(Exception):
            self.plugin.calcular_atr(None)
