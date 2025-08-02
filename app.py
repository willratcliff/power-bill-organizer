#!/usr/bin/env python3
"""
Power Bill Analysis Web Application
A simple Flask app for analyzing Georgia Power usage data
"""

import os
import json
from flask import Flask, request, jsonify, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np
from datetime import datetime
import calendar

# Import existing analysis modules
from final_exact_analysis import ExactTraditionalRateCalculator
from corrected_tou_calculator import CorrectedTOURateCalculator
from tou_reo_calculator import TOUREOCalculator
from data_processor import PowerDataProcessor
from demand_calculator import DemandCalculator

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.secret_key = 'power_analysis_secret_key'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page with file upload form."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle CSV file upload and redirect to analysis."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Validate CSV format
        try:
            # Try reading with different encodings to handle BOM
            encodings = ['utf-8-sig', 'utf-8', 'latin-1']
            df = None
            for encoding in encodings:
                try:
                    df = pd.read_csv(filepath, skiprows=2, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                os.remove(filepath)
                return jsonify({'error': 'Unable to read CSV file with any encoding'}), 400
            
            required_columns = ['Hour', 'kWh', 'Temp']
            if not all(col in df.columns for col in required_columns):
                os.remove(filepath)  # Clean up invalid file
                return jsonify({'error': 'Invalid CSV format. Required columns: Hour, kWh, Temp'}), 400
                
            # Test datetime parsing on the first few rows
            try:
                pd.to_datetime(df['Hour'].head(5))
            except Exception as datetime_error:
                os.remove(filepath)
                return jsonify({'error': f'Invalid datetime format in Hour column: {str(datetime_error)}'}), 400
                
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': f'Error reading CSV file: {str(e)}'}), 400
        
        return jsonify({'success': True, 'filename': filename})
    
    return jsonify({'error': 'Invalid file type. Please upload a CSV file.'}), 400

@app.route('/api/analyze/<filename>')
def analyze_file(filename):
    """Analyze uploaded CSV file with configurable load shifting scenarios."""
    # Get user-configurable parameters from query string
    peak_reduction = float(request.args.get('peak_reduction', 40.0)) / 100  # Default 40%
    energy_shift = float(request.args.get('energy_shift', 25.0)) / 100     # Default 25%
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        # Process the data using existing modules
        print(f"Processing file: {filepath}")
        
        # Create a custom data processor that handles encoding issues
        class WebDataProcessor(PowerDataProcessor):
            def load_data(self):
                """Load and clean the CSV data with better encoding handling."""
                # Try reading with different encodings to handle BOM
                encodings = ['utf-8-sig', 'utf-8', 'latin-1']
                for encoding in encodings:
                    try:
                        self.data = pd.read_csv(self.csv_path, skiprows=2, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                
                if self.data is None:
                    raise ValueError("Unable to read CSV file with any encoding")
                
                # Convert Hour column to datetime
                self.data['datetime'] = pd.to_datetime(self.data['Hour'])
                
                # Extract time components
                self.data['date'] = self.data['datetime'].dt.date
                self.data['hour'] = self.data['datetime'].dt.hour
                self.data['day_of_week'] = self.data['datetime'].dt.dayofweek  # 0=Monday, 6=Sunday
                self.data['month'] = self.data['datetime'].dt.month
                self.data['year'] = self.data['datetime'].dt.year
                
                # Clean kWh column - ensure it's numeric
                self.data['kWh'] = pd.to_numeric(self.data['kWh'], errors='coerce')
                
                # Remove any rows with missing kWh data
                self.data = self.data.dropna(subset=['kWh'])
                
                # Sort by datetime
                self.data = self.data.sort_values('datetime').reset_index(drop=True)
                
                return self.data
        
        data_processor = WebDataProcessor(filepath)
        print("Loading data...")
        data_processor.load_data()
        print("Classifying time periods...")
        processed_data = data_processor.classify_time_periods()
        
        demand_calculator = DemandCalculator(processed_data)
        monthly_demands = demand_calculator.calculate_monthly_demands()
        
        # Get monthly data for analysis
        traditional_monthly_data = demand_calculator.get_traditional_monthly_data()  # Dict with (year,month) keys
        tou_monthly_data = demand_calculator.get_tou_monthly_data()  # List[Dict]
        
        # Initialize calculators
        traditional_calc = ExactTraditionalRateCalculator()
        tou_rd_calc = CorrectedTOURateCalculator()  # TOU with demand charges
        tou_reo_calc = TOUREOCalculator()  # TOU without demand charges
        
        # Calculate monthly bills for each plan
        monthly_results = []
        
        # Create a lookup for TOU data by (year, month)
        tou_lookup = {}
        for tou_month in tou_monthly_data:
            key = (tou_month['year'], tou_month['month'])
            tou_lookup[key] = tou_month
        
        # Iterate through traditional monthly data (dict with (year, month) keys)
        for (year, month), total_kwh in traditional_monthly_data.items():
            month_name = calendar.month_name[month]
            days_in_month = calendar.monthrange(year, month)[1]
            
            # Traditional plan
            trad_result = traditional_calc.calculate_monthly_bill(total_kwh, month, days_in_month)
            
            # Get corresponding TOU data for this month
            tou_key = (year, month)
            if tou_key in tou_lookup:
                tou_data = tou_lookup[tou_key]
                peak_kwh = tou_data['peak_usage_kwh']
                off_peak_kwh = tou_data['off_peak_usage_kwh']
                max_demand_kw = tou_data['max_demand_kw']
                
                # TOU-RD-11 (with demand charges)
                tou_rd_result = tou_rd_calc.calculate_monthly_bill(
                    peak_kwh, off_peak_kwh, max_demand_kw, days_in_month
                )
                
                # TOU-REO-18 (without demand charges)
                tou_reo_result = tou_reo_calc.calculate_monthly_bill(
                    peak_kwh, off_peak_kwh, max_demand_kw, days_in_month
                )
                
                # Load shifting scenario - redistribute energy to reduce peak demand
                # User-configurable peak demand reduction and energy shifting
                reduced_demand = max_demand_kw * (1 - peak_reduction)
                shifted_energy = peak_kwh * energy_shift
                new_peak_kwh = peak_kwh - shifted_energy
                new_off_peak_kwh = off_peak_kwh + shifted_energy
                
                tou_rd_shifted = tou_rd_calc.calculate_monthly_bill(
                    new_peak_kwh, new_off_peak_kwh, reduced_demand, days_in_month
                )
                
                monthly_results.append({
                    'month': month_name,
                    'year': int(year),
                    'month_num': int(month),
                    'traditional_cost': float(trad_result['total_bill']),
                    'tou_rd_cost': float(tou_rd_result['total_bill']),
                    'tou_reo_cost': float(tou_reo_result['total_bill']),
                    'tou_rd_shifted_cost': float(tou_rd_shifted['total_bill']),
                    'demand_charge': float(tou_rd_result.get('demand_charge', 0)),
                    'demand_kw': float(max_demand_kw),
                    'reduced_demand': float(reduced_demand),
                    'shifted_savings': float(tou_rd_result['total_bill'] - tou_rd_shifted['total_bill']),
                    'total_kwh': float(total_kwh),
                    'original_peak_kwh': float(peak_kwh),
                    'original_off_peak_kwh': float(off_peak_kwh),
                    'shifted_peak_kwh': float(new_peak_kwh),
                    'shifted_off_peak_kwh': float(new_off_peak_kwh),
                    'energy_shifted': float(shifted_energy),
                    # Include the scenario parameters for reference
                    'peak_reduction_pct': float(peak_reduction * 100),
                    'energy_shift_pct': float(energy_shift * 100)
                })
        
        # Calculate annual totals
        annual_traditional = sum(m['traditional_cost'] for m in monthly_results)
        annual_tou_rd = sum(m['tou_rd_cost'] for m in monthly_results)
        annual_tou_reo = sum(m['tou_reo_cost'] for m in monthly_results)
        annual_tou_rd_shifted = sum(m['tou_rd_shifted_cost'] for m in monthly_results)
        
        annual_demand_charges = sum(m['demand_charge'] for m in monthly_results)
        annual_shifted_savings = sum(m['shifted_savings'] for m in monthly_results)
        
        total_energy_shifted = sum(m['energy_shifted'] for m in monthly_results)
        
        # Summary statistics
        summary = {
            'annual_costs': {
                'traditional': annual_traditional,
                'tou_rd': annual_tou_rd,
                'tou_reo': annual_tou_reo,
                'tou_rd_shifted': annual_tou_rd_shifted
            },
            'annual_savings': {
                'tou_rd_vs_traditional': annual_traditional - annual_tou_rd,
                'tou_reo_vs_traditional': annual_traditional - annual_tou_reo,
                'load_shifting_savings': annual_shifted_savings
            },
            'total_usage': sum(m['total_kwh'] for m in monthly_results),
            'total_original_peak_usage': sum(m['original_peak_kwh'] for m in monthly_results),
            'total_demand_charges': annual_demand_charges,
            'total_energy_shifted': total_energy_shifted,
            'load_shifting_details': {
                'peak_reduction_percent': peak_reduction * 100,
                'energy_shift_percent': energy_shift * 100,
                'energy_shifted_kwh': total_energy_shifted,
                'annual_savings': annual_shifted_savings
            },
            'best_plan': 'tou_rd_shifted'  # Best optimized scenario
        }
        
        return jsonify({
            'success': True,
            'monthly_results': monthly_results,
            'summary': summary
        })
        
    except Exception as e:
        print(f"Analysis error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/results/<filename>')
def show_results(filename):
    """Display analysis results page."""
    return render_template('results.html', filename=filename)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
