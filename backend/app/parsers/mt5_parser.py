"""
MT5 Administrator HTML Parser
Extracts deal data from MT5 HTML exports (UTF-16 encoding)
"""
from bs4 import BeautifulSoup
import pandas as pd
from typing import List, Dict
import re

def parse_mt5_html(file_path: str) -> pd.DataFrame:
    """
    Parse MT5 Administrator HTML export and return DataFrame with deals
    
    Args:
        file_path: Path to HTML file (UTF-16 encoded)
        
    Returns:
        DataFrame with 25 columns: Deal, Login, Order, Symbol, Action, Entry, Volume, 
        Price, S/L, T/P, Price_2, Commission, Swap, Profit, Fee, Comment, Magic, 
        Gateway, Modification_Flags, Time, Reason, Expert_ID, Position_ID, External_ID, Digits
    """
    # Read file with UTF-16 encoding
    with open(file_path, 'r', encoding='utf-16') as f:
        html_content = f.read()
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all tables
    tables = soup.find_all('table')
    
    if not tables:
        raise ValueError("No tables found in HTML file")
    
    # The deals table is typically the largest one
    deals_table = max(tables, key=lambda t: len(t.find_all('tr')))
    
    # Extract headers
    header_row = deals_table.find('tr')
    headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
    
    # Extract data rows
    data_rows = deals_table.find_all('tr')[1:]  # Skip header
    
    deals = []
    for row in data_rows:
        cells = row.find_all('td')
        if len(cells) >= 25:  # Ensure we have all columns
            deal = [cell.get_text(strip=True) for cell in cells]
            deals.append(deal)
    
    # Create DataFrame
    df = pd.DataFrame(deals, columns=headers[:25])
    
    # Clean and convert data types
    numeric_columns = ['Deal', 'Login', 'Order', 'Volume', 'Price', 'S/L', 'T/P', 
                      'Price_2', 'Commission', 'Swap', 'Profit', 'Fee', 'Magic', 
                      'Expert_ID', 'Position_ID', 'Digits']
    
    for col in numeric_columns:
        if col in df.columns:
            # Remove spaces and convert to numeric
            df[col] = pd.to_numeric(df[col].str.replace(' ', ''), errors='coerce')
    
    return df


def parse_mt5_html_bytes(file_bytes: bytes) -> pd.DataFrame:
    """
    Parse MT5 HTML from bytes (for file uploads)
    
    Args:
        file_bytes: HTML file content as bytes
        
    Returns:
        DataFrame with deals data
    """
    # Try different encodings
    html_content = None
    for encoding in ['utf-16', 'utf-8', 'latin-1']:
        try:
            html_content = file_bytes.decode(encoding)
            break
        except:
            continue
    
    if html_content is None:
        raise ValueError("Could not decode file. Tried: utf-16, utf-8, latin-1")
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all tables
    tables = soup.find_all('table')
    
    if not tables:
        raise ValueError("No tables found in HTML file")
    
    # The deals table is typically the largest one
    deals_table = max(tables, key=lambda t: len(t.find_all('tr')))
    
    # Extract headers
    header_row = deals_table.find('tr')
    headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
    
    # Extract data rows
    data_rows = deals_table.find_all('tr')[1:]  # Skip header
    
    deals = []
    for row in data_rows:
        cells = row.find_all('td')
        if len(cells) >= 25:  # Ensure we have all columns
            deal = [cell.get_text(strip=True) for cell in cells]
            deals.append(deal)
    
    # Create DataFrame
    df = pd.DataFrame(deals, columns=headers[:25])
    
    # Clean and convert data types
    numeric_columns = ['Deal', 'Login', 'Order', 'Volume', 'Price', 'S/L', 'T/P', 
                      'Price_2', 'Commission', 'Swap', 'Profit', 'Fee', 'Magic', 
                      'Expert_ID', 'Position_ID', 'Digits']
    
    for col in numeric_columns:
        if col in df.columns:
            # Remove spaces and convert to numeric
            df[col] = pd.to_numeric(df[col].str.replace(' ', ''), errors='coerce')
    
    # Parse Time column to datetime
    if 'Time' in df.columns:
        df['Time'] = pd.to_datetime(df['Time'], errors='coerce')
    
    # Calculate trade duration (group by Position_ID)
    if 'Position_ID' in df.columns and 'Time' in df.columns:
        df = calculate_trade_duration(df)
    
    return df


def calculate_trade_duration(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate trade duration in minutes for each position
    Groups deals by Position_ID and calculates time difference between entry and exit
    """
    # Group by Position_ID and find min/max time
    position_times = df.groupby('Position_ID')['Time'].agg(['min', 'max']).reset_index()
    position_times['duration_minutes'] = (position_times['max'] - position_times['min']).dt.total_seconds() / 60
    
    # Merge back to original dataframe
    df = df.merge(position_times[['Position_ID', 'duration_minutes']], on='Position_ID', how='left')
    
    return df


def get_summary_stats(df: pd.DataFrame) -> Dict:
    """
    Calculate summary statistics from deals DataFrame
    
    Returns:
        Dict with total_deals, unique_accounts, total_volume, total_pnl, etc.
    """
    return {
        'total_deals': len(df),
        'unique_accounts': df['Login'].nunique() if 'Login' in df.columns else 0,
        'unique_symbols': df['Symbol'].nunique() if 'Symbol' in df.columns else 0,
        'total_volume': float(df['Volume'].sum()) if 'Volume' in df.columns else 0,
        'total_pnl': float(df['Profit'].sum()) if 'Profit' in df.columns else 0,
        'total_commission': float(df['Commission'].sum()) if 'Commission' in df.columns else 0,
        'total_swap': float(df['Swap'].sum()) if 'Swap' in df.columns else 0,
    }
