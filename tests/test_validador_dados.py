import unittest
from unittest.mock import Mock, patch
import numpy as np
from plugins.plugin import Plugin
from plugins.validador_dados import ValidadorDados


class TestValidadorDados(unittest.TestCase):

    def setUp(self):
        """Configuração inicial para cada teste."""
        self.plugin = ValidadorDados()
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
        plugin1 = ValidadorDados()
        plugin2 = ValidadorDados()
        self.assertIs(plugin1, plugin2, "As instâncias devem ser as mesmas (singleton)")

    def test_nome_plugin(self):
        """Testa se o nome do plugin está correto."""
        self.assertEqual(self.plugin.nome, "Validador de Dados")
        self.assertTrue(hasattr(self.plugin, "descricao"))

    def test_plugin_initialization(self):
        """Testa se o plugin foi inicializado corretamente."""
        self.assertIsInstance(self.plugin, Plugin)
        self.assertTrue(type(self.plugin).__name__ == "ValidadorDados")

    def test_inicializacao(self):
        """Testa a inicialização do plugin."""
        config = Mock()
        self.plugin.inicializar(config)
        self.assertIsNotNone(self.plugin._config)
        self.assertIsInstance(self.plugin.cache_validacoes, dict)

    def test_validar_dados_invalidos(self):
        """Testa a validação com dados inválidos."""
        casos_teste = [
            None,
            [],
            np.array([], dtype=np.float64),
            np.array([[]], dtype=np.float64),
            np.array([[1, 2]], dtype=np.float64),  # Dados incompletos
        ]

        for dados in casos_teste:
            with self.assertRaises(ValueError):
                self.plugin.validar_dados(dados)

    def test_validar_dados_corrompidos(self):
        """Testa a validação com dados corrompidos."""
        dados_corrompidos = np.array(
            [
                [0, np.nan, 105.0, 95.0, 102.0, 1000.0],
                [0, 102.0, np.inf, 97.0, 104.0, 1100.0],
                [0, 104.0, 109.0, -np.inf, 106.0, 1200.0],
            ],
            dtype=np.float64,
        )

        with self.assertRaises(ValueError):
            self.plugin.validar_dados(dados_corrompidos)


if __name__ == "__main__":
    unittest.main()
