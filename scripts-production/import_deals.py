#!/usr/bin/env python3
"""
IB Analytics Production - Batch Importer
Importa archivos HTML gigantes a PostgreSQL línea por línea
"""

import sys
import os
import re
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
from collections import defaultdict

BATCH_SIZE = 10000  # Insertar cada 10k filas


def parse_mt5_datetime(dt_str):
    """Convierte formato MT5 a timestamp PostgreSQL"""
    try:
        # Formato: 2026.05.18 01:03:38.696
        return datetime.strptime(dt_str, "%Y.%m.%d %H:%M:%S.%f")
    except:
        try:
            return datetime.strptime(dt_str, "%Y.%m.%d %H:%M:%S")
        except:
            return None


def extract_cell_text(html_cell):
    """Extrae texto de celda HTML"""
    text = re.sub(r'<[^>]+>', '', html_cell)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
    return text.strip()


def safe_float(value):
    """Convierte a float seguro"""
    if not value or value == '':
        return 0.0
    try:
        return float(value.replace(',', ''))
    except:
        return 0.0


def safe_int(value):
    """Convierte a int seguro"""
    if not value or value == '':
        return None
    try:
        return int(value.replace(',', ''))
    except:
        return None


def import_html_to_postgres(file_path, db_config):
    """Importa HTML a PostgreSQL en modo streaming"""
    
    print("\n" + "="*60)
    print("🚀 IB Analytics - Importación a PostgreSQL")
    print("="*60)
    
    file_size = os.path.getsize(file_path)
    file_size_mb = file_size / (1024 * 1024)
    filename = os.path.basename(file_path)
    
    print(f"📁 Archivo: {filename}")
    print(f"💾 Tamaño: {file_size_mb:.1f} MB")
    print(f"📦 Batch size: {BATCH_SIZE:,} filas")
    print("="*60)
    
    # Conectar a PostgreSQL
    print("\n🔌 Conectando a PostgreSQL...")
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        print("✅ Conexión establecida")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return
    
    # Registrar inicio de importación
    start_time = datetime.now()
    cur.execute("""
        INSERT INTO import_logs (filename, file_size_bytes, started_at, status)
        VALUES (%s, %s, %s, 'running')
        RETURNING id
    """, (filename, file_size, start_time))
    import_log_id = cur.fetchone()[0]
    conn.commit()
    
    # Detectar encoding
    encodings = ['utf-8', 'utf-16', 'latin-1']
    file_handle = None
    
    for encoding in encodings:
        try:
            file_handle = open(file_path, 'r', encoding=encoding, errors='ignore')
            file_handle.readline()
            file_handle.seek(0)
            print(f"  ✅ Encoding: {encoding}")
            break
        except:
            if file_handle:
                file_handle.close()
            continue
    
    if not file_handle:
        print("❌ No se pudo abrir el archivo")
        return
    
    # Variables de procesamiento
    in_table = False
    in_row = False
    current_row_cells = []
    headers = []
    
    batch = []
    total_lines = 0
    total_imported = 0
    last_progress = 0
    
    print("\n📖 Leyendo archivo...")
    
    # Leer línea por línea
    for line_num, line in enumerate(file_handle, 1):
        total_lines = line_num
        
        # Progress cada 1M líneas
        if line_num % 1000000 == 0:
            progress_mb = (file_handle.tell() / file_size) * 100
            print(f"  {line_num:,} líneas | {total_imported:,} deals | {progress_mb:.1f}% completado")
            last_progress = line_num
        
        # Detectar tabla
        if '<table' in line.lower():
            in_table = True
            continue
        
        if '</table' in line.lower():
            in_table = False
            break
        
        if not in_table:
            continue
        
        # Detectar fila
        if '<tr' in line.lower():
            in_row = True
            current_row_cells = []
            continue
        
        if '</tr' in line.lower():
            in_row = False
            
            if not current_row_cells:
                continue
            
            # Primera fila = headers
            if not headers:
                headers = current_row_cells
                print(f"  📋 Headers: {len(headers)} columnas detectadas")
                continue
            
            # Validar columnas
            if len(current_row_cells) != len(headers):
                continue
            
            # Crear dict del deal
            deal = {headers[i]: current_row_cells[i] for i in range(len(headers))}
            
            # Extraer campos
            time = parse_mt5_datetime(deal.get('Time', ''))
            if not time:
                continue
            
            login = deal.get('Login', '')
            if not login:
                continue
            
            symbol = deal.get('Symbol', '')
            if not symbol:
                continue
            
            # Preparar row para insert
            row = (
                time,
                login,
                safe_int(deal.get('Deal', '')),
                deal.get('ID', ''),
                safe_int(deal.get('Order', '')),
                safe_int(deal.get('Position', '')),
                symbol,
                deal.get('Action', ''),
                deal.get('Entry', ''),
                safe_float(deal.get('Volume', '0')),
                safe_float(deal.get('Volume Closed', '')),
                safe_float(deal.get('Gateway Volume', '')),
                safe_float(deal.get('Price', '')),
                safe_float(deal.get('Stop Loss', '')),
                safe_float(deal.get('Take Profit', '')),
                safe_float(deal.get('Market Bid', '')),
                safe_float(deal.get('Market Ask', '')),
                safe_float(deal.get('Market Last', '')),
                deal.get('Reason', ''),
                safe_float(deal.get('Fee', '0')),
                safe_float(deal.get('Swap', '0')),
                safe_float(deal.get('Value', '')),
                safe_float(deal.get('Profit', '0')),
                deal.get('Dealer', ''),
                deal.get('Comment', '')
            )
            
            batch.append(row)
            
            # Insertar batch cuando alcanza el tamaño
            if len(batch) >= BATCH_SIZE:
                try:
                    execute_batch(cur, """
                        INSERT INTO deals (
                            time, login, deal_id, external_id, order_id, position_id,
                            symbol, action, entry, volume, volume_closed, gateway_volume,
                            price, stop_loss, take_profit, market_bid, market_ask, market_last,
                            reason, fee, swap, value, profit, dealer, comment
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, batch)
                    conn.commit()
                    total_imported += len(batch)
                    batch = []
                except Exception as e:
                    print(f"\n⚠️  Error en batch: {e}")
                    conn.rollback()
                    batch = []
            
            continue
        
        # Extraer celdas de la línea
        if in_row:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', line, re.IGNORECASE | re.DOTALL)
            for cell_html in cells:
                cell_text = extract_cell_text(cell_html)
                current_row_cells.append(cell_text)
    
    # Insertar último batch
    if batch:
        try:
            execute_batch(cur, """
                INSERT INTO deals (
                    time, login, deal_id, external_id, order_id, position_id,
                    symbol, action, entry, volume, volume_closed, gateway_volume,
                    price, stop_loss, take_profit, market_bid, market_ask, market_last,
                    reason, fee, swap, value, profit, dealer, comment
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, batch)
            conn.commit()
            total_imported += len(batch)
        except Exception as e:
            print(f"\n⚠️  Error en último batch: {e}")
            conn.rollback()
    
    file_handle.close()
    
    # Actualizar log
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    cur.execute("""
        UPDATE import_logs
        SET lines_read = %s, deals_imported = %s, completed_at = %s,
            duration_seconds = %s, status = 'completed'
        WHERE id = %s
    """, (total_lines, total_imported, end_time, int(duration), import_log_id))
    conn.commit()
    
    # Refresh vistas materializadas
    print("\n🔄 Actualizando vistas materializadas...")
    cur.execute("SELECT refresh_materialized_views()")
    conn.commit()
    
    # Obtener resumen
    cur.execute("SELECT * FROM deals_summary")
    summary = cur.fetchone()
    
    cur.close()
    conn.close()
    
    # Imprimir resultados
    print("\n" + "="*60)
    print("✅ IMPORTACIÓN COMPLETADA")
    print("="*60)
    print(f"Líneas leídas:        {total_lines:,}")
    print(f"Deals importados:     {total_imported:,}")
    print(f"Tiempo total:         {duration:.1f}s ({duration/60:.1f} min)")
    print(f"Velocidad:            {total_imported/duration:.0f} deals/segundo")
    
    if summary:
        print("\n📊 RESUMEN EN BASE DE DATOS:")
        print(f"Total deals:          {summary[0]:,}")
        print(f"Cuentas únicas:       {summary[1]:,}")
        print(f"Símbolos únicos:      {summary[2]:,}")
        print(f"Volumen total:        {summary[3]:,.2f} lotes")
        print(f"Revenue bruto:        ${summary[7]:,.2f}")
        print(f"P&L total:            ${summary[4]:,.2f}")
    
    print("\n🎉 Listo para consultas!")


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 import_deals.py <archivo.html>")
        print("\nVariable de entorno DATABASE_URL requerida:")
        print("export DATABASE_URL='postgresql://user:pass@host:5432/dbname'")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"❌ Archivo no encontrado: {file_path}")
        sys.exit(1)
    
    # Configuración de base de datos desde ENV
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ Variable DATABASE_URL no definida")
        print("export DATABASE_URL='postgresql://user:pass@host:5432/dbname'")
        sys.exit(1)
    
    # Parsear DATABASE_URL
    import re
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
    if not match:
        print("❌ DATABASE_URL inválido")
        sys.exit(1)
    
    db_config = {
        'user': match.group(1),
        'password': match.group(2),
        'host': match.group(3),
        'port': int(match.group(4)),
        'database': match.group(5)
    }
    
    import_html_to_postgres(file_path, db_config)


if __name__ == '__main__':
    main()
