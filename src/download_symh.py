#!/usr/bin/env python3
import urllib.request
import urllib.parse
import sys
import os
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, 'data')

MAX_RECORDS = 500000  # OMNIWeb limit is 600000, use 500000 for safety

def parse_yymmdd(date_str):
    """Convert YYMMDD to YYYYMMDD00 (adding hour 00)"""
    if len(date_str) != 6:
        return None
    
    yy = int(date_str[:2])
    mm = int(date_str[2:4])
    dd = int(date_str[4:6])
    
    if yy >= 80:
        year = 1900 + yy
    else:
        year = 2000 + yy
    
    if mm < 1 or mm > 12 or dd < 1 or dd > 31:
        return None
    
    return datetime(year, mm, dd, 0, 0, 0)

def download_chunk(start_dt, end_dt):
    """Download a single chunk of data from OMNIWeb."""
    base_url = "https://omniweb.gsfc.nasa.gov/cgi/nx1.cgi"
    
    start_str = start_dt.strftime('%Y%m%d00')
    end_str = end_dt.strftime('%Y%m%d23')
    
    params = {
        'activity': 'retrieve',
        'res': 'min',
        'spacecraft': 'omni_min',
        'start_date': start_str,
        'end_date': end_str,
        'vars': '41',  # SYM/H variable
        'scale': 'Linear',
        'ymin': '',
        'ymax': '',
        'view': '0',
        'charsize': '',
        'xstyle': '0',
        'ystyle': '0',
        'symbol': '0',
        'symsize': '',
        'linestyle': 'solid',
        'table': '1',
        'imagex': '640',
        'imagey': '480',
        'color': '',
        'back': ''
    }
    
    data = urllib.parse.urlencode(params).encode('ascii')
    req = urllib.request.Request(base_url, data=data)
    
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            content = response.read().decode('utf-8')
        
        lines = content.strip().split('\n')
        
        output_lines = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('>') or line.startswith('YEAR') or line.startswith('---') or line.startswith('<'):
                continue
            
            parts = line.split()
            if len(parts) >= 5:
                try:
                    year = int(parts[0])
                    doy = int(parts[1])
                    hour = int(parts[2])
                    minute = int(parts[3])
                    sym_h = int(parts[4])
                    
                    if sym_h == 99999:
                        continue
                    
                    output_lines.append(f"{year} {doy} {hour:3d} {minute:3d} {sym_h:6d}")
                except (ValueError, IndexError):
                    continue
        
        return output_lines
        
    except Exception as e:
        print(f"  Warning: Error downloading chunk: {e}")
        return []

def download_symh(start_dt, end_dt):
    """Download SYM-H data from NASA OMNIWeb, splitting into chunks if needed."""
    print(f"Downloading SYM-H data from OMNIWeb...")
    print(f"  Start: {start_dt.strftime('%Y-%m-%d')}")
    print(f"  End: {end_dt.strftime('%Y-%m-%d')}")
    
    total_days = (end_dt - start_dt).days
    chunk_days = MAX_RECORDS // 1440  # 1440 minutes per day
    
    all_lines = []
    current_start = start_dt
    
    while current_start < end_dt:
        current_end = min(current_start + timedelta(days=chunk_days - 1), end_dt)
        
        days_str = f"{current_start.strftime('%Y-%m-%d')} to {current_end.strftime('%Y-%m-%d')}"
        print(f"  Fetching: {days_str}...")
        
        chunk_lines = download_chunk(current_start, current_end)
        all_lines.extend(chunk_lines)
        print(f"    Got {len(chunk_lines)} records")
        
        current_start = current_end + timedelta(days=1)
    
    if not all_lines:
        print("Error: No valid data received from OMNIWeb")
        return False
    
    os.makedirs(DATA_DIR, exist_ok=True)
    output_file = os.path.join(DATA_DIR, 'data.txt')
    
    with open(output_file, 'w') as f:
        f.write('\n'.join(all_lines) + '\n')
    
    print(f"Downloaded {len(all_lines)} total data points to data/data.txt")
    return True

def main():
    if len(sys.argv) < 3:
        print("""
Usage: ./src/download_symh.py <start_date> <end_date>

Dates format: YYMMDD

Examples:
  ./src/download_symh.py 980228 031120
  ./src/download_symh.py 240510 240513
  ./src/download_symh.py 240101 260101
""")
        sys.exit(1)
    
    start_input = sys.argv[1]
    end_input = sys.argv[2]
    
    start_dt = parse_yymmdd(start_input)
    end_dt = parse_yymmdd(end_input)
    
    if start_dt is None or end_dt is None:
        print("Error: Dates must be in YYMMDD format (6 characters)")
        sys.exit(1)
    
    if start_dt > end_dt:
        print("Error: Start date must be before end date")
        sys.exit(1)
    
    success = download_symh(start_dt, end_dt)
    
    if success:
        print("Done! Run 'make storm' to analyze the data.")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
