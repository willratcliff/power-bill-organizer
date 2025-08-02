#!/usr/bin/env python3
"""
TOU-REO-18 Calculator - Residential Energy Only (No Demand Charges)
"Nights and Weekends" plan
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import calendar

class TOUREOCalculator:
    """
    TOU-REO-18 rate calculator - Residential Energy Only (No Demand Charges).
    This is the "Nights and Weekends" plan.
    """
    
    def __init__(self):
        # TOU-REO-18 rates (from tariff document)
        self.basic_service_charge = 0.4603  # per day (same as TOU-RD-11)
        self.on_peak_rate = 0.297868  # per kWh (29.7868¢)
        self.off_peak_rate = 0.076281  # per kWh (7.6281¢)
        
        # NO DEMAND CHARGES in this plan!
        self.demand_charge_rate = 0.0  # $0/kW
        
        # Hidden fee factor (same as other plans)
        self.fee_factor = 1.137  # 13.7% increase for all fees
        
        # Fee breakdown (same as other plans)
        self.fees = {
            'environmental_compliance': 'Environmental Compliance Cost Recovery',
            'demand_side_management': 'Demand Side Management Residential Schedule',
            'fuel_cost_recovery': 'Fuel Cost Recovery',
            'municipal_franchise': 'Municipal Franchise Fee'
        }
    
    def calculate_monthly_bill(self, peak_usage_kwh: float, off_peak_usage_kwh: float, 
                             max_demand_kw: float, days_in_month: int) -> Dict:
        """
        Calculate monthly TOU-REO bill (no demand charges).
        
        Args:
            peak_usage_kwh: kWh used during peak hours
            off_peak_usage_kwh: kWh used during off-peak hours
            max_demand_kw: Maximum hourly demand (not used in REO)
            days_in_month: Number of days in the billing month
            
        Returns:
            Dictionary with bill breakdown including fees
        """
        # Base charges (published rates)
        basic_charge = self.basic_service_charge * days_in_month
        peak_energy_charge = peak_usage_kwh * self.on_peak_rate
        off_peak_energy_charge = off_peak_usage_kwh * self.off_peak_rate
        demand_charge = 0.0  # NO demand charges in REO plan
        
        # Subtotal before fees
        subtotal = basic_charge + peak_energy_charge + off_peak_energy_charge + demand_charge
        
        # Apply hidden fees (13.7% increase)
        fee_amount = subtotal * (self.fee_factor - 1)
        total_bill = subtotal + fee_amount
        
        total_energy_charge = peak_energy_charge + off_peak_energy_charge
        total_usage = peak_usage_kwh + off_peak_usage_kwh
        
        return {
            'basic_charge': basic_charge,
            'peak_energy_charge': peak_energy_charge,
            'off_peak_energy_charge': off_peak_energy_charge,
            'total_energy_charge': total_energy_charge,
            'demand_charge': demand_charge,  # Always $0
            'subtotal': subtotal,
            'fee_amount': fee_amount,
            'fee_factor': self.fee_factor,
            'total_bill': total_bill,
            'peak_usage_kwh': peak_usage_kwh,
            'off_peak_usage_kwh': off_peak_usage_kwh,
            'total_usage_kwh': total_usage,
            'max_demand_kw': max_demand_kw,  # Recorded but not charged
            'days_in_month': days_in_month,
            'avg_rate_per_kwh': total_bill / total_usage if total_usage > 0 else 0,
            'energy_rate_per_kwh': total_energy_charge / total_usage if total_usage > 0 else 0
        }
    
    def calculate_annual_bill(self, monthly_data: List[Dict]) -> Dict:
        """
        Calculate annual TOU-REO bill (no demand charges).
        
        Args:
            monthly_data: List of monthly data dictionaries
            
        Returns:
            Dictionary with annual bill breakdown
        """
        monthly_bills = []
        total_bill = 0
        total_peak_usage = 0
        total_off_peak_usage = 0
        total_demand_charges = 0  # Always $0
        total_fee_amount = 0
        total_subtotal = 0
        
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
            total_demand_charges += bill['demand_charge']  # Always $0
            total_fee_amount += bill['fee_amount']
            total_subtotal += bill['subtotal']
        
        total_usage = total_peak_usage + total_off_peak_usage
        
        return {
            'monthly_bills': monthly_bills,
            'total_annual_bill': total_bill,
            'total_peak_usage': total_peak_usage,
            'total_off_peak_usage': total_off_peak_usage,
            'total_annual_usage': total_usage,
            'total_demand_charges': total_demand_charges,  # Always $0
            'total_fee_amount': total_fee_amount,
            'total_subtotal': total_subtotal,
            'average_monthly_bill': total_bill / len(monthly_bills) if monthly_bills else 0,
            'average_rate_per_kwh': total_bill / total_usage if total_usage > 0 else 0,
            'fee_impact_percent': (total_fee_amount / total_subtotal) * 100 if total_subtotal > 0 else 0
        }
    
    def calculate_shifting_scenario(self, monthly_data: List[Dict], shift_percentage: float) -> Dict:
        """
        Calculate bill impact of shifting peak usage to off-peak (no demand charges to reduce).
        
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
            
            # No demand charge impact in REO plan
            new_max_demand = month_data['max_demand_kw']  # Unchanged (not used anyway)
            
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
    
    def get_rate_breakdown(self) -> Dict:
        """Get detailed rate breakdown including fee information."""
        return {
            'basic_service_charge': f"${self.basic_service_charge:.4f}/day",
            'on_peak_rate': f"{self.on_peak_rate:.6f} $/kWh",
            'off_peak_rate': f"{self.off_peak_rate:.6f} $/kWh",
            'demand_charge_rate': f"${self.demand_charge_rate:.2f}/kW (NO DEMAND CHARGES)",
            'fee_factor': f"{self.fee_factor:.3f}x ({(self.fee_factor-1)*100:.1f}% increase)",
            'included_fees': list(self.fees.values()),
            'plan_type': 'TOU-REO-18 (Residential Energy Only - Nights and Weekends)'
        }


