# 🏃 HYROX Course Correct

**Fair cross-venue performance comparison for HYROX athletes**

HYROX Course Correct calculates venue-specific course correction factors that enable fair performance comparisons across different event locations. Different venues have varying run loop lengths, Roxzone distances, and layouts—this tool accounts for those differences.

![HYROX Course Correct](https://img.shields.io/badge/Season-8%20(2025%2F2026)-orange)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0+-green)

## ✨ Features

- **🔄 Time Conversion**: Convert your finish time between venues or to a normalized reference
- **📊 Course Factors**: Statistical modeling to calculate venue difficulty
- **🌐 Web Interface**: Clean, modern web app for easy conversions
- **📈 Data-Driven**: Based on analysis of real HYROX results

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
   cd web
   python app.py
   ```

4. **Open your browser**
   ```
   http://localhost:5000
   ```

That's it! The web app is now running locally.

## 🖥️ Using the Web App

1. **Enter your finish time** (format: HH:MM:SS or MM:SS)
2. **Select your venue** (where you competed)
3. **Choose conversion target**:
   - **Normalized**: Your time adjusted to a reference venue
   - **Specific Venue**: What your time would be at another venue
4. **Click "Convert Time"** to see your adjusted performance

### Example

If you ran **1:15:00** at Anaheim 2025, your normalized time would be **1:13:22** because Anaheim is 2.2% slower than the reference venue.

## 📊 Current Venue Factors (Season 8)

| Venue | Course Factor | Interpretation |
|-------|--------------|----------------|
| London Excel 2025 | 1.000 | Reference (fastest) |
| Anaheim 2025 | 1.022 | 2.2% slower |

*More venues will be added as Season 8 progresses*

## 🔧 How It Works

The system uses a **3-layer architecture**:

1. **Data Collection**: Browser-based scraper extracts results from HYROX results pages
2. **Statistical Modeling**: Mixed-effects regression isolates venue difficulty from athlete ability
3. **Web Application**: Flask-based interface for easy time conversions

### The Math

```
Adjusted Time = Raw Time / Venue Handicap

Example:
1:13:22 = 1:15:00 / 1.022
```

## 📁 Project Structure

```
hyroxcoursecorrect/
├── web/
│   ├── app.py              # Flask application
│   ├── templates/
│   │   └── index.html      # Main page
│   └── static/
│       ├── css/styles.css  # Styling
│       └── js/app.js       # Frontend logic
├── execution/
│   ├── scrape_hyrox_results.py
│   ├── clean_hyrox_data.py
│   ├── venue_eda.py
│   └── build_handicap_model.py
├── directives/
│   └── *.md                # Process documentation
├── requirements.txt
└── README.md
```

## 🚀 Advanced Usage

### Running the Full Pipeline

To update venue factors with new data:

```bash
# 1. Generate sample data (or scrape real data)
python execution/generate_sample_data.py

# 2. Clean the data
python execution/clean_hyrox_data.py \
  --input .tmp/raw_results_combined.csv \
  --output .tmp/cleaned_results.csv

# 3. Run exploratory analysis
python execution/venue_eda.py \
  --input .tmp/cleaned_results.csv \
  --output-dir .tmp/eda_plots

# 4. Build handicap model
python execution/build_handicap_model.py \
  --input .tmp/cleaned_results.csv \
  --output .tmp/venue_handicaps.csv
```

### API Endpoints

The web app exposes REST API endpoints:

- `POST /convert` - Convert a finish time
- `GET /venues` - List all venues and their handicaps

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- Add more Season 8 venues
- Collect station-by-station splits
- Mobile app development
- Division-specific handicaps (Men vs Women)

## 📝 Methodology

The course correction factors are calculated using:

1. **Data Collection**: Top 200 Men/Women Individual results per venue
2. **Athlete Matching**: Only athletes with unique IDs (bib number or DOB) are treated as repeat competitors
3. **Statistical Model**: Mixed-effects regression controlling for athlete ability
4. **Validation**: Cross-validation using repeat athletes

**Key Assumption**: Athlete populations are similar across venues, so performance differences reflect venue difficulty rather than athlete selection bias.

## ⚠️ Disclaimer

Course correction factors are statistical estimates based on available data. Actual performance varies based on many factors including fitness, pacing, and conditions. Use these conversions as a guide, not absolute truth.

## 📄 License

MIT License - feel free to use and modify

## 🙏 Acknowledgments

- HYROX community for the inspiration
- All athletes whose results contributed to the analysis

---

**Built with ❤️ for the HYROX community**

Questions? Open an issue or reach out!
