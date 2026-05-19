"""
IB Analytics Platform - FastAPI Backend
Upload MT5 HTML exports and calculate IB metrics
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import io
from typing import Optional
from pathlib import Path

from app.parsers.mt5_parser import parse_mt5_html_bytes, get_summary_stats
from app.parsers.excel_parser import parse_account_list, parse_account_list_csv
from app.services.metrics import calculate_metrics, calculate_by_symbol, calculate_by_account

app = FastAPI(
    title="IB Analytics Platform", 
    version="1.0.0",
    # Increase upload size limit to 100MB
    swagger_ui_parameters={"defaultModelsExpandDepth": -1}
)

# Increase max body size
from starlette.datastructures import UploadFile as StarletteUploadFile
StarletteUploadFile.spool_max_size = 100 * 1024 * 1024  # 100MB

# Mount static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for uploaded data (temporary)
storage = {
    'deals_df': None,
    'account_filter': None
}

@app.get("/")
async def root():
    """Serve main interface"""
    try:
        html_path = Path(__file__).parent / "static" / "index.html"
        if html_path.exists():
            return FileResponse(html_path)
    except:
        pass
    return {
        "status": "online",
        "service": "IB Analytics Platform",
        "version": "1.0.0",
        "endpoints": {
            "upload_deals": "POST /api/upload/deals",
            "upload_accounts": "POST /api/upload/accounts",
            "get_metrics": "GET /api/metrics?min_duration=0",
            "export": "GET /api/export/excel?min_duration=0",
            "test_upload": "/static/test-upload.html"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "IB Analytics Platform",
        "version": "1.0.0"
    }

@app.post("/api/upload/deals")
async def upload_deals(file: UploadFile = File(...)):
    """
    Upload MT5 Administrator HTML export
    Returns summary statistics
    """
    import traceback
    try:
        print(f"[DEBUG] Received file: {file.filename}, content_type: {file.content_type}")
        
        # Read file content
        content = await file.read()
        print(f"[DEBUG] File size: {len(content)} bytes")
        
        # Parse HTML
        df = parse_mt5_html_bytes(content)
        print(f"[DEBUG] Parsed {len(df)} deals successfully")
        
        # Store in memory
        storage['deals_df'] = df
        print(f"[DEBUG] Stored in memory")
        
        # Calculate summary stats
        stats = get_summary_stats(df)
        
        return {
            "success": True,
            "message": f"Uploaded {len(df)} deals from {stats['unique_accounts']} accounts",
            "stats": stats,
            "filename": file.filename
        }
    
    except Exception as e:
        print(f"[ERROR] Exception in upload_deals: {str(e)}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=f"Error parsing HTML: {str(e)}")


@app.post("/api/upload/accounts")
async def upload_accounts(file: UploadFile = File(...)):
    """
    Upload Excel/CSV with account list (Login column)
    Filters deals to only these accounts
    """
    try:
        # Read file content
        content = await file.read()
        
        # Parse based on file type
        if file.filename.endswith('.csv'):
            accounts = parse_account_list_csv(io.BytesIO(content))
        elif file.filename.endswith(('.xls', '.xlsx')):
            accounts = parse_account_list(io.BytesIO(content), file.filename)
        else:
            raise ValueError("File must be .csv, .xls, or .xlsx")
        
        # Store filter
        storage['account_filter'] = accounts
        
        return {
            "success": True,
            "message": f"Loaded {len(accounts)} accounts for filtering",
            "accounts_count": len(accounts),
            "filename": file.filename
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing account list: {str(e)}")


@app.get("/api/metrics")
async def get_metrics(min_duration: float = 0):
    """
    Calculate and return all metrics
    Uses account filter if provided
    
    Args:
        min_duration: Minimum trade duration in minutes (default: 0 = no filter)
    """
    if storage['deals_df'] is None:
        raise HTTPException(status_code=400, detail="No deals data uploaded. Upload HTML first.")
    
    try:
        # Calculate overall metrics
        metrics = calculate_metrics(storage['deals_df'], storage['account_filter'], min_duration)
        
        # Calculate by symbol
        by_symbol = calculate_by_symbol(storage['deals_df'], storage['account_filter'], min_duration)
        
        # Calculate by account
        by_account = calculate_by_account(storage['deals_df'], storage['account_filter'], min_duration)
        
        return {
            "success": True,
            "metrics": metrics,
            "by_symbol": by_symbol[:20],  # Top 20 symbols
            "by_account": by_account[:50],  # Top 50 accounts
            "filter_applied": storage['account_filter'] is not None,
            "filtered_accounts": len(storage['account_filter']) if storage['account_filter'] else 0
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating metrics: {str(e)}")


@app.get("/api/export/excel")
async def export_excel(min_duration: float = 0):
    """
    Export results to Excel file
    
    Args:
        min_duration: Minimum trade duration in minutes (default: 0 = no filter)
    """
    if storage['deals_df'] is None:
        raise HTTPException(status_code=400, detail="No deals data uploaded. Upload HTML first.")
    
    try:
        # Calculate metrics
        metrics = calculate_metrics(storage['deals_df'], storage['account_filter'], min_duration)
        by_symbol = calculate_by_symbol(storage['deals_df'], storage['account_filter'], min_duration)
        by_account = calculate_by_account(storage['deals_df'], storage['account_filter'], min_duration)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Summary sheet
            summary_df = pd.DataFrame([metrics])
            summary_df.to_excel(writer, sheet_name='Resumen General', index=False)
            
            # By Symbol sheet
            symbol_df = pd.DataFrame(by_symbol)
            symbol_df.to_excel(writer, sheet_name='Por Símbolo', index=False)
            
            # By Account sheet
            account_df = pd.DataFrame(by_account)
            account_df.to_excel(writer, sheet_name='Por Cuenta', index=False)
            
            # Filtered deals (if filter applied)
            filtered_df = storage['deals_df'].copy()
            if storage['account_filter']:
                filtered_df = filtered_df[filtered_df['Login'].isin(storage['account_filter'])]
            if min_duration > 0 and 'duration_minutes' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['duration_minutes'] >= min_duration]
            
            if storage['account_filter'] or min_duration > 0:
                filtered_df.to_excel(writer, sheet_name='Deals Filtrados', index=False)
        
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=ib_analytics_export.xlsx"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting Excel: {str(e)}")


@app.delete("/api/reset")
async def reset_data():
    """
    Clear all uploaded data
    """
    storage['deals_df'] = None
    storage['account_filter'] = None
    
    return {
        "success": True,
        "message": "All data cleared"
    }


@app.get("/api/status")
async def get_status():
    """
    Get current system status
    """
    return {
        "deals_uploaded": storage['deals_df'] is not None,
        "deals_count": len(storage['deals_df']) if storage['deals_df'] is not None else 0,
        "filter_applied": storage['account_filter'] is not None,
        "filtered_accounts": len(storage['account_filter']) if storage['account_filter'] else 0
    }


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8100))
    uvicorn.run(app, host="0.0.0.0", port=port)
