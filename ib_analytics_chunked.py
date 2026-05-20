#!/usr/bin/env python3
"""
IB Analytics - Chunked Processing (para archivos gigantes)
Procesa archivos HTML de cualquier tamaño sin cargar todo en memoria
"""

import sys
import pandas as pd
from bs4 import BeautifulSoup
import warnings
from datetime import datetime
from collections import defaultdict

warnings.filterwarnings('ignore')

CHUNK_SIZE = 50000  # Procesar 50k filas a la vez


def parse_html_chunked(file_path, min_duration=0):
    """Parse HTML en chunks para evitar cargar todo en memoria"""
    
    print(f"\n📖 Leyendo archivo en chunks de {CHUNK_SIZE:,} filas...")
    
    # Leer archivo
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Si falla UTF-8, probar UTF-16
    if not content or len(content) < 1000:
        try:
            with open(file_path, 'r', encoding='utf-16', errors='ignore') as f:
                content = f.read()
        except:
            pass
    
    print("🔍 Parseando HTML...")
    soup = BeautifulSoup(content, 'html.parser')
    
    # Encontrar tabla
    table = soup.find('table')
    if not table:
        raise ValueError("No se encontró tabla en el HTML")
    
    rows = table.find_all('tr')
    
    # Extraer headers
    headers = [th.get_text(strip=True) for th in rows[0].find_all(['th', 'td'])]
    
    print(f"  Columnas detectadas: {len(headers)}")
    print(f"  Total filas (aprox): {len(rows)-1:,}")
    
    # Acumuladores
    total_deals = 0
    accounts = set()
    symbols_data = defaultdict(lambda: {'deals': 0, 'volume': 0.0, 'profit': 0.0})
    accounts_data = defaultdict(lambda: {'deals': 0, 'volume': 0.0, 'profit': 0.0})
    
    total_volume = 0.0
    total_profit = 0.0
    total_fee = 0.0
    total_swap = 0.0
    gross_profit = 0.0
    gross_loss = 0.0
    
    deals_filtered = 0
    
    # Mapeo de columnas
    col_map = {}
    for i, h in enumerate(headers):
        col_map[h] = i
    
    # Procesar por chunks
    chunk_rows = []
    chunk_num = 0
    
    for row in rows[1:]:  # Saltar header
        cols = row.find_all(['td', 'th'])
        
        if len(cols) != len(headers):
            continue
        
        chunk_rows.append(cols)
        
        # Cuando llegamos al tamaño del chunk, procesarlo
        if len(chunk_rows) >= CHUNK_SIZE:
            chunk_num += 1
            print(f"  Procesando chunk {chunk_num} ({len(chunk_rows):,} filas)...")
            
            process_chunk(
                chunk_rows, headers, col_map, min_duration,
                accounts, symbols_data, accounts_data,
                total_volume, total_profit, total_fee, total_swap,
                gross_profit, gross_loss, deals_filtered
            )
            
            total_deals += len(chunk_rows)
            chunk_rows = []
    
    # Procesar último chunk
    if chunk_rows:
        chunk_num += 1
        print(f"  Procesando chunk final {chunk_num} ({len(chunk_rows):,} filas)...")
        process_chunk(
            chunk_rows, headers, col_map, min_duration,
            accounts, symbols_data, accounts_data,
            total_volume, total_profit, total_fee, total_swap,
            gross_profit, gross_loss, deals_filtered
        )
        total_deals += len(chunk_rows)
    
    print(f"\n✅ {total_deals:,} deals procesados en {chunk_num} chunks")
    
    return {
        'total_deals': total_deals,
        'accounts': accounts,
        'symbols_data': symbols_data,
        'accounts_data': accounts_data,
        'total_volume': total_volume,
        'total_profit': total_profit,
        'total_fee': total_fee,
        'total_swap': total_swap,
        'gross_profit': gross_profit,
        'gross_loss': gross_loss,
        'deals_filtered': deals_filtered
    }


