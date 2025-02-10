import unittest
from plugins.gerenciadores.gerenciador_plugins import (
    obter_calculo_alavancagem,
    obter_banco_dados,
)
from configparser import ConfigParser
from unittest.mock import patch, Mock


class TestGerentePlugin(unittest.TestCase):
    """
    Testes unitários para o gerente de plugins.
    """

    def test_obter_calculo_alavancagem(self):
        """
        Testa a obtenção do cálculo de alavancagem.
        """
        calculo = obter_calculo_alavancagem()
        self.assertIsNotNone(calculo)

    def test_obter_banco_dados(self):
        """
        Testa a obtenção do banco de dados.
        """
        config = ConfigParser()
        config.add_section("database")
        config.set("database", "host", "localhost")
        config.set("database", "database", "bybit_watcher_db")
        config.set("database", "user", "postgres")
        config.set("database", "password", "123456")

        with patch("plugins.banco_dados.psycopg2.connect") as mock_connect:
            mock_connect.return_value = Mock()
            banco = obter_banco_dados(config)
            self.assertIsNotNone(banco)

    def test_calculo_alavancagem(self):
        # Teste adicional para verificar o cálculo de alavancagem
        calculo = obter_calculo_alavancagem()
        self.assertTrue(callable(calculo.calcular_alavancagem))


if __name__ == "__main__":
    unittest.main()
