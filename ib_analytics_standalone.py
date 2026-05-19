#!/usr/bin/env python3
"""
IB Analytics - Script Standalone
Procesa archivos HTML de MT5 Administrator localmente
No requiere estructura de proyecto, solo pandas y beautifulsoup4

Instalación:
  pip3 install pandas beautifulsoup4 openpyxl

Uso:
  python3 ib_analytics_standalone.py archivo.html
  python3 ib_analytics_standalone.py archivo.html 3  # Con filtro de 3 minutos
"""

import sys
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup

# Configuración
REVENUE_PER_LOT = 25.0  # $25 USD por lote

def parse_html(file_path: str) -> pd.DataFrame:
    """Parse MT5 HTML export"""
    print(f"📖 Leyendo archivo...")
    
    # Try different encodings
    html_content = None
    for encoding in ['utf-16', 'utf-8', 'latin-1']:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                html_content = f.read()
            break
        except:
            continue
    
    if html_content is None:
        raise ValueError("No se pudo leer el archivo")
    
    print(f"🔍 Parseando HTML...")
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table')
    
    if not tables:
        raise ValueError("No se encontraron tablas en el HTML")
    
    # Find the largest table (deals table)
    deals_table = max(tables, key=lambda t: len(t.find_all('tr')))
    
    # Extract headers
    header_row = deals_table.find('tr')
    headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
    
    # Extract data
    data_rows = deals_table.find_all('tr')[1:]
    deals = []
    
    for i, row in enumerate(data_rows):
        if i % 10000 == 0 and i > 0:
            print(f"  Procesando: {i:,} filas...")
        
        cells = row.find_all('td')
        if len(cells) >= 25:
            deal = [cell.get_text(strip=True) for cell in cells]
            deals.append(deal)
    
    print(f"✅ {len(deals):,} deals extraídos")
    
    # Create DataFrame
    df = pd.DataFrame(deals, columns=headers[:25])
    
    # Convert numeric columns
    numeric_columns = ['Deal', 'Login', 'Order', 'Volume', 'Price', 'S/L', 'T/P', 
                      'Price_2', 'Commission', 'Swap', 'Profit', 'Fee', 'Magic', 
                      'Expert_ID', 'Position_ID', 'Digits']
    
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].str.replace(' ', ''), errors='coerce')
    
    # Parse Time
    if 'Time' in df.columns:
        df['Time'] = pd.to_datetime(df['Time'], errors='coerce')
    
    # Calculate trade duration
    if 'Position_ID' in df.columns and 'Time' in df.columns:
        position_times = df.groupby('Position_ID')['Time'].agg(['min', 'max']).reset_index()
        position_times['duration_minutes'] = (position_times['max'] - position_times['min']).dt.total_seconds() / 60
        df = df.merge(position_times[['Position_ID', 'duration_minutes']], on='Position_ID', how='left')
    
    return df

