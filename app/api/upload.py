"""
Upload endpoints - HTML MT5 + Excel accounts
"""
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import logging
from typing import Optional

from app.parsers.mt5_parser import MT5HTMLParser
from app.services.data_store import DataStore

router = APIRouter()
logger = logging.getLogger(__name__)

# Store singleton (in-memory por ahora)
data_store = DataStore()
parser = MT5HTMLParser()


@router.post("/mt5-html")
async def upload_mt5_html(file: UploadFile = File(...)):
    """
    Upload MT5 Administrator HTML export
    
    Returns:
        Summary de los deals parseados
    """
    try:
        # Validar archivo
        if not file.filename.endswith('.html'):
            raise HTTPException(400, "El archivo debe ser HTML")
        
        # Leer contenido
        content = await file.read()
        
        # Detectar encoding (UTF-16 típico de MT5)
        try:
            html_content = content.decode('utf-16')
        except:
            try:
                html_content = content.decode('utf-8')
            except:
                raise HTTPException(400, "No se pudo decodificar el HTML")
        
        # Parsear
        df = parser.parse_html(html_content)
        
        # Guardar en store
        data_store.set_deals(df)
        
        # Generar resumen
        summary = parser.get_summary(df)
        
        logger.info(f"✅ HTML procesado: {summary['total_deals']} deals")
        
        return {
            "success": True,
            "message": f"Procesados {summary['total_deals']} deals correctamente",
            "summary": summary
        }
        
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Error procesando HTML: {e}")
        raise HTTPException(500, f"Error interno: {str(e)}")


@router.post("/accounts-excel")
async def upload_accounts_excel(file: UploadFile = File(...)):
    """
    Upload Excel con lista de cuentas a analizar
    
    Formato esperado:
    - Columna 'Login' con números de cuenta
    
    Returns:
        Lista de cuentas cargadas
    """
    try:
        # Validar archivo
        if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
            raise HTTPException(400, "El archivo debe ser Excel (.xlsx o .xls)")
        
        # Leer Excel
        content = await file.read()
        df = pd.read_excel(content)
        
        # Validar que tenga columna Login
        if 'Login' not in df.columns:
            raise HTTPException(
                400, 
                "El Excel debe tener una columna llamada 'Login' con los números de cuenta"
            )
        
        # Extraer logins y convertir a string
        accounts = df['Login'].astype(str).tolist()
        
        # Limpiar valores vacíos
        accounts = [acc.strip() for acc in accounts if acc.strip() and acc != 'nan']
        
        if not accounts:
            raise HTTPException(400, "No se encontraron cuentas válidas en el Excel")
        
        # Guardar en store
        data_store.set_accounts(accounts)
        
        logger.info(f"✅ Cargadas {len(accounts)} cuentas del Excel")
        
        return {
            "success": True,
            "message": f"Cargadas {len(accounts)} cuentas correctamente",
            "accounts": accounts[:10],  # Mostrar primeras 10
            "total": len(accounts)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando Excel: {e}")
        raise HTTPException(500, f"Error interno: {str(e)}")


@router.get("/status")
async def upload_status():
    """
    Status de los datos cargados
    """
    deals_df = data_store.get_deals()
    accounts = data_store.get_accounts()
    
    return {
        "deals_loaded": deals_df is not None,
        "deals_count": len(deals_df) if deals_df is not None else 0,
        "accounts_loaded": accounts is not None,
        "accounts_count": len(accounts) if accounts is not None else 0,
        "ready_for_analysis": deals_df is not None and accounts is not None
    }


@router.delete("/clear")
async def clear_data():
    """
    Limpiar todos los datos cargados
    """
    data_store.clear()
    
    return {
        "success": True,
        "message": "Datos limpiados correctamente"
    }
