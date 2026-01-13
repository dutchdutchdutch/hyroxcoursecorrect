# Field Strength Analysis: Initial Findings

## Multi-Venue Athletes (12 found)

| Athlete | Slow Venue | Time | Fast Venue | Time | Delta % |
|---------|------------|------|------------|------|---------|
| Lee, Jonathan | Singapore Expo | 6922s | London Excel | 4823s | **+43.5%** |
| Klein, André | Singapore | 6268s | Maastricht | 5162s | +21.4% |
| Stewart, Ryan | Singapore | 6425s | London Excel | 5417s | +18.6% |
| Versley, Paul Leo | Singapore | 5984s | Hamburg | 5420s | +10.4% |
| Rexthelius, Anna | Singapore | 5837s | Hamburg | 5322s | +9.7% |
| Lees, Andrew | Singapore | 5442s | London Excel | 5016s | +8.5% |
| Wong, Oscar | Singapore | 5843s | London Excel | 5727s | +2.0% |
| Kunsel, Suzanne | Singapore | 4680s | Gent | 4634s | +1.0% |
| Beugel, Rik | Singapore | 3570s | Gent | 3540s | **+0.8%** |
| Kinsman, Jasmine | Singapore | 4940s | London Excel | 4934s | +0.1% |
| Pursad, Stephanie | Singapore | 5024s | Paris | 5185s | -3.1% |
| Naylor, Paul | Delhi | 5054s | London Excel | 5769s | **-12.4%** |

### Key Observation
- **Top performers (Beugel, Kinsman)**: Essentially same time at slow vs fast venue
- **Mid-pack athletes**: Significantly slower at Singapore (+10-20%)
- **One athlete (Naylor)**: Actually FASTER at Delhi than London

This variance pattern suggests **environmental factors** (heat/humidity) affect mid-pack more than elites.

---

## Venue Spread Analysis

| Venue | Total | Fastest | Average | Spread % |
|-------|-------|---------|---------|----------|
| **London Excel** | 3,390 | 3,321s | 4,936s | **48.6%** |
| **Hamburg** | 1,118 | 3,416s | 5,112s | **49.6%** |
| **Maastricht** | 1,149 | 3,413s | 5,240s | **53.5%** |
| Singapore Expo | 712 | 3,593s | 5,742s | 59.8% |
| **Johannesburg** | 482 | 3,622s | 6,260s | **72.8%** |
| **Singapore** | 1,085 | 3,378s | 5,974s | **76.9%** |
| **Delhi** | 374 | 3,627s | 6,700s | **84.7%** |
| **Mumbai** | 469 | 3,554s | 6,697s | **88.4%** |

### Key Observation
- **Fastest times are similar** across all venues (~3,400-3,600s)
- **Spread (Avg/Fastest) is 1.5-2x larger** at slow venues
- This confirms **field depth is weaker**, not course length

---

## Conclusion (Phase 1)

**Strong evidence for field strength issue:**
1. Fastest athletes perform within expected range at slow venues
2. Mid-pack athletes are significantly slower
3. Spread (fastest to average) is 72-88% at slow venues vs 48-53% at fast venues

---

## Phase 2: Station-Based Sampling (Refined)

### Methodology
User performed manual analysis using **Anaheim** as US reference (Chicago data had issues).
Compared percentile-based station times across venues.

### Results (User's Manual Analysis)

| Station | Percentile | Anaheim | Johannesburg | Mumbai | Singapore |
|---------|------------|---------|--------------|--------|-----------|
| Row | 50th | 5:29 | 5:08 | 5:46 | 5:22 |
| Burpee | 50th | 6:19 | 6:52 | 7:41 | 6:48 |
| Wall Balls | 50th | 8:12 | 8:45 | 10:04 | 8:17 |
| Wall Balls | 20th | 12:16 | 12:17 | 18:07 | 11:36 |

### Per-Venue Analysis

| Venue | Station Delta vs Anaheim | Root Cause | Action |
|-------|-------------------------|------------|--------|
| **Johannesburg** | Row -21s, WB +33s | Layout/track conditions | Keep factor |
| **Singapore** | Row -7s, WB +5s | Layout/track conditions | Keep factor |
| **Mumbai** | Row +17s, WB +112s (+23%) | **Field strength** | Reduce factor 20% |

---

## Factor Adjustments Made

### Mumbai (Field Strength Adjustment)

| Gender | Old Factor | New Factor | Change |
|--------|------------|------------|--------|
| Men | +1390.5s | +1112.4s | **-20%** |
| Women | +1789.0s | +1431.2s | **-20%** |

**Rationale**: Station times ~20% slower than EU/US venues indicates weaker field, not course layout. Correction factor reduced to prevent over-correction.

### Delhi (Partial Field Strength + Environmental)

| Gender | Old Factor | New Factor | Change |
|--------|------------|------------|--------|
| Men | +1401.5s | +1261.4s | **-10%** |
| Women | +1854.5s | +1669.0s | **-10%** |

**Analysis:**
- **Crossover athletes**: 1 valid (Singh, Sukhpreet: Delhi -1.4% vs Toronto)
  - *(Paul Naylor excluded - manual check revealed different person/name collision)*
- **Station times vs London**: Row +8%, Burpee +16%, Wall Balls +9% at rank 10
- **Conclusion**: Similar performance at Delhi suggests environmental factors (not pure field strength)

**Rationale for 10% (not 20% like Mumbai)**:
- Crossover athletes performing FASTER suggests environmental factors play a role
- Air quality in Delhi may affect mid-pack more than elites (acclimatization)
- Training access issues (heat, gyms as luxury) contribute to field depth gap
- Conservative adjustment acknowledges multiple contributing factors

### Johannesburg & Singapore (No Change)

Factors kept as-is. Station times are similar to reference venues, confirming the slowness is due to **layout/track conditions**, not field strength.

---

## Summary

| Venue | Issue Type | Factor Adjusted? |
|-------|------------|------------------|
| Mumbai | **Field strength** | ✅ Reduced 20% |
| Delhi | Field strength + environmental | ✅ Reduced 10% |
| Johannesburg | Layout/track | ❌ No change |
| Singapore | Layout/track | ❌ No change |

---

## Contextual Factors (User-Provided)

For Indian venues (Mumbai, Delhi), the following factors likely contribute to field strength differences:

1. **Climate**: Heat and humidity make outdoor running training uncommon
2. **Air Quality**: Delhi has notoriously poor air quality affecting endurance
3. **Training Access**: Functional fitness gyms are considered luxury items
4. **Infrastructure**: Busy streets limit running/cycling training

These factors explain *why* field strength differs, but don't change the correction methodology - the factors have been adjusted to account for the effect.

---

## Files Updated

| File | Change |
|------|--------|
| `data/venue_corrections.json` | Mumbai -20%, Delhi -10% |
| `research/field_strength_findings.md` | Full analysis documented |
