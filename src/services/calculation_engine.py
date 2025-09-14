"""
Calculation engine for URDB Tariff Viewer.

This module contains the core utility bill calculation logic and validation functions.
"""

import pandas as pd
import numpy as np
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Union

from src.utils.exceptions import InvalidTariffError, InvalidLoadProfileError


def validate_tariff(tariff: Dict, default_voltage: float = 480.0) -> None:
    """Validate that tariff has required fields and structure
    
    Parameters:
    -----------
    tariff : Dict
        The tariff data to validate
    default_voltage : float
        The default voltage level of the customer (default: 480V)
    """
    # Check for required energy fields
    required_fields = [
        'energyratestructure',
        'energyweekdayschedule',
        'energyweekendschedule'
    ]
    
    # Define fields that must be present if demand charges exist
    demand_fields = [
        'demandratestructure',
        'demandweekdayschedule',
        'demandweekendschedule'
    ]
    
    for field in required_fields:
        if field not in tariff:
            raise InvalidTariffError(f"Missing required field: {field}")
        
    # Validate energy schedule lengths
    if len(tariff['energyweekdayschedule']) != 12 or len(tariff['energyweekendschedule']) != 12:
        raise InvalidTariffError("Energy schedules must have 12 months")
        
    # Validate flat demand structure if present
    if 'flatdemandstructure' in tariff and 'flatdemandmonths' in tariff:
        if len(tariff['flatdemandmonths']) != 12:
            raise InvalidTariffError("Flat demand months must have 12 entries")
            
    # Check demand schedules only if demand rates exist
    if 'demandratestructure' in tariff and tariff['demandratestructure']:
        if 'demandweekdayschedule' not in tariff or 'demandweekendschedule' not in tariff:
            raise InvalidTariffError("Demand schedules required when demand rates exist")
        if len(tariff['demandweekdayschedule']) != 12 or len(tariff['demandweekendschedule']) != 12:
            raise InvalidTariffError("Demand schedules must have 12 months")
            
    # Check if any demand fields are present - if one is present, all must be
    has_demand = any(field in tariff for field in demand_fields)
    if has_demand:
        missing_demand = [field for field in demand_fields if field not in tariff]
        if missing_demand:
            raise InvalidTariffError(f"Missing demand fields: {', '.join(missing_demand)}")
    
    # Validate rate structures have at least one tier
    if not tariff['energyratestructure']:
        raise InvalidTariffError("Energy rate structure cannot be empty")
    
    if has_demand and not tariff['demandratestructure']:
        raise InvalidTariffError("Demand rate structure cannot be empty when demand charges are present")
        
    # Validate voltage level compatibility
    min_voltage = float(tariff.get('voltageminimum', 0))
    max_voltage = float(tariff.get('voltagemaximum', float('inf')))
    
    if min_voltage > default_voltage:
        print(f"WARNING: Tariff minimum voltage ({min_voltage}V) is higher than default voltage ({default_voltage}V)")
    if max_voltage < default_voltage:
        print(f"WARNING: Tariff maximum voltage ({max_voltage}V) is lower than default voltage ({default_voltage}V)")


def get_rate_for_consumption(structure: List[Dict], consumption: float) -> tuple:
    """Calculate rate and adjustment for given consumption across tiers
    Returns (total_charge, total_adj)"""
    remaining = consumption
    total_charge = 0
    total_adj = 0
    
    for tier in structure:
        tier_max = tier.get('max', float('inf'))
        rate = tier.get('rate', 0)
        adj = tier.get('adj', 0)
        
        # Amount that falls into this tier
        amount = min(remaining, tier_max) if tier_max != float('inf') else remaining
        total_charge += amount * rate
        total_adj += amount * adj
        remaining -= amount
        
        if remaining <= 0:
            break
            
    return total_charge, total_adj


