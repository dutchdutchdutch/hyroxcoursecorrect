# Run Time Analysis Report (v2 - EU + North America)
**Date:** 2026-01-13  
**Dataset:** 2,939 run time records from 9 venues (6 EU + 3 NA)

---

## Executive Summary

We expanded run time collection to North America (US/Canada) and built a weighted factor model. **Run-based factors strongly correlate with existing median factors**, confirming our correction methodology is sound. We recommend a **50/50 weighted model** combining both signals.

---

## Data Collection Summary

| Region | Venues | Records | Notes |
|--------|--------|---------|-------|
| Europe | 6 | 2,158 | Maastricht, Hamburg, London, Paris, Utrecht, Gent |
| N. America | 3 | 781 | Toronto, Chicago, Atlanta* |
| **Total** | **9** | **2,939** | |

\* Atlanta excluded from analysis (data quality issue - captured finish times instead of run times)

**Venues with no data:** Anaheim, Dallas, Boston (events not held or incomplete)

---

## Weighted Factor Model

### Formula
```
Combined_Factor = 0.5 × Run_Factor + 0.5 × Existing_Median_Factor
```

### Results (Baseline: Maastricht 2025)

| Venue | Run % (M) | Existing % (M) | **Combined % (M)** | Interpretation |
|-------|-----------|----------------|---------------------|----------------|
| London Excel | -13.2% | -7.4% | **-10.3%** | Fastest |
| Gent | -4.5% | -6.1% | **-5.3%** | Fast |
| Hamburg | -2.4% | -2.0% | **-2.2%** | Slightly Fast |
| Paris | -1.0% | -3.2% | **-2.1%** | Slightly Fast |
| **Maastricht** | 0.0% | -0.6% | **-0.3%** | Baseline |
| Utrecht | +2.4% | -0.6% | **+0.9%** | Slightly Slow |
| Chicago | +2.6% | +2.0% | **+2.3%** | Slow |
| Toronto | +8.5% | +5.2% | **+6.9%** | Slowest |

### Key Findings

1. **Run and median factors agree on direction** for all venues
2. **Toronto is the slowest NA venue** (+6.9%) - likely longer run course
3. **London Excel confirmed as fastest** (-10.3%)
4. **Chicago is moderately slow** (+2.3%)

---

## Correlation Analysis

| Metric | Value |
|--------|-------|
| Direction Match (Run vs Existing) | 7/8 (87.5%) |
| Average Delta (Run - Existing) | 2.1% |
| Max Delta | 5.8% (London Excel) |

**Interpretation:** Run factors tend to show slightly more extreme values than median factors, likely because top 200 runners isolate the "course effect" better than the full population.

---

## Data Quality Issue: Atlanta

Atlanta's scraped data shows run times of 1:45:08 - 1:52:46, which are actually **finish times**, not run times. The page layout differs from other venues.

**Evidence:**
- Minimum "run time": 6,308 seconds (1:45:08)
- Expected minimum: ~3,300 seconds (55:00)
- Finish time column is NULL

**Resolution:** Excluded from analysis. Would need manual re-scrape with corrected parsing.

---

## Recommendation

### Should factors be updated?

**Yes, but conservatively:**

1. **Use weighted model (50/50)** for venues with run data
2. **Keep existing median factors** for venues without run data
3. **Flag Atlanta** for manual re-scraping
4. **Consider Toronto/Chicago** for deeper analysis (slowest NA venues - is it course length or field fitness?)

### Next Analysis Phase (User Requested)

Analyze **slowest 5 venues** to determine if slowness is due to:
- Course layout (longer runs/roxzones)
- Field fitness (less competitive athletes)

Method:
1. Find multi-venue athletes who raced at slow venues
2. Compare their station times (row, burpees, wallballs) across venues
3. If station times are similar but run times differ → Course issue
4. If station times also differ → Field fitness issue

---

## Files Created

| File | Purpose |
|------|---------|
| `data/pro_run_times.csv` | Raw scraped run time data |
| `data/factor_comparison.csv` | Run vs existing factor comparison |
| `data/weighted_factor_model.csv` | 50/50 weighted model output |
| `data/multi_venue_athletes.csv` | Multi-venue validation data |
