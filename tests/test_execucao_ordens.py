import unittest
from unittest.mock import Mock, patch
from plugins.execucao_ordens import ExecucaoOrdens


class TestExecucaoOrdens(unittest.TestCase):

    def setUp(self):
        """Configuração inicial para cada teste."""
        self.plugin = ExecucaoOrdens()
        self.plugin.gerente = Mock()
        self.plugin.gerente._singleton_plugins = {"conexao": Mock()}

    def test_singleton(self):
        """Testa se o padrão singleton está funcionando."""
        plugin1 = ExecucaoOrdens()
        plugin2 = ExecucaoOrdens()
        self.assertIs(plugin1, plugin2, "As instâncias devem ser as mesmas (singleton)")

    def test_nome_plugin(self):
        """Testa se o nome do plugin está correto."""
        self.assertEqual(self.plugin.nome, "Execução de Ordens")
        self.assertTrue(hasattr(self.plugin, "descricao"))

    def test_inicializacao(self):
        """Testa a inicialização do plugin."""
        config = Mock()
        self.plugin.inicializar(config)
        self.assertIsNotNone(self.plugin._config)
        self.assertIsInstance(self.plugin._ordens_pendentes, dict)


if __name__ == "__main__":
    unittest.main()
