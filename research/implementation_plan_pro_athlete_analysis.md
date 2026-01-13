# Implementation Plan: Pro Athlete Run Time Analysis (v3 - Simplified)

## Overview
Refine venue correction factors by analyzing **Pro athlete total run times** from leaderboards. The key insight: run times can be scraped directly from the results list (no detail page needed) when using the correct ranking parameter.

---

## Key Discovery: URL Structure for Run Times

### URL Pattern
```
https://results.hyrox.com/season-8/index.php?event={EVENT_ID}&ranking=time_49&num_results=100&search[sex]=M|W&page=1|2
```

### Critical Parameters
| Parameter | Value | Purpose |
|-----------|-------|---------|
| `event` | `HPRO_{City}{Year}_OVERALL` | Specific Pro division ID (e.g., `HPRO_Utrecht2025_OVERALL`) |
| `ranking` | `time_49` | **Sorts by Total Run** (not finish time) |
| `num_results` | `100` | Results per page |
| `search[sex]` | `M` or `W` | Gender filter |
| `page` | `1`, `2`, etc. | Pagination (101-200 on page 2) |

### Data Available on Run Total Leaderboard
- Rank (Division + Overall)
- Athlete Name
- Nationality
- Age Group
- **Run Total** ← Primary data point
- Finish Total (for reference)

---

## Pilot Scope: European Cluster

| Venue | Event ID Pattern |
|-------|------------------|
| Utrecht | `HPRO_Utrecht2025_OVERALL` |
| Maastricht | `HPRO_Maastricht2025_OVERALL` |
| Gent | `HPRO_Gent2025_OVERALL` |
| Hamburg | `HPRO_Hamburg25_OVERALL` |
| Frankfurt | `HPRO_Frankfurt2025_OVERALL` |
| London | `HPRO_LondonExcel2025_OVERALL` |
| Paris | `HPRO_Paris2025_OVERALL` |

> **Note**: Event IDs may vary slightly. The scraper should detect available divisions dynamically.

---

## Phase 1: Run Time Leaderboard Scraping

### Objective
Collect Top 200 Pro Men + Top 200 Pro Women **Total Run Times** per pilot venue.

### Implementation

| Component | Details |
|-----------|---------|
| **Script** | `execution/scrape_pro_run_times.py` (NEW) |
| **Method** | Selenium (pages are JS-rendered) |
| **Rate Limit** | 1.5 sec/page |
| **Storage** | `data/pro_run_times.csv` + SQLite `pro_run_times` table |

### Scraping Flow
```
1. Load event config (pilot venues)
2. For each venue:
   a. Build URL with event_id + ranking=time_49 + sex=M
   b. Scrape pages 1-2 (200 results)
   c. Build URL with sex=W
   d. Scrape pages 1-2 (200 results)
3. Parse table rows: Name, Nationality, Age Group, Run Total, Finish Total
4. Save to CSV + DB
```

### Output Schema
```csv
venue, gender, rank, athlete_name, nationality, age_group, run_total_seconds, finish_total_seconds
Utrecht 2025, M, 1, Martyn Paterson, GBR, 30-34, 1767, 4020
Utrecht 2025, M, 2, Jaime Geerts, NED, 25-29, 1769, 4760
```

---

## Phase 2: Multi-Venue Athlete Matching

### Objective
Identify athletes who competed at 2+ pilot venues to validate run time consistency.

### Matching Key
`athlete_name + nationality` (primary)
`athlete_name + nationality + age_group` (stricter if needed)

### SQL Query
```sql
SELECT 
    athlete_name, 
    nationality,
    COUNT(DISTINCT venue) as venue_count,
    GROUP_CONCAT(venue || ':' || run_total_seconds, ' | ') as venues_data
FROM pro_run_times
GROUP BY athlete_name, nationality
HAVING venue_count >= 2
ORDER BY venue_count DESC
```

### Output
```csv
athlete_name, nationality, venue_count, venues_data
Hunter McIntyre, USA, 3, London:1650 | Hamburg:1720 | Frankfurt:1695
```

---

## Phase 3: Run Distance Factor Calculation

### Methodology
1. Calculate **Median Run Total** per venue (Men/Women separately)
2. Select baseline venue (Hamburg or Frankfurt - central EU, stable data)
3. Compute: `Run_Factor = Venue_Median / Baseline_Median`

### Expected Output
```csv
venue, men_median_run, women_median_run, run_factor_men, run_factor_women
London Excel 2025, 1650, 1980, 0.96, 0.95
Hamburg 2025, 1720, 2080, 1.00, 1.00
Paris 2025, 1800, 2150, 1.05, 1.03
```

---

## Phase 4: Roxzone Analysis (Smaller Sample)

### Objective
Collect roxzone splits for a targeted sample to detect layout differences.

### Sample Strategy
| Group | Size | Rationale |
|-------|------|-----------|
| Top 20 finishers per venue | ~140 | Elite athletes have consistent workout times, so roxzone variance is more apparent |
| Multi-venue athletes (from Phase 2) | ~100-200 | Same athletes across venues = direct comparison |

### Implementation
- Requires detail page scraping (Selenium click-through)
- Parse "Race Replay" section for Roxzone 1-8 splits
- Store in `data/pro_roxzone_times.csv`

### Output Schema
```csv
venue, athlete_name, rox1, rox2, ..., rox8, total_roxzone
Utrecht 2025, Martyn Paterson, 45, 52, 48, 55, 50, 47, 53, 49, 399
```

---

## New Files to Create

| File | Purpose |
|------|---------|
| `execution/scrape_pro_run_times.py` | Leaderboard scraper for Total Run |
| `execution/match_multi_venue_athletes.py` | SQL matching + manual review CSV |
| `execution/calculate_run_factors.py` | Median analysis per venue |
| `execution/scrape_roxzone_details.py` | Detail page scraper (Phase 4) |
| `data/pro_run_times.csv` | Raw run time data |
| `data/multi_venue_matches.csv` | Matched athletes |
| `data/venue_run_factors.csv` | Calculated factors |

---

## Database Schema Addition

```sql
CREATE TABLE IF NOT EXISTS pro_run_times (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venue TEXT,
    event_id TEXT,
    gender TEXT,
    rank INTEGER,
    athlete_name TEXT,
    nationality TEXT,
    age_group TEXT,
    run_total_seconds INTEGER,
    finish_total_seconds INTEGER,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Execution Order

| Phase | Effort | Dependency | Expected Duration |
|-------|--------|------------|-------------------|
| Phase 1 (Run Leaderboards) | Medium | Selenium script | 1-2 days |
| Phase 2 (Matching) | Low | Phase 1 data | Few hours |
| Phase 3 (Factor Calc) | Low | Phase 1 data | Few hours |
| Phase 4 (Roxzone) | High | Optional, after Phase 3 | 2-3 days if pursued |

---

## Summary of Simplifications (vs v2)

| v2 Approach | v3 Approach |
|-------------|-------------|
| Detail page for run splits | **Leaderboard only** (`ranking=time_49`) |
| 8 individual run segments | **Total Run only** |
| Complex HTML parsing | Simple table scraping |
| High request volume | ~4 requests per venue (2 genders × 2 pages) |

This is now a much lighter lift!
