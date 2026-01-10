# Calculate Venue Handicap Factors

## Goal
Build a statistical model to calculate venue-specific handicap factors that isolate venue difficulty from athlete ability, enabling fair cross-venue performance comparisons.

## Inputs
- `.tmp/cleaned_results.csv` - Cleaned results dataset
- `.tmp/venue_summary_stats.csv` - Venue statistics from EDA
- Configuration from `.env` (reference venue, minimum thresholds)

## Tools/Scripts
- `execution/build_handicap_model.py` - Statistical modeling script
- `execution/apply_handicap.py` - Apply handicaps to athlete times

## Process

### 1. Build the Handicap Model

Run the modeling script:
```bash
cd /Users/dutch/Workspace/hyroxranks
python execution/build_handicap_model.py --input .tmp/cleaned_results.csv --output .tmp/venue_handicaps.csv
```

### 2. Modeling Approach

#### Mixed-Effects Regression
Use statsmodels to fit a linear mixed-effects model:

```python
# Model specification
# finish_time ~ venue + (1|athlete_id)
# 
# Fixed effects: venue (captures venue difficulty)
# Random effects: athlete_id (captures individual ability)
```

**CRITICAL REQUIREMENT**: This approach ONLY works with verified repeat athletes who have unique identifiers (bib number or DOB). Athletes matched by name alone are NOT included in the random effects to prevent false matches.

This approach:
- Controls for athlete ability using random intercepts
- Isolates venue-specific effects as fixed effects
- Requires athletes who competed at multiple venues WITH unique IDs
- Falls back to simpler percentile approach if insufficient verified repeat athletes

#### Handicap Factor Calculation
1. Extract venue fixed effects from the model
2. Normalize to reference venue (from `.env` config):
   - `fastest`: Set fastest venue handicap = 1.00
   - `median`: Set median venue handicap = 1.00
   - Specific venue name: Set that venue = 1.00
3. Calculate handicap factors:
   - Handicap = (Venue Effect / Reference Effect)
   - Values > 1.00 = harder venue
   - Values < 1.00 = easier venue

#### Model Validation
- Cross-validation: Hold out 20% of data, test predictions
- R² score: Should be >0.70 for good fit
- Residual analysis: Check for normality, homoscedasticity
- Venue effect significance: p-values < 0.05

### 3. Apply Handicaps

Run the application script:
```bash
python execution/apply_handicap.py --results .tmp/cleaned_results.csv --handicaps .tmp/venue_handicaps.csv --output .tmp/adjusted_results.csv
```

Calculation:
```python
adjusted_time = raw_time / venue_handicap
```

Example:
- Athlete runs 1:15:00 at a venue with handicap 1.05 (5% harder)
- Adjusted time = 1:15:00 / 1.05 = 1:11:26
- This represents equivalent performance at the reference venue

## Expected Outputs

### Model Outputs
- `.tmp/venue_handicaps.csv` - Handicap factors with columns:
  - `venue` - Venue name
  - `handicap_factor` - Multiplicative adjustment (1.00 = reference)
  - `std_error` - Standard error of estimate
  - `confidence_interval_low` - 95% CI lower bound
  - `confidence_interval_high` - 95% CI upper bound
  - `sample_size` - Number of results at this venue
  - `p_value` - Statistical significance

### Model Diagnostics
- `.tmp/model_diagnostics.txt` - Model fit statistics
- `.tmp/eda_plots/residual_plot.png` - Residual analysis
- `.tmp/eda_plots/qq_plot.png` - Q-Q plot for normality
- `.tmp/eda_plots/predicted_vs_actual.png` - Model predictions

### Adjusted Results
- `.tmp/adjusted_results.csv` - All results with added columns:
  - `venue_handicap` - Applied handicap factor
  - `adjusted_time_seconds` - Handicap-adjusted finish time
  - `adjusted_rank_overall` - Re-ranking based on adjusted times

## Edge Cases & Learnings

### Insufficient Repeat Athletes
- Mixed-effects models require athletes at multiple venues
- If <50 repeat athletes: Fall back to simpler approach
  - Use percentile normalization instead
  - Calculate venue difficulty as median percentile deviation

### Venue Sample Size
- Exclude venues with <20 athletes (unreliable estimates)
- Flag venues with <50 athletes as "low confidence"

### Extreme Handicap Values
- Sanity check: Handicaps should be in range [0.90, 1.10]
- If outside this range, investigate data quality issues
- May indicate venue layout changes or data errors

### Model Convergence
- Mixed-effects models can fail to converge with sparse data
- If convergence issues: Increase max iterations or simplify model
- Consider Bayesian approach (PyMC3) for better handling of uncertainty

### Time-Varying Venue Effects
- If same venue shows different effects over time:
  - Treat as separate venues (venue + year)
  - Or include temporal random effect

## Success Criteria
- Model converges successfully
- R² > 0.70 on validation set
- All venue effects statistically significant (p < 0.05)
- Handicap factors within reasonable range (0.90-1.10)
- Adjusted rankings make intuitive sense for known athletes
- At least 80% of venues have confidence intervals <0.03 wide
