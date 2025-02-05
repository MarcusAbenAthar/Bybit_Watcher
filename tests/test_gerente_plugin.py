import unittest
from plugins.gerente_plugin import obter_calculo_alavancagem, obter_banco_dados


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
        banco = obter_banco_dados()
        self.assertIsNotNone(banco)

    def test_calculo_alavancagem(self):
        # Teste adicional para verificar o cálculo de alavancagem
        calculo = obter_calculo_alavancagem()
        self.assertTrue(callable(calculo.calcular_alavancagem))


if __name__ == "__main__":
    unittest.main()
