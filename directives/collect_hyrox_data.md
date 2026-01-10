# Collect HYROX Event Results Data

## Goal
Gather comprehensive HYROX event results data including athlete finish times, venue information, and event metadata to enable venue handicap factor analysis.

## Inputs
- **Data Source**: HYROX results website (https://results.hyrox.com) or provided dataset
- **Time Period**: Specify date range for events to analyze
- **Divisions**: Men's/Women's Individual, Doubles, Relay (focus on Individual for initial analysis)

## Tools/Scripts
- `execution/scrape_hyrox_results.py` - Web scraper for HYROX results
- `execution/clean_hyrox_data.py` - Data cleaning and validation

## Process

### 1. Data Collection
Run the scraper to collect raw results:
```bash
cd /Users/dutch/Workspace/hyroxranks
python execution/scrape_hyrox_results.py --start-date 2024-01-01 --end-date 2025-12-31
```

The scraper will:
- Identify all events in the specified date range
- Extract results for each event/division
- Save raw HTML/JSON to `.tmp/raw_results/`
- Output consolidated CSV: `.tmp/raw_results_combined.csv`

### 2. Data Cleaning
Clean and validate the raw data:
```bash
python execution/clean_hyrox_data.py --input .tmp/raw_results_combined.csv --output .tmp/cleaned_results.csv
```

Cleaning steps:
- Parse time strings (HH:MM:SS) to seconds
- Standardize venue names (e.g., "NYC" → "New York City")
- Handle DNF (Did Not Finish) and DNS (Did Not Start) entries
- Remove outliers beyond 3 standard deviations
- Validate data completeness (required fields present)

## Expected Outputs
- `.tmp/raw_results_combined.csv` - Raw scraped data
- `.tmp/cleaned_results.csv` - Cleaned dataset with columns:
  - `athlete_id` - Unique identifier (name + DOB or bib number)
  - `athlete_name` - Full name
  - `event_id` - Unique event identifier
  - `event_name` - Event name (e.g., "HYROX New York 2024")
  - `event_date` - Date (YYYY-MM-DD)
  - `venue` - Standardized venue name
  - `division` - Men/Women Individual/Doubles/Relay
  - `finish_time_seconds` - Total finish time in seconds
  - `run_time_seconds` - Total running time (if available)
  - `workout_time_seconds` - Total workout time (if available)
  - `roxzone_time_seconds` - Roxzone transition time (if available)
  - `rank_overall` - Overall rank in division
  - `rank_age_group` - Age group rank (if available)

## Edge Cases & Learnings

### Rate Limiting
- HYROX results site may have rate limits
- Implement 1-2 second delays between requests
- Use session management to avoid IP blocks

### Data Availability
- Not all events have split times (run/workout/roxzone)
- Early events may have less detailed data
- Some venues host multiple events - ensure proper event_id separation

### Athlete Identification
- **CRITICAL**: Athletes may compete under slightly different names
- **DO NOT** assume athletes with the same name are the same person
- **ONLY** treat as repeat athletes if they have:
  - Bib number match, OR
  - Date of birth match
- Without unique identifiers, create event-specific IDs to prevent false matches
- This ensures course correction only uses verified repeat athletes

### Venue Name Variations
- Same venue may appear with different names across events
- Maintain a venue mapping dictionary in the cleaning script
- Example: "Javits Center" = "Jacob K. Javits Convention Center" = "NYC Javits"

## Success Criteria
- At least 10,000 athlete results collected
- At least 20 unique venues represented
- At least 100 athletes who competed at 2+ different venues (for model validation)
- Data completeness: >95% of records have finish_time, venue, event_date
- No duplicate athlete-event combinations
