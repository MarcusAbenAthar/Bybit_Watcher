import unittest
from unittest.mock import Mock, patch
from plugins.gerenciador_bot import GerenciadorBot


class TestGerenciadorBot(unittest.TestCase):

    def setUp(self):
        """Configuração inicial para cada teste."""
        self.plugin = GerenciadorBot()

    def test_singleton(self):
        """Testa se o padrão singleton está funcionando."""
        plugin1 = GerenciadorBot()
        plugin2 = GerenciadorBot()
        self.assertIs(plugin1, plugin2, "As instâncias devem ser as mesmas (singleton)")

    def test_nome_plugin(self):
        """Testa se o nome do plugin está correto."""
        self.assertEqual(self.plugin.nome, "Gerenciador do Bot")
        self.assertTrue(hasattr(self.plugin, "descricao"))

    def test_inicializacao(self):
        """Testa a inicialização do plugin."""
        config = Mock()
        self.plugin.inicializar(config)
        self.assertIsNotNone(self.plugin._config)
        self.assertEqual(self.plugin._status, "parado")
        self.assertIsInstance(self.plugin._plugins_ativos, dict)


if __name__ == "__main__":
    unittest.main()