def calculate_metrics(df: pd.DataFrame, min_duration: float = 0):
    """Calculate all metrics"""
    print(f"\n🔢 Calculando métricas...")
    
    deals_before = len(df)
    
    # Filter by duration
    deals_filtered = 0
    if min_duration > 0 and 'duration_minutes' in df.columns:
        df = df[df['duration_minutes'] >= min_duration]
        deals_filtered = deals_before - len(df)
        if deals_filtered > 0:
            print(f"⚠️  {deals_filtered:,} deals excluidos por duración < {min_duration} min")
    
    if len(df) == 0:
        return None, None, None
    
    # Basic stats
    total_deals = len(df)
    unique_accounts = df['Login'].nunique()
    total_volume = float(df['Volume'].sum())
    revenue_bruto = total_volume * REVENUE_PER_LOT
    pnl_agregado = float(df['Profit'].sum())
    total_commission = float(df['Commission'].sum())
    total_swap = float(df['Swap'].sum())
    
    # Profit Factor
    df_wins = df[df['Profit'] > 0]
    df_loss = df[df['Profit'] < 0]
    gross_profit = float(df_wins['Profit'].sum()) if len(df_wins) > 0 else 0
    gross_loss = abs(float(df_loss['Profit'].sum())) if len(df_loss) > 0 else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    # Blow-up Rate
    account_pnl = df.groupby('Login')['Profit'].sum()
    blowup_accounts = (account_pnl < -1000).sum()
    blowup_rate = (blowup_accounts / unique_accounts * 100) if unique_accounts > 0 else 0
    
    # Margen Neto (70% para broker)
    margen_neto_broker = revenue_bruto * 0.70
    
    metrics = {
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
        'deals_filtered': deals_filtered,
    }
    
    # By Symbol
    by_symbol = df.groupby('Symbol').agg({
        'Deal': 'count',
        'Volume': 'sum',
        'Profit': 'sum',
        'Commission': 'sum',
        'Swap': 'sum'
    }).reset_index()
    by_symbol.columns = ['symbol', 'total_deals', 'total_volume', 'pnl', 'commission', 'swap']
    by_symbol['revenue'] = by_symbol['total_volume'] * REVENUE_PER_LOT
    by_symbol = by_symbol.sort_values('total_volume', ascending=False)
    
    # By Account
    by_account = df.groupby('Login').agg({
        'Deal': 'count',
        'Volume': 'sum',
        'Profit': 'sum',
        'Commission': 'sum',
        'Swap': 'sum'
    }).reset_index()
    by_account.columns = ['account', 'total_deals', 'total_volume', 'pnl', 'commission', 'swap']
    by_account['revenue'] = by_account['total_volume'] * REVENUE_PER_LOT
    by_account = by_account.sort_values('total_volume', ascending=False)
    
    return metrics, by_symbol, by_account

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 ib_analytics_standalone.py <archivo_html> [min_duration_minutos]")
        print("\nEjemplo:")
        print("  python3 ib_analytics_standalone.py deals.html")
        print("  python3 ib_analytics_standalone.py deals.html 3")
        sys.exit(1)
    
    html_file = sys.argv[1]
    min_duration = float(sys.argv[2]) if len(sys.argv) > 2 else 0
    
    if not Path(html_file).exists():
        print(f"❌ Error: Archivo no encontrado: {html_file}")
        sys.exit(1)
    
    print(f"🚀 IB Analytics - Procesamiento Local")
    print(f"{'='*60}")
    print(f"📁 Archivo: {html_file}")
    print(f"💾 Tamaño: {Path(html_file).stat().st_size / (1024*1024):.1f} MB")
    if min_duration > 0:
        print(f"⏱️  Filtro: duración mínima {min_duration} minutos")
    print(f"{'='*60}\n")
    
    # Parse HTML
    try:
        df = parse_html(html_file)
    except Exception as e:
        print(f"❌ Error al parsear HTML: {e}")
        sys.exit(1)
    
    # Calculate metrics
    try:
        metrics, by_symbol, by_account = calculate_metrics(df, min_duration)
        if metrics is None:
            print("❌ No hay datos después de aplicar filtros")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error al calcular métricas: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Print summary
    print("\n" + "="*60)
    print("📈 RESUMEN GENERAL")
    print("="*60)
    print(f"Total Deals:          {metrics['total_deals']:,}")
    print(f"Cuentas Únicas:       {metrics['unique_accounts']:,}")
    print(f"Volumen Total:        {metrics['total_volume_lots']:,.2f} lotes")
    print(f"Revenue Bruto:        ${metrics['revenue_bruto']:,.2f}")
    print(f"P&L Agregado:         ${metrics['pnl_agregado']:,.2f}")
    print(f"Profit Factor:        {metrics['profit_factor']:.2f}")
    print(f"Blow-up Rate:         {metrics['blowup_rate']:.2f}%")
    print(f"Margen Neto Broker:   ${metrics['margen_neto_broker']:,.2f}")
    
    print("\n" + "="*60)
    print("🎯 TOP 10 SÍMBOLOS")
    print("="*60)
    for i, row in enumerate(by_symbol.head(10).itertuples(), 1):
        print(f"{i:2d}. {row.symbol:12s} - {row.total_volume:8,.2f} lotes - Revenue: ${row.revenue:,.0f}")
    
    print("\n" + "="*60)
    print("👥 TOP 10 CUENTAS")
    print("="*60)
    for i, row in enumerate(by_account.head(10).itertuples(), 1):
        print(f"{i:2d}. {int(row.account):10d} - {row.total_volume:8,.2f} lotes - P&L: ${row.pnl:,.0f}")
    
    # Export to Excel
    output_file = Path(html_file).stem + "_analytics.xlsx"
    print(f"\n📥 Exportando resultados a: {output_file}")
    
    try:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Summary
            pd.DataFrame([metrics]).to_excel(writer, sheet_name='Resumen General', index=False)
            # By Symbol
            by_symbol.to_excel(writer, sheet_name='Por Símbolo', index=False)
            # By Account
            by_account.to_excel(writer, sheet_name='Por Cuenta', index=False)
        
        print(f"✅ Excel generado exitosamente")
        print(f"📍 Ubicación: {Path(output_file).absolute()}")
        
    except Exception as e:
        print(f"❌ Error al generar Excel: {e}")
        sys.exit(1)
    
    print(f"\n🎉 Proceso completado!")

if __name__ == "__main__":
    main()
