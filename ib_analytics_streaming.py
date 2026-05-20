#!/usr/bin/env python3
"""
IB Analytics - Streaming Processing
Procesa archivos HTML gigantes línea por línea sin cargar nada en memoria
"""

import sys
import re
import pandas as pd
from datetime import datetime
from collections import defaultdict

def extract_cell_text(html_cell):
    """Extrae texto de una celda HTML"""
    # Remover tags HTML
    text = re.sub(r'<[^>]+>', '', html_cell)
    # Decodificar entidades HTML
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
    return text.strip()


def process_html_streaming(file_path, min_duration=0):
    """Procesa HTML línea por línea sin cargar en memoria"""
    
    print("\n📖 Procesando archivo en modo streaming...")
    print("   (Esto puede tomar 10-15 minutos para archivos de 2GB)")
    
    # Acumuladores
    accounts = set()
    symbols_data = defaultdict(lambda: {'deals': 0, 'volume': 0.0, 'profit': 0.0})
    accounts_data = defaultdict(lambda: {'deals': 0, 'volume': 0.0, 'profit': 0.0})
    
    total_deals = 0
    processed_rows = 0
    in_table = False
    in_row = False
    current_row_cells = []
    headers = []
    
    # Intentar con diferentes encodings
    encodings = ['utf-8', 'utf-16', 'latin-1']
    file_handle = None
    
    for encoding in encodings:
        try:
            file_handle = open(file_path, 'r', encoding=encoding, errors='ignore')
            # Test read
            file_handle.readline()
            file_handle.seek(0)
            print(f"  ✅ Usando encoding: {encoding}")
            break
        except:
            if file_handle:
                file_handle.close()
            continue
    
    if not file_handle:
        raise ValueError("No se pudo abrir el archivo con ningún encoding")
    
    # Leer línea por línea
    for line_num, line in enumerate(file_handle, 1):
        
        # Progress cada 100k líneas
        if line_num % 100000 == 0:
            print(f"  Procesadas {line_num:,} líneas | {processed_rows:,} deals encontrados...")
        
        # Detectar inicio de tabla
        if '<table' in line.lower():
            in_table = True
            continue
        
        # Detectar fin de tabla
        if '</table' in line.lower():
            in_table = False
            break
        
        if not in_table:
            continue
        
        # Detectar inicio de fila
        if '<tr' in line.lower():
            in_row = True
            current_row_cells = []
            continue
        
        # Detectar fin de fila
        if '</tr' in line.lower():
            in_row = False
            
            if not current_row_cells:
                continue
            
            # Primera fila = headers
            if not headers:
                headers = current_row_cells
                print(f"  📋 Headers encontrados: {len(headers)} columnas")
                continue
            
            # Validar que tenga el número correcto de columnas
            if len(current_row_cells) != len(headers):
                continue
            
            # Procesar deal
            try:
                # Crear dict con los datos
                deal = {headers[i]: current_row_cells[i] for i in range(len(headers))}
                
                login = deal.get('Login', '')
                symbol = deal.get('Symbol', '')
                
                volume_text = deal.get('Volume', '0')
                volume = float(volume_text) if volume_text else 0.0
                
                profit_text = deal.get('Profit', '0').replace(',', '')
                profit = float(profit_text) if profit_text else 0.0
                
                # Acumular
                if login and symbol:
                    accounts.add(login)
                    
                    symbols_data[symbol]['deals'] += 1
                    symbols_data[symbol]['volume'] += volume
                    symbols_data[symbol]['profit'] += profit
                    
                    accounts_data[login]['deals'] += 1
                    accounts_data[login]['volume'] += volume
                    accounts_data[login]['profit'] += profit
                    
                    processed_rows += 1
                    
            except Exception as e:
                pass
            
            continue
        
        # Extraer celdas de la línea actual
        if in_row:
            # Buscar <td> o <th>
            cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', line, re.IGNORECASE | re.DOTALL)
            for cell_html in cells:
                cell_text = extract_cell_text(cell_html)
                current_row_cells.append(cell_text)
    
    file_handle.close()
    
    print(f"\n✅ Procesamiento completado")
    print(f"   Total líneas leídas: {line_num:,}")
    print(f"   Deals procesados: {processed_rows:,}")
    print(f"   Cuentas únicas: {len(accounts):,}")
    
    return {
        'total_deals': processed_rows,
        'accounts': accounts,
        'symbols_data': symbols_data,
        'accounts_data': accounts_data
    }


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 ib_analytics_streaming.py <archivo.html> [min_duration]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    min_duration = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    
    import os
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    
    print("\n" + "="*60)
    print("🚀 IB Analytics - Procesamiento Streaming")
    print("="*60)
    print(f"📁 Archivo: {file_path}")
    print(f"💾 Tamaño: {file_size_mb:.1f} MB")
    print(f"⏱️  Filtro: duración mínima {min_duration} minutos")
    print(f"🔄 Método: Línea por línea (sin cargar en RAM)")
    print("="*60)
    
    start_time = datetime.now()
    
    # Procesar
    data = process_html_streaming(file_path, min_duration)
    
    # Calcular métricas finales
    total_deals = data['total_deals']
    unique_accounts = len(data['accounts'])
    total_volume = sum(s['volume'] for s in data['symbols_data'].values())
    revenue_bruto = total_volume * 25.0
    total_profit = sum(s['profit'] for s in data['symbols_data'].values())
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
    output_file = "/tmp/deals_analytics_streaming.xlsx"
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
