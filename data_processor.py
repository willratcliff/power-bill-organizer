import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple


class PowerDataProcessor:
    """
    Processes hourly power usage data from Georgia Power CSV files.
    Handles data loading, cleaning, and time period classification.
    """
    
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.data = None
        self.processed_data = None
        
    def load_data(self) -> pd.DataFrame:
        """Load and clean the CSV data."""
        # Read CSV, skipping the disclaimer rows
        self.data = pd.read_csv(self.csv_path, skiprows=2)
        
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
    
    def classify_time_periods(self) -> pd.DataFrame:
        """
        Classify each hour as peak/off-peak and summer/winter.
        
        Peak hours: 2-7 PM (14:00-19:00), Monday-Friday, June-September
        Holidays (Independence Day, Labor Day) are considered off-peak
        """
        if self.data is None:
            raise ValueError("Data not loaded. Call load_data() first.")
            
        # Create a copy for processing
        self.processed_data = self.data.copy()
        
        # Define summer months (June-September)
        summer_months = [6, 7, 8, 9]
        
        # Define peak hours (2 PM to 7 PM = 14:00 to 18:59)
        peak_hours = list(range(14, 19))
        
        # Define weekdays (Monday=0 to Friday=4)
        weekdays = list(range(0, 5))
        
        # Initialize all periods as off-peak
        self.processed_data['is_peak'] = False
        self.processed_data['season'] = 'winter'
        
        # Mark summer months
        self.processed_data.loc[self.processed_data['month'].isin(summer_months), 'season'] = 'summer'
        
        # Mark peak hours: summer months, weekdays, 2-7 PM
        peak_condition = (
            (self.processed_data['month'].isin(summer_months)) &
            (self.processed_data['day_of_week'].isin(weekdays)) &
            (self.processed_data['hour'].isin(peak_hours))
        )
        
        self.processed_data.loc[peak_condition, 'is_peak'] = True
        
        # Handle holidays (Independence Day and Labor Day as off-peak)
        self._handle_holidays()
        
        return self.processed_data
    
    def _handle_holidays(self):
        """Mark Independence Day and Labor Day as off-peak."""
        # Independence Day (July 4th)
        july_4th = self.processed_data[
            (self.processed_data['month'] == 7) &
            (self.processed_data['datetime'].dt.day == 4)
        ]
        
        # Labor Day (first Monday in September)
        september_data = self.processed_data[self.processed_data['month'] == 9]
        for year in september_data['year'].unique():
            # Find first Monday in September
            first_monday = None
            for day in range(1, 8):
                try:
                    date = datetime(year, 9, day)
                    if date.weekday() == 0:  # Monday
                        first_monday = day
                        break
                except ValueError:
                    continue
            
            if first_monday:
                labor_day = self.processed_data[
                    (self.processed_data['month'] == 9) &
                    (self.processed_data['datetime'].dt.day == first_monday) &
                    (self.processed_data['year'] == year)
                ]
                self.processed_data.loc[labor_day.index, 'is_peak'] = False
        
        # Mark July 4th as off-peak
        self.processed_data.loc[july_4th.index, 'is_peak'] = False
    
    def get_monthly_summary(self) -> pd.DataFrame:
        """Generate monthly usage summary."""
        if self.processed_data is None:
            raise ValueError("Data not processed. Call classify_time_periods() first.")
        
        # Group by year and month
        monthly_summary = self.processed_data.groupby(['year', 'month']).agg({
            'kWh': ['sum', 'mean', 'max'],
            'is_peak': lambda x: (x == True).sum(),  # Count of peak hours
            'season': 'first'
        }).round(2)
        
        # Flatten column names
        monthly_summary.columns = ['total_kwh', 'avg_hourly_kwh', 'max_hourly_kwh', 'peak_hours_count', 'season']
        
        # Add peak and off-peak totals
        peak_usage = self.processed_data[self.processed_data['is_peak']].groupby(['year', 'month'])['kWh'].sum()
        off_peak_usage = self.processed_data[~self.processed_data['is_peak']].groupby(['year', 'month'])['kWh'].sum()
        
        monthly_summary['peak_kwh'] = peak_usage
        monthly_summary['off_peak_kwh'] = off_peak_usage
        
        # Fill NaN values with 0
        monthly_summary = monthly_summary.fillna(0)
        
        return monthly_summary
    
    def get_peak_usage_stats(self) -> Dict:
        """Get statistics about peak usage for shifting analysis."""
        if self.processed_data is None:
            raise ValueError("Data not processed. Call classify_time_periods() first.")
        
        peak_data = self.processed_data[self.processed_data['is_peak']]
        
        stats = {
            'total_peak_kwh': peak_data['kWh'].sum(),
            'avg_peak_kwh_per_hour': peak_data['kWh'].mean(),
            'max_peak_kwh': peak_data['kWh'].max(),
            'peak_hours_count': len(peak_data),
            'peak_kwh_by_month': peak_data.groupby(['year', 'month'])['kWh'].sum().to_dict(),
            'peak_kwh_by_hour': peak_data.groupby('hour')['kWh'].sum().to_dict()
        }
        
        return stats
    
    def get_data_summary(self) -> Dict:
        """Get overall data summary."""
        if self.processed_data is None:
            raise ValueError("Data not processed. Call classify_time_periods() first.")
        
        return {
            'total_records': len(self.processed_data),
            'date_range': {
                'start': self.processed_data['datetime'].min(),
                'end': self.processed_data['datetime'].max()
            },
            'total_usage_kwh': self.processed_data['kWh'].sum(),
            'peak_usage_kwh': self.processed_data[self.processed_data['is_peak']]['kWh'].sum(),
            'off_peak_usage_kwh': self.processed_data[~self.processed_data['is_peak']]['kWh'].sum(),
            'summer_usage_kwh': self.processed_data[self.processed_data['season'] == 'summer']['kWh'].sum(),
            'winter_usage_kwh': self.processed_data[self.processed_data['season'] == 'winter']['kWh'].sum()
        }