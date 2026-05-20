#!/usr/bin/env python3
"""
IB Analytics - Procesador Local
Procesa archivos HTML grandes de MT5 Administrator sin límites de tamaño
"""

import sys
import pandas as pd
from pathlib import Path
from app.parsers.mt5_parser import parse_mt5_html
from app.services.metrics import calculate_metrics, calculate_by_symbol, calculate_by_account

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 process_local.py <archivo_html> [min_duration_minutos]")
        print("\nEjemplo:")
        print("  python3 process_local.py deals.html")
        print("  python3 process_local.py deals.html 3")
        sys.exit(1)
    
    html_file = sys.argv[1]
    min_duration = float(sys.argv[2]) if len(sys.argv) > 2 else 0
    
    if not Path(html_file).exists():
        print(f"❌ Error: Archivo no encontrado: {html_file}")
        sys.exit(1)
    
    print(f"🚀 Procesando: {html_file}")
    print(f"📁 Tamaño: {Path(html_file).stat().st_size / (1024*1024):.1f} MB")
    
    if min_duration > 0:
        print(f"⏱️  Filtro: duración mínima {min_duration} minutos")
    
    print("\n📊 Leyendo y parseando HTML...")
    try:
        df = parse_mt5_html(html_file)
        print(f"✅ {len(df):,} deals cargados")
        print(f"✅ {df['Login'].nunique():,} cuentas únicas")
    except Exception as e:
        print(f"❌ Error al parsear HTML: {e}")
        sys.exit(1)
    
    print("\n🔢 Calculando métricas...")
    metrics = calculate_metrics(df, None, min_duration)
    by_symbol = calculate_by_symbol(df, None, min_duration)
    by_account = calculate_by_account(df, None, min_duration)
    
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
    
    if metrics.get('deals_filtered_by_duration', 0) > 0:
        print(f"\n⚠️  {metrics['deals_filtered_by_duration']:,} deals excluidos por duración < {min_duration} min")
    
    print("\n" + "="*60)
    print("🎯 TOP 10 SÍMBOLOS")
    print("="*60)
    for i, s in enumerate(by_symbol[:10], 1):
        print(f"{i:2d}. {s['symbol']:12s} - {s['total_volume']:8,.2f} lotes - Revenue: ${s['revenue']:,.0f}")
    
    print("\n" + "="*60)
    print("👥 TOP 10 CUENTAS")
    print("="*60)
    for i, a in enumerate(by_account[:10], 1):
        print(f"{i:2d}. {int(a['account']):10d} - {a['total_volume']:8,.2f} lotes - P&L: ${a['pnl']:,.0f}")
    
    # Exportar a Excel
    output_file = Path(html_file).stem + "_analytics.xlsx"
    print(f"\n📥 Exportando resultados a: {output_file}")
    
    try:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Resumen General
            summary_df = pd.DataFrame([metrics])
            summary_df.to_excel(writer, sheet_name='Resumen General', index=False)
            
            # Por Símbolo
            symbol_df = pd.DataFrame(by_symbol)
            symbol_df.to_excel(writer, sheet_name='Por Símbolo', index=False)
            
            # Por Cuenta
            account_df = pd.DataFrame(by_account)
            account_df.to_excel(writer, sheet_name='Por Cuenta', index=False)
            
            # Deals filtrados (si hay filtro)
            if min_duration > 0:
                filtered_df = df[df['duration_minutes'] >= min_duration] if 'duration_minutes' in df.columns else df
                filtered_df.to_excel(writer, sheet_name='Deals Filtrados', index=False)
        
        print(f"✅ Excel generado exitosamente")
        print(f"📍 Ubicación: {Path(output_file).absolute()}")
        
    except Exception as e:
        print(f"❌ Error al generar Excel: {e}")
        sys.exit(1)
    
    print("\n🎉 Proceso completado!")

if __name__ == "__main__":
    main()
