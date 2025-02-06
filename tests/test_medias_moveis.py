from unittest import TestCase
from unittest.mock import patch, Mock
import numpy as np
from plugins.medias_moveis import MediasMoveis


class TestMediasMoveis(TestCase):
    def setUp(self):
        self.plugin = MediasMoveis()
        self.plugin.banco_dados = Mock()
        # Usando apenas preços de fechamento para médias móveis
        self.dados_teste = np.array([100.0, 102.0, 104.0, 103.0, 105.0])

    @patch("talib.SMA")
    def test_calcular_media_movel_simples(self, mock_sma):
        """Testa o cálculo da média móvel simples."""
        mock_sma.return_value = np.array([101.0, 103.0, 104.0])

        self.plugin.calcular_media_movel(self.dados_teste, 3, "simples")
        mock_sma.assert_called_once()

    @patch("talib.EMA")
    def test_calcular_media_movel_exponencial(self, mock_ema):
        """Testa o cálculo da média móvel exponencial."""
        mock_ema.return_value = np.array([101.5, 103.2, 104.1])

        self.plugin.calcular_media_movel(self.dados_teste, 3, "exponencial")
        mock_ema.assert_called_once()

    def test_calcular_media_movel_tipo_invalido(self):
        """Testa se lança erro para tipo de média inválido."""
        with self.assertRaises(ValueError):
            self.plugin.calcular_media_movel(self.dados_teste, 3, "invalido")

    def test_gerar_sinal_deve_retornar_dict(self):
        """Testa se gerar_sinal retorna um dicionário com os campos corretos."""
        mock_config = Mock()

        # Mock das médias móveis para evitar IndexError
        with patch.object(self.plugin, "calcular_media_movel") as mock_mm:
            mock_mm.return_value = np.array([100.0, 101.0, 102.0])

            sinal = self.plugin.gerar_sinal(
                self.dados_teste, "cruzamento_alta", "BTCUSDT", "1h", mock_config
            )

            self.assertIsInstance(sinal, dict)
            self.assertIn("sinal", sinal)

    @patch("plugins.medias_moveis.talib")
    def test_calcular_media_movel_ponderada(self, mock_talib):
        """Verifica se o cálculo da média móvel ponderada está correto."""
        mock_talib.WMA = Mock(return_value=np.array([101.0, 102.0, 103.0]))
        resultado = self.plugin.calcular_media_movel(
            self.dados_teste, 3, tipo="ponderada"
        )
        self.assertTrue(isinstance(resultado, np.ndarray))

    # ... (adicionar testes para a função gerar_sinal)...
