from unittest import TestCase
from unittest.mock import patch, Mock
import numpy as np
from plugins.indicadores.indicadores_volume import IndicadoresVolume


class TestIndicadoresVolume(TestCase):
    def setUp(self):
        """Configura o ambiente para cada teste."""
        self.plugin = IndicadoresVolume()
        self.plugin.banco_dados = Mock()

        # Dados de teste em formato numpy array (OHLCV)
        self.dados_teste = np.array(
            [
                [100.0, 105.0, 95.0, 102.0, 1000],
                [102.0, 107.0, 97.0, 104.0, 1500],
                [104.0, 109.0, 99.0, 106.0, 2000],
            ]
        )

    @patch("talib.OBV")
    def test_calcular_obv(self, mock_obv):
        """Testa o cálculo do On Balance Volume."""
        mock_obv.return_value = np.array([1000.0, 2500.0, 4500.0])

        resultado = self.plugin.calcular_obv(self.dados_teste)

        mock_obv.assert_called_once()
        self.assertIsInstance(resultado, np.ndarray)

    @patch("talib.AD")
    def test_calcular_ad(self, mock_ad):
        """Testa o cálculo do Accumulation/Distribution."""
        mock_ad.return_value = np.array([500.0, 1200.0, 2000.0])

        resultado = self.plugin.calcular_ad(self.dados_teste)

        mock_ad.assert_called_once()
        self.assertIsInstance(resultado, np.ndarray)

    def test_gerar_sinal_deve_retornar_dict(self):
        """Testa se gerar_sinal retorna um dicionário com os campos corretos."""
        mock_config = Mock()

        sinal = self.plugin.gerar_sinal(
            self.dados_teste, "obv", "alta", "BTCUSDT", "1h", mock_config
        )

        self.assertIsInstance(sinal, dict)
        self.assertIn("sinal", sinal)

    def test_dados_invalidos(self):
        """Testa o comportamento com dados inválidos."""
        with self.assertRaises(Exception):
            self.plugin.calcular_obv(None)