def get_rate_for_demand(structure: List[Dict], demand: float, reactive_power_charge: float = 0.0, power_factor: float = 0.95) -> tuple:
    """Calculate demand rate and adjustment for given demand across tiers
    
    Parameters:
    -----------
    structure : List[Dict]
        The demand rate structure from the tariff
    demand : float
        The demand value to calculate charges for
    reactive_power_charge : float
        The charge per kVAR for reactive power (default: 0.0)
    power_factor : float
        The power factor for reactive power calculations (default: 0.95)
        
    Returns:
    --------
    tuple
        (total_charge, total_adj) including reactive power charges if applicable
    """
    total_charge = 0
    total_adj = 0
    remaining = demand
    
    # Add reactive power charge if applicable
    if reactive_power_charge > 0 and power_factor < 1:
        apparent_power = demand / power_factor
        reactive_power = (apparent_power**2 - demand**2)**0.5
        total_charge += reactive_power * reactive_power_charge

    for tier in structure:
        tier_max = tier.get('max', float('inf'))
        rate = tier.get('rate', 0)
        adj = tier.get('adj', 0)
        
        amount = min(remaining, tier_max) if tier_max != float('inf') else remaining
        total_charge += amount * rate
        total_adj += amount * adj
        remaining -= amount
        
        if remaining <= 0:
            break
            
    return total_charge, total_adj


def extract_adjustments(tariff: Dict) -> Dict[str, float]:
    """Extract rate adjustments from tariff
    Returns a dictionary of adjustments with their values and types (per_kwh or per_kw)"""
    adjustments = {}
    description = tariff.get('description', '')
    energy_comments = tariff.get('energycomments', '')
    demand_comments = tariff.get('demandcomments', '')

    # Look for EV discount
    if "electric vehicle discount" in description.lower():
        ev_pattern = r'-(\d+\.?\d*)\s*cents\/kWh'
        ev_matches = re.findall(ev_pattern, description)
        if ev_matches:
            adjustments['ev_discount'] = -float(ev_matches[0])/100  # Convert cents to dollars
            
    # Extract any kWh-based charges from energy comments
    if 'delivery charges' in energy_comments.lower():
        delivery_pattern = r'delivery\s+charges.*?(\d+\.?\d*)'
        delivery_matches = re.findall(delivery_pattern, energy_comments, re.IGNORECASE)
        if delivery_matches:
            adjustments['delivery_per_kwh'] = float(delivery_matches[0])
            
    # Look for adjustments in parentheses
    adj_pattern = r'([A-Za-z]+)\s*\([\$]?([\d.]+)\)'
    found_adjustments = re.findall(adj_pattern, description)
    
    for adj_name, adj_value in found_adjustments:
        adj_name = adj_name.strip()
        value = float(adj_value)
        
        # Determine if it's per kWh or per kW based on the adjustment name
        if adj_name in ['ECA', 'VEA', 'CRPSEA', 'VRPSEA']:
            adjustments[f'{adj_name}_per_kwh'] = value
        elif adj_name in ['ESA', 'RCA', 'IRCA']:
            adjustments[f'{adj_name}_per_kw'] = value
            
    return adjustments


def ensure_integer_columns(df: pd.DataFrame, integer_columns: List[str]) -> pd.DataFrame:
    """Ensure specified columns are integers"""
    for col in integer_columns:
        if col in df.columns:
            df[col] = df[col].astype(int)
    return df


def load_profile_csv(path: str) -> pd.DataFrame:
    """Load and validate load profile data"""
    try:
        df = pd.read_csv(path, parse_dates=['timestamp'])
        if 'timestamp' not in df.columns:
            raise InvalidLoadProfileError("CSV must have 'timestamp' column")
            
        if 'load_kW' in df.columns:
            # 15-min interval: kWh = kW * 0.25
            df['kWh'] = df['load_kW'] * 0.25
        elif 'kWh' in df.columns:
            pass  # Already has kWh
        else:
            raise InvalidLoadProfileError("CSV must have 'load_kW' or 'kWh' column")
            
        # Validate timestamp sorting and continuity
        if not df['timestamp'].is_monotonic_increasing:
            df = df.sort_values('timestamp')
            
        df['month'] = df['timestamp'].dt.month
        df['year'] = df['timestamp'].dt.year
        df['hour'] = df['timestamp'].dt.hour
        df['weekday'] = df['timestamp'].dt.weekday
        
        # Ensure integer columns
        integer_columns = ['month', 'year', 'hour', 'weekday']
        df = ensure_integer_columns(df, integer_columns)
        
        return df
    except Exception as e:
        raise InvalidLoadProfileError(f"Error loading load profile: {str(e)}")


