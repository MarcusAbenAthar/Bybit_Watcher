from unittest import TestCase
from unittest.mock import patch, Mock
import numpy as np
from plugins.indicadores.indicadores_osciladores import IndicadoresOsciladores


class TestIndicadoresOsciladores(TestCase):
    def setUp(self):
        """Configura o ambiente para cada teste."""
        self.plugin = IndicadoresOsciladores()
        # Mock do banco de dados
        self.plugin.banco_dados = Mock()

        # Dados de teste em formato numpy array (OHLCV)
        self.dados_teste = np.array(
            [
                [100.0, 105.0, 95.0, 102.0, 1000],
                [102.0, 107.0, 97.0, 104.0, 1500],
                [104.0, 109.0, 99.0, 106.0, 2000],
            ]
        )

    @patch("talib.RSI")
    def test_calcular_rsi(self, mock_rsi):
        """Testa o cálculo do RSI."""
        mock_rsi.return_value = np.array([45.0, 55.0, 65.0])

        resultado = self.plugin.calcular_rsi(self.dados_teste)

        mock_rsi.assert_called_once()
        self.assertIsInstance(resultado, np.ndarray)

    @patch("talib.STOCH")
    def test_calcular_estocastico(self, mock_stoch):
        """Testa o cálculo do Estocástico."""
        mock_stoch.return_value = (
            np.array([20.0, 30.0, 40.0]),  # slowk
            np.array([25.0, 35.0, 45.0]),  # slowd
        )

        k, d = self.plugin.calcular_estocastico(self.dados_teste)

        mock_stoch.assert_called_once()
        self.assertIsInstance(k, np.ndarray)
        self.assertIsInstance(d, np.ndarray)

    def test_gerar_sinal_deve_retornar_dict(self):
        """Testa se gerar_sinal retorna um dicionário com os campos corretos."""
        mock_config = Mock()

        sinal = self.plugin.gerar_sinal(
            self.dados_teste, "rsi", "sobrevenda", "BTCUSDT", "1h", mock_config
        )

        self.assertIsInstance(sinal, dict)
        self.assertIn("sinal", sinal)

    def test_dados_invalidos(self):
        """Testa o comportamento com dados inválidos."""
        with self.assertRaises(Exception):
            self.plugin.calcular_rsi(None)
