import unittest
from unittest.mock import Mock, patch
import numpy as np
from plugins.medias_moveis import MediasMoveis


class TestMediasMoveis(unittest.TestCase):

    def setUp(self):
        """Configuração inicial para cada teste."""
        self.plugin = MediasMoveis()
        self.plugin.gerente = Mock()
        self.plugin.gerente._singleton_plugins = {"conexao": Mock()}

        # Dados de teste
        self.dados_teste = np.array(
            [
                [
                    0,
                    100.0,
                    105.0,
                    95.0,
                    102.0,
                    1000.0,
                ],  # timestamp, open, high, low, close, volume
                [0, 102.0, 107.0, 97.0, 104.0, 1100.0],
                [0, 104.0, 109.0, 99.0, 106.0, 1200.0],
            ],
            dtype=np.float64,
        )

    def test_singleton(self):
        """Testa se o padrão singleton está funcionando."""
        plugin1 = MediasMoveis()
        plugin2 = MediasMoveis()
        self.assertIs(plugin1, plugin2, "As instâncias devem ser as mesmas (singleton)")

    def test_nome_plugin(self):
        """Testa se o nome do plugin está correto."""
        self.assertEqual(self.plugin.nome, "Médias Móveis")
        self.assertTrue(hasattr(self.plugin, "descricao"))

    def test_inicializacao(self):
        """Testa a inicialização do plugin."""
        config = Mock()
        self.plugin.inicializar(config)
        self.assertIsNotNone(self.plugin._config)
        self.assertIsInstance(self.plugin.cache_medias, dict)

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


if __name__ == "__main__":
    unittest.main()
