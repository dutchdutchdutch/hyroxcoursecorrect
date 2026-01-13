# Implementation Plan: Field Strength Analysis for Slow Venues

## Objective
Determine whether Johannesburg, Singapore, Mumbai, and Delhi are slow due to **course layout** or **field strength** (less fit athletes).

---

## Execution Priority

| Priority | Analysis | Rationale |
|----------|----------|-----------|
| **1** | Multi-venue athletes | Direct comparison eliminates confounding variables |
| **2** | Station-based sampling | Measures field fitness at depth intervals |
| **3** | Pro Top 10 comparison | Validates that elite athletes are globally competitive |

---

## Phase 1: Multi-Venue Athlete Analysis

### Goal
Find athletes who competed at BOTH a slow venue (Johannesburg/Singapore/Mumbai/Delhi) AND a fast/average venue (London/Hamburg/Paris/etc.). Compare their finish times.

### Method
1. Query existing `race_results` DB for athletes by name + nationality
2. Identify those with appearances at slow + fast venues
3. Calculate time delta and compare to expected venue correction

### Output
```csv
athlete_name, nationality, slow_venue, slow_time, fast_venue, fast_time, observed_delta, expected_delta
```

### Interpretation
- If `observed_delta ≈ expected_delta` → Field strength issue (athlete performed similarly relative to venue)
- If `observed_delta >> expected_delta` → Environmental/course issue (athlete struggled more than expected)

---

## Phase 2: Station-Based Sampling

### Goal
Compare workout station times at depth intervals (50th, 100th, 150th, 200th) across venues.

### Stations
- Row (Station 4)
- Burpee Broad Jump (Station 5)
- Kettlebell Carry (Station 7, but actually Farmers Carry, will verify)
- Wall Balls (Station 8)

### URL Pattern
```
https://results.hyrox.com/season-8/?event_main_group={VENUE}&ranking=time_{STATION_CODE}&num_results=100&search[sex]=M
```

Need to discover station codes (`time_40` = Row, `time_41` = Burpees, etc.)

### Sampling Strategy
| Rank | Rationale |
|------|-----------|
| 50 | Top competitive tier |
| 100 | Upper mid-pack |
| 150 | Mid-pack |
| 200 | Lower mid-pack |

### Data Collection
- Scrape 4 stations × 4 venues × 2 genders × 200 results = ~6,400 records
- Actually only need specific ranks, so ~64 data points per venue

### Output
```csv
venue, station, gender, rank_50_time, rank_100_time, rank_150_time, rank_200_time
```

---

## Phase 3: Pro Top 10 Analysis

### Goal
Verify that Pro athletes at slow venues have finish times within global range.

### Method
1. Scrape Pro Top 10 for Johannesburg, Singapore, Mumbai, Delhi
2. Compare to Pro Top 10 at London, Hamburg, Paris
3. If Pro times are similar → Course is fine, field depth is the issue

---

## Scripts to Create

| Script | Purpose |
|--------|---------|
| `execution/analyze_multi_venue_field.py` | Query DB for multi-venue athletes at slow venues |
| `execution/scrape_station_times.py` | Scrape station-based leaderboards |
| `execution/analyze_field_strength.py` | Compare station times across venues |

---

## Data Requirements

### Slow Venues to Analyze
- 2025 Johannesburg
- 2025 Singapore
- 2025 Mumbai
- 2025 Delhi

### Reference Venues (from existing data)
- London Excel 2025
- Hamburg 2025
- Paris 2025
- Maastricht 2025

---

## Verification Plan

### Phase 1 Verification
- Run multi-venue query on DB
- Expect: List of athletes with times at both slow and fast venues
- Manual check: Spot-check 3 athletes on HYROX website to confirm data accuracy

### Phase 2 Verification
- After scraping, compare fastest station time at slow venue to fastest at fast venue
- Expect: Fastest times should be similar (Pro/elite athletes)
- If fastest is also much slower → Course layout issue
- If only depth is slower → Field strength issue

---

## Estimated Timeline
- Phase 1: 30 min (DB query only)
- Phase 2: 1-2 hours (scraping)
- Phase 3: 30 min (Pro subset)
