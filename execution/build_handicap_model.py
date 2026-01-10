#!/usr/bin/env python3
"""
HYROX Venue Handicap Model Builder

Builds mixed-effects regression model to calculate venue handicap factors.

Usage:
    python build_handicap_model.py --input .tmp/cleaned_results.csv --output .tmp/venue_handicaps.csv
    python build_handicap_model.py --validate  # Run with cross-validation
"""

import argparse
import os
from pathlib import Path
from typing import Tuple, Dict

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
from dotenv import load_dotenv

# Try importing statsmodels for mixed-effects
try:
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    from statsmodels.regression.mixed_linear_model import MixedLM
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    print("⚠️  statsmodels not installed - will use simpler approach")


load_dotenv()

REFERENCE_VENUE = os.getenv('REFERENCE_VENUE', 'fastest')
MIN_ATHLETES_PER_VENUE = int(os.getenv('MIN_ATHLETES_PER_VENUE', '20'))
MIN_REPEAT_ATHLETES = int(os.getenv('MIN_REPEAT_ATHLETES', '10'))


def prepare_model_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare data for modeling.
    
    Filters to venues with sufficient sample size and athletes who
    competed at multiple venues.
    """
    print("Preparing model data...")
    
    # Filter venues with sufficient sample size
    venue_counts = df['venue'].value_counts()
    valid_venues = venue_counts[venue_counts >= MIN_ATHLETES_PER_VENUE].index
    df = df[df['venue'].isin(valid_venues)]
    print(f"  Venues with n≥{MIN_ATHLETES_PER_VENUE}: {len(valid_venues)}")
    
    # Count athletes at multiple venues
    athlete_venue_counts = df.groupby('athlete_id')['venue'].nunique()
    repeat_athletes = athlete_venue_counts[athlete_venue_counts >= 2].index
    
    print(f"  Repeat athletes (2+ venues): {len(repeat_athletes)}")
    
    if len(repeat_athletes) < MIN_REPEAT_ATHLETES:
        print(f"⚠️  Warning: Only {len(repeat_athletes)} repeat athletes found")
        print(f"    Mixed-effects model may not be reliable")
        print(f"    Consider using simpler percentile-based approach")
    
    return df, repeat_athletes


def build_mixed_effects_model(df: pd.DataFrame) -> Tuple[any, pd.DataFrame]:
    """
    Build mixed-effects regression model.
    
    Model: finish_time ~ venue + (1|athlete_id)
    
    Returns:
        Fitted model and venue effects DataFrame
    """
    print("\nBuilding mixed-effects model...")
    
    if not HAS_STATSMODELS:
        raise ImportError("statsmodels required for mixed-effects modeling")
    
    # Prepare formula
    # Use C() for categorical venue variable
    formula = 'finish_time_seconds ~ C(venue)'
    
    try:
        # Fit mixed-effects model with random intercept for athlete
        model = smf.mixedlm(formula, df, groups=df['athlete_id'])
        result = model.fit(method='lbfgs', maxiter=200)
        
        print("  Model converged successfully")
        print(f"  Log-likelihood: {result.llf:.2f}")
        print(f"  AIC: {result.aic:.2f}")
        
        # Extract venue effects
        venue_effects = extract_venue_effects(result, df)
        
        return result, venue_effects
        
    except Exception as e:
        print(f"❌ Model fitting failed: {e}")
        print("   Falling back to simpler approach...")
        return None, None


def extract_venue_effects(model_result, df: pd.DataFrame) -> pd.DataFrame:
    """Extract venue fixed effects from model."""
    
    # Get fixed effects parameters
    params = model_result.params
    std_errors = model_result.bse
    pvalues = model_result.pvalues
    conf_int = model_result.conf_int()
    
    # Extract venue effects (parameters starting with 'C(venue)')
    venue_params = {k: v for k, v in params.items() if k.startswith('C(venue)')}
    
    # Build venue effects dataframe
    venue_effects = []
    
    # Get reference venue (first in alphabetical order by default)
    all_venues = sorted(df['venue'].unique())
    reference_venue = all_venues[0]
    
    # Reference venue has effect = 0 (baseline)
    venue_effects.append({
        'venue': reference_venue,
        'effect': 0.0,
        'std_error': 0.0,
        'p_value': 1.0,
        'ci_low': 0.0,
        'ci_high': 0.0,
    })
    
    # Other venues
    for param_name, effect in venue_params.items():
        # Extract venue name from parameter
        venue = param_name.replace('C(venue)[T.', '').replace(']', '')
        
        venue_effects.append({
            'venue': venue,
            'effect': effect,
            'std_error': std_errors[param_name],
            'p_value': pvalues[param_name],
            'ci_low': conf_int.loc[param_name, 0],
            'ci_high': conf_int.loc[param_name, 1],
        })
    
    effects_df = pd.DataFrame(venue_effects)
    
    return effects_df


def calculate_handicap_factors(venue_effects: pd.DataFrame, df: pd.DataFrame,
                               reference: str = 'fastest') -> pd.DataFrame:
    """
    Convert venue effects to handicap factors.
    
    Args:
        venue_effects: DataFrame with venue effects from model
        df: Original data for sample sizes
        reference: Reference venue normalization ('fastest', 'median', or venue name)
    
    Returns:
        DataFrame with handicap factors
    """
    print(f"\nCalculating handicap factors (reference: {reference})...")
    
    # Add sample sizes
    venue_counts = df['venue'].value_counts()
    venue_effects['sample_size'] = venue_effects['venue'].map(venue_counts)
    
    # Determine reference value
    if reference == 'fastest':
        ref_effect = venue_effects['effect'].min()
    elif reference == 'median':
        ref_effect = venue_effects['effect'].median()
    else:
        # Specific venue name
        ref_row = venue_effects[venue_effects['venue'] == reference]
        if len(ref_row) == 0:
            print(f"⚠️  Reference venue '{reference}' not found, using fastest")
            ref_effect = venue_effects['effect'].min()
        else:
            ref_effect = ref_row['effect'].iloc[0]
    
    # Calculate mean time for normalization
    mean_time = df['finish_time_seconds'].mean()
    
    # Handicap factor = (venue_effect - ref_effect) / mean_time + 1.0
    # Positive effect = slower venue = handicap > 1.0
    venue_effects['handicap_factor'] = ((venue_effects['effect'] - ref_effect) / mean_time) + 1.0
    
    # Calculate confidence intervals for handicap
    venue_effects['handicap_ci_low'] = ((venue_effects['ci_low'] - ref_effect) / mean_time) + 1.0
    venue_effects['handicap_ci_high'] = ((venue_effects['ci_high'] - ref_effect) / mean_time) + 1.0
    
    # Sort by handicap (easiest to hardest)
    venue_effects = venue_effects.sort_values('handicap_factor')
    
    print(f"  Handicap range: {venue_effects['handicap_factor'].min():.3f} to {venue_effects['handicap_factor'].max():.3f}")
    print(f"  Mean handicap: {venue_effects['handicap_factor'].mean():.3f}")
    
    return venue_effects


def simple_percentile_approach(df: pd.DataFrame) -> pd.DataFrame:
    """
    Simpler approach using percentile normalization.
    
    Used when insufficient repeat athletes for mixed-effects model.
    """
    print("\nUsing percentile-based approach...")
    
    venue_stats = []
    
    for venue in df['venue'].unique():
        venue_data = df[df['venue'] == venue]['finish_time_seconds']
        
        if len(venue_data) < MIN_ATHLETES_PER_VENUE:
            continue
        
        # Calculate median percentile relative to global distribution
        global_median = df['finish_time_seconds'].median()
        venue_median = venue_data.median()
        
        # Handicap based on median difference
        handicap = venue_median / global_median
        
        venue_stats.append({
            'venue': venue,
            'handicap_factor': handicap,
            'sample_size': len(venue_data),
            'median_time': venue_median,
            'std_error': venue_data.std() / np.sqrt(len(venue_data)),
            'p_value': np.nan,  # Not applicable for this approach
        })
    
    handicaps = pd.DataFrame(venue_stats).sort_values('handicap_factor')
    
    print(f"  Calculated handicaps for {len(handicaps)} venues")
    
    return handicaps


def validate_model(df: pd.DataFrame, handicaps: pd.DataFrame) -> Dict:
    """
    Validate model with cross-validation.
    
    Returns:
        Dictionary of validation metrics
    """
    print("\nValidating model...")
    
    # Merge handicaps with data
    df_with_handicap = df.merge(handicaps[['venue', 'handicap_factor']], on='venue')
    
    # Calculate adjusted times
    df_with_handicap['adjusted_time'] = df_with_handicap['finish_time_seconds'] / df_with_handicap['handicap_factor']
    
    # For repeat athletes, check if variance decreases after adjustment
    athlete_venue_counts = df_with_handicap.groupby('athlete_id')['venue'].nunique()
    repeat_athletes = athlete_venue_counts[athlete_venue_counts >= 2].index
    
    if len(repeat_athletes) > 0:
        repeat_data = df_with_handicap[df_with_handicap['athlete_id'].isin(repeat_athletes)]
        
        # Variance before adjustment
        raw_variance = repeat_data.groupby('athlete_id')['finish_time_seconds'].var().mean()
        
        # Variance after adjustment
        adjusted_variance = repeat_data.groupby('athlete_id')['adjusted_time'].var().mean()
        
        variance_reduction = (raw_variance - adjusted_variance) / raw_variance
        
        print(f"  Raw time variance (repeat athletes): {raw_variance:.0f}")
        print(f"  Adjusted time variance: {adjusted_variance:.0f}")
        print(f"  Variance reduction: {variance_reduction:.1%}")
        
        return {
            'raw_variance': raw_variance,
            'adjusted_variance': adjusted_variance,
            'variance_reduction': variance_reduction,
            'num_repeat_athletes': len(repeat_athletes),
        }
    else:
        print("  No repeat athletes for validation")
        return {}


def plot_diagnostics(handicaps: pd.DataFrame, output_dir: Path):
    """Generate diagnostic plots."""
    print("\nGenerating diagnostic plots...")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Plot 1: Handicap factors with confidence intervals
    fig, ax = plt.subplots(figsize=(12, 8))
    
    x = range(len(handicaps))
    ax.barh(x, handicaps['handicap_factor'], color='steelblue')
    
    # Add confidence intervals if available
    if 'handicap_ci_low' in handicaps.columns:
        xerr_low = handicaps['handicap_factor'] - handicaps['handicap_ci_low']
        xerr_high = handicaps['handicap_ci_high'] - handicaps['handicap_factor']
        ax.errorbar(handicaps['handicap_factor'], x, 
                   xerr=[xerr_low, xerr_high],
                   fmt='none', color='black', capsize=3)
    
    ax.set_yticks(x)
    ax.set_yticklabels(handicaps['venue'])
    ax.set_xlabel('Handicap Factor')
    ax.set_title('HYROX Venue Handicap Factors\n(1.0 = reference, >1.0 = harder venue)')
    ax.axvline(x=1.0, color='red', linestyle='--', label='Reference')
    ax.legend()
    plt.tight_layout()
    
    plt.savefig(output_dir / 'handicap_factors.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  Saved: {output_dir / 'handicap_factors.png'}")


def main():
    parser = argparse.ArgumentParser(description='Build HYROX venue handicap model')
    parser.add_argument('--input', type=Path, default=Path('.tmp/cleaned_results.csv'))
    parser.add_argument('--output', type=Path, default=Path('.tmp/venue_handicaps.csv'))
    parser.add_argument('--validate', action='store_true', help='Run validation')
    parser.add_argument('--simple', action='store_true', 
                       help='Force simple percentile approach')
    
    args = parser.parse_args()
    
    # Load data
    if not args.input.exists():
        print(f"❌ Input file not found: {args.input}")
        return
    
    df = pd.read_csv(args.input)
    print(f"Loaded {len(df)} records")
    
    # Prepare data
    df_model, repeat_athletes = prepare_model_data(df)
    
    # Build model
    if args.simple or len(repeat_athletes) < MIN_REPEAT_ATHLETES or not HAS_STATSMODELS:
        handicaps = simple_percentile_approach(df_model)
    else:
        model_result, venue_effects = build_mixed_effects_model(df_model)
        
        if model_result is None:
            # Fallback to simple approach
            handicaps = simple_percentile_approach(df_model)
        else:
            handicaps = calculate_handicap_factors(venue_effects, df_model, REFERENCE_VENUE)
    
    # Validate
    if args.validate:
        metrics = validate_model(df_model, handicaps)
    
    # Save results
    args.output.parent.mkdir(parents=True, exist_ok=True)
    handicaps.to_csv(args.output, index=False)
    print(f"\n✓ Handicap factors saved to {args.output}")
    
    # Generate plots
    plot_diagnostics(handicaps, Path('.tmp/eda_plots'))
    
    # Print summary
    print("\n" + "="*60)
    print("VENUE HANDICAP FACTORS")
    print("="*60)
    print(handicaps.to_string(index=False))
    print("="*60)


if __name__ == '__main__':
    main()
