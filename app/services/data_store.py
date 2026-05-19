"""
In-memory data store
Almacena deals y accounts para análisis
"""
import pandas as pd
from typing import Optional, List


class DataStore:
    """Singleton para almacenar datos temporalmente"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._deals_df = None
            cls._instance._accounts = None
        return cls._instance
    
    def set_deals(self, df: pd.DataFrame):
        """Guardar deals"""
        self._deals_df = df
    
    def get_deals(self) -> Optional[pd.DataFrame]:
        """Obtener deals"""
        return self._deals_df
    
    def set_accounts(self, accounts: List[str]):
        """Guardar lista de cuentas"""
        self._accounts = accounts
    
    def get_accounts(self) -> Optional[List[str]]:
        """Obtener lista de cuentas"""
        return self._accounts
    
    def clear(self):
        """Limpiar todos los datos"""
        self._deals_df = None
        self._accounts = None
    
    def is_ready(self) -> bool:
        """Verificar si hay datos listos para análisis"""
        return self._deals_df is not None and self._accounts is not None
