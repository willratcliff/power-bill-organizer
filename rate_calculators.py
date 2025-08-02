import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime


class TraditionalRateCalculator:
    """
    Calculates electricity bills under Georgia Power's Traditional Residential (R-30) rate structure.
    
    Rate Structure:
    - Basic Service Charge: $0.4603 per day
    - Winter (Oct-May): 8.0602¢/kWh for all usage
    - Summer (Jun-Sep): Tiered pricing
        - First 650 kWh: 8.6121¢/kWh
        - Next 350 kWh: 14.3047¢/kWh
        - Over 1000 kWh: 14.8051¢/kWh
    """
    
    def __init__(self):
        self.basic_service_charge = 0.4603  # per day
        self.winter_rate = 0.080602  # per kWh
        self.summer_tier1_rate = 0.086121  # per kWh (first 650 kWh)
        self.summer_tier2_rate = 0.143047  # per kWh (next 350 kWh)
        self.summer_tier3_rate = 0.148051  # per kWh (over 1000 kWh)
        self.summer_tier1_limit = 650  # kWh
        self.summer_tier2_limit = 1000  # kWh
        self.summer_months = [6, 7, 8, 9]
    
    def calculate_monthly_bill(self, usage_kwh: float, month: int, days_in_month: int) -> Dict:
        """
        Calculate monthly bill for given usage and month.
        
        Args:
            usage_kwh: Total kWh used in the month
            month: Month number (1-12)
            days_in_month: Number of days in the billing month
            
        Returns:
            Dictionary with bill breakdown
        """
        basic_charge = self.basic_service_charge * days_in_month
        
        if month in self.summer_months:
            energy_charge = self._calculate_summer_energy_charge(usage_kwh)
            season = 'summer'
        else:
            energy_charge = usage_kwh * self.winter_rate
            season = 'winter'
        
        total_bill = basic_charge + energy_charge
        
        return {
            'basic_charge': basic_charge,
            'energy_charge': energy_charge,
            'total_bill': total_bill,
            'usage_kwh': usage_kwh,
            'season': season,
            'month': month,
            'days_in_month': days_in_month,
            'avg_rate_per_kwh': energy_charge / usage_kwh if usage_kwh > 0 else 0
        }
    
    def _calculate_summer_energy_charge(self, usage_kwh: float) -> float:
        """Calculate energy charge for summer months with tiered pricing."""
        energy_charge = 0
        
        if usage_kwh <= self.summer_tier1_limit:
            # All usage in tier 1
            energy_charge = usage_kwh * self.summer_tier1_rate
        elif usage_kwh <= self.summer_tier2_limit:
            # Usage spans tier 1 and tier 2
            tier1_charge = self.summer_tier1_limit * self.summer_tier1_rate
            tier2_usage = usage_kwh - self.summer_tier1_limit
            tier2_charge = tier2_usage * self.summer_tier2_rate
            energy_charge = tier1_charge + tier2_charge
        else:
            # Usage spans all three tiers
            tier1_charge = self.summer_tier1_limit * self.summer_tier1_rate
            tier2_usage = self.summer_tier2_limit - self.summer_tier1_limit
            tier2_charge = tier2_usage * self.summer_tier2_rate
            tier3_usage = usage_kwh - self.summer_tier2_limit
            tier3_charge = tier3_usage * self.summer_tier3_rate
            energy_charge = tier1_charge + tier2_charge + tier3_charge
        
        return energy_charge
    
    def calculate_annual_bill(self, monthly_usage: Dict) -> Dict:
        """
        Calculate annual bill from monthly usage data.
        
        Args:
            monthly_usage: Dictionary with (year, month) keys and usage values
            
        Returns:
            Dictionary with annual bill breakdown
        """
        monthly_bills = []
        total_bill = 0
        total_usage = 0
        
        for (year, month), usage in monthly_usage.items():
            # Get days in month
            if month == 2:  # February
                days_in_month = 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28
            elif month in [4, 6, 9, 11]:
                days_in_month = 30
            else:
                days_in_month = 31
            
            bill = self.calculate_monthly_bill(usage, month, days_in_month)
            monthly_bills.append(bill)
            total_bill += bill['total_bill']
            total_usage += usage
        
        return {
            'monthly_bills': monthly_bills,
            'total_annual_bill': total_bill,
            'total_annual_usage': total_usage,
            'average_monthly_bill': total_bill / len(monthly_bills) if monthly_bills else 0,
            'average_rate_per_kwh': total_bill / total_usage if total_usage > 0 else 0
        }


