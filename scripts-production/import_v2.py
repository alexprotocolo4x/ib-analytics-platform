#!/usr/bin/env python3
import sys, os, re, psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime

BATCH_SIZE = 10000

def parse_dt(s):
    try: return datetime.strptime(s, "%Y.%m.%d %H:%M:%S.%f")
    except: 
        try: return datetime.strptime(s, "%Y.%m.%d %H:%M:%S")
        except: return None

def clean(h):
    return re.sub(r'<[^>]+>', '', h).replace('&nbsp;', ' ').replace('&amp;', '&').strip()

def sf(v):
    if not v: return 0.0
    try: return float(v.replace(',', ''))
    except: return 0.0

def si(v):
    if not v: return None
    try: return int(v.replace(',', ''))
    except: return None

file_path = sys.argv[1]
db_url = os.getenv('DATABASE_URL')
m = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
db = {'user': m.group(1), 'password': m.group(2), 'host': m.group(3), 'port': int(m.group(4)), 'database': m.group(5)}

print("\n" + "="*60)
print("IB Analytics - Importacion")
print("="*60 + "\n")

conn = psycopg2.connect(**db)
cur = conn.cursor()
print("Conectado\n")

fh = None
for enc in ['utf-8', 'utf-16', 'latin-1']:
    try:
        fh = open(file_path, 'r', encoding=enc, errors='ignore')
        fh.readline()
        fh.seek(0)
        print(f"Encoding: {enc}\n")
        break
    except: 
        if fh: fh.close()

in_t = in_r = False
row = []
headers = []
batch = []
total = imported = 0

print("Procesando...\n")

for n, line in enumerate(fh, 1):
    total = n
    if n % 5000000 == 0: print(f"{n:,} lineas | {imported:,} deals")
    
    if '<table' in line.lower(): in_t = True; continue
    if '</table' in line.lower(): break
    if not in_t: continue
    
    if '<tr' in line.lower(): in_r = True; row = []; continue
    
    if '</tr' in line.lower():
        in_r = False
        if not row: continue
        if not headers: headers = row; print(f"{len(headers)} columnas\n"); continue
        if len(row) != len(headers): continue
        
        d = {headers[i]: row[i] for i in range(len(headers))}
        t = parse_dt(d.get('Time', ''))
        if not t or not d.get('Login') or not d.get('Symbol'): continue
        
        batch.append((t, d.get('Login'), si(d.get('Deal')), d.get('ID'), si(d.get('Order')), si(d.get('Position')), d.get('Symbol'), d.get('Action'), d.get('Entry'), sf(d.get('Volume', '0')), sf(d.get('Volume Closed')), sf(d.get('Gateway Volume')), sf(d.get('Price')), sf(d.get('Stop Loss')), sf(d.get('Take Profit')), sf(d.get('Market Bid')), sf(d.get('Market Ask')), sf(d.get('Market Last')), d.get('Reason'), sf(d.get('Fee', '0')), sf(d.get('Swap', '0')), sf(d.get('Value')), sf(d.get('Profit', '0')), d.get('Dealer'), d.get('Comment')))
        
        if len(batch) >= BATCH_SIZE:
            try:
                execute_batch(cur, "INSERT INTO deals (time,login,deal_id,external_id,order_id,position_id,symbol,action,entry,volume,volume_closed,gateway_volume,price,stop_loss,take_profit,market_bid,market_ask,market_last,reason,fee,swap,value,profit,dealer,comment) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", batch)
                conn.commit()
                imported += len(batch)
                batch = []
            except: conn.rollback(); batch = []
        continue
    
    if in_r:
        for c in re.findall(r'<td[^>]*>(.*?)</td>', line, re.I | re.DOTALL):
            row.append(clean(c))

if batch:
    try:
        execute_batch(cur, "INSERT INTO deals (time,login,deal_id,external_id,order_id,position_id,symbol,action,entry,volume,volume_closed,gateway_volume,price,stop_loss,take_profit,market_bid,market_ask,market_last,reason,fee,swap,value,profit,dealer,comment) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", batch)
        conn.commit()
        imported += len(batch)
    except: conn.rollback()

fh.close()
cur.close()
conn.close()

print(f"\nCOMPLETADO")
print(f"Lineas: {total:,}")
print(f"Deals: {imported:,}\n")
