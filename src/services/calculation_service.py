"""
Calculation service for URDB Tariff Viewer.

This module provides utility bill calculation services and load profile analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any, Tuple
from pathlib import Path

from src.models.tariff import TariffViewer
from src.services.calculation_engine import calculate_utility_costs_for_app
from src.utils.exceptions import InvalidTariffError, InvalidLoadProfileError


class CalculationService:
    """Service for utility bill calculations and load profile analysis."""
    
    @staticmethod
    def calculate_utility_bill(
        tariff_viewer: TariffViewer,
        load_profile_path: Union[str, Path],
        customer_voltage: float = 480.0
    ) -> Dict[str, Any]:
        """
        Calculate utility bill costs for a given load profile.
        
        Args:
            tariff_viewer (TariffViewer): Tariff viewer instance
            load_profile_path (Union[str, Path]): Path to load profile CSV
            customer_voltage (float): Customer voltage level in volts
            
        Returns:
            Dict[str, Any]: Calculation results including costs and breakdowns
            
        Raises:
            InvalidTariffError: If tariff data is invalid
            InvalidLoadProfileError: If load profile data is invalid
        """
        try:
            # Extract the actual tariff data from the wrapper structure
            if 'items' in tariff_viewer.data:
                tariff_data = tariff_viewer.data['items'][0]
            else:
                tariff_data = tariff_viewer.data
                
            # Use the existing calculation function
            results = calculate_utility_costs_for_app(
                tariff_data=tariff_data,
                load_profile_path=str(load_profile_path),
                default_voltage=customer_voltage
            )
            
            return results
            
        except (InvalidTariffError, InvalidLoadProfileError) as e:
            raise e
        except Exception as e:
            raise Exception(f"Calculation error: {str(e)}")
    
    @staticmethod
    def analyze_load_profile(load_profile_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze a load profile and return statistics.
        
        Args:
            load_profile_df (pd.DataFrame): Load profile DataFrame
            
        Returns:
            Dict[str, Any]: Load profile analysis results
        """
        try:
            # Ensure required columns exist
            required_columns = ['timestamp', 'load_kW']
            missing_columns = [col for col in required_columns if col not in load_profile_df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
            
            # Convert timestamp if it's not already datetime
            if not pd.api.types.is_datetime64_any_dtype(load_profile_df['timestamp']):
                load_profile_df['timestamp'] = pd.to_datetime(load_profile_df['timestamp'])
            
            # Add derived columns
            df = load_profile_df.copy()
            df['month'] = df['timestamp'].dt.month
            df['hour'] = df['timestamp'].dt.hour
            df['weekday'] = df['timestamp'].dt.weekday  # 0=Monday, 6=Sunday
            df['day_name'] = df['timestamp'].dt.day_name()
            df['is_weekend'] = df['weekday'] >= 5
            
            # Calculate kWh if not present (assuming 15-minute intervals)
            if 'kWh' not in df.columns:
                df['kWh'] = df['load_kW'] * 0.25  # 15 minutes = 0.25 hours
            
            # Basic statistics
            total_kwh = df['kWh'].sum()
            peak_kw = df['load_kW'].max()
            avg_kw = df['load_kW'].mean()
            min_kw = df['load_kW'].min()
            load_factor = avg_kw / peak_kw if peak_kw > 0 else 0
            
            # Monthly statistics
            monthly_stats = df.groupby('month').agg({
                'load_kW': ['mean', 'max', 'min'],
                'kWh': 'sum'
            }).round(4)
            
            # Convert month numbers to abbreviations
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            monthly_stats.index = [month_names[i-1] for i in monthly_stats.index]
            
            # Hourly statistics
            hourly_stats = df.groupby('hour').agg({
                'load_kW': ['mean', 'max', 'min'],
                'kWh': 'sum'
            }).round(4)
            
            # Weekend vs weekday statistics
            weekday_stats = df[~df['is_weekend']].agg({
                'load_kW': ['mean', 'max', 'min'],
                'kWh': 'sum'
            }).round(4)
            
            weekend_stats = df[df['is_weekend']].agg({
                'load_kW': ['mean', 'max', 'min'],
                'kWh': 'sum'
            }).round(4)
            
            # Peak demand by month
            monthly_peaks = df.groupby('month')['load_kW'].max()
            # Convert month numbers to abbreviations for monthly_peaks
            monthly_peaks.index = [month_names[i-1] for i in monthly_peaks.index]
            
            # Daily energy consumption by day of week
            daily_energy = df.groupby('day_name')['kWh'].sum().round(2)
            # Reorder days to start with Monday
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            daily_energy = daily_energy.reindex(day_order)
            
            # Hourly energy consumption (total across all days)
            hourly_energy = df.groupby('hour')['kWh'].sum().round(2)
            
            # Time of peak demand
            peak_time = df.loc[df['load_kW'].idxmax(), 'timestamp']
            
            # Load duration curve data (for plotting)
            sorted_loads = df['load_kW'].sort_values(ascending=False).reset_index(drop=True)
            duration_percentiles = np.arange(0, 100.1, 1)  # 0 to 100% in 1% increments
            duration_loads = np.percentile(sorted_loads, 100 - duration_percentiles)
            
            # Full load profile data for time series plotting
            full_load_profile_data = {
                'timestamps': df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                'loads': df['load_kW'].tolist(),
                'date_range': {
                    'start': df['timestamp'].min().strftime('%Y-%m-%d'),
                    'end': df['timestamp'].max().strftime('%Y-%m-%d')
                }
            }
            
            analysis_results = {
                'basic_stats': {
                    'total_kwh': round(total_kwh, 2),
                    'peak_kw': round(peak_kw, 4),
                    'avg_kw': round(avg_kw, 4),
                    'min_kw': round(min_kw, 4),
                    'load_factor': round(load_factor, 4),
                    'peak_time': peak_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'data_points': len(df),
                    'date_range': {
                        'start': df['timestamp'].min().strftime('%Y-%m-%d'),
                        'end': df['timestamp'].max().strftime('%Y-%m-%d')
                    }
                },
                'monthly_stats': monthly_stats.to_dict(),
                'hourly_stats': hourly_stats.to_dict(),
                'weekday_stats': weekday_stats.to_dict(),
                'weekend_stats': weekend_stats.to_dict(),
                'monthly_peaks': monthly_peaks.to_dict(),
                'daily_energy': daily_energy.to_dict(),
                'hourly_energy': hourly_energy.to_dict(),
                'load_profile': full_load_profile_data,
                'duration_curve': {
                    'percentiles': duration_percentiles.tolist(),
                    'loads': duration_loads.tolist()
                }
            }
            
            return analysis_results
            
        except Exception as e:
            raise Exception(f"Load profile analysis error: {str(e)}")
    
    @staticmethod
    def compare_tariffs(
        tariff_viewers: List[TariffViewer],
        load_profile_path: Union[str, Path],
        customer_voltage: float = 480.0
    ) -> Dict[str, Any]:
        """
        Compare multiple tariffs using the same load profile.
        
        Args:
            tariff_viewers (List[TariffViewer]): List of tariff viewer instances
            load_profile_path (Union[str, Path]): Path to load profile CSV
            customer_voltage (float): Customer voltage level in volts
            
        Returns:
            Dict[str, Any]: Comparison results
        """
        comparison_results = {
            'tariff_results': [],
            'summary': {}
        }
        
        try:
            for viewer in tariff_viewers:
                try:
                    result = CalculationService.calculate_utility_bill(
                        viewer, load_profile_path, customer_voltage
                    )
                    
                    tariff_result = {
                        'utility_name': viewer.utility_name,
                        'rate_name': viewer.rate_name,
                        'sector': viewer.sector,
                        'total_cost': result.get('total_annual_cost', 0),
                        'energy_cost': result.get('total_energy_cost', 0),
                        'demand_cost': result.get('total_demand_cost', 0),
                        'fixed_cost': result.get('total_fixed_cost', 0),
                        'calculation_successful': True,
                        'full_results': result
                    }
                    
                except Exception as e:
                    tariff_result = {
                        'utility_name': viewer.utility_name,
                        'rate_name': viewer.rate_name,
                        'sector': viewer.sector,
                        'total_cost': 0,
                        'energy_cost': 0,
                        'demand_cost': 0,
                        'fixed_cost': 0,
                        'calculation_successful': False,
                        'error': str(e)
                    }
                
                comparison_results['tariff_results'].append(tariff_result)
            
            # Calculate summary statistics
            successful_results = [r for r in comparison_results['tariff_results'] if r['calculation_successful']]
            
            if successful_results:
                total_costs = [r['total_cost'] for r in successful_results]
                comparison_results['summary'] = {
                    'lowest_cost': min(total_costs),
                    'highest_cost': max(total_costs),
                    'average_cost': sum(total_costs) / len(total_costs),
                    'cost_range': max(total_costs) - min(total_costs),
                    'successful_calculations': len(successful_results),
                    'failed_calculations': len(tariff_viewers) - len(successful_results)
                }
                
                # Find best and worst tariffs
                best_tariff = min(successful_results, key=lambda x: x['total_cost'])
                worst_tariff = max(successful_results, key=lambda x: x['total_cost'])
                
                comparison_results['summary']['best_tariff'] = {
                    'utility': best_tariff['utility_name'],
                    'rate': best_tariff['rate_name'],
                    'cost': best_tariff['total_cost']
                }
                
                comparison_results['summary']['worst_tariff'] = {
                    'utility': worst_tariff['utility_name'],
                    'rate': worst_tariff['rate_name'],
                    'cost': worst_tariff['total_cost']
                }
            
            return comparison_results
            
        except Exception as e:
            raise Exception(f"Tariff comparison error: {str(e)}")
    
    @staticmethod
    def validate_load_profile(load_profile_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate a load profile file.
        
        Args:
            load_profile_path (Union[str, Path]): Path to load profile CSV
            
        Returns:
            Dict[str, Any]: Validation results
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'info': {}
        }
        
        try:
            # Load the CSV file
            df = pd.read_csv(load_profile_path)
            
            # Check required columns
            required_columns = ['timestamp', 'load_kW']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                validation_results['errors'].append(f"Missing required columns: {', '.join(missing_columns)}")
                validation_results['is_valid'] = False
                return validation_results
            
            # Validate timestamp column
            try:
                pd.to_datetime(df['timestamp'])
            except Exception:
                validation_results['errors'].append("Invalid timestamp format")
                validation_results['is_valid'] = False
            
            # Validate load_kW column
            if not pd.api.types.is_numeric_dtype(df['load_kW']):
                validation_results['errors'].append("load_kW column must be numeric")
                validation_results['is_valid'] = False
            
            # Check for negative values
            if (df['load_kW'] < 0).any():
                validation_results['warnings'].append("Negative load values found")
            
            # Check for missing values
            if df['load_kW'].isna().any():
                validation_results['warnings'].append("Missing load values found")
            
            # Add info about the file
            validation_results['info'] = {
                'row_count': len(df),
                'columns': list(df.columns),
                'date_range': {
                    'start': df['timestamp'].min() if validation_results['is_valid'] else None,
                    'end': df['timestamp'].max() if validation_results['is_valid'] else None
                },
                'load_range': {
                    'min': df['load_kW'].min() if validation_results['is_valid'] else None,
                    'max': df['load_kW'].max() if validation_results['is_valid'] else None,
                    'avg': df['load_kW'].mean() if validation_results['is_valid'] else None
                }
            }
            
        except Exception as e:
            validation_results['errors'].append(f"File reading error: {str(e)}")
            validation_results['is_valid'] = False
        
        return validation_results