class TOURateCalculator:
    """
    Calculates electricity bills under Georgia Power's Time-of-Use Residential Demand (TOU-RD-11) rate structure.
    
    Rate Structure:
    - Basic Service Charge: $0.4603 per day
    - On-Peak (2-7 PM, Mon-Fri, Jun-Sep): 14.2986¢/kWh
    - Off-Peak (all other times): 1.5288¢/kWh
    - Demand Charge: $12.21 per kW (monthly peak)
    """
    
    def __init__(self):
        self.basic_service_charge = 0.4603  # per day
        self.on_peak_rate = 0.142986  # per kWh
        self.off_peak_rate = 0.015288  # per kWh
        self.demand_charge_rate = 12.21  # per kW
    
    def calculate_monthly_bill(self, peak_usage_kwh: float, off_peak_usage_kwh: float, 
                             max_demand_kw: float, days_in_month: int) -> Dict:
        """
        Calculate monthly bill for TOU rate structure.
        
        Args:
            peak_usage_kwh: kWh used during peak hours
            off_peak_usage_kwh: kWh used during off-peak hours
            max_demand_kw: Maximum hourly demand during the month
            days_in_month: Number of days in the billing month
            
        Returns:
            Dictionary with bill breakdown
        """
        basic_charge = self.basic_service_charge * days_in_month
        peak_energy_charge = peak_usage_kwh * self.on_peak_rate
        off_peak_energy_charge = off_peak_usage_kwh * self.off_peak_rate
        demand_charge = max_demand_kw * self.demand_charge_rate
        
        total_energy_charge = peak_energy_charge + off_peak_energy_charge
        total_bill = basic_charge + total_energy_charge + demand_charge
        total_usage = peak_usage_kwh + off_peak_usage_kwh
        
        return {
            'basic_charge': basic_charge,
            'peak_energy_charge': peak_energy_charge,
            'off_peak_energy_charge': off_peak_energy_charge,
            'total_energy_charge': total_energy_charge,
            'demand_charge': demand_charge,
            'total_bill': total_bill,
            'peak_usage_kwh': peak_usage_kwh,
            'off_peak_usage_kwh': off_peak_usage_kwh,
            'total_usage_kwh': total_usage,
            'max_demand_kw': max_demand_kw,
            'days_in_month': days_in_month,
            'avg_rate_per_kwh': total_energy_charge / total_usage if total_usage > 0 else 0
        }
    
    def calculate_annual_bill(self, monthly_data: List[Dict]) -> Dict:
        """
        Calculate annual bill from monthly TOU data.
        
        Args:
            monthly_data: List of monthly data dictionaries with keys:
                - peak_usage_kwh
                - off_peak_usage_kwh
                - max_demand_kw
                - days_in_month
                - year
                - month
                
        Returns:
            Dictionary with annual bill breakdown
        """
        monthly_bills = []
        total_bill = 0
        total_peak_usage = 0
        total_off_peak_usage = 0
        total_demand_charges = 0
        
        for month_data in monthly_data:
            bill = self.calculate_monthly_bill(
                month_data['peak_usage_kwh'],
                month_data['off_peak_usage_kwh'],
                month_data['max_demand_kw'],
                month_data['days_in_month']
            )
            
            # Add month/year info to bill
            bill['year'] = month_data['year']
            bill['month'] = month_data['month']
            
            monthly_bills.append(bill)
            total_bill += bill['total_bill']
            total_peak_usage += bill['peak_usage_kwh']
            total_off_peak_usage += bill['off_peak_usage_kwh']
            total_demand_charges += bill['demand_charge']
        
        total_usage = total_peak_usage + total_off_peak_usage
        
        return {
            'monthly_bills': monthly_bills,
            'total_annual_bill': total_bill,
            'total_peak_usage': total_peak_usage,
            'total_off_peak_usage': total_off_peak_usage,
            'total_annual_usage': total_usage,
            'total_demand_charges': total_demand_charges,
            'average_monthly_bill': total_bill / len(monthly_bills) if monthly_bills else 0,
            'average_rate_per_kwh': (total_bill - total_demand_charges) / total_usage if total_usage > 0 else 0
        }
    
    def calculate_shifting_scenario(self, monthly_data: List[Dict], shift_percentage: float) -> Dict:
        """
        Calculate bill impact of shifting peak usage to off-peak.
        
        Args:
            monthly_data: List of monthly data dictionaries
            shift_percentage: Percentage of peak usage to shift (0.0 to 1.0)
            
        Returns:
            Dictionary with shifting scenario results
        """
        original_bills = []
        shifted_bills = []
        total_peak_kwh_shifted = 0
        
        for month_data in monthly_data:
            # Calculate original bill
            original_bill = self.calculate_monthly_bill(
                month_data['peak_usage_kwh'],
                month_data['off_peak_usage_kwh'],
                month_data['max_demand_kw'],
                month_data['days_in_month']
            )
            original_bills.append(original_bill)
            
            # Calculate shifted usage
            peak_kwh_to_shift = month_data['peak_usage_kwh'] * shift_percentage
            new_peak_usage = month_data['peak_usage_kwh'] - peak_kwh_to_shift
            new_off_peak_usage = month_data['off_peak_usage_kwh'] + peak_kwh_to_shift
            total_peak_kwh_shifted += peak_kwh_to_shift
            
            # Assume demand reduction proportional to peak usage reduction
            # This is a simplification - actual demand reduction depends on which hours are shifted
            new_max_demand = month_data['max_demand_kw'] * (1 - shift_percentage * 0.5)
            
            # Calculate bill with shifted usage
            shifted_bill = self.calculate_monthly_bill(
                new_peak_usage,
                new_off_peak_usage,
                new_max_demand,
                month_data['days_in_month']
            )
            shifted_bills.append(shifted_bill)
        
        original_total = sum(bill['total_bill'] for bill in original_bills)
        shifted_total = sum(bill['total_bill'] for bill in shifted_bills)
        total_savings = original_total - shifted_total
        
        return {
            'shift_percentage': shift_percentage,
            'total_peak_kwh_shifted': total_peak_kwh_shifted,
            'original_annual_bill': original_total,
            'shifted_annual_bill': shifted_total,
            'annual_savings': total_savings,
            'savings_percentage': (total_savings / original_total * 100) if original_total > 0 else 0,
            'original_monthly_bills': original_bills,
            'shifted_monthly_bills': shifted_bills
        }