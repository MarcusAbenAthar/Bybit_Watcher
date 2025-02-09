import unittest
from unittest.mock import Mock, patch
import numpy as np
from plugins.plugin import Plugin
from plugins.price_action import PriceAction  # Ensure proper import


class TestPriceAction(unittest.TestCase):
    """
    Testes unitários para o plugin PriceAction.
    """

    def setUp(self):
        """Configuração inicial para cada teste."""
        self.plugin = PriceAction()
        self.plugin.gerente = Mock()
        self.plugin.gerente._singleton_plugins = {"conexao": Mock()}

        # Dados de teste em formato de dicionário
        self.candle_teste = {
            "open": 100.0,
            "high": 105.0,
            "low": 95.0,
            "close": 102.0,
            "volume": 1000.0,
        }

        # Adiciona dados de teste para padrão martelo
        self.candle_martelo = {
            "open": 100.0,
            "high": 105.0,
            "low": 90.0,
            "close": 104.0,
            "volume": 1000.0,
        }

    def test_plugin_initialization(self):
        """Testa se o plugin foi inicializado corretamente."""
        self.assertIsInstance(self.plugin, Plugin)  # Verifica se é subclasse de Plugin
        self.assertTrue(
            type(self.plugin).__name__ == "PriceAction"
        )  # Verifica o nome da classe

    def test_analisar_padrao(self):
        """Testa a análise de padrões."""
        resultado = self.plugin.analisar_padrao(self.candle_teste)
        self.assertIsInstance(resultado, dict)

    def test_calcular_forca(self):
        """Testa o cálculo de força."""
        forca = self.plugin.calcular_forca(self.candle_teste)
        self.assertIsInstance(forca, float)

    def test_gerar_sinal_raises_not_implemented(self):
        """Testa se gerar_sinal lança NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.plugin.gerar_sinal(self.candle_teste, "doji")

    def test_analisar_tendencia(self):
        """Testa a análise de tendência."""
        tendencia = self.plugin.analisar_tendencia(self.candle_teste)
        self.assertIn(tendencia, ["ALTA", "BAIXA", "LATERAL"])

    def test_calcular_forca_padrao(self):
        """
        Testa o cálculo de força do padrão.
        """
        padrao = "martelo"
        forca = self.plugin.calcular_forca_padrao(self.candle_martelo)
        self.assertIsInstance(forca, float)

    def test_identificar_padrao_deve_lancar_not_implemented(self):
        """Testa se identificar_padrao lança NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.plugin.identificar_padrao(self.candle_teste)

    def test_dados_invalidos(self):
        """Testa o comportamento com dados inválidos."""
        with self.assertRaises(NotImplementedError):
            self.plugin.identificar_padrao(None)

    def test_gerar_sinal_deve_lancar_not_implemented(self):
        """Testa se gerar_sinal lança NotImplementedError."""
        padrao = "doji"
        with self.assertRaises(NotImplementedError):
            self.plugin.gerar_sinal(self.candle_teste, padrao)

    def test_singleton(self):
        """Testa se o padrão singleton está funcionando."""
        plugin1 = PriceAction()
        plugin2 = PriceAction()
        self.assertIs(plugin1, plugin2, "As instâncias devem ser as mesmas (singleton)")

    def test_nome_plugin(self):
        """Testa se o nome do plugin está correto."""
        self.assertEqual(self.plugin.nome, "Price Action")
        self.assertTrue(hasattr(self.plugin, "descricao"))

    def test_inicializacao(self):
        """Testa a inicialização do plugin."""
        config = Mock()
        self.plugin.inicializar(config)
        self.assertIsNotNone(self.plugin._config)
        self.assertIsInstance(self.plugin.cache_padroes, dict)


if __name__ == "__main__":
    unittest.main()
