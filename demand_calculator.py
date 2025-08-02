import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import calendar


class DemandCalculator:
    """
    Calculates monthly peak demand from hourly usage data.
    Handles demand calculations for TOU rate structures.
    """
    
    def __init__(self, processed_data: pd.DataFrame):
        """
        Initialize with processed data from PowerDataProcessor.
        
        Args:
            processed_data: DataFrame with datetime, kWh, and time period classifications
        """
        self.data = processed_data.copy()
        self.monthly_demands = None
    
    def calculate_monthly_demands(self) -> pd.DataFrame:
        """
        Calculate monthly peak demand (highest hourly usage) for each month.
        
        Returns:
            DataFrame with monthly peak demands and related statistics
        """
        # Group by year and month, find max hourly usage
        monthly_demands = self.data.groupby(['year', 'month']).agg({
            'kWh': ['max', 'mean', 'std', 'sum'],
            'datetime': ['min', 'max', 'count']
        }).round(4)
        
        # Flatten column names
        monthly_demands.columns = [
            'peak_demand_kw', 'avg_hourly_usage', 'std_hourly_usage', 'total_usage',
            'month_start', 'month_end', 'hours_in_month'
        ]
        
        # Add additional calculated fields
        monthly_demands['days_in_month'] = monthly_demands['hours_in_month'] / 24
        monthly_demands['load_factor'] = (monthly_demands['avg_hourly_usage'] / 
                                        monthly_demands['peak_demand_kw']).round(4)
        
        # Add month names for readability
        monthly_demands['month_name'] = monthly_demands.index.get_level_values('month').map(
            {i: calendar.month_name[i] for i in range(1, 13)}
        )
        
        # Find the datetime of peak demand occurrence
        peak_demand_times = []
        for (year, month), row in monthly_demands.iterrows():
            month_data = self.data[
                (self.data['year'] == year) & 
                (self.data['month'] == month)
            ]
            peak_time = month_data.loc[month_data['kWh'].idxmax(), 'datetime']
            peak_demand_times.append(peak_time)
        
        monthly_demands['peak_demand_time'] = peak_demand_times
        
        # Add day of week and hour of peak demand
        monthly_demands['peak_day_of_week'] = [
            dt.strftime('%A') for dt in peak_demand_times
        ]
        monthly_demands['peak_hour'] = [
            dt.hour for dt in peak_demand_times
        ]
        
        # Classify if peak occurred during TOU peak hours
        monthly_demands['peak_during_tou_peak'] = [
            self._is_tou_peak_time(dt) for dt in peak_demand_times
        ]
        
        self.monthly_demands = monthly_demands
        return monthly_demands
    
    def _is_tou_peak_time(self, dt: datetime) -> bool:
        """Check if datetime falls during TOU peak hours."""
        # TOU peak: 2-7 PM (14-18), Monday-Friday, June-September
        if dt.month not in [6, 7, 8, 9]:
            return False
        if dt.weekday() > 4:  # Saturday=5, Sunday=6
            return False
        if dt.hour < 14 or dt.hour > 18:
            return False
        
        # Check for holidays (simplified - just July 4th and Labor Day)
        if dt.month == 7 and dt.day == 4:
            return False
        
        # Labor Day (first Monday in September)
        if dt.month == 9:
            first_monday = None
            for day in range(1, 8):
                if datetime(dt.year, 9, day).weekday() == 0:
                    first_monday = day
                    break
            if first_monday and dt.day == first_monday:
                return False
        
        return True
    
    def get_demand_statistics(self) -> Dict:
        """Get summary statistics for demand patterns."""
        if self.monthly_demands is None:
            self.calculate_monthly_demands()
        
        return {
            'avg_monthly_peak_demand': self.monthly_demands['peak_demand_kw'].mean(),
            'max_annual_peak_demand': self.monthly_demands['peak_demand_kw'].max(),
            'min_monthly_peak_demand': self.monthly_demands['peak_demand_kw'].min(),
            'std_monthly_peak_demand': self.monthly_demands['peak_demand_kw'].std(),
            'avg_load_factor': self.monthly_demands['load_factor'].mean(),
            'peaks_during_tou_hours': self.monthly_demands['peak_during_tou_peak'].sum(),
            'peak_hour_distribution': self.monthly_demands['peak_hour'].value_counts().to_dict(),
            'peak_day_distribution': self.monthly_demands['peak_day_of_week'].value_counts().to_dict()
        }
    
    def calculate_demand_charges(self) -> pd.DataFrame:
        """
        Calculate monthly demand charges based on TOU-RD-11 rates.
        
        Returns:
            DataFrame with monthly demand charges
        """
        if self.monthly_demands is None:
            self.calculate_monthly_demands()
        
        demand_rate = 12.21  # $/kW from TOU-RD-11 rate
        
        demand_charges = self.monthly_demands.copy()
        demand_charges['demand_charge'] = (
            demand_charges['peak_demand_kw'] * demand_rate
        ).round(2)
        
        return demand_charges[['peak_demand_kw', 'demand_charge', 'month_name', 
                              'peak_demand_time', 'peak_during_tou_peak']]
    
    def analyze_demand_reduction_potential(self, target_reduction_percent: float = 0.1) -> Dict:
        """
        Analyze potential for demand reduction through peak shaving.
        
        Args:
            target_reduction_percent: Target reduction in peak demand (0.0 to 1.0)
            
        Returns:
            Dictionary with demand reduction analysis
        """
        if self.monthly_demands is None:
            self.calculate_monthly_demands()
        
        demand_rate = 12.21  # $/kW
        
        # Calculate current annual demand charges
        current_annual_demand_charge = (
            self.monthly_demands['peak_demand_kw'] * demand_rate
        ).sum()
        
        # Calculate potential savings from demand reduction
        reduced_peaks = self.monthly_demands['peak_demand_kw'] * (1 - target_reduction_percent)
        potential_annual_demand_charge = (reduced_peaks * demand_rate).sum()
        potential_savings = current_annual_demand_charge - potential_annual_demand_charge
        
        # Analyze which months have highest savings potential
        monthly_savings = (self.monthly_demands['peak_demand_kw'] * target_reduction_percent * demand_rate)
        
        return {
            'target_reduction_percent': target_reduction_percent,
            'current_annual_demand_charge': current_annual_demand_charge,
            'potential_annual_demand_charge': potential_annual_demand_charge,
            'potential_annual_savings': potential_savings,
            'avg_monthly_savings': potential_savings / 12,
            'monthly_savings_potential': monthly_savings.to_dict(),
            'highest_savings_months': monthly_savings.nlargest(3).index.tolist(),
            'avg_peak_reduction_kw': (self.monthly_demands['peak_demand_kw'] * target_reduction_percent).mean()
        }
    
    def get_tou_monthly_data(self) -> List[Dict]:
        """
        Prepare monthly data for TOU rate calculations.
        
        Returns:
            List of monthly data dictionaries for TOU calculator
        """
        if self.monthly_demands is None:
            self.calculate_monthly_demands()
        
        # Get peak and off-peak usage by month
        monthly_tou_data = []
        
        for (year, month), demand_row in self.monthly_demands.iterrows():
            month_data = self.data[
                (self.data['year'] == year) & 
                (self.data['month'] == month)
            ]
            
            peak_usage = month_data[month_data['is_peak']]['kWh'].sum()
            off_peak_usage = month_data[~month_data['is_peak']]['kWh'].sum()
            
            monthly_tou_data.append({
                'year': year,
                'month': month,
                'peak_usage_kwh': peak_usage,
                'off_peak_usage_kwh': off_peak_usage,
                'max_demand_kw': demand_row['peak_demand_kw'],
                'days_in_month': int(demand_row['days_in_month'])
            })
        
        return monthly_tou_data
    
    def get_traditional_monthly_data(self) -> Dict:
        """
        Prepare monthly data for traditional rate calculations.
        
        Returns:
            Dictionary with (year, month) keys and total usage values
        """
        monthly_usage = {}
        
        for (year, month), group in self.data.groupby(['year', 'month']):
            monthly_usage[(year, month)] = group['kWh'].sum()
        
        return monthly_usage