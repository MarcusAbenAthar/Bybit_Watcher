from unittest import TestCase
import unittest
from unittest.mock import patch, Mock
import numpy as np
from plugins.analise_candles import AnaliseCandles


class TestAnaliseCandles(TestCase):
    """
    Testes unitários para o plugin AnaliseCandles.
    """

    def setUp(self):
        """Configura o ambiente para cada teste."""
        self.plugin = AnaliseCandles()
        # Mock do banco de dados
        self.plugin.banco_dados = Mock()
        # Mock GerentePlugin
        self.plugin.gerente = Mock()
        self.plugin.gerente._singleton_plugins = {"conexao": Mock()}

        # Dados de teste em formato numpy array (OHLC)
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

    @patch("talib.CDL2CROWS")
    def test_identificar_padrao_deve_chamar_talib(self, mock_cdl):
        """Testa se identificar_padrao chama corretamente o TALib."""
        # Setup
        mock_cdl.return_value = np.array([0, 0, 100])
        dados_np = np.array(self.dados_teste)

        # Execute
        self.plugin.identificar_padrao(self.dados_teste)

        # Verify - Comparando arrays usando numpy.array_equal
        call_args = mock_cdl.call_args[0]  # Pega argumentos posicionais
        self.assertTrue(np.array_equal(call_args[0], dados_np[:, 1]))  # open
        self.assertTrue(np.array_equal(call_args[1], dados_np[:, 2]))  # high
        self.assertTrue(np.array_equal(call_args[2], dados_np[:, 3]))  # low
        self.assertTrue(np.array_equal(call_args[3], dados_np[:, 4]))  # close
        self.assertEqual(mock_cdl.call_count, 1)  # Verifica se foi chamado uma vez

    def test_calcular_confianca(self):
        """Testa o cálculo de confiança."""
        confianca = self.plugin.calcular_confianca(self.dados_teste)
        self.assertIsInstance(confianca, float)
        self.assertGreaterEqual(confianca, 0.0)
        self.assertLessEqual(confianca, 1.0)

    def test_calcular_forca_padrao(self):
        """Testa o cálculo de força do padrão."""
        forca = self.plugin.calcular_forca_padrao(self.dados_teste)
        self.assertIsInstance(forca, float)
        self.assertGreaterEqual(forca, 0.0)
        self.assertLessEqual(forca, 1.0)

    def test_gerar_sinal_deve_retornar_dict(self):
        """Testa se gerar_sinal retorna um dicionário com os campos corretos."""
        # Mock da configuração
        mock_config = Mock()

        sinal = self.plugin.gerar_sinal(self.dados_teste, "BTCUSDT", "1h")
        self.assertIsInstance(sinal, dict)
        campos_esperados = [
            "sinal",
            "padrao",
            "stop_loss",
            "take_profit",
            "forca",
            "confianca",
        ]
        for campo in campos_esperados:
            self.assertIn(campo, sinal)

    def test_identificar_padrao_com_dados_invalidos(self):
        """Testa se identificar_padrao trata corretamente dados inválidos."""
        resultado = self.plugin.identificar_padrao(None)
        self.assertIsNone(resultado)

    def test_singleton(self):
        """Testa se o padrão singleton está funcionando."""
        plugin1 = AnaliseCandles()
        plugin2 = AnaliseCandles()
        self.assertIs(plugin1, plugin2, "As instâncias devem ser as mesmas (singleton)")

    def test_nome_plugin(self):
        """Testa se o nome do plugin está correto."""
        self.assertEqual(self.plugin.nome, "Análise de Candles")
        self.assertTrue(hasattr(self.plugin, "descricao"))


if __name__ == "__main__":
    unittest.main()
