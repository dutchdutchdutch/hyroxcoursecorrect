# 🏃 HYROX Course Correct

**Fair cross-venue performance comparison for HYROX athletes**

HYROX Course Correct calculates venue-specific course correction factors that enable fair performance comparisons across different event locations. Different venues have varying run loop lengths, Roxzone distances, and layouts—this tool accounts for those differences.

![HYROX Course Correct](https://img.shields.io/badge/Season-8%20(2025%2F2026)-orange)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0+-green)
![Tests](https://img.shields.io/badge/Tests-40%20passing-brightgreen)

## ✨ Features

- **🔄 Time Conversion**: Convert your finish time between 10 venues or to a normalized reference
- **📊 Course Factors**: Statistical modeling based on 18,657 athlete results
- **🌐 Web Interface**: Clean, modern web app for easy conversions
- **📈 Data-Driven**: Analysis of top 1,000 finishers per venue (filtered for quality)
- **🧪 Test Coverage**: 40 automated tests ensuring accuracy and reliability
- **📍 10 Venues**: Comprehensive coverage across North America and Europe

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
   - **Normalized**: Your time adjusted to reference venue
   - **Specific Venue**: What your time would be at another venue
4. **Click "Convert Time"** to see your adjusted performance

### Venue Analysis
- View performance distributions across all venues
- Compare venue difficulty rankings
- See statistics for 18,657 athletes

### Example

If you ran **1:25:00** at Frankfurt 2025, your time at London Excel 2025 would be **01:12:21** (12:39 faster) because London Excel is 15.7% faster than the reference venue.

## 📊 Current Venue Factors (Season 8, Phase 3)

| Rank | Venue | Course Factor | Difficulty | Median Time |
|------|-------|---------------|------------|-------------|
| 1 | London Excel 2025 | 0.843 | -15.7% (fastest) | 70.7 min |
| 2 | Bordeaux 2025 | 0.913 | -8.7% | 76.6 min |
| 3 | Dublin 2025 | 0.922 | -7.8% | 77.3 min |
| 4 | Valencia 2025 | 0.965 | -3.5% | 81.0 min |
| 5 | Frankfurt 2025 | 0.991 | -0.9% | 83.1 min |
| 6 | **Maastricht 2025** | **1.000** | **Reference** | **83.9 min** |
| 7 | Utrecht 2025 | 1.000 | +0.0% | 83.9 min |
| 8 | Chicago 2025 | 1.039 | +3.9% | 87.2 min |
| 9 | Atlanta 2025 | 1.067 | +6.7% | 89.5 min |
| 10 | Anaheim 2025 | 1.071 | +7.1% (slowest) | 89.9 min |

**Dataset:** 18,657 results (10,000 Men, 8,657 Women) from top 1,000 finishers per venue, filtered to top 80% for venues with incomplete fields.

## 🔧 How It Works

The system uses a **3-layer architecture**:

1. **Data Collection**: Automated Selenium scraper extracts results from HYROX results pages
2. **Data Processing**: Cleans, validates, and filters results for quality
3. **Statistical Analysis**: Calculates median-based handicap factors
4. **Web Application**: Flask-based interface for easy time conversions

### The Math

```
Normalized Time = Raw Time / Venue Handicap

Example:
01:12:21 = 01:25:00 / 0.991  (Frankfurt to normalized)
```

## 📁 Project Structure

```
hyroxcoursecorrect/
├── web/
│   ├── app.py              # Flask application
│   ├── templates/          # HTML templates
│   └── static/             # CSS and JavaScript
├── execution/
│   ├── scrape_venues.py    # Automated scraper (Selenium)
│   ├── process_scraped_data.py
│   ├── calculate_venue_handicap.py
│   └── venues.json         # Venue configuration
├── tests/
│   ├── test_unit.py        # Unit tests
│   ├── test_components.py  # Component tests
│   └── test_integration.py # Integration tests
├── data/
│   ├── hyrox_9venues_100each.csv         # 18,657 results
│   └── venue_handicaps_10venues_1000each.csv
├── directives/
│   └── *.md                # Process documentation
├── progress_reports/       # Build reports
├── requirements.txt
└── README.md
```

## 🚀 Advanced Usage

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=web --cov=execution

# Run specific test categories
pytest tests/test_unit.py          # Unit tests only
pytest tests/test_integration.py   # Integration tests only
```

### Updating Venue Data

To scrape fresh data from HYROX results:

```bash
# Scrape top 1000 results per venue
python3 execution/scrape_venues.py --limit 1000

# Process scraped data (includes filtering)
python3 execution/process_scraped_data.py

# Calculate updated handicaps
python3 execution/calculate_venue_handicap.py \
  --input data/hyrox_9venues_100each.csv \
  --output data/venue_handicaps_10venues_1000each.csv
```

### API Endpoints

The web app exposes REST API endpoints:

- `GET /` - Main time converter page
- `GET /analysis` - Venue analysis page
- `POST /convert` - Convert a finish time (JSON)
- `GET /venues` - List all venues and their handicaps (JSON)

## 🧪 Testing

The project includes a comprehensive test suite:

- **40 tests** across 3 categories
- **Unit Tests (13)**: Time parsing, formatting, handicap calculations
- **Component Tests (14)**: Data processing, file validation, data quality
- **Integration Tests (13)**: Flask API endpoints, error handling

All tests run in < 1 second and validate:
- ✅ Time conversion accuracy
- ✅ Data integrity (no duplicates, valid times)
- ✅ API endpoint functionality
- ✅ Configuration file validity

## 📝 Methodology

The course correction factors are calculated using:

1. **Data Collection**: Top 1,000 Men/Women Individual results per venue
2. **Quality Filtering**: Top 80% of results for venues with <1,000 finishers (removes slow outliers)
3. **Statistical Model**: Median-based handicap calculation
4. **Reference Venue**: Auto-selected as median venue (Maastricht 2025)
5. **Validation**: 40 automated tests + manual browser testing

**Key Assumption**: Athlete populations are similar across venues, so performance differences reflect venue difficulty rather than athlete selection bias.

### Handicap Evolution

As the dataset grew from 100 to 1,000 results per venue, handicap factors refined:

- London Excel: 0.890 → 0.843 (-5.24% change)
- Atlanta: 1.034 → 1.067 (+3.27% change)
- Maastricht: Stable at 1.000 (reference venue)

The larger sample revealed that fast venues were underestimated and slow venues were underestimated in the smaller dataset.

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- Monitor for Boston, Frankfurt, Seoul results (currently unavailable)
- Implement gender-specific handicaps
- Add percentile calculator
- Create normalized global leaderboard
- Mobile app development

## ⚠️ Disclaimer

Course correction factors are statistical estimates based on available data. Actual performance varies based on many factors including fitness, pacing, and conditions. Use these conversions as a guide, not absolute truth.

## 📄 License

MIT License - feel free to use and modify

## 🙏 Acknowledgments

- HYROX community for the inspiration
- 18,657 athletes whose results contributed to the analysis
- Season 8 (2025/2026) event organizers

---

**Built with ❤️ for the HYROX community**

**Version:** 1.0.0 (Phase 3 Complete)  
**Last Updated:** January 10, 2026  
**Dataset:** 18,657 results across 10 venues

Questions? Open an issue or reach out!
