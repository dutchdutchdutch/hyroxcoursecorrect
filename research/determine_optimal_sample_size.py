
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

DATA_FILE = Path('research/data/full_leaderboards.csv')
OUTPUT_MD = Path('research/sampling_strategy_recommendation.md')

def load_data():
    if not DATA_FILE.exists():
        print(f"File not found: {DATA_FILE}")
        return None
    return pd.read_csv(DATA_FILE)

def calculate_medians(df):
    """Calculate true medians for each group."""
    return df.groupby(['venue', 'gender'])['finish_seconds'].median()

def simulate_sampling(df, true_medians):
    results = []
    
    strategies = [
        ('Top 50', lambda d: d.nsmallest(50, 'finish_seconds')),
        ('Top 100', lambda d: d.nsmallest(100, 'finish_seconds')),
        ('Top 200', lambda d: d.nsmallest(200, 'finish_seconds')),
        ('Top 500', lambda d: d.nsmallest(500, 'finish_seconds')),
        ('Top 10%', lambda d: d.nsmallest(int(len(d)*0.1), 'finish_seconds')),
        ('Top 25%', lambda d: d.nsmallest(int(len(d)*0.25), 'finish_seconds')),
        ('Top 50%', lambda d: d.nsmallest(int(len(d)*0.5), 'finish_seconds')),
        ('Top 80%', lambda d: d.nsmallest(int(len(d)*0.8), 'finish_seconds')),
        ('Every 5th', lambda d: d.iloc[::5]),
        ('Every 10th', lambda d: d.iloc[::10]),
        ('Every 20th', lambda d: d.iloc[::20]),
        ('Every 50th', lambda d: d.iloc[::50]),
        ('Every 100th', lambda d: d.iloc[::100]),
    ]
    
    # Simulate Page Sampling (Assuming 50 results per page)
    # We create a new valid sample by taking groups of 50
    def get_every_kth_page(df, k):
        chunks = [df.iloc[i:i+50] for i in range(0, len(df), 50)]
        sampled_chunks = chunks[::k]
        if not sampled_chunks: return pd.DataFrame()
        return pd.concat(sampled_chunks)

    page_strategies = [
        ('Every 2nd Page', lambda d: get_every_kth_page(d, 2)),
        ('Every 5th Page', lambda d: get_every_kth_page(d, 5)),
        ('Every 10th Page', lambda d: get_every_kth_page(d, 10)),
    ]
    
    strategies.extend(page_strategies)

    for (venue, gender), group in df.groupby(['venue', 'gender']):
        group = group.sort_values('finish_seconds').reset_index(drop=True)
        true_median = true_medians.loc[(venue, gender)]
        n_total = len(group)
        
        for name, strategy_func in strategies:
            sample = strategy_func(group)
            if len(sample) == 0:
                continue
                
            sample_median = sample['finish_seconds'].median()
            abs_error = abs(sample_median - true_median)
            pct_error = (abs_error / true_median) * 100
            
            results.append({
                'venue': venue,
                'gender': gender,
                'total_athletes': n_total,
                'strategy': name,
                'sample_size': len(sample),
                'true_median': true_median,
                'sample_median': sample_median,
                'abs_error_seconds': abs_error,
                'pct_error': pct_error
            })
            
    return pd.DataFrame(results)

def generate_report(results_df):
    summary = results_df.groupby('strategy').agg({
        'abs_error_seconds': ['mean', 'max'],
        'pct_error': ['mean', 'max'],
        'sample_size': 'mean'
    }).round(2)
    
    summary.columns = ['Mean Err (s)', 'Max Err (s)', 'Mean % Err', 'Max % Err', 'Avg Sample Size']
    summary = summary.sort_values('Mean % Err')
    
    markdown = "# HYROX Sampling Strategy Research\n\n"
    markdown += "## Objective\nTo determine the optimal scraping strategy (sample size/method) for calculating reliable course correction factors.\n\n"
    markdown += "## Methodology\n"
    markdown += "- **Datasets**: Full leaderboards for Anaheim 2025 and Maastricht 2025 (Men & Women Open).\n"
    markdown += "- **Ground Truth**: Median finish time of the full population.\n"
    markdown += "- **Metric**: Deviation from the true median (Absolute Seconds and Percentage).\n\n"
    
    
    markdown += "## Results Summary\n\n"
    # Manual markdown table to avoid tabulate dependency
    markdown += "| Strategy | " + " | ".join(summary.columns) + " |\n"
    markdown += "|---|" + "|".join(["---"] * len(summary.columns)) + "|\n"
    for idx, row in summary.iterrows():
        markdown += f"| {idx} | " + " | ".join(map(str, row.values)) + " |\n"
    markdown += "\n"
    
    markdown += "## Detailed Analysis\n\n"
    
    # Top N Analysis
    markdown += "### Top N vs Full Population\n"
    top_n_stats = results_df[results_df['strategy'].str.startswith('Top')].sort_values('pct_error')
    markdown += "Using only 'Top N' results (e.g., Top 100) consistently underestimates the median time (making the course look 'faster' than it is for the average athlete). "
    markdown += "This is because the distribution is right-skewed; the elite are much faster than the average.\n\n"
    
    # Systematic Analysis
    markdown += "### Systematic Sampling (Every Nth)\n"
    sys_stats = results_df[results_df['strategy'].str.startswith('Every')].sort_values('pct_error')
    markdown += "Systematic sampling (taking every Nth result) preserves the distribution shape and provides a much more accurate estimate of the median with fewer requests.\n\n"
    
    # Recommendation
    best_strategy = summary[summary['Max % Err'] < 1.0].iloc[0].name
    
    markdown += "## Recommendation\n\n"
    markdown += f"**Recommended Strategy: {best_strategy}**\n\n"
    markdown += f"Based on the analysis, **{best_strategy}** provides a reliable estimate with minimal error "
    markdown += "(typically < 1%). This balances data accuracy with scraping load.\n"
    
    if "Every" in best_strategy:
        markdown += "- **Why?** It captures the full range of athlete abilities without needing to process every single row.\n"
        markdown += "- **Implementation**: Scrape every page, but only store/process every Nth row? OR (better) scrape every Nth page if results are sorted by time (which is default).\n"
        markdown += "  - *Note*: If we can jump pages, we save requests. If not, we still download everything but calculate faster.\n"
    
    with open(OUTPUT_MD, 'w') as f:
        f.write(markdown)
    
    print(f"Report generated: {OUTPUT_MD}")
    print(summary)

def main():
    df = load_data()
    if df is None or df.empty:
        print("No data found.")
        return
        
    print(f"Loaded {len(df)} records.")
    true_medians = calculate_medians(df)
    results_df = simulate_sampling(df, true_medians)
    generate_report(results_df)

if __name__ == '__main__':
    main()
