import pandas as pd
import statistics

# Load the data
df = pd.read_csv('data/hyrox_9venues_100each.csv')

# Calculate median times for each venue by gender
results = {}

for venue in df['venue'].unique():
    venue_df = df[df['venue'] == venue]
    
    # Get median times
    men_times = venue_df[venue_df['gender'] == 'M']['finish_seconds'].tolist()
    women_times = venue_df[venue_df['gender'] == 'W']['finish_seconds'].tolist()
    
    if men_times and women_times:
        men_median = sorted(men_times)[len(men_times) // 2]
        women_median = sorted(women_times)[len(women_times) // 2]
        
        results[venue] = {
            'men_median': men_median,
            'women_median': women_median
        }

# Find reference venue (London Excel 2025 - fastest overall)
reference_venue = 'London Excel 2025'
men_reference = results[reference_venue]['men_median']
women_reference = results[reference_venue]['women_median']

# Calculate handicaps for each gender
print('Venue Handicap Analysis by Gender')
print('=' * 80)
print(f"{'Venue':<25} {'Men Handicap':>12} {'Women Handicap':>15} {'Difference':>12}")
print('-' * 80)

for venue in sorted(results.keys(), key=lambda v: results[v]['men_median']):
    men_handicap = results[venue]['men_median'] / men_reference
    women_handicap = results[venue]['women_median'] / women_reference
    difference = abs(men_handicap - women_handicap)
    
    print(f'{venue:<25} {men_handicap:>12.4f} {women_handicap:>15.4f} {difference:>12.4f}')

print()
print('Analysis:')
print('-' * 80)

# Calculate correlation
men_handicaps = [results[v]['men_median'] / men_reference for v in results.keys()]
women_handicaps = [results[v]['women_median'] / women_reference for v in results.keys()]

differences = [abs(m - w) for m, w in zip(men_handicaps, women_handicaps)]
avg_diff = statistics.mean(differences)
max_diff = max(differences)

print(f'Average difference between gender handicaps: {avg_diff:.4f} ({avg_diff*100:.2f}%)')
print(f'Maximum difference: {max_diff:.4f} ({max_diff*100:.2f}%)')
print()

if avg_diff < 0.02:  # Less than 2% difference
    print('✓ CONCLUSION: Venue difficulty is CONSISTENT across genders.')
    print('  The relative differences between venues are very similar for men and women.')
    print('  A single handicap factor is appropriate for both genders.')
else:
    print('✗ CONCLUSION: Venue difficulty varies SIGNIFICANTLY by gender.')
    print('  Separate handicap factors may be needed for men and women.')
