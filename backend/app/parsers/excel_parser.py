"""
Excel Account List Parser
Extracts account numbers from Excel files (Login column)
"""
import pandas as pd
from typing import List, Set

def parse_account_list(file_bytes: bytes, filename: str) -> Set[int]:
    """
    Parse Excel file and extract account numbers from 'Login' column
    
    Args:
        file_bytes: Excel file content as bytes
        filename: Original filename (to determine .xls vs .xlsx)
        
    Returns:
        Set of account numbers (Login values)
    """
    # Determine engine based on file extension
    engine = 'xlrd' if filename.endswith('.xls') else 'openpyxl'
    
    # Read Excel file
    df = pd.read_excel(file_bytes, engine=engine)
    
    # Find Login column (case-insensitive)
    login_col = None
    for col in df.columns:
        if col.lower() == 'login':
            login_col = col
            break
    
    if login_col is None:
        raise ValueError("No 'Login' column found in Excel file. Available columns: " + ", ".join(df.columns))
    
    # Extract unique account numbers
    accounts = set(df[login_col].dropna().astype(int).unique())
    
    return accounts


def parse_account_list_csv(file_bytes: bytes) -> Set[int]:
    """
    Parse CSV file and extract account numbers from 'Login' column
    
    Args:
        file_bytes: CSV file content as bytes
        
    Returns:
        Set of account numbers (Login values)
    """
    # Read CSV
    df = pd.read_csv(file_bytes)
    
    # Find Login column (case-insensitive)
    login_col = None
    for col in df.columns:
        if col.lower() == 'login':
            login_col = col
            break
    
    if login_col is None:
        raise ValueError("No 'Login' column found in CSV file. Available columns: " + ", ".join(df.columns))
    
    # Extract unique account numbers
    accounts = set(df[login_col].dropna().astype(int).unique())
    
    return accounts
