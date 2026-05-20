#!/usr/bin/env python3
"""
IB Analytics Production - Query Tool
Ejecuta consultas analíticas sobre la base de datos
"""

import sys
import os
import psycopg2
import pandas as pd
from datetime import datetime, timedelta


def connect_db():
    """Conecta a PostgreSQL"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ Variable DATABASE_URL no definida")
        sys.exit(1)
    
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
    
    return psycopg2.connect(**db_config)


def query_summary():
    """Resumen general"""
    conn = connect_db()
    
    query = "SELECT * FROM deals_summary"
    df = pd.read_sql(query, conn)
    
    print("\n" + "="*60)
    print("📊 RESUMEN GENERAL")
    print("="*60)
    
    for _, row in df.iterrows():
        print(f"Total Deals:          {row['total_deals']:,}")
        print(f"Cuentas Únicas:       {row['unique_accounts']:,}")
        print(f"Símbolos Únicos:      {row['unique_symbols']:,}")
        print(f"Volumen Total:        {row['total_volume']:,.2f} lotes")
        print(f"Revenue Bruto:        ${row['revenue_bruto']:,.2f}")
        print(f"P&L Total:            ${row['total_profit']:,.2f}")
        print(f"Gross Profit:         ${row['gross_profit']:,.2f}")
        print(f"Gross Loss:           ${row['gross_loss']:,.2f}")
        
        profit_factor = row['gross_profit'] / row['gross_loss'] if row['gross_loss'] > 0 else 0
        print(f"Profit Factor:        {profit_factor:.2f}")
        print(f"Margen Neto (70%):    ${row['revenue_bruto'] * 0.70:,.2f}")
        print(f"Período:              {row['first_deal']} → {row['last_deal']}")
    
    conn.close()


def query_top_symbols(limit=10):
    """Top símbolos por volumen"""
    conn = connect_db()
    
    query = f"""
        SELECT * FROM deals_by_symbol
        ORDER BY total_volume DESC
        LIMIT {limit}
    """
    df = pd.read_sql(query, conn)
    
    print("\n" + "="*60)
    print(f"🎯 TOP {limit} SÍMBOLOS")
    print("="*60)
    
    for i, row in df.iterrows():
        print(f"{i+1:2d}. {row['symbol']:12s} - {row['total_volume']:8,.2f} lotes - "
              f"Revenue: ${row['revenue']:,.0f} - P&L: ${row['total_profit']:,.0f}")
    
    conn.close()


def query_top_accounts(limit=10):
    """Top cuentas por volumen"""
    conn = connect_db()
    
    query = f"""
        SELECT * FROM deals_by_account
        ORDER BY total_volume DESC
        LIMIT {limit}
    """
    df = pd.read_sql(query, conn)
    
    print("\n" + "="*60)
    print(f"👥 TOP {limit} CUENTAS")
    print("="*60)
    
    for i, row in df.iterrows():
        print(f"{i+1:2d}. {row['login']:10s} - {row['total_volume']:8,.2f} lotes - "
              f"P&L: ${row['total_profit']:,.0f}")
    
    conn.close()


def query_by_date_range(start_date, end_date):
    """Análisis por rango de fechas"""
    conn = connect_db()
    
    query = """
        SELECT 
            COUNT(*) as total_deals,
            COUNT(DISTINCT login) as unique_accounts,
            SUM(volume) as total_volume,
            SUM(profit) as total_profit,
            SUM(volume) * 25.0 as revenue
        FROM deals
        WHERE time >= %s AND time < %s
    """
    
    cur = conn.cursor()
    cur.execute(query, (start_date, end_date))
    row = cur.fetchone()
    
    print("\n" + "="*60)
    print(f"📅 RANGO: {start_date} → {end_date}")
    print("="*60)
    print(f"Total Deals:          {row[0]:,}")
    print(f"Cuentas Únicas:       {row[1]:,}")
    print(f"Volumen Total:        {row[2]:,.2f} lotes")
    print(f"Revenue:              ${row[4]:,.2f}")
    print(f"P&L:                  ${row[3]:,.2f}")
    
    cur.close()
    conn.close()


def export_to_excel(output_file="/tmp/ib_analytics_export.xlsx"):
    """Exporta análisis completo a Excel"""
    conn = connect_db()
    
    print(f"\n📥 Exportando a: {output_file}")
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Resumen
        df_summary = pd.read_sql("SELECT * FROM deals_summary", conn)
        df_summary.to_excel(writer, sheet_name='Resumen General', index=False)
        
        # Top símbolos
        df_symbols = pd.read_sql("""
            SELECT * FROM deals_by_symbol ORDER BY total_volume DESC LIMIT 100
        """, conn)
        df_symbols.to_excel(writer, sheet_name='Top Símbolos', index=False)
        
        # Top cuentas
        df_accounts = pd.read_sql("""
            SELECT * FROM deals_by_account ORDER BY total_volume DESC LIMIT 100
        """, conn)
        df_accounts.to_excel(writer, sheet_name='Top Cuentas', index=False)
        
        # Por día
        df_daily = pd.read_sql("""
            SELECT 
                DATE(time) as date,
                COUNT(*) as deals,
                COUNT(DISTINCT login) as accounts,
                SUM(volume) as volume,
                SUM(profit) as profit,
                SUM(volume) * 25.0 as revenue
            FROM deals
            GROUP BY DATE(time)
            ORDER BY date DESC
        """, conn)
        df_daily.to_excel(writer, sheet_name='Por Día', index=False)
    
    conn.close()
    print("✅ Excel generado")


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 query_analytics.py <comando> [opciones]")
        print("\nComandos disponibles:")
        print("  summary                    - Resumen general")
        print("  symbols [limit]            - Top símbolos (default: 10)")
        print("  accounts [limit]           - Top cuentas (default: 10)")
        print("  date <start> <end>         - Análisis por rango (YYYY-MM-DD)")
        print("  export [archivo.xlsx]      - Exportar a Excel")
        print("\nEjemplos:")
        print("  python3 query_analytics.py summary")
        print("  python3 query_analytics.py symbols 20")
        print("  python3 query_analytics.py date 2026-05-01 2026-05-31")
        print("  python3 query_analytics.py export /tmp/report.xlsx")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'summary':
        query_summary()
        query_top_symbols(10)
        query_top_accounts(10)
    
    elif command == 'symbols':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        query_top_symbols(limit)
    
    elif command == 'accounts':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        query_top_accounts(limit)
    
    elif command == 'date':
        if len(sys.argv) < 4:
            print("❌ Faltan parámetros: python3 query_analytics.py date YYYY-MM-DD YYYY-MM-DD")
            sys.exit(1)
        start = sys.argv[2]
        end = sys.argv[3]
        query_by_date_range(start, end)
    
    elif command == 'export':
        output = sys.argv[2] if len(sys.argv) > 2 else "/tmp/ib_analytics_export.xlsx"
        export_to_excel(output)
    
    else:
        print(f"❌ Comando desconocido: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
