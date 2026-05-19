#!/usr/bin/env python3
"""
Test del backend con datos reales
"""
import sys
sys.path.append('.')

from app.parsers.mt5_parser import MT5HTMLParser
from app.services.calculator import MetricsCalculator
import pandas as pd

def test_parser():
    """Test del parser con HTML real"""
    print("="*80)
    print("TEST 1: Parser MT5 HTML")
    print("="*80)
    
    html_path = "/Users/vierneslopez/.openclaw/media/inbound/MetaTrader 5 Administrator Deals.html"
    
    with open(html_path, 'r', encoding='utf-16') as f:
        html_content = f.read()
    
    parser = MT5HTMLParser()
    df = parser.parse_html(html_content)
    
    print(f"✅ Parseados {len(df)} deals")
    print(f"✅ Columnas: {list(df.columns)}")
    
    summary = parser.get_summary(df)
    print(f"\n📊 RESUMEN:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    return df

def test_calculator(df):
    """Test del calculator con cuentas de ejemplo"""
    print("\n" + "="*80)
    print("TEST 2: Calculator con cuentas de ejemplo")
    print("="*80)
    
    # Tomar las primeras 10 cuentas como ejemplo
    sample_accounts = df['login'].unique()[:10].tolist()
    
    print(f"Cuentas de ejemplo: {sample_accounts}")
    
    calculator = MetricsCalculator()
    
    # KPIs
    kpis = calculator.calculate_kpis(df, sample_accounts)
    
    print(f"\n📊 KPIs:")
    for key, value in kpis.items():
        print(f"  {key}: {value}")
    
    # Por cuenta
    by_account = calculator.calculate_by_account(df, sample_accounts)
    
    print(f"\n💰 Top 5 cuentas:")
    for acc in by_account[:5]:
        print(f"  {acc['login']}: {acc['total_lots']} lotes, P&L: ${acc['pnl']}")
    
    # Por símbolo
    by_symbol = calculator.calculate_by_symbol(df, sample_accounts)
    
    print(f"\n🎯 Top 5 símbolos:")
    for sym in by_symbol[:5]:
        print(f"  {sym['symbol']}: {sym['total_lots']} lotes, P&L: ${sym['pnl']}")

if __name__ == "__main__":
    try:
        df = test_parser()
        test_calculator(df)
        
        print("\n" + "="*80)
        print("✅ TODOS LOS TESTS PASARON")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
