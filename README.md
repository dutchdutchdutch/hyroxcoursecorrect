# 🏃 HYROX Course Correct

**Fair cross-venue performance comparison for HYROX athletes**

HYROX Course Correct alculates venue-specific course correction factors that enable fair performance comparisons across different event locations. Different venues have varying run loop lengths, Roxzone distances, and layouts—this tool accounts for those differences to normalize your time.

![HYROX Course Correct](https://img.shields.io/badge/Season-8%20(2025%2F2026)-Complete-green)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0+-green)
![SQLite](https://img.shields.io/badge/SQLite-3-blue)
![Data](https://img.shields.io/badge/Records-58%2C000%2B-orange)

## ✨ Features

- **🔄 Time Conversion**: Convert your finish time between 44+ venues or to a normalized reference
- **📊 Course Factors**: Robust statistical modeling based on **58,247** athlete results
- **👫 Gender Specific**: Independent correction factors for Men and Women to account for biomechanical differences
- **🌐 Web Interface**: Clean, modern web app with interactive charts and tables
- **📈 Advanced Analysis**: Outlier-free distribution charts (box plots) and top-80% performance statistics
- **🛡️ Quality Data**: Automatic filtering of errors and outliers (<50 min / >2.5 hours)
- **📍 44 Venues**: Comprehensive coverage of the entire Season 8 calendar globally

## 🎯 Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/hyroxcoursecorrect.git
   cd hyroxcoursecorrect
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the web app**
   ```bash
   python3 web/app.py
   ```

4. **Open your browser**
   ```
   http://localhost:5000
   ```

That's it! The web app is now running locally.

## 🖥️ Using the Web App

### Time Converter
1. **Enter your finish time** (format: HH:MM:SS or MM:SS)
2. **Select your venue** (where you competed)
3. **Choose conversion target**:
   - **Normalized**: Your time adjusted to the reference venue (Rio de Janeiro 2025)
   - **Specific Venue**: What your time would be at another venue
4. **Click "Convert Time"** to see your adjusted performance

### Venue Analysis
- **Distribution Charts**: Interactive box plots showing finish time spreads (outliers hidden for clarity).
- **Rankings**: Venues sorted by median finish time ("Mid-pack" performance).
- **Gender Comparison**: Switch between Men's and Women's specific data views.

### Statistics
- Detailed breakdown of **Fastest**, **Slowest**, and **Median** times per venue.
- **Top 80% Filter**: Metrics are calculated using only the top 80% of finishers to ensure competitive relevance.
- **Benchmarks**: Gender-specific mid-pack benchmarks for every venue.

## 📊 Current Venue Factors (Season 8 Snapshot)

**Reference Venue:** 2025 Rio de Janeiro (Correction: 0.00%)

| Venue | Men's Factor | Women's Factor | Difficulty |
|-------|--------------|----------------|------------|
| **Dublin** | -7:02 | -6:56 | ⚡️ Fastest |
| **Bordeaux** | -7:15 | -2:16 | ⚡️ Very Fast |
| **London Excel** | -7:41 | -5:48 | ⚡️ Very Fast |
| **Rio de Janeiro** | **0:00** | **0:00** | ⚖️ **Baseline** |
| **Chicago** | +1:41 | -3:59 | 🏃 Mixed |
| **Anaheim** | +6:13 | +6:24 | 🐢 Slow |
| **Delhi** | +23:21 | +30:54 | 🔥 Hardest |

*> Note: Positive factors mean the course is slower (you subtract time to normalize). Negative factors mean the course is faster (you add time).*

## 🔧 How It Works

The system uses a robust **4-layer architecture**:

1. **Data Collection**: Automated scripts (`update_season8_data.py`) scrape official HYROX results, handling multi-day events.
2. **Data Storage**: Raw results are validated and stored in a **SQLite database** (`hyrox_results.db`) for efficient querying.
3. **Statistical Analysis**: 
   - filters outliers (<50m, >2.5h)
   - calculates the **Median** finish time for each venue by gender
   - determines a global median "Baseline Venue"
   - computes the time difference (offset) for every other venue
4. **Web Application**: Flask-based interface serves these insights dynamically.

### The Math

```
Normalized Time = Raw Time - Venue Correction

Example (Men):
You ran 1:10:00 at London Excel (-7:41 correction).
Normalized = 1:10:00 - (-0:07:41) = 1:17:41
(You add time because London is faster than the baseline)
```

## 📁 Project Structure

```
hyroxcoursecorrect/
├── web/
│   ├── app.py                  # Flask application & Analysis Logic
│   ├── templates/              # HTML templates (Analysis, Stats, Home)
│   ├── static/                 # CSS and JavaScript
│   └── utils/                  # Helper modules (database, calculations)
├── execution/
│   ├── update_season8_data.py  # Main scraper for Season 8
│   ├── populate_db_from_json.py # Database population utility
│   ├── calculate_venue_handicap.py # Core math logic
│   └── season_8_events.json    # Event configuration
├── data/
│   ├── hyrox_results.db        # SQLite Database (The Source of Truth)
│   ├── venue_corrections.json  # Pre-calculated factors for the UI
│   └── backup_raw_results/     # JSON backups of raw scrapes
├── tests/
│   └── ...                     # Unit and Integration tests
└── README.md
```

## 🚀 Advanced Usage

### Updating Venue Data

To fetch the latest results (e.g., after a race weekend):

```bash
# 1. Scrape new results (updates raw JSONs and Database)
python3 execution/update_season8_data.py

# 2. Recalculate correction factors based on new data
python3 execution/calculate_venue_handicap.py \
  --input data/all_season8_results.csv \
  --output data/venue_corrections.json
```

### Accessing the Database directly

You can query the SQLite database for custom analysis:

```bash
sqlite3 data/hyrox_results.db
sqlite> SELECT venue, count(*) FROM race_results GROUP BY venue;
```

## 📝 Methodology changes in v1.0

- **Top 80% Filtering**: We now exclude the bottom 20% of finishers when calculating averages and benchmarks to reduce the skew from walking/injured athletes.
- **Gender Specificity**: Recognizing that "Run-heavy" vs "Sled-heavy" courses impact men and women differently, we now calculate separate baselines.
- **Outlier Removal**: Times under 50 minutes and over 2.5 hours are strictly excluded from statistical models.

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- [ ] Add previous seasons (Season 6, 7) for historical comparison
- [ ] Create a "Percentile Calculator" (e.g., "You are in the top 15% of your age group")
- [ ] Mobile-native app version (React Native / Swift)
- [ ] API for 3rd party integrations

## ⚠️ Disclaimer

Course correction factors are statistical estimates based on available public data. Actual performance varies based on fitness, pacing, temperature, and race-day conditions. Use these conversions as a guide, not absolute truth.

## 📄 License

MIT License - feel free to use and modify.

---

**Built with ❤️ for the HYROX community**

**Version:** 1.0.0 (Season 8 Complete)  
**Last Updated:** January 11, 2026  
**Dataset:** 58,247 results across 44 venues  

Questions? Open an issue or reach out!