def main():
    """Test the TOU-REO calculator."""
    from data_processor import PowerDataProcessor
    from demand_calculator import DemandCalculator
    
    # Load data
    data_processor = PowerDataProcessor('GPC_Usage_2024-06-01-2025-07-14.csv')
    data_processor.load_data()
    processed_data = data_processor.classify_time_periods()
    
    demand_calculator = DemandCalculator(processed_data)
    tou_monthly_data = demand_calculator.get_tou_monthly_data()
    
    # Calculate TOU-REO bill
    tou_reo_calc = TOUREOCalculator()
    tou_reo_results = tou_reo_calc.calculate_annual_bill(tou_monthly_data)
    
    print("=" * 60)
    print("TOU-REO-18 CALCULATOR TEST")
    print("=" * 60)
    print(f"Plan: {tou_reo_calc.get_rate_breakdown()['plan_type']}")
    print(f"On-Peak Rate: {tou_reo_calc.on_peak_rate:.6f} $/kWh")
    print(f"Off-Peak Rate: {tou_reo_calc.off_peak_rate:.6f} $/kWh")
    print(f"Demand Charges: {tou_reo_calc.get_rate_breakdown()['demand_charge_rate']}")
    print()
    print(f"Annual Bill: ${tou_reo_results['total_annual_bill']:,.2f}")
    print(f"Peak Usage: {tou_reo_results['total_peak_usage']:,.0f} kWh")
    print(f"Off-Peak Usage: {tou_reo_results['total_off_peak_usage']:,.0f} kWh")
    print(f"Total Usage: {tou_reo_results['total_annual_usage']:,.0f} kWh")
    print(f"Average Rate: ${tou_reo_results['average_rate_per_kwh']:.4f}/kWh")
    print(f"Hidden Fees: ${tou_reo_results['total_fee_amount']:,.2f}")


if __name__ == "__main__":
    main()