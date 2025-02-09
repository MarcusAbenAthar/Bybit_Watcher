import unittest
from unittest.mock import Mock, patch
import numpy as np
from plugins.calculo_risco import CalculoRisco


class TestCalculoRisco(unittest.TestCase):

    def setUp(self):
        """Configuração inicial para cada teste."""
        self.plugin = CalculoRisco()
        # Mock GerentePlugin
        self.plugin.gerente = Mock()
        self.plugin.gerente._singleton_plugins = {"conexao": Mock()}

    def test_singleton(self):
        """Testa se o padrão singleton está funcionando."""
        plugin1 = CalculoRisco()
        plugin2 = CalculoRisco()
        self.assertIs(plugin1, plugin2, "As instâncias devem ser as mesmas (singleton)")

    def test_nome_plugin(self):
        """Testa se o nome do plugin está correto."""
        self.assertEqual(self.plugin.nome, "Cálculo de Risco")
        self.assertTrue(hasattr(self.plugin, "descricao"))

    def test_inicializacao(self):
        """Testa a inicialização do plugin."""
        config = Mock()
        self.plugin.inicializar(config)
        self.assertIsNotNone(self.plugin._config)


if __name__ == "__main__":
    unittest.main()
