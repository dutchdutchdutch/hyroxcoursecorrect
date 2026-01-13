# Build Report: v1.0.0 / Season 8 Data & UI Overhaul
**Date:** 2026-01-11  
**Build Status:** Staged (Local)

## Executive Summary
This iteration focused on finalizing the dataset for HYROX Season 8 and overhauling the user interface to provide actionable insights. We successfully scraped and consolidated results from over 50 events (covering 58,000+ athlete records), establishing a robust data foundation.

The web application was significantly enhanced to leverage this data. The Course Correction methodology was refined to use a gender-specific median baseline (Rio de Janeiro 2025), and the UI was updated to display these factors clearly. Advanced analysis features, including outlier-free distribution charts and top-80% performance statistics, were implemented to help athletes benchmark themselves accurately against global standards.

## Story Status

### Story: Season 8 Data Acquisition
**Status:** Completed  
Successfully scraped full results for all Season 8 events to date (May 2025 - Jan 2026). Handled complex multi-day event splits (e.g., Madrid, Mexico City) and identified cancelled/empty events (Abu Dhabi). Consolidated duplicate venue entries (e.g., "Dublin 2025" vs "2025 Dublin") into a clean list of 44 unique venues.

### Story: Course Correction Factors UI
**Status:** Completed  
Redesigned the main page to display correction factors in a sorted, 4-column table (Venue, Men, Women, Overall). Implemented color-coded badges (green/red) for easier interpretation of fast vs. slow courses.

### Story: Venue Analysis & Charts
**Status:** Completed  
Upgraded the Plotly-based distribution charts. Removed visual noise by hiding outliers and implemented a cleaner "alternating label" system for median times. Added a clear legend and colored axis markers to improve readability.

### Story: Detailed Statistics
**Status:** Completed  
Overhauled the Statistics page to calculate metrics based strictly on the top 80% of finishers, excluding irrelevant outliers (times <50m or >2h30m). Added dynamic gender-specific benchmarks and highlighted the baseline venue for reference.

## Technical Implementation

### Data Pipeline Refinement
- **Outlier Filtering**: Implemented strict filtering at the application level to exclude times under 50 minutes (likely errors) and over 2.5 hours (likely injuries/walking), ensuring statistical relevance.
- **Top 80% Logic**: Statistical averages and benchmarks are now derived solely from the top 80% of the field, providing a more realistic "competitive" benchmark than the raw mean.

### Venue Correction Algorithm
- **Baseline Selection**: Shifted from an arbitrary baseline to a calculated median venue (2025 Rio de Janeiro) based on the full dataset.
- **Gender Specificity**: Corrections are now calculated independently for men and women, acknowledging that certain course layouts (e.g., run-heavy vs. sled-heavy) affect genders differently.

### UI/UX Improvements
- **CSS Grid Layouts**: Migrated lists to structured tables with sticky headers for better data density and usability.
- **Dynamic visual cues**: Added conditional styling (e.g., `.baseline-row`, `.badge.positive`) to visually guide the user to key information without reading every number.

## Detailed Updates

<details>
<summary>Data Processing - Acceptance Criteria</summary>
- [x] Scrape multi-day events correctly (Madrid, Mexico City)
- [x] Consolidate "City Year" vs "Year City" naming conventions
- [x] Store raw JSON backups for all 55 scraped files
- [x] Populate SQLite database with 58,247 validated records
</details>

<details>
<summary>Analysis Page - Acceptance Criteria</summary>
- [x] Box plots hide outliers/bubbles
- [x] Median time labels alternate (above/below) to prevent overlapping
- [x] X-axis labels include colored dots matching the bars
- [x] Legend explains Box (Mid 50%), Line (Median), and Whiskers (Typical Range)
</details>

<details>
<summary>Statistics Page - Acceptance Criteria</summary>
- [x] "Sample Size" reflects accumulated top 80% of Men + Women
- [x] Baseline row (0.00%) highlighted in green
- [x] Columns for Men's and Women's specific median benchmarks added
- [x] Average column removed from Rankings table to focus on Median
</details>