def load_urdb_json(path: str) -> Dict:
    """Load and validate tariff data"""
    try:
        # First check if file exists
        if not os.path.exists(path):
            raise InvalidTariffError(f"Tariff file not found: {path}")
            
        with open(path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise InvalidTariffError(f"Invalid JSON format in tariff file: {str(e)}")
                
        if not isinstance(data, dict):
            raise InvalidTariffError("Tariff file must contain a JSON object")
            
        # Handle both direct tariff data and wrapped in 'items'
        if 'items' in data:
            if not isinstance(data['items'], list) or len(data['items']) == 0:
                raise InvalidTariffError("Tariff file 'items' must be a non-empty array")
            tariff = data['items'][0]  # Assume first item is the tariff
        else:
            tariff = data  # Direct tariff object
            
        validate_tariff(tariff)
        return tariff
        
    except InvalidTariffError:
        raise
    except Exception as e:
        raise InvalidTariffError(f"Error loading tariff: {str(e)}")


def calculate_monthly_bill(load_profile_path: str, urdb_json_path: str, save_csv: bool = False, default_voltage: float = 480.0) -> pd.DataFrame:
    """Calculate monthly utility bill with detailed breakdown of charges
    
    Parameters:
    -----------
    load_profile_path : str
        Path to CSV file containing load profile data with timestamp and load_kW columns
    urdb_json_path : str
        Path to JSON file containing URDB tariff data
    save_csv : bool, optional
        Whether to save results to a CSV file (default: False)
    default_voltage : float, optional
        The default voltage level of the customer (default: 480V)
        
    Returns:
    --------
    pd.DataFrame
        Monthly billing summary including:
        - Energy charges (base rate and adjustments)
        - Demand charges (TOU and flat rates)
        - Fixed charges
        - Period-specific usage and peaks
        - Load factors and statistics
    """
    
    # Load and validate inputs
    df = load_profile_csv(load_profile_path)
    tariff = load_urdb_json(urdb_json_path)
    
    # Validate tariff including voltage levels
    validate_tariff(tariff, default_voltage)
    
    # Get rate adjustments from tariff
    adjustments = extract_adjustments(tariff)
    
    # Document TOU periods
    period_mapping = {
        'energy': {
            0: 'super_off_peak',
            1: 'off_peak',
            2: 'on_peak',
            3: 'super_off_peak_summer',
            4: 'mid_peak_summer',
            5: 'on_peak_summer'
        },
        'demand': {
            0: 'off_peak',
            1: 'mid_peak',
            2: 'high_peak',
            3: 'critical_peak'
        },
        'season': {
            'summer': [6, 7, 8, 9],  # Jun-Sep
            'winter': [1, 2, 3, 4, 5, 10, 11, 12]  # Oct-May
        }
    }
    
    def get_period_name(period_type: str, period_num: int, month: int) -> str:
        """Get the name of a TOU period"""
        if period_type not in period_mapping:
            return f"period_{period_num}"
            
        # Determine season
        season = 'summer' if month in period_mapping['season']['summer'] else 'winter'
        period_dict = period_mapping[period_type]
        
        # Try to get period name
        period_name = period_dict.get(period_num, f"period_{period_num}")
        
        # Add season for clarity
        return f"{period_name}_{season}"
    
    # Convert numeric columns to proper types
    df['month'] = df['month'].astype(int)
    df['year'] = df['year'].astype(int)
    df['hour'] = df['hour'].astype(int)
    df['weekday'] = df['weekday'].astype(int)
    
    # Calculate TOU periods
    df['is_weekend'] = df['weekday'] >= 5
    df['energy_period'] = [int(tariff['energyweekendschedule'][row['month']-1][row['hour']])
                          if row['is_weekend'] else int(tariff['energyweekdayschedule'][row['month']-1][row['hour']])
                          for idx, row in df.iterrows()]
    
    # Add demand periods only if demand structure and schedules exist
    has_demand = ('demandratestructure' in tariff and tariff['demandratestructure'] and
                 'demandweekdayschedule' in tariff and 'demandweekendschedule' in tariff)
    
    if has_demand:
        df['demand_period'] = [int(tariff['demandweekendschedule'][row['month']-1][row['hour']])
                              if row['is_weekend'] else int(tariff['demandweekdayschedule'][row['month']-1][row['hour']])
                              for idx, row in df.iterrows()]
    else:
        df['demand_period'] = 0  # Default to single period if no demand structure

    # Energy charges by period with adjustments
    energy_charges = []
    energy_adjs = []
    for idx, row in df.iterrows():
        period = int(row['energy_period'])
        kwh = row['kWh']
        charge, adj = get_rate_for_consumption(tariff['energyratestructure'][period], kwh)
        energy_charges.append(charge)
        energy_adjs.append(adj)
    df['energy_charge'] = energy_charges
    df['energy_adjustment'] = energy_adjs

    # Demand charges by period with ratchet
    peak_history = {}  # Store historical peaks for ratchet
    demand_charges = []
    
    # Get reactive power charge if present
    reactive_power_charge = tariff.get('demandreactivepowercharge', 0.0)
    
    # Sort by timestamp to process months in order
    # First get the demand periods per timestamp if demand charges exist
    has_demand_charges = ('demandratestructure' in tariff and tariff['demandratestructure'] and
                         'demandweekdayschedule' in tariff and 'demandweekendschedule' in tariff)
    
    demand_charges = []
    if has_demand_charges:
        # Process demand charges
        demand_peaks = df.groupby(['year', 'month', 'demand_period'])['load_kW'].max().reset_index()
        demand_peaks['demand_period'] = demand_peaks['demand_period'].astype(int)
        demand_peaks['year'] = demand_peaks['year'].astype(int)
        demand_peaks['month'] = demand_peaks['month'].astype(int)
        
        # Process each demand peak
        for _, row in demand_peaks.iterrows():
            year = int(row['year'])
            month = int(row['month'])
            period = int(row['demand_period'])
            peak_kw = float(row['load_kW'])  # Keep as float for calculations
            
            # Apply demand ratchet if applicable
            month_idx = month - 1  # Convert to 0-based index
            ratchet_pct = tariff.get('demandratchetpercentage', [0]*12)[month_idx]
            min_ratchet = tariff.get('mindemandratchet', [0]*12)[month_idx]
            power_factor = tariff.get('powerfactor', 0.95)  # Default power factor if not specified
            
            if ratchet_pct > 0 or min_ratchet > 0:
                # Look back 11 months for historical peak
                historical_peak = max([v for k, v in peak_history.items() 
                                    if k[0] == year and k[1] < month] or [0])
                                    
                # Apply percentage ratchet
                if ratchet_pct > 0:
                    peak_kw = max(peak_kw, historical_peak * ratchet_pct/100)
                    
                # Apply minimum ratchet if specified
                if min_ratchet > 0:
                    peak_kw = max(peak_kw, min_ratchet)
            
            # Store this peak for future ratchet calculations
            peak_history[(year, month)] = peak_kw
            
            # Calculate demand charge and adjustment including reactive power
            charge, adj = get_rate_for_demand(
                tariff['demandratestructure'][int(period)], 
                peak_kw,
                reactive_power_charge=reactive_power_charge,
                power_factor=power_factor)
            
            demand_charges.append({
                'year': year,
                'month': month,
                'demand_period': period,
                'peak_kw': peak_kw,
                'demand_charge': charge,
                'demand_adjustment': adj
            })
    
    demand_charges_df = pd.DataFrame(demand_charges)

    # Calculate flat demand charges
    flat_demand_charges = []
    monthly_max = df.groupby(['year', 'month'])['load_kW'].max().reset_index()
    monthly_max['year'] = monthly_max['year'].astype(int)
    monthly_max['month'] = monthly_max['month'].astype(int)
    
    for _, row in monthly_max.iterrows():
        year = int(row['year'])
        month = int(row['month'])
        peak_kw = float(row['load_kW'])  # Keep as float for calculations
        
        if 'flatdemandstructure' in tariff and 'flatdemandmonths' in tariff:
            month_idx = month - 1  # Convert to 0-based index
            flat_period = int(tariff['flatdemandmonths'][month_idx])
            flat_structure = tariff['flatdemandstructure'][flat_period]
            charge, adj = get_rate_for_demand(flat_structure, peak_kw)
        else:
            charge, adj = 0, 0
            
        flat_demand_charges.append({
            'year': year,
            'month': month,
            'peak_kw': peak_kw,
            'flat_demand_charge': charge,
            'flat_demand_adjustment': adj
        })
        
    flat_demand_charges_df = pd.DataFrame(flat_demand_charges)

    # Convert period columns to integers to avoid float index issues
    df['energy_period'] = df['energy_period'].astype(int)
    df['demand_period'] = df['demand_period'].astype(int)

    # Fixed charges
    fixed_monthly = tariff.get('fixedmonthlycharge', 0)
    min_monthly = tariff.get('minmonthlycharge', 0)

    # Prepare monthly summary
    summary = []
    for (year, month), group in df.groupby(['year', 'month']):
        year = int(year)
        month = int(month)
        total_kwh = group['kWh'].sum()
        avg_load = group['load_kW'].mean()
        peak_kw = group['load_kW'].max()
        load_factor = avg_load / peak_kw if peak_kw > 0 else 0
        
        # Energy charges
        energy_charge = group['energy_charge'].sum()
        energy_adj = group['energy_adjustment'].sum()
        
        # Demand charges (if applicable)
        demand_charge = 0
        demand_adj = 0
        if has_demand_charges:
            period_demand = demand_charges_df[
                (demand_charges_df['year'] == year) & 
                (demand_charges_df['month'] == month)
            ]
            demand_charge = period_demand['demand_charge'].sum()
            demand_adj = period_demand['demand_adjustment'].sum()
        
        # Flat demand charges
        flat_demand = flat_demand_charges_df[
            (flat_demand_charges_df['year'] == year) & 
            (flat_demand_charges_df['month'] == month)
        ]
        flat_demand_charge = flat_demand['flat_demand_charge'].sum()
        flat_demand_adj = flat_demand['flat_demand_adjustment'].sum()
        
        # Fixed charges - use fixedchargefirstmeter if available
        fixed_charge = tariff.get('fixedchargefirstmeter', 
                                max(fixed_monthly, min_monthly))
        
        # Apply additional adjustments
        # Separate per_kwh and per_kw adjustments
        kwh_adjustments = sum(v for k, v in adjustments.items() 
                            if k.endswith('_per_kwh') or k == 'ev_discount')
        kw_adjustments = sum(v for k, v in adjustments.items() 
                           if k.endswith('_per_kw'))
        total_kwh_adj = sum(v for k, v in adjustments.items() 
                           if k.lower().endswith('kwh')) * total_kwh
        total_kw_adj = sum(v for k, v in adjustments.items() 
                          if k.lower().endswith('kw')) * peak_kw
        
        # Calculate totals
        total_charge = (
            energy_charge + energy_adj +
            demand_charge + demand_adj +
            flat_demand_charge + flat_demand_adj +
            fixed_charge +
            total_kwh_adj + total_kw_adj
        )
        
        # Energy usage by TOU period
        kwh_by_period = group.groupby('energy_period')['kWh'].sum().to_dict()
        
        # Peak demand by TOU period
        peak_by_period = group.groupby('demand_period')['load_kW'].max().to_dict()
        
        # Create named period summaries
        named_energy_periods = {
            get_period_name('energy', period, month): kwh 
            for period, kwh in kwh_by_period.items()
        }
        named_demand_periods = {
            get_period_name('demand', period, month): kw
            for period, kw in peak_by_period.items()
        }
        
        # Determine season and seasonal metrics
        season = 'summer' if month in period_mapping['season']['summer'] else 'winter'
        seasonal_peak = peak_kw
        seasonal_consumption = total_kwh
        
        summary.append({
            'year': year,
            'month': month,
            'total_kwh': total_kwh,
            'peak_kw': peak_kw,
            'avg_load': avg_load,
            'load_factor': load_factor,
            'energy_charge': energy_charge,
            'energy_adjustment': energy_adj,
            'demand_charge': demand_charge,
            'demand_adjustment': demand_adj,
            'flat_demand_charge': flat_demand_charge,
            'flat_demand_adjustment': flat_demand_adj,
            'fixed_charge': fixed_charge,
            'additional_kwh_adjustment': total_kwh_adj,
            'additional_kw_adjustment': total_kw_adj,
            'total_charge': total_charge,
            'kwh_by_period': named_energy_periods,
            'peak_kw_by_period': named_demand_periods,
            'season': season,
            'seasonal_peak': seasonal_peak,
            'seasonal_consumption': seasonal_consumption
        })

    summary_df = pd.DataFrame(summary)
    
    # Expand kwh_by_period and peak_kw_by_period into columns
    kwh_periods = pd.json_normalize(summary_df['kwh_by_period']).add_prefix('kwh_period_')
    peak_periods = pd.json_normalize(summary_df['peak_kw_by_period']).add_prefix('peak_kw_period_')
    summary_df = pd.concat([
        summary_df.drop(['kwh_by_period', 'peak_kw_by_period'], axis=1),
        kwh_periods,
        peak_periods
    ], axis=1)

    if save_csv:
        os.makedirs('results', exist_ok=True)
        out_path = os.path.join('results', 
                               f"utility_bill_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        summary_df.to_csv(out_path, index=False)
        print(f"Results saved to {out_path}")

    # Convert period columns to integers in the expanded data
    for col in summary_df.columns:
        if 'period_' in col:
            summary_df[col] = pd.to_numeric(summary_df[col], errors='ignore')

    return summary_df


def calculate_utility_costs_for_app(tariff_data: Dict, load_profile_path: str, default_voltage: float = 480.0) -> pd.DataFrame:
    """Simplified function for app integration that takes tariff data directly
    
    Parameters:
    -----------
    tariff_data : Dict
        The tariff data dictionary (already loaded)
    load_profile_path : str
        Path to CSV file containing load profile data
    default_voltage : float, optional
        Default voltage level in volts (default: 480.0)
        
    Returns:
    --------
    pd.DataFrame
        Monthly billing summary with simplified columns for display
    """
    try:
        # Load load profile
        df = load_profile_csv(load_profile_path)
        
        # Validate tariff
        validate_tariff(tariff_data)
        
        # Use the existing calculation logic but with tariff data directly
        # Temporarily save tariff to a file for the main function
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'items': [tariff_data]}, f)
            temp_tariff_path = f.name
        
        try:
            # Calculate using existing function
            full_results = calculate_monthly_bill(load_profile_path, temp_tariff_path, save_csv=False, default_voltage=default_voltage)
            
            # Simplify results for app display
            simplified_results = full_results[[
                'year', 'month', 'total_kwh', 'peak_kw', 'avg_load', 'load_factor',
                'energy_charge', 'energy_adjustment', 'demand_charge', 'demand_adjustment',
                'flat_demand_charge', 'flat_demand_adjustment', 'fixed_charge', 'total_charge'
            ]].copy()
            
            # Add combined columns for cleaner display
            simplified_results['total_energy_cost'] = (
                simplified_results['energy_charge'] + simplified_results['energy_adjustment']
            )
            simplified_results['total_demand_cost'] = (
                simplified_results['demand_charge'] + simplified_results['demand_adjustment'] + 
                simplified_results['flat_demand_charge'] + simplified_results['flat_demand_adjustment']
            )
            
            # Add month names for better display
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            simplified_results['month_name'] = simplified_results['month'].apply(lambda x: month_names[x-1])
            
            # Round numerical columns for display
            numeric_cols = ['total_kwh', 'peak_kw', 'avg_load', 'load_factor', 
                           'total_energy_cost', 'total_demand_cost', 'fixed_charge', 'total_charge']
            for col in numeric_cols:
                if col in simplified_results.columns:
                    simplified_results[col] = simplified_results[col].round(2)
            
            return simplified_results
            
        finally:
            # Clean up temporary file
            os.unlink(temp_tariff_path)
            
    except Exception as e:
        raise Exception(f"Error calculating utility costs: {str(e)}")


def main():
    """Main function for standalone execution (used for testing)."""
    # Example file paths (adjust as needed)
    load_profile_path = "data/load_profiles/ev_fast_charging_load_profile_2025.csv"
    urdb_json_path = "data/tariffs/FPL_GSLD1.json"
    try:
        # Enable pandas display of data types for debugging
        pd.set_option('display.max_columns', None)
        
        df = calculate_monthly_bill(load_profile_path, urdb_json_path, save_csv=True)
        
        print("\nMonthly Bill Summary:")
        print(df[['year', 'month', 'season', 'total_kwh', 'peak_kw', 'seasonal_peak', 'total_charge']].to_string(index=False))
        
        # Print period summaries
        print("\nSeasonal Analysis:")
        seasonal_summary = df.groupby('season').agg({
            'total_kwh': 'sum',
            'peak_kw': 'max',
            'total_charge': 'sum'
        }).round(2)
        print(seasonal_summary)
        
        # Print debug info about any float columns that should be integers
        period_cols = [col for col in df.columns if 'period' in col.lower()]
        if period_cols:
            print("\nPeriod column types:")
            for col in period_cols:
                print(f"{col}: {df[col].dtype}")
                
    except (InvalidLoadProfileError, InvalidTariffError) as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
