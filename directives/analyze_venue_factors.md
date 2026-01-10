# Analyze Venue Factors

## Goal
Perform exploratory data analysis to understand how venue characteristics (run loop length, Roxzone distance, station spacing, congestion) affect athlete performance and identify key factors for the handicap model.

## Inputs
- `.tmp/cleaned_results.csv` - Cleaned HYROX results dataset
- Venue layout specifications (if available)

## Tools/Scripts
- `execution/venue_eda.py` - Exploratory data analysis script

## Process

### 1. Run Venue Analysis
Execute the EDA script:
```bash
cd /Users/dutch/Workspace/hyroxranks
python execution/venue_eda.py --input .tmp/cleaned_results.csv --output-dir .tmp/eda_plots
```

### 2. Analysis Components

#### Venue-Level Statistics
For each venue, calculate:
- Mean, median, std dev of finish times
- Sample size (number of athletes)
- Distribution of times (histogram, box plot)
- Percentile rankings (10th, 25th, 50th, 75th, 90th)

#### Cross-Venue Comparison
- Compare time distributions across venues
- Identify consistently faster/slower venues
- Control for athlete ability using repeat competitors

#### Venue Characteristics Analysis
If venue layout data is available:
- Correlate run loop length with total run time
- Analyze Roxzone distance impact on transition times
- Assess congestion effects (event size vs. average time)

#### Repeat Athlete Analysis
For athletes who competed at multiple venues:
- Calculate within-athlete variance across venues
- Identify venues where same athletes perform better/worse
- This is critical for isolating venue effects from athlete ability

## Expected Outputs

### Data Files
- `.tmp/venue_summary_stats.csv` - Summary statistics per venue
- `.tmp/repeat_athlete_analysis.csv` - Performance variance for multi-venue athletes

### Visualizations (saved to `.tmp/eda_plots/`)
- `venue_time_distributions.png` - Box plots of finish times by venue
- `venue_comparison_heatmap.png` - Heatmap of mean times across venues
- `repeat_athlete_variance.png` - Scatter plot showing athlete performance across venues
- `venue_sample_sizes.png` - Bar chart of athlete counts per venue
- `time_by_venue_characteristic.png` - Scatter plots (if layout data available)

### Analysis Report
- `.tmp/eda_report.txt` - Text summary of key findings

## Edge Cases & Learnings

### Small Sample Sizes
- Some venues may have <20 athletes - flag these for exclusion
- Use minimum sample size threshold from `.env` config

### Outlier Events
- Special events (celebrity races, charity) may skew results
- Filter by division to ensure competitive comparisons

### Temporal Effects
- Venue layouts may change over time (different halls, reconfigurations)
- Consider event_date in analysis - may need to treat same venue at different times as separate

### Missing Split Data
- Not all events have run/workout/roxzone splits
- Focus on total finish time as primary metric
- Use splits for validation where available

### Athlete Ability Confounding
- Faster athletes may self-select into certain events/venues
- This is why repeat athlete analysis is crucial
- Look for within-athlete venue effects, not just between-athlete

## Success Criteria
- Summary statistics generated for all venues with >20 athletes
- At least 50 repeat athletes identified for model validation
- Clear visualization of venue-to-venue variation
- Identification of at least 3 venue characteristics that correlate with performance
- EDA report highlights venues with statistically significant differences
