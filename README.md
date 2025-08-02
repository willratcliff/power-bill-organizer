# Georgia Power Bill Analyzer

A web application for analyzing Georgia Power usage data and comparing rate plans. Upload your CSV usage data to see potential savings from switching to time-of-use plans and load shifting strategies.

## Features

- **Rate Plan Comparison**: Compare Traditional, TOU-RD-11, and TOU-REO-18 plans
- **Interactive Charts**: Monthly cost analysis and demand charge visualization
- **Load Shifting Analysis**: User-configurable scenarios to optimize usage patterns
- **Real-time Updates**: Adjust parameters and see immediate cost impact
- **Validated Calculations**: Based on reverse-engineered exact rates (0.074% accuracy)

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Georgia Power CSV usage data (download from your online account)

### Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

1. Start the web server:
   ```bash
   python app.py
   ```

2. Open your browser to: `http://127.0.0.1:5000`

3. Upload your Georgia Power CSV file and analyze!

### Testing

Test the application with the included sample data:
```bash
python test_upload.py
```

## How to Get Your Data

1. Log into your Georgia Power account at georgiapower.com
2. Go to "My Usage" or "Usage History"
3. Download hourly usage data as CSV
4. Upload the CSV file to this analyzer

## CSV Format Requirements

Your CSV file should have these columns:
- `Hour`: Timestamp (e.g., "2024-06-01 01:00:00")
- `kWh`: Energy usage in kilowatt-hours
- `Temp`: Temperature (optional but recommended)

## Rate Plans Analyzed

### Traditional Residential (R-30)
- Fixed basic service charge
- Tiered energy rates (increases with usage)
- No time-of-use pricing

### TOU-RD-11 (Time-of-Use with Demand)
- Lower basic service charge
- Peak hours: Monday-Friday, 2-7 PM (June-September)
- Demand charges based on peak kW usage
- Lower off-peak rates

### TOU-REO-18 (Time-of-Use without Demand)
- Similar to TOU-RD-11 but no demand charges
- Higher energy rates to compensate

## Load Shifting Analysis

The application lets you model different load shifting scenarios:

- **Peak Demand Reduction**: Reduce maximum power draw (10-80%)
- **Energy Shifting**: Move peak-hour usage to off-peak times (5-60%)

These scenarios help you understand potential savings from:
- Smart thermostats and appliances
- Battery storage systems
- Electric vehicle charging schedules
- Pool pump and water heater timers

## Technical Details

### Accuracy
This analysis uses reverse-engineered exact rates validated against actual billing data, achieving 0.074% accuracy. Published tariff rates exclude significant hidden fees that this tool accounts for.

### Rate Validation
The calculator includes actual fees and adjustments not shown in published tariffs:
- Basic service charges are ~326% higher than published
- Energy rates are 16-59% higher than published
- TOU plans include estimated 13.7% hidden fee factor

### File Structure
```
power-bill-analyzer/
├── app.py                      # Main Flask application
├── templates/
│   ├── index.html             # Upload interface
│   └── results.html           # Analysis dashboard
├── final_exact_analysis.py    # Core analysis engine
├── corrected_tou_calculator.py # TOU rate calculator
├── data_processor.py          # CSV data processing
├── demand_calculator.py       # Peak demand analysis
├── sample_data/               # Test data
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Deployment Options

### Local Development
```bash
python app.py
```

### Production Deployment

#### Option 1: Railway (Recommended)
1. Push to GitHub repository
2. Connect to Railway.app
3. Deploy automatically

#### Option 2: Heroku
1. Create `Procfile`:
   ```
   web: python app.py
   ```
2. Deploy to Heroku

#### Option 3: Docker
1. Create `Dockerfile`:
   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   EXPOSE 5000
   CMD ["python", "app.py"]
   ```

## Security Notes

- Files are temporarily stored for analysis and automatically cleaned up
- No personal data is permanently stored
- Run on localhost for maximum privacy
- For production deployment, consider adding authentication

## Known Limitations

- Only works with Georgia Power CSV format
- Requires hourly usage data
- TOU rate calculations include estimated hidden fees
- Demand charges estimated for TOU plans (varies by actual usage patterns)

## Contributing

This tool is part of ongoing research at Georgia Tech. For issues or improvements:

1. Check existing files for similar functionality
2. Follow existing code patterns and documentation style
3. Validate any rate changes against actual billing data
4. Test thoroughly with sample data

## Support

For technical issues:
1. Ensure your CSV file matches the required format
2. Check browser developer tools (F12) for JavaScript errors
3. Try the test script: `python test_upload.py`
4. Verify Flask app is running on the correct port

## License

This project is for educational and research purposes. Rate calculations are provided as estimates - verify against your actual bills before making plan changes.

---

**Disclaimer**: This tool provides estimates based on historical usage patterns. Actual savings may vary due to rate changes, usage pattern changes, and billing adjustments not captured in the analysis. Always verify calculations against your actual Georgia Power bills.