"""
Plugin centralizado para Machine Learning.
Responsável por treinar, validar e fazer previsões usando modelos ML.
"""

from typing import Dict, List, Optional, Tuple, Union, Any
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import os
from datetime import datetime

from utils.logging_config import get_logger, log_rastreamento
from plugins.plugin import Plugin
from utils.config import carregar_config

logger = get_logger(__name__)


class MachineLearning(Plugin):
    """
    Plugin centralizado para Machine Learning.
    - Responsabilidade única: gerenciar modelos ML
    - Modular, testável, documentado e sem hardcode
    - Autoidentificação de dependências/plugins
    """

    PLUGIN_NAME = "machine_learning"
    PLUGIN_CATEGORIA = "plugin"
    PLUGIN_TAGS = ["ml", "machine_learning", "modelos"]
    PLUGIN_PRIORIDADE = 100

    def __init__(self, **kwargs):
        """Inicializa o plugin de Machine Learning."""
        super().__init__(**kwargs)
        config = carregar_config()
        self._config = (
            config.get("plugins", {}).get("machine_learning", {}).copy()
            if "plugins" in config and "machine_learning" in config["plugins"]
            else {}
        )

        # Configurações padrão
        self._modelo_dir = self._config.get("modelo_dir", "modelos")
        self._scaler_dir = self._config.get("scaler_dir", "scalers")
        self._test_size = self._config.get("test_size", 0.2)
        self._random_state = self._config.get("random_state", 42)

        # Inicializa componentes
        self._scaler = StandardScaler()
        self._modelo = RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=self._random_state
        )

        # Cria diretórios se não existirem
        os.makedirs(self._modelo_dir, exist_ok=True)
        os.makedirs(self._scaler_dir, exist_ok=True)

    @property
    def plugin_schema_versao(self) -> str:
        return "1.0"

    @property
    def plugin_tabelas(self) -> dict:
        return {
            "modelos_ml": {
                "schema": {
                    "id": "SERIAL PRIMARY KEY",
                    "timestamp": "TIMESTAMP NOT NULL",
                    "symbol": "VARCHAR(20) NOT NULL",
                    "timeframe": "VARCHAR(10) NOT NULL",
                    "modelo": "VARCHAR(50) NOT NULL",
                    "versao": "VARCHAR(10) NOT NULL",
                    "acuracia": "DECIMAL(5,2)",
                    "precisao": "DECIMAL(5,2)",
                    "recall": "DECIMAL(5,2)",
                    "f1_score": "DECIMAL(5,2)",
                    "features": "JSONB",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                },
                "modo_acesso": "own",
                "plugin": self.PLUGIN_NAME,
            }
        }

    def inicializar(self, config: dict) -> bool:
        """
        Inicializa o plugin com a configuração fornecida.

        Args:
            config: Dicionário com configurações

        Returns:
            bool: True se inicializado com sucesso
        """
        try:
            if not super().inicializar(config):
                logger.error(f"[{self.nome}] Falha na inicialização base")
                return False

            ml_config = config.get("machine_learning", {})
            self._modelo_dir = ml_config.get("modelo_dir", self._modelo_dir)
            self._scaler_dir = ml_config.get("scaler_dir", self._scaler_dir)
            self._test_size = ml_config.get("test_size", self._test_size)
            self._random_state = ml_config.get("random_state", self._random_state)

            logger.info(f"[{self.nome}] inicializado com sucesso")
            return True

        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao inicializar: {e}")
            return False

    def _preparar_dados(
        self, dados: Dict[str, Any], features: List[str], target: str
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepara os dados para treinamento.

        Args:
            dados: Dicionário com os dados
            features: Lista de features a serem usadas
            target: Nome da coluna alvo

        Returns:
            Tuple[np.ndarray, np.ndarray]: X (features) e y (target)
        """
        try:
            df = pd.DataFrame(dados)
            X = df[features].values
            y = df[target].values

            log_rastreamento(
                f"[{self.nome}] Dados preparados: {len(X)} amostras, "
                f"{len(features)} features"
            )

            return X, y

        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao preparar dados: {e}")
            raise

    def treinar_modelo(
        self,
        dados: Dict[str, Any],
        features: List[str],
        target: str,
        symbol: str,
        timeframe: str,
    ) -> Dict[str, float]:
        """
        Treina um novo modelo com os dados fornecidos.

        Args:
            dados: Dicionário com os dados
            features: Lista de features
            target: Nome da coluna alvo
            symbol: Símbolo do par
            timeframe: Timeframe

        Returns:
            Dict[str, float]: Métricas do modelo
        """
        try:
            # Prepara dados
            X, y = self._preparar_dados(dados, features, target)

            # Split treino/teste
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=self._test_size, random_state=self._random_state
            )

            # Normaliza dados
            X_train_scaled = self._scaler.fit_transform(X_train)
            X_test_scaled = self._scaler.transform(X_test)

            # Treina modelo
            self._modelo.fit(X_train_scaled, y_train)

            # Avalia modelo
            y_pred = self._modelo.predict(X_test_scaled)
            metricas = {
                "acuracia": accuracy_score(y_test, y_pred),
                "precisao": precision_score(y_test, y_pred, average="weighted"),
                "recall": recall_score(y_test, y_pred, average="weighted"),
                "f1_score": f1_score(y_test, y_pred, average="weighted"),
            }

            # Salva modelo e scaler
            self._salvar_modelo(symbol, timeframe)

            log_rastreamento(
                f"[{self.nome}] Modelo treinado para {symbol}-{timeframe}: "
                f"acuracia={metricas['acuracia']:.2f}"
            )

            return metricas

        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao treinar modelo: {e}")
            raise

    def _salvar_modelo(self, symbol: str, timeframe: str) -> None:
        """
        Salva o modelo e scaler treinados.

        Args:
            symbol: Símbolo do par
            timeframe: Timeframe
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Salva modelo
            modelo_path = os.path.join(
                self._modelo_dir, f"modelo_{symbol}_{timeframe}_{timestamp}.joblib"
            )
            joblib.dump(self._modelo, modelo_path)

            # Salva scaler
            scaler_path = os.path.join(
                self._scaler_dir, f"scaler_{symbol}_{timeframe}_{timestamp}.joblib"
            )
            joblib.dump(self._scaler, scaler_path)

            log_rastreamento(
                componente=f"{self.nome}/modelo",
                acao="salvamento",
                detalhes=f"Modelo e scaler salvos: {modelo_path}",
            )

        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao salvar modelo: {e}")
            raise

    def carregar_modelo(self, symbol: str, timeframe: str) -> bool:
        """
        Carrega o modelo e scaler mais recentes.

        Args:
            symbol: Símbolo do par
            timeframe: Timeframe

        Returns:
            bool: True se carregado com sucesso
        """
        try:
            # Encontra arquivos mais recentes
            modelo_files = [
                f
                for f in os.listdir(self._modelo_dir)
                if f.startswith(f"modelo_{symbol}_{timeframe}")
            ]
            scaler_files = [
                f
                for f in os.listdir(self._scaler_dir)
                if f.startswith(f"scaler_{symbol}_{timeframe}")
            ]

            if not modelo_files or not scaler_files:
                logger.error(
                    f"[{self.nome}] Modelo não encontrado para {symbol}-{timeframe}"
                )
                return False

            # Carrega arquivos mais recentes
            modelo_path = os.path.join(self._modelo_dir, sorted(modelo_files)[-1])
            scaler_path = os.path.join(self._scaler_dir, sorted(scaler_files)[-1])

            self._modelo = joblib.load(modelo_path)
            self._scaler = joblib.load(scaler_path)

            log_rastreamento(
                componente=f"{self.nome}/modelo",
                acao="carregamento",
                detalhes=f"Modelo e scaler carregados: {modelo_path}",
            )

            return True

        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao carregar modelo: {e}")
            return False

    def prever(
        self, dados: Dict[str, Any], features: List[str], symbol: str, timeframe: str
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Faz previsões usando o modelo treinado.

        Args:
            dados: Dicionário com os dados
            features: Lista de features
            symbol: Símbolo do par
            timeframe: Timeframe

        Returns:
            Tuple[np.ndarray, np.ndarray]: Previsões e probabilidades
        """
        try:
            # Carrega modelo se necessário
            if not hasattr(self._modelo, "predict"):
                if not self.carregar_modelo(symbol, timeframe):
                    raise ValueError("Modelo não encontrado")

            # Prepara dados
            X, _ = self._preparar_dados(dados, features, None)

            # Normaliza dados
            X_scaled = self._scaler.transform(X)

            # Faz previsões
            previsoes = self._modelo.predict(X_scaled)
            probabilidades = self._modelo.predict_proba(X_scaled)

            log_rastreamento(
                f"[{self.nome}] Previsões geradas para {symbol}-{timeframe}: "
                f"{len(previsoes)} amostras"
            )

            return previsoes, probabilidades

        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao fazer previsões: {e}")
            raise

    def executar(self, *args, **kwargs) -> dict:
        """
        Executa o plugin de Machine Learning.
        Aceita argumentos nomeados (symbol, timeframe, dados_completos, etc) para compatibilidade total.
        Sempre retorna um dicionário de resultado.
        """
        try:
            # Compatibilidade: aceita tanto dados_completos como kwargs
            dados_completos = kwargs.get("dados_completos")
            if dados_completos is None and args:
                dados_completos = args[0]
            if not isinstance(dados_completos, dict):
                logger.error(
                    f"[{self.nome}] dados_completos não é um dicionário: {type(dados_completos)}"
                )
                return {}
            if not self._validar_dados_entrada(dados_completos):
                return dados_completos

            symbol = dados_completos.get("symbol")
            timeframe = dados_completos.get("timeframe")

            # Extrai features dos dados
            features = self._extrair_features(dados_completos)

            # Faz previsões
            previsoes, probabilidades = self.prever(
                dados_completos, features, symbol, timeframe
            )

            # Atualiza dados_completos
            dados_completos[self.PLUGIN_NAME] = {
                "previsoes": previsoes,
                "probabilidades": probabilidades,
                "features": features,
            }

            return dados_completos

        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao executar: {e}")
            return {}

    def _validar_dados_entrada(self, dados_completos: dict) -> bool:
        """
        Valida os dados de entrada.

        Args:
            dados_completos: Dicionário com os dados

        Returns:
            bool: True se válido
        """
        try:
            campos_obrigatorios = ["symbol", "timeframe"]
            for campo in campos_obrigatorios:
                if campo not in dados_completos:
                    logger.error(f"[{self.nome}] Campo obrigatório ausente: {campo}")
                    return False
            return True

        except Exception as e:
            logger.error(f"[{self.nome}] Erro na validação: {e}")
            return False

    def _extrair_features(self, dados_completos: dict) -> List[str]:
        """
        Extrai features dos dados para ML.

        Args:
            dados_completos: Dicionário com os dados

        Returns:
            List[str]: Lista de features
        """
        features = []

        # Features de indicadores
        if "osciladores" in dados_completos:
            features.extend(
                [
                    "rsi",
                    "mfi",
                    "stoch_k",
                    "stoch_d",
                    "cci",
                    "williams_r",
                    "stoch_rsi",
                    "roc",
                ]
            )

        if "tendencia" in dados_completos:
            features.extend(
                ["macd", "macd_signal", "macd_hist", "adx", "plus_di", "minus_di"]
            )

        if "volatilidade" in dados_completos:
            features.extend(
                [
                    "atr",
                    "bb_upper",
                    "bb_middle",
                    "bb_lower",
                    "kc_upper",
                    "kc_middle",
                    "kc_lower",
                ]
            )

        if "volume" in dados_completos:
            features.extend(["obv", "mfi", "cmf", "vwap"])

        return features

    def finalizar(self) -> bool:
        """
        Finaliza o plugin.

        Returns:
            bool: True se finalizado com sucesso
        """
        try:
            if not super().finalizar():
                return False

            # Limpa recursos
            self._modelo = None
            self._scaler = None

            logger.info(f"[{self.nome}] finalizado com sucesso")
            return True

        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao finalizar: {e}")
            return False
