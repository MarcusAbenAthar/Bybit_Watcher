import unittest
from unittest.mock import Mock, patch
import numpy as np
from plugins.indicadores.indicadores_tendencia import IndicadoresTendencia
from configparser import ConfigParser


class TestIndicadoresTendencia(unittest.TestCase):
    def setUp(self):
        """Configura o ambiente de teste."""
        self.config = ConfigParser()
        self.config.add_section("database")
        self.config.set("database", "host", "localhost")
        self.config.set("database", "database", "bybit_watcher_db")
        self.config.set("database", "user", "postgres")
        self.config.set("database", "password", "123456")
        self.config.set("database", "port", "5432")

        self.config.add_section("timeframes")
        self.config.set("timeframes", "timeframe1", "1m")
        self.config.set("timeframes", "timeframe2", "5m")
        self.config.set("timeframes", "timeframe3", "15m")
        self.config.set("timeframes", "timeframe4", "30m")
        self.config.set("timeframes", "timeframe5", "1h")
        self.config.set("timeframes", "timeframe6", "4h")
        self.config.set("timeframes", "timeframe7", "1d")

        self.tendencia = IndicadoresTendencia(self.config)
        self.mock_banco = Mock()
        self.mock_calculo = Mock()
        self.tendencia.banco_dados = self.mock_banco
        self.tendencia.calculo_alavancagem = self.mock_calculo

        self.dados_teste = np.array(
            [
                [1000000000, 100.0, 105.0, 95.0, 102.0, 1000],
                [2000000000, 102.0, 107.0, 97.0, 104.0, 1000],
                [3000000000, 104.0, 109.0, 99.0, 106.0, 1000],
            ]
        )

    @patch("talib.MACD")
    def test_calcular_macd(self, mock_macd):
        """Testa o cálculo do MACD."""
        mock_macd.return_value = (
            np.array([1.0, 1.5, 2.0]),  # macd
            np.array([0.5, 1.0, 1.5]),  # signal
            np.array([0.5, 0.5, 0.5]),  # hist
        )
        macd, signal, hist = self.tendencia.calcular_macd(self.dados_teste)
        self.assertIsInstance(macd, np.ndarray)
        self.assertIsInstance(signal, np.ndarray)
        self.assertIsInstance(hist, np.ndarray)
        mock_macd.assert_called_once()

    @patch("talib.ADX")
    def test_calcular_adx(self, mock_adx):
        """Testa o cálculo do ADX."""
        mock_adx.return_value = np.array([20.0, 25.0, 30.0])
        adx = self.tendencia.calcular_adx(self.dados_teste)
        self.assertIsInstance(adx, np.ndarray)
        mock_adx.assert_called_once()

    def test_gerar_sinal(self):
        """Testa a geração de sinais."""
        sinal = self.tendencia.gerar_sinal(
            self.dados_teste, "macd", "cruzamento_alta", "BTCUSDT", "1h", self.config
        )
        self.assertIsInstance(sinal, dict)
        self.assertIn("sinal", sinal)
        self.assertIn("stop_loss", sinal)
        self.assertIn("take_profit", sinal)

    def test_executar(self):
        """Testa a execução completa do indicador."""
        self.tendencia.executar(self.dados_teste, "BTCUSDT", "1h")
        self.mock_banco.conn.cursor.assert_called()

    def test_dados_invalidos(self):
        """Testa o comportamento com dados inválidos."""
        with self.assertRaises(Exception):
            self.tendencia.calcular_macd(None)
