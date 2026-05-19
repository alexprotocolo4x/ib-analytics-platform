"""
Calculadora de métricas de trading
Basado en el mockup del dashboard
"""
import pandas as pd
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Calcula métricas de trading desde deals"""
    
    # Configuración por defecto (pueden ser override)
    DEFAULT_REVENUE_PER_LOT = 25.00  # USD por lote
    DEFAULT_IB_PAYOUT_PER_LOT = 17.00  # USD por lote al IB
    
    def __init__(
        self,
        revenue_per_lot: float = DEFAULT_REVENUE_PER_LOT,
        ib_payout_per_lot: float = DEFAULT_IB_PAYOUT_PER_LOT
    ):
        self.revenue_per_lot = revenue_per_lot
        self.ib_payout_per_lot = ib_payout_per_lot
    
    def calculate_kpis(self, df: pd.DataFrame, accounts: List[str]) -> Dict[str, Any]:
        """
        Calcula KPIs principales
        
        Args:
            df: DataFrame con todos los deals
            accounts: Lista de cuentas a filtrar
            
        Returns:
            Dict con KPIs calculados
        """
        # Filtrar solo cuentas del grupo
        df_filtered = df[df['login'].isin(accounts)].copy()
        
        if len(df_filtered) == 0:
            logger.warning("No se encontraron deals para las cuentas especificadas")
            return self._empty_kpis()
        
        # 1. Lotes Totales (solo trades cerrados)
        df_closed = df_filtered[df_filtered['entry'] == 'out']
        total_lots = float(df_closed['volume'].sum())
        
        # 2. Revenue Bruto
        revenue_bruto = total_lots * self.revenue_per_lot
        
        # 3. Pago al IB
        pago_ib = total_lots * self.ib_payout_per_lot
        
        # 4. Margen Neto Broker
        margen_neto = revenue_bruto - pago_ib
        
        # 5. P&L Agregado Clientes
        pnl_total = float(df_closed['profit'].sum())
        
        # 6. Profit Factor (gross_profit / |gross_loss|)
        gross_profit = float(df_closed[df_closed['profit'] > 0]['profit'].sum())
        gross_loss = abs(float(df_closed[df_closed['profit'] < 0]['profit'].sum()))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # 7. Win Rate
        winning_trades = len(df_closed[df_closed['profit'] > 0])
        total_trades = len(df_closed)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # 8. Cuentas Activas (con al menos 1 trade)
        cuentas_activas = df_filtered['login'].nunique()
        cuentas_totales = len(accounts)
        
        # 9. Total Deals
        total_deals = len(df_closed)
        
        # 10. Swap y Commission
        total_swap = float(df_closed['swap'].sum())
        total_commission = float(df_closed['commission'].sum())
        
        # 11. Average profit per trade
        avg_profit_per_trade = pnl_total / total_trades if total_trades > 0 else 0
        
        return {
            'total_lots': round(total_lots, 2),
            'revenue_bruto': round(revenue_bruto, 2),
            'pago_ib': round(pago_ib, 2),
            'margen_neto': round(margen_neto, 2),
            'pnl_total': round(pnl_total, 2),
            'profit_factor': round(profit_factor, 2),
            'win_rate': round(win_rate, 2),
            'cuentas_activas': cuentas_activas,
            'cuentas_totales': cuentas_totales,
            'total_deals': total_deals,
            'total_swap': round(total_swap, 2),
            'total_commission': round(total_commission, 2),
            'gross_profit': round(gross_profit, 2),
            'gross_loss': round(gross_loss, 2),
            'avg_profit_per_trade': round(avg_profit_per_trade, 2)
        }
    
    def calculate_by_account(self, df: pd.DataFrame, accounts: List[str]) -> List[Dict[str, Any]]:
        """
        Calcula métricas por cuenta individual
        
        Returns:
            Lista de dicts con métricas por cuenta
        """
        df_filtered = df[df['login'].isin(accounts)].copy()
        df_closed = df_filtered[df_filtered['entry'] == 'out']
        
        if len(df_closed) == 0:
            return []
        
        results = []
        
        for account in accounts:
            df_account = df_closed[df_closed['login'] == account]
            
            if len(df_account) == 0:
                # Cuenta sin trades
                results.append({
                    'login': account,
                    'total_lots': 0,
                    'total_deals': 0,
                    'pnl': 0,
                    'revenue': 0,
                    'profit_factor': 0,
                    'win_rate': 0,
                    'status': 'inactive'
                })
                continue
            
            total_lots = float(df_account['volume'].sum())
            pnl = float(df_account['profit'].sum())
            revenue = total_lots * self.revenue_per_lot
            
            # Profit factor
            gross_profit = float(df_account[df_account['profit'] > 0]['profit'].sum())
            gross_loss = abs(float(df_account[df_account['profit'] < 0]['profit'].sum()))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
            
            # Win rate
            winning_trades = len(df_account[df_account['profit'] > 0])
            total_trades = len(df_account)
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Swap y commission
            swap = float(df_account['swap'].sum())
            commission = float(df_account['commission'].sum())
            
            results.append({
                'login': account,
                'total_lots': round(total_lots, 2),
                'total_deals': total_trades,
                'pnl': round(pnl, 2),
                'revenue': round(revenue, 2),
                'profit_factor': round(profit_factor, 2),
                'win_rate': round(win_rate, 2),
                'swap': round(swap, 2),
                'commission': round(commission, 2),
                'status': 'active'
            })
        
        # Ordenar por revenue descendente
        results = sorted(results, key=lambda x: x['revenue'], reverse=True)
        
        return results
    
    def calculate_by_symbol(self, df: pd.DataFrame, accounts: List[str]) -> List[Dict[str, Any]]:
        """
        Calcula métricas por símbolo
        """
        df_filtered = df[df['login'].isin(accounts)].copy()
        df_closed = df_filtered[df_filtered['entry'] == 'out']
        
        if len(df_closed) == 0:
            return []
        
        # Agrupar por símbolo
        grouped = df_closed.groupby('symbol').agg({
            'volume': 'sum',
            'profit': 'sum',
            'deal_id': 'count'
        }).reset_index()
        
        grouped.columns = ['symbol', 'total_lots', 'pnl', 'total_deals']
        
        # Calcular revenue
        grouped['revenue'] = grouped['total_lots'] * self.revenue_per_lot
        
        # Ordenar por volumen
        grouped = grouped.sort_values('total_lots', ascending=False)
        
        return grouped.to_dict('records')
    
    def _empty_kpis(self) -> Dict[str, Any]:
        """KPIs vacíos cuando no hay datos"""
        return {
            'total_lots': 0,
            'revenue_bruto': 0,
            'pago_ib': 0,
            'margen_neto': 0,
            'pnl_total': 0,
            'profit_factor': 0,
            'win_rate': 0,
            'cuentas_activas': 0,
            'cuentas_totales': 0,
            'total_deals': 0,
            'total_swap': 0,
            'total_commission': 0,
            'gross_profit': 0,
            'gross_loss': 0,
            'avg_profit_per_trade': 0
        }
