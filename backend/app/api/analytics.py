"""
Analytics endpoints - Cálculo de métricas
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
import logging

from app.services.data_store import DataStore
from app.services.calculator import MetricsCalculator

router = APIRouter()
logger = logging.getLogger(__name__)

data_store = DataStore()
calculator = MetricsCalculator()


@router.get("/kpis")
async def get_kpis():
    """
    Obtener KPIs principales calculados
    
    Returns:
        KPIs del grupo de cuentas cargado
    """
    if not data_store.is_ready():
        raise HTTPException(
            400,
            "Faltan datos. Sube primero el HTML de MT5 y el Excel de cuentas"
        )
    
    df = data_store.get_deals()
    accounts = data_store.get_accounts()
    
    kpis = calculator.calculate_kpis(df, accounts)
    
    return {
        "success": True,
        "kpis": kpis
    }


@router.get("/accounts")
async def get_accounts_metrics():
    """
    Obtener métricas por cuenta individual
    
    Returns:
        Lista de cuentas con sus métricas
    """
    if not data_store.is_ready():
        raise HTTPException(
            400,
            "Faltan datos. Sube primero el HTML de MT5 y el Excel de cuentas"
        )
    
    df = data_store.get_deals()
    accounts = data_store.get_accounts()
    
    accounts_metrics = calculator.calculate_by_account(df, accounts)
    
    return {
        "success": True,
        "accounts": accounts_metrics,
        "total": len(accounts_metrics)
    }


@router.get("/symbols")
async def get_symbols_metrics():
    """
    Obtener métricas por símbolo
    
    Returns:
        Lista de símbolos con volumen y P&L
    """
    if not data_store.is_ready():
        raise HTTPException(
            400,
            "Faltan datos. Sube primero el HTML de MT5 y el Excel de cuentas"
        )
    
    df = data_store.get_deals()
    accounts = data_store.get_accounts()
    
    symbols_metrics = calculator.calculate_by_symbol(df, accounts)
    
    return {
        "success": True,
        "symbols": symbols_metrics,
        "total": len(symbols_metrics)
    }


@router.get("/deals")
async def get_deals(
    limit: Optional[int] = 100,
    offset: Optional[int] = 0
):
    """
    Obtener deals individuales (paginado)
    
    Args:
        limit: Número máximo de deals a retornar
        offset: Offset para paginación
    
    Returns:
        Lista de deals filtrados
    """
    if not data_store.is_ready():
        raise HTTPException(
            400,
            "Faltan datos. Sube primero el HTML de MT5 y el Excel de cuentas"
        )
    
    df = data_store.get_deals()
    accounts = data_store.get_accounts()
    
    # Filtrar por cuentas
    df_filtered = df[df['login'].isin(accounts)]
    
    # Solo trades cerrados
    df_closed = df_filtered[df_filtered['entry'] == 'out']
    
    # Ordenar por fecha descendente
    df_closed = df_closed.sort_values('time', ascending=False)
    
    # Paginar
    df_page = df_closed.iloc[offset:offset + limit]
    
    # Convertir a dict
    deals = df_page.to_dict('records')
    
    return {
        "success": True,
        "deals": deals,
        "total": len(df_closed),
        "limit": limit,
        "offset": offset
    }


@router.get("/export/csv")
async def export_csv():
    """
    Exportar deals a CSV
    
    Returns:
        URL de descarga del CSV
    """
    if not data_store.is_ready():
        raise HTTPException(
            400,
            "Faltan datos. Sube primero el HTML de MT5 y el Excel de cuentas"
        )
    
    df = data_store.get_deals()
    accounts = data_store.get_accounts()
    
    # Filtrar
    df_filtered = df[df['login'].isin(accounts)]
    df_closed = df_filtered[df_filtered['entry'] == 'out']
    
    # Convertir a CSV
    csv_data = df_closed.to_csv(index=False)
    
    return {
        "success": True,
        "csv": csv_data,
        "total_rows": len(df_closed)
    }
