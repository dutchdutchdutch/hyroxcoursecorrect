# HYROX Sampling Strategy Research

## Objective
To determine the optimal scraping strategy (sample size/method) for calculating reliable course correction factors.

## Methodology
- **Datasets**: Full leaderboards for Anaheim 2025 and Maastricht 2025 (Men & Women Open).
- **Ground Truth**: Median finish time of the full population.
- **Metric**: Deviation from the true median (Absolute Seconds and Percentage).

## Results Summary

| Strategy | Mean Err (s) | Max Err (s) | Mean % Err | Max % Err | Avg Sample Size |
|---|---|---|---|---|---|
| Every 5th | 2.62 | 3.5 | 0.05 | 0.06 | 152.75 |
| Every 10th | 8.88 | 13.5 | 0.16 | 0.23 | 76.5 |
| Every 20th | 17.38 | 28.0 | 0.3 | 0.48 | 38.5 |
| Every 50th | 45.88 | 83.0 | 0.78 | 1.34 | 15.75 |
| Every 2nd Page | 54.62 | 81.5 | 0.93 | 1.41 | 392.0 |
| Every 100th | 109.62 | 181.0 | 1.88 | 2.93 | 8.0 |
| Top 80% | 245.62 | 279.0 | 4.26 | 4.52 | 608.75 |
| Every 5th Page | 279.5 | 449.0 | 4.84 | 7.81 | 162.5 |
| Top 500 | 389.5 | 628.5 | 6.83 | 10.88 | 492.25 |
| Top 50% | 637.88 | 745.5 | 11.05 | 12.08 | 380.5 |
| Every 10th Page | 678.12 | 1208.5 | 11.89 | 21.03 | 87.5 |
| Top 200 | 966.5 | 1110.0 | 16.78 | 19.18 | 200.0 |
| Top 25% | 1020.25 | 1201.0 | 17.67 | 19.46 | 190.0 |
| Top 100 | 1233.0 | 1419.0 | 21.39 | 23.82 | 100.0 |
| Top 10% | 1348.62 | 1569.0 | 23.36 | 25.42 | 75.5 |
| Top 50 | 1451.5 | 1632.0 | 25.18 | 27.78 | 50.0 |

## Detailed Analysis

### Top N vs Full Population
Using only 'Top N' results (e.g., Top 100) consistently underestimates the median time (making the course look 'faster' than it is for the average athlete). This is because the distribution is right-skewed; the elite are much faster than the average.

### Systematic Sampling (Every Nth)
Systematic sampling (taking every Nth result) preserves the distribution shape and provides a much more accurate estimate of the median with fewer requests.

## Recommendation

**Recommended Strategy: Full Scrape (All Results)**

Based on the analysis, the most reliable approach is to scrape **all** results for each event.

### Rationale:
1.  **Top N is Flawed**: Using "Top 100" or similar strategies results in massive error (20%+) because it biases the sample towards elite athletes, completely missing the "average" experience we are trying to correct for.
2.  **Page Subsampling is Risky**: "Every 5th Page" introduces ~5% error. "Every 2nd Page" introduces ~1% error but only saves 50% of requests.
3.  **Feasibility**: With only ~2,000 athletes per event and 50 results per page, scraping an entire event requires only ~40 HTTP requests. This is negligible. 
4.  **Conclusion**: The bandwidth savings from subsampling are not worth the potential loss in accuracy.

**Action Plan**:
- Target **ALL** pages for "HYROX Men" and "HYROX Women" divisions.
- Do not stop until 0 results are returned.
- This ensures 100% accuracy for the median calculation.
