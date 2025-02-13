from unittest import TestCase
import unittest
from unittest.mock import patch, Mock
from plugins.plugin import Plugin
from plugins.sinais_plugin import SinaisPlugin


class TestSinaisPlugin(TestCase):
    """
    Testes unitários para o plugin SinaisPlugin.
    """

    def setUp(self):
        """Configura o ambiente para cada teste."""
        self.plugin = SinaisPlugin()
        self.plugin.gerente = Mock()
        self.plugin.gerente._singleton_plugins = {"conexao": Mock()}
        self.sinal_teste = {
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "direcao": "COMPRA",
            "stop_loss": 100.0,
            "take_profit": 110.0,
        }

    def test_logar_sinal_deve_retornar_dict(self):
        """Testa se logar_sinal retorna um dicionário quando recebe dados válidos."""
        with patch("plugins.sinais_plugin.logger"):
            # Configura o mock do banco de dados
            mock_db = Mock()
            self.plugin.gerente._singleton_plugins["banco_dados"] = mock_db

            resultado = self.plugin.logar_sinal(
                self.sinal_teste["symbol"],
                self.sinal_teste["timeframe"],
                self.sinal_teste,
            )

            # Verifica o resultado
            self.assertIsInstance(resultado, dict)
            self.assertEqual(resultado["symbol"], "BTCUSDT")
            self.assertEqual(resultado["timeframe"], "1h")
            self.assertEqual(resultado["direcao"], "COMPRA")

    def test_logar_sinal_deve_lancar_erro_com_dados_invalidos(self):
        """Testa se logar_sinal lança erro quando recebe dados inválidos."""
        with patch("plugins.sinais_plugin.logger"):
            with self.assertRaises(Exception):
                self.plugin.logar_sinal(None, None, None)

    def test_singleton(self):
        """Testa se o padrão singleton está funcionando."""
        plugin1 = SinaisPlugin()
        plugin2 = SinaisPlugin()
        self.assertIs(plugin1, plugin2, "As instâncias devem ser as mesmas (singleton)")

    def test_nome_plugin(self):
        """Testa se o nome do plugin está correto."""
        self.assertEqual(self.plugin.nome, "Sinais")
        self.assertTrue(hasattr(self.plugin, "descricao"))

    def test_plugin_initialization(self):
        """Testa se o plugin foi inicializado corretamente."""
        self.assertIsInstance(self.plugin, Plugin)
        self.assertTrue(type(self.plugin).__name__ == "SinaisPlugin")

    def test_inicializacao(self):
        """Testa a inicialização do plugin."""
        config = Mock()
        self.plugin.inicializar(config)
        self.assertIsNotNone(self.plugin._config)
        self.assertIsInstance(self.plugin.cache_sinais, dict)


if __name__ == "__main__":
    unittest.main()