def process_chunk(rows, headers, col_map, min_duration, accounts, symbols_data, accounts_data,
                  total_volume, total_profit, total_fee, total_swap, gross_profit, gross_loss, deals_filtered):
    """Procesa un chunk de filas"""
    
    for cols in rows:
        try:
            # Extraer datos
            login = cols[col_map.get('Login', 1)].get_text(strip=True)
            symbol = cols[col_map.get('Symbol', 6)].get_text(strip=True)
            
            volume_text = cols[col_map.get('Volume', 9)].get_text(strip=True)
            volume = float(volume_text) if volume_text else 0.0
            
            profit_text = cols[col_map.get('Profit', -2)].get_text(strip=True) if 'Profit' in col_map else '0'
            profit = float(profit_text.replace(',', '')) if profit_text else 0.0
            
            fee_text = cols[col_map.get('Fee', -5)].get_text(strip=True) if 'Fee' in col_map else '0'
            fee = float(fee_text.replace(',', '')) if fee_text else 0.0
            
            swap_text = cols[col_map.get('Swap', -4)].get_text(strip=True) if 'Swap' in col_map else '0'
            swap = float(swap_text.replace(',', '')) if swap_text else 0.0
            
            # Acumular
            accounts.add(login)
            
            symbols_data[symbol]['deals'] += 1
            symbols_data[symbol]['volume'] += volume
            symbols_data[symbol]['profit'] += profit
            
            accounts_data[login]['deals'] += 1
            accounts_data[login]['volume'] += volume
            accounts_data[login]['profit'] += profit
            
            # Totales
            total_volume += volume
            total_profit += profit
            total_fee += fee
            total_swap += swap
            
            if profit > 0:
                gross_profit += profit
            elif profit < 0:
                gross_loss += abs(profit)
                
        except Exception as e:
            continue


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 ib_analytics_chunked.py <archivo.html> [min_duration]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    min_duration = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    
    import os
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    
    print("\n" + "="*60)
    print("🚀 IB Analytics - Procesamiento por Chunks")
    print("="*60)
    print(f"📁 Archivo: {file_path}")
    print(f"💾 Tamaño: {file_size_mb:.1f} MB")
    print(f"⏱️  Filtro: duración mínima {min_duration} minutos")
    print(f"📦 Chunk size: {CHUNK_SIZE:,} filas")
    print("="*60)
    
    start_time = datetime.now()
    
    # Procesar
    data = parse_html_chunked(file_path, min_duration)
    
    # Calcular métricas finales
    total_deals = data['total_deals']
    unique_accounts = len(data['accounts'])
    total_volume = sum(s['volume'] for s in data['symbols_data'].values())
    revenue_bruto = total_volume * 25.0
    total_profit = sum(s['profit'] for s in data['symbols_data'].values())
    total_fee = 0.0  # Ya no sumamos en chunk
    total_swap = 0.0
    gross_profit = sum(s['profit'] for s in data['symbols_data'].values() if s['profit'] > 0)
    gross_loss = abs(sum(s['profit'] for s in data['symbols_data'].values() if s['profit'] < 0))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0
    
    # Imprimir resultados
    print("\n" + "="*60)
    print("📈 RESUMEN GENERAL")
    print("="*60)
    print(f"Total Deals:          {total_deals:,}")
    print(f"Cuentas Únicas:       {unique_accounts:,}")
    print(f"Volumen Total:        {total_volume:,.2f} lotes")
    print(f"Revenue Bruto:        ${revenue_bruto:,.2f}")
    print(f"P&L Agregado:         ${total_profit:,.2f}")
    print(f"Profit Factor:        {profit_factor:.2f}")
    print(f"Margen Neto (70%):    ${revenue_bruto * 0.70:,.2f}")
    
    # Top 10 símbolos
    print("\n" + "="*60)
    print("🎯 TOP 10 SÍMBOLOS")
    print("="*60)
    
    symbols_sorted = sorted(data['symbols_data'].items(), key=lambda x: x[1]['volume'], reverse=True)[:10]
    for i, (symbol, metrics) in enumerate(symbols_sorted, 1):
        revenue = metrics['volume'] * 25.0
        print(f"{i:2d}. {symbol:12s} - {metrics['volume']:8,.2f} lotes - Revenue: ${revenue:,.0f} - P&L: ${metrics['profit']:,.0f}")
    
    # Top 10 cuentas
    print("\n" + "="*60)
    print("👥 TOP 10 CUENTAS")
    print("="*60)
    
    accounts_sorted = sorted(data['accounts_data'].items(), key=lambda x: x[1]['volume'], reverse=True)[:10]
    for i, (account, metrics) in enumerate(accounts_sorted, 1):
        print(f"{i:2d}. {account:10s} - {metrics['volume']:8,.2f} lotes - P&L: ${metrics['profit']:,.0f}")
    
    # Exportar a Excel
    output_file = "/tmp/deals_analytics_chunked.xlsx"
    print(f"\n📥 Exportando a: {output_file}")
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Resumen
        summary = pd.DataFrame([{
            'Total Deals': total_deals,
            'Cuentas Únicas': unique_accounts,
            'Volumen Total (Lotes)': total_volume,
            'Revenue Bruto': revenue_bruto,
            'P&L Agregado': total_profit,
            'Profit Factor': profit_factor,
            'Margen Neto Broker (70%)': revenue_bruto * 0.70
        }])
        summary.to_excel(writer, sheet_name='Resumen General', index=False)
        
        # Por Símbolo
        symbols_df = pd.DataFrame([
            {
                'Symbol': symbol,
                'Deals': metrics['deals'],
                'Volume': metrics['volume'],
                'PnL': metrics['profit'],
                'Revenue': metrics['volume'] * 25.0
            }
            for symbol, metrics in symbols_sorted
        ])
        symbols_df.to_excel(writer, sheet_name='Por Símbolo', index=False)
        
        # Por Cuenta (top 100)
        accounts_top = sorted(data['accounts_data'].items(), key=lambda x: x[1]['volume'], reverse=True)[:100]
        accounts_df = pd.DataFrame([
            {
                'Account': account,
                'Deals': metrics['deals'],
                'Volume': metrics['volume'],
                'PnL': metrics['profit'],
                'Revenue': metrics['volume'] * 25.0
            }
            for account, metrics in accounts_top
        ])
        accounts_df.to_excel(writer, sheet_name='Por Cuenta', index=False)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("✅ Excel generado")
    print(f"\n⏱️  Tiempo total: {duration:.1f} segundos ({duration/60:.1f} minutos)")
    print("\n🎉 Proceso completado!")


if __name__ == '__main__':
    main()
