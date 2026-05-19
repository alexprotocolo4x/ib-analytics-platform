"""
IB Metrics Calculation Service
Calculate broker revenue, profit factor, blow-up rate, etc.
"""
import pandas as pd
from typing import Dict, List, Set

# Broker revenue per lot
REVENUE_PER_LOT = 25.0  # $25 USD per lot

def calculate_metrics(df: pd.DataFrame, account_filter: Set[int] = None, min_duration_minutes: float = 0) -> Dict:
    """
    Calculate comprehensive metrics for IB analysis
    
    Args:
        df: DataFrame with MT5 deals
        account_filter: Optional set of account numbers to filter
        min_duration_minutes: Minimum trade duration in minutes (0 = no filter)
        
    Returns:
        Dict with all calculated metrics
    """
    # Store original count
    total_deals_before = len(df)
    
    # Filter by accounts if provided
    if account_filter:
        df = df[df['Login'].isin(account_filter)]
    
    # Filter by minimum duration if provided
    deals_filtered_by_duration = 0
    if min_duration_minutes > 0 and 'duration_minutes' in df.columns:
        deals_before_duration = len(df)
        df = df[df['duration_minutes'] >= min_duration_minutes]
        deals_filtered_by_duration = deals_before_duration - len(df)
    
    if len(df) == 0:
        return {
            'total_deals': 0,
            'unique_accounts': 0,
            'total_volume_lots': 0,
            'revenue_bruto': 0,
            'pnl_agregado': 0,
            'total_commission': 0,
            'total_swap': 0,
            'profit_factor': 0,
            'blowup_rate': 0,
            'margen_neto_broker': 0,
        }
    
    # Basic stats
    total_deals = len(df)
    unique_accounts = df['Login'].nunique()
    total_volume = float(df['Volume'].sum())
    
    # Revenue = $25 per lot
    revenue_bruto = total_volume * REVENUE_PER_LOT
    
    # P&L agregado (total client profit/loss)
    pnl_agregado = float(df['Profit'].sum())
    
    # Commissions and Swaps
    total_commission = float(df['Commission'].sum())
    total_swap = float(df['Swap'].sum())
    
    # Profit Factor = Gross Profit / Gross Loss
    df_wins = df[df['Profit'] > 0]
    df_loss = df[df['Profit'] < 0]
    
    gross_profit = float(df_wins['Profit'].sum()) if len(df_wins) > 0 else 0
    gross_loss = abs(float(df_loss['Profit'].sum())) if len(df_loss) > 0 else 0
    
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    # Blow-up Rate (simplified - accounts with large losses)
    # In production, this would check final equity = 0
    account_pnl = df.groupby('Login')['Profit'].sum()
    blowup_accounts = (account_pnl < -1000).sum()  # Lost > $1000
    blowup_rate = (blowup_accounts / unique_accounts * 100) if unique_accounts > 0 else 0
    
    # Margen Neto Broker (revenue - potential IB payout)
    # Assuming IB gets 30% commission, broker keeps 70%
    margen_neto_broker = revenue_bruto * 0.70
    
    return {
        'total_deals': total_deals,
        'unique_accounts': unique_accounts,
        'total_volume_lots': round(total_volume, 2),
        'revenue_bruto': round(revenue_bruto, 2),
        'pnl_agregado': round(pnl_agregado, 2),
        'total_commission': round(total_commission, 2),
        'total_swap': round(total_swap, 2),
        'profit_factor': round(profit_factor, 2),
        'gross_profit': round(gross_profit, 2),
        'gross_loss': round(gross_loss, 2),
        'blowup_rate': round(blowup_rate, 2),
        'margen_neto_broker': round(margen_neto_broker, 2),
        'deals_filtered_by_duration': deals_filtered_by_duration,
        'min_duration_applied': min_duration_minutes,
    }


def calculate_by_symbol(df: pd.DataFrame, account_filter: Set[int] = None, min_duration_minutes: float = 0) -> List[Dict]:
    """
    Calculate metrics grouped by trading symbol
    """
    if account_filter:
        df = df[df['Login'].isin(account_filter)]
    
    # Filter by minimum duration if provided
    if min_duration_minutes > 0 and 'duration_minutes' in df.columns:
        df = df[df['duration_minutes'] >= min_duration_minutes]
    
    if len(df) == 0:
        return []
    
    grouped = df.groupby('Symbol').agg({
        'Deal': 'count',
        'Volume': 'sum',
        'Profit': 'sum',
        'Commission': 'sum',
        'Swap': 'sum'
    }).reset_index()
    
    grouped.columns = ['symbol', 'total_deals', 'total_volume', 'pnl', 'commission', 'swap']
    grouped['revenue'] = grouped['total_volume'] * REVENUE_PER_LOT
    
    # Sort by volume descending
    grouped = grouped.sort_values('total_volume', ascending=False)
    
    return grouped.to_dict('records')


def calculate_by_account(df: pd.DataFrame, account_filter: Set[int] = None, min_duration_minutes: float = 0) -> List[Dict]:
    """
    Calculate metrics grouped by account (Login)
    """
    if account_filter:
        df = df[df['Login'].isin(account_filter)]
    
    # Filter by minimum duration if provided
    if min_duration_minutes > 0 and 'duration_minutes' in df.columns:
        df = df[df['duration_minutes'] >= min_duration_minutes]
    
    if len(df) == 0:
        return []
    
    grouped = df.groupby('Login').agg({
        'Deal': 'count',
        'Volume': 'sum',
        'Profit': 'sum',
        'Commission': 'sum',
        'Swap': 'sum'
    }).reset_index()
    
    grouped.columns = ['account', 'total_deals', 'total_volume', 'pnl', 'commission', 'swap']
    grouped['revenue'] = grouped['total_volume'] * REVENUE_PER_LOT
    
    # Sort by volume descending
    grouped = grouped.sort_values('total_volume', ascending=False)
    
    return grouped.to_dict('records')
