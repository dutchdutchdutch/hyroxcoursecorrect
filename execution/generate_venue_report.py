#!/usr/bin/env python3
"""
Generate HYROX Venue Handicap Report

Creates comprehensive report in Google Sheets with venue rankings,
handicap factors, and visualizations.

Usage:
    python generate_venue_report.py
"""

import os
from pathlib import Path
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv

# Try importing Google Sheets libraries
try:
    import gspread
    from google.oauth2.service_account import Credentials
    HAS_GSPREAD = True
except ImportError:
    HAS_GSPREAD = False
    print("⚠️  gspread not installed - will export to Excel instead")


load_dotenv()

SHEET_NAME = os.getenv('OUTPUT_SHEET_NAME', 'HYROX Venue Handicap Analysis')
CREDENTIALS_PATH = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH', 'credentials.json')


def create_google_sheet(handicaps_df: pd.DataFrame, stats_df: pd.DataFrame) -> str:
    """
    Create Google Sheet with venue handicap analysis.
    
    Returns:
        URL of created sheet
    """
    if not HAS_GSPREAD:
        print("❌ Google Sheets integration not available")
        return None
    
    if not Path(CREDENTIALS_PATH).exists():
        print(f"❌ Credentials file not found: {CREDENTIALS_PATH}")
        print("   Please set up Google Sheets API credentials")
        return None
    
    print("Creating Google Sheet...")
    
    # Set up credentials
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=scopes)
    client = gspread.authorize(creds)
    
    # Create new spreadsheet
    sheet_title = f"{SHEET_NAME} - {datetime.now().strftime('%Y-%m-%d')}"
    spreadsheet = client.create(sheet_title)
    
    # Share with user (make it accessible)
    # spreadsheet.share('user@example.com', perm_type='user', role='writer')
    
    # Add worksheets
    # 1. Venue Handicaps
    ws_handicaps = spreadsheet.sheet1
    ws_handicaps.update_title('Venue Handicaps')
    ws_handicaps.update([handicaps_df.columns.tolist()] + handicaps_df.values.tolist())
    
    # 2. Venue Statistics
    ws_stats = spreadsheet.add_worksheet('Venue Statistics', 
                                         rows=len(stats_df)+1, 
                                         cols=len(stats_df.columns))
    stats_df_reset = stats_df.reset_index()
    ws_stats.update([stats_df_reset.columns.tolist()] + stats_df_reset.values.tolist())
    
    # 3. Summary
    ws_summary = spreadsheet.add_worksheet('Summary', rows=20, cols=2)
    summary_data = [
        ['HYROX Venue Handicap Analysis', ''],
        ['Generated', datetime.now().strftime('%Y-%m-%d %H:%M')],
        ['', ''],
        ['Total Venues', len(handicaps_df)],
        ['Easiest Venue', handicaps_df.iloc[0]['venue']],
        ['Easiest Handicap', f"{handicaps_df.iloc[0]['handicap_factor']:.3f}"],
        ['Hardest Venue', handicaps_df.iloc[-1]['venue']],
        ['Hardest Handicap', f"{handicaps_df.iloc[-1]['handicap_factor']:.3f}"],
        ['Handicap Range', f"{handicaps_df['handicap_factor'].max() - handicaps_df['handicap_factor'].min():.3f}"],
    ]
    ws_summary.update(summary_data)
    
    url = spreadsheet.url
    print(f"✓ Google Sheet created: {url}")
    
    return url


def export_to_excel(handicaps_df: pd.DataFrame, stats_df: pd.DataFrame, 
                   output_file: Path):
    """Export to Excel as fallback."""
    print(f"Exporting to Excel: {output_file}")
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Venue Handicaps
        handicaps_df.to_excel(writer, sheet_name='Venue Handicaps', index=False)
        
        # Venue Statistics
        stats_df.to_excel(writer, sheet_name='Venue Statistics')
        
        # Summary
        summary_df = pd.DataFrame({
            'Metric': [
                'Total Venues',
                'Easiest Venue',
                'Easiest Handicap',
                'Hardest Venue',
                'Hardest Handicap',
                'Handicap Range',
            ],
            'Value': [
                len(handicaps_df),
                handicaps_df.iloc[0]['venue'],
                f"{handicaps_df.iloc[0]['handicap_factor']:.3f}",
                handicaps_df.iloc[-1]['venue'],
                f"{handicaps_df.iloc[-1]['handicap_factor']:.3f}",
                f"{handicaps_df['handicap_factor'].max() - handicaps_df['handicap_factor'].min():.3f}",
            ]
        })
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    print(f"✓ Excel file created: {output_file}")


def main():
    # Load data
    handicaps_file = Path('.tmp/venue_handicaps.csv')
    stats_file = Path('.tmp/venue_summary_stats.csv')
    
    if not handicaps_file.exists():
        print(f"❌ Handicaps file not found: {handicaps_file}")
        print("   Run build_handicap_model.py first")
        return
    
    handicaps_df = pd.read_csv(handicaps_file)
    
    if stats_file.exists():
        stats_df = pd.read_csv(stats_file, index_col=0)
    else:
        print("⚠️  Venue statistics not found, skipping")
        stats_df = pd.DataFrame()
    
    print(f"Loaded {len(handicaps_df)} venue handicaps")
    
    # Try Google Sheets first
    if HAS_GSPREAD and Path(CREDENTIALS_PATH).exists():
        url = create_google_sheet(handicaps_df, stats_df)
        if url:
            print(f"\n✓ Report available at: {url}")
            return
    
    # Fallback to Excel
    output_file = Path('.tmp/venue_handicap_report.xlsx')
    export_to_excel(handicaps_df, stats_df, output_file)
    print(f"\n✓ Report saved to: {output_file}")


if __name__ == '__main__':
    main()
