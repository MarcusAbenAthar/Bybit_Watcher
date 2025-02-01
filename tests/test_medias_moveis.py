import unittest
from unittest.mock import MagicMock, patch
import numpy as np

from plugins.medias_moveis import MediasMoveis
from plugins.gerente_plugin import obter_calculo_alavancagem


class TestMediasMoveis(unittest.TestCase):
    """
    Classe de teste para o plugin MediasMoveis, que verifica o cálculo das médias móveis e a geração de sinais.
    """

    @patch("plugins.medias_moveis.talib")  # Substitui o talib por um mock
    def test_calcular_media_movel_simples(self, mock_talib):
        """
        Verifica se o cálculo da média móvel simples está correto.
        """
        # Cria um mock para o objeto CalculoAlavancagem
        mock_calculo_alavancagem = MagicMock()
        # Cria uma instância do plugin MediasMoveis, passando o mock como argumento
        plugin = MediasMoveis(mock_calculo_alavancagem)
        # Cria um mock para a função SMA do talib
        mock_talib.SMA = MagicMock(return_value=np.array())

        # Chama a função calcular_media_movel com tipo "simples"
        resultado = plugin.calcular_media_movel([], 3, tipo="simples")

        # Verifica se a função SMA do talib foi chamada com os argumentos corretos
        mock_talib.SMA.assert_called_once_with([], timeperiod=3)

        # Verifica se o resultado é o esperado
        self.assertTrue(np.array_equal(resultado, np.array()))

    @patch("plugins.medias_moveis.talib")  # Substitui o talib por um mock
    def test_calcular_media_movel_exponencial(self, mock_talib):
        """
        Verifica se o cálculo da média móvel exponencial está correto.
        """
        # Cria um mock para o objeto CalculoAlavancagem
        mock_calculo_alavancagem = MagicMock()
        # Cria uma instância do plugin MediasMoveis, passando o mock como argumento
        plugin = MediasMoveis(mock_calculo_alavancagem)
        # Cria um mock para a função EMA do talib
        mock_talib.EMA = MagicMock(return_value=np.array())

        # Chama a função calcular_media_movel com tipo "exponencial"
        resultado = plugin.calcular_media_movel([], 3, tipo="exponencial")

        # Verifica se a função EMA do talib foi chamada com os argumentos corretos
        mock_talib.EMA.assert_called_once_with([], timeperiod=3)

        # Verifica se o resultado é o esperado
        self.assertTrue(np.array_equal(resultado, np.array()))

    @patch("plugins.medias_moveis.talib")  # Substitui o talib por um mock
    def test_calcular_media_movel_ponderada(self, mock_talib):
        """
        Verifica se o cálculo da média móvel ponderada está correto.
        """
        # Cria um mock para o objeto CalculoAlavancagem
        mock_calculo_alavancagem = MagicMock()
        # Cria uma instância do plugin MediasMoveis, passando o mock como argumento
        plugin = MediasMoveis(mock_calculo_alavancagem)
        # Cria um mock para a função WMA do talib
        mock_talib.WMA = MagicMock(return_value=np.array())

        # Chama a função calcular_media_movel com tipo "ponderada"
        resultado = plugin.calcular_media_movel([], 3, tipo="ponderada")

        # Verifica se a função WMA do talib foi chamada com os argumentos corretos
        mock_talib.WMA.assert_called_once_with([], timeperiod=3)

        # Verifica se o resultado é o esperado
        self.assertTrue(np.array_equal(resultado, np.array()))

    # ... (adicionar testes para a função gerar_sinal)...
