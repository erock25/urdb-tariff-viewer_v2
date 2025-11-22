"""
Tariff data model for URDB Tariff Viewer.

This module contains the TariffViewer class responsible for loading and processing
utility rate structures from URDB JSON files.
"""

import json
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import streamlit as st

from src.config.constants import MONTHS, HOURS


class TariffViewer:
    """
    A class for processing and visualizing URDB tariff data.
    
    This class handles loading, parsing, and analyzing utility rate structures
    from the U.S. Utility Rate Database (URDB) JSON format.
    
    Attributes:
        utility_name (str): Name of the utility company
        rate_name (str): Name of the rate schedule
        sector (str): Customer sector (Residential/Commercial/Industrial)
        description (str): Rate description
        data (Dict): Complete tariff data from JSON
        tariff (Dict): Main tariff structure
        months (List[str]): Month abbreviations
        hours (List[int]): Hours 0-23
        weekday_df (pd.DataFrame): Weekday energy rates by month/hour
        weekend_df (pd.DataFrame): Weekend energy rates by month/hour
        demand_weekday_df (pd.DataFrame): Weekday demand rates by month/hour
        demand_weekend_df (pd.DataFrame): Weekend demand rates by month/hour
        flat_demand_df (pd.DataFrame): Flat demand rates by month
        
    Example:
        >>> viewer = TariffViewer('path/to/tariff.json')
        >>> heatmap = viewer.plot_heatmap(is_weekday=True)
    """
    
    def __init__(self, json_file: Union[str, Path]):
        """
        Initialize TariffViewer with a JSON tariff file.
        
        Args:
            json_file (Union[str, Path]): Path to the URDB JSON tariff file
            
        Raises:
            Exception: If the file cannot be loaded or parsed
        """
        try:
            with open(json_file, 'r') as file:
                self.data = json.load(file)
            
            # Handle both direct tariff data and wrapped in 'items'
            if 'items' in self.data:
                self.tariff = self.data['items'][0]
            else:
                self.tariff = self.data
                self.data = {'items': [self.data]}  # Wrap for consistency
                
            # Extract basic information with fallbacks
            self.utility_name = self.tariff.get('utility', 'Unknown Utility')
            self.rate_name = self.tariff.get('name', 'Unknown Rate')
            self.sector = self.tariff.get('sector', 'Unknown Sector')
            self.description = self.tariff.get('description', 'No description available')
            
        except Exception as e:
            st.error(f"Error loading tariff file: {str(e)}")
            raise
        
        # Setup data structures
        self.months = MONTHS
        self.hours = HOURS
        self.update_rate_dataframes()
        
    def get_rate(self, period_index: int, rate_structure: List[List[Dict]]) -> float:
        """
        Get the rate for a specific period from the rate structure.
        
        Args:
            period_index (int): Index of the time period
            rate_structure (List[List[Dict]]): Rate structure from tariff
            
        Returns:
            float: Rate value including any adjustments
        """
        if period_index < len(rate_structure):
            rate = rate_structure[period_index][0]['rate']
            adj = rate_structure[period_index][0].get('adj', 0)
            return rate + adj
        return 0
    
    def get_demand_rate(self, period_index: int, rate_structure: List[List[Dict]]) -> float:
        """
        Get the demand rate for a specific period from the rate structure.
        
        Args:
            period_index (int): Index of the time period
            rate_structure (List[List[Dict]]): Demand rate structure from tariff
            
        Returns:
            float: Demand rate value including any adjustments
        """
        if period_index < len(rate_structure):
            rate = rate_structure[period_index][0]['rate']
            adj = rate_structure[period_index][0].get('adj', 0)
            return rate + adj
        return 0
    
    def update_rate_dataframes(self) -> None:
        """
        Update all rate DataFrames from the tariff data.
        
        This method processes the tariff structure and creates DataFrames for:
        - Weekday and weekend energy rates
        - Weekday and weekend demand rates  
        - Flat demand rates
        """
        # Energy rates
        energy_rates = self.tariff.get('energyratestructure', [])
        weekday_schedule = self.tariff.get('energyweekdayschedule', [])
        weekend_schedule = self.tariff.get('energyweekendschedule', [])
        
        # Create weekday energy rates DataFrame
        if energy_rates and weekday_schedule:
            weekday_rates = []
            for month_schedule in weekday_schedule:
                rates = [self.get_rate(period, energy_rates) for period in month_schedule]
                weekday_rates.append(rates)
            self.weekday_df = pd.DataFrame(weekday_rates, index=self.months, columns=self.hours)
        else:
            self.weekday_df = pd.DataFrame(0, index=self.months, columns=self.hours)
        
        # Create weekend energy rates DataFrame
        if energy_rates and weekend_schedule:
            weekend_rates = []
            for month_schedule in weekend_schedule:
                rates = [self.get_rate(period, energy_rates) for period in month_schedule]
                weekend_rates.append(rates)
            self.weekend_df = pd.DataFrame(weekend_rates, index=self.months, columns=self.hours)
        else:
            self.weekend_df = pd.DataFrame(0, index=self.months, columns=self.hours)
        
        # Demand rates
        demand_rates = self.tariff.get('demandratestructure', [])
        demand_weekday_schedule = self.tariff.get('demandweekdayschedule', [])
        demand_weekend_schedule = self.tariff.get('demandweekendschedule', [])
        
        # Create weekday demand rates DataFrame
        if demand_rates and demand_weekday_schedule:
            demand_weekday_rates = []
            for month_schedule in demand_weekday_schedule:
                rates = [self.get_demand_rate(period, demand_rates) for period in month_schedule]
                demand_weekday_rates.append(rates)
            self.demand_weekday_df = pd.DataFrame(demand_weekday_rates, index=self.months, columns=self.hours)
        else:
            self.demand_weekday_df = pd.DataFrame(0, index=self.months, columns=self.hours)
        
        # Create weekend demand rates DataFrame
        if demand_rates and demand_weekend_schedule:
            demand_weekend_rates = []
            for month_schedule in demand_weekend_schedule:
                rates = [self.get_demand_rate(period, demand_rates) for period in month_schedule]
                demand_weekend_rates.append(rates)
            self.demand_weekend_df = pd.DataFrame(demand_weekend_rates, index=self.months, columns=self.hours)
        else:
            self.demand_weekend_df = pd.DataFrame(0, index=self.months, columns=self.hours)
        
        # Flat demand rates (seasonal/monthly)
        flat_demand_rates = self.tariff.get('flatdemandstructure', [])
        flat_demand_months = self.tariff.get('flatdemandmonths', [])
        
        if flat_demand_rates and flat_demand_months:
            flat_demand_rates_list = []
            for month_idx in range(12):
                period_idx = flat_demand_months[month_idx] if month_idx < len(flat_demand_months) else 0
                if period_idx < len(flat_demand_rates) and flat_demand_rates[period_idx]:
                    rate = flat_demand_rates[period_idx][0].get('rate', 0)
                    adj = flat_demand_rates[period_idx][0].get('adj', 0)
                    flat_demand_rates_list.append(rate + adj)
                else:
                    flat_demand_rates_list.append(0)
            self.flat_demand_df = pd.DataFrame(flat_demand_rates_list, index=self.months, columns=['Rate ($/kW)'])
        else:
            self.flat_demand_df = pd.DataFrame(0, index=self.months, columns=['Rate ($/kW)'])
    
    def create_tou_labels_table(self) -> pd.DataFrame:
        """
        Create a table showing TOU labels with their corresponding energy rates.
        
        Returns:
            pd.DataFrame: Table with TOU period information
        """
        import calendar
        
        energy_labels = self.tariff.get('energytoulabels', None)
        energy_rates = self.tariff.get('energyratestructure', [])

        # If no energy rate structure, return empty DataFrame
        if not energy_rates:
            return pd.DataFrame()

        # Get weekday and weekend schedules
        weekday_schedule = self.tariff.get('energyweekdayschedule', [])
        weekend_schedule = self.tariff.get('energyweekendschedule', [])

        # Calculate annual hours for each period
        period_hours = {}
        total_hours = 0
        year = 2024  # Reference year for calendar calculations
        
        if len(weekday_schedule) >= 12 and len(weekend_schedule) >= 12:
            for month in range(12):
                # Get the calendar for this month
                cal = calendar.monthcalendar(year, month + 1)
                
                # Count weekdays and weekend days
                weekday_count = 0
                weekend_count = 0
                
                for week in cal:
                    for day_idx, day in enumerate(week):
                        if day == 0:  # Not part of this month
                            continue
                        if day_idx < 5:  # Monday-Friday (0-4)
                            weekday_count += 1
                        else:  # Saturday-Sunday (5-6)
                            weekend_count += 1
                
                # Count hours per period for this month
                for hour in range(24):
                    period = weekday_schedule[month][hour]
                    period_hours[period] = period_hours.get(period, 0) + weekday_count
                
                for hour in range(24):
                    period = weekend_schedule[month][hour]
                    period_hours[period] = period_hours.get(period, 0) + weekend_count
                
                total_hours += (weekday_count + weekend_count) * 24

        # Create table data
        table_data = []

        # If we have labels, use them; otherwise create generic labels
        if energy_labels:
            labels_to_use = energy_labels
        else:
            labels_to_use = ["TOU Label Not In Tariff JSON"] * len(energy_rates)

        for i, label in enumerate(labels_to_use):
            if i < len(energy_rates) and energy_rates[i]:
                rate_info = energy_rates[i][0]  # Get first tier
                rate = rate_info.get('rate', 0)
                adj = rate_info.get('adj', 0)
                total_rate = rate + adj

                # If using generic label, add period number for distinction
                if not energy_labels:
                    period_label = f"Period {i} - TOU Label Not In Tariff JSON"
                else:
                    period_label = label

                # Determine which months this TOU period appears in
                months_present = self._get_months_for_tou_period(i, weekday_schedule, weekend_schedule)
                
                # Get hours and percentage for this period
                hours = period_hours.get(i, 0)
                percentage = (hours / total_hours * 100) if total_hours > 0 else 0

                table_data.append({
                    'TOU Period': period_label,
                    'Base Rate ($/kWh)': f"${rate:.4f}",
                    'Adjustment ($/kWh)': f"${adj:.4f}",
                    'Total Rate ($/kWh)': f"${total_rate:.4f}",
                    'Hours/Year': hours,
                    '% of Year': f"{percentage:.1f}%",
                    'Months Present': months_present
                })

        return pd.DataFrame(table_data)

    def create_demand_labels_table(self) -> pd.DataFrame:
        """
        Create a table showing demand charge labels with their corresponding rates.
        
        Returns:
            pd.DataFrame: Table with demand period information
        """
        demand_labels = self.tariff.get('demandlabels', None)
        demand_rates = self.tariff.get('demandratestructure', [])

        # If no demand rate structure, return empty DataFrame
        if not demand_rates:
            return pd.DataFrame()

        # Get weekday and weekend schedules
        demand_weekday_schedule = self.tariff.get('demandweekdayschedule', [])
        demand_weekend_schedule = self.tariff.get('demandweekendschedule', [])

        # Create table data
        table_data = []

        # If we have labels, use them; otherwise create generic labels
        if demand_labels:
            labels_to_use = demand_labels
        else:
            labels_to_use = ["Demand Label Not In Tariff JSON"] * len(demand_rates)

        for i, label in enumerate(labels_to_use):
            if i < len(demand_rates) and demand_rates[i]:
                rate_info = demand_rates[i][0]  # Get first tier
                rate = rate_info.get('rate', 0)
                adj = rate_info.get('adj', 0)
                total_rate = rate + adj

                # If using generic label, add period number for distinction
                if not demand_labels:
                    period_label = f"Period {i} - Demand Label Not In Tariff JSON"
                else:
                    period_label = label

                # Determine which months this demand period appears in
                months_present = self._get_months_for_demand_period(i, demand_weekday_schedule, demand_weekend_schedule)

                table_data.append({
                    'Demand Period': period_label,
                    'Base Rate ($/kW)': f"${rate:.4f}",
                    'Adjustment ($/kW)': f"${adj:.4f}",
                    'Total Rate ($/kW)': f"${total_rate:.4f}",
                    'Months Present': months_present
                })

        return pd.DataFrame(table_data)

    def _get_months_for_demand_period(self, period_index: int, weekday_schedule: List, weekend_schedule: List) -> str:
        """
        Determine which months a demand period appears in for weekday and weekend schedules.
        
        Args:
            period_index (int): Index of the demand period
            weekday_schedule (List): Weekday schedule from tariff
            weekend_schedule (List): Weekend schedule from tariff
            
        Returns:
            str: Formatted string describing when the period is used
        """
        weekday_months = []
        weekend_months = []

        # Get demand rates structure to check valid period indices
        demand_rates = self.tariff.get('demandratestructure', [])

        # Check weekday schedule
        for month_idx, month_schedule in enumerate(weekday_schedule):
            if month_idx < len(month_schedule) and period_index < len(demand_rates) and period_index in month_schedule:
                weekday_months.append(self.months[month_idx])

        # Check weekend schedule
        for month_idx, month_schedule in enumerate(weekend_schedule):
            if month_idx < len(month_schedule) and period_index < len(demand_rates) and period_index in month_schedule:
                weekend_months.append(self.months[month_idx])

        # Format the result
        parts = []
        if weekday_months:
            parts.append(f"{self._format_month_range(weekday_months)} (Weekday)")
        if weekend_months:
            parts.append(f"{self._format_month_range(weekend_months)} (Weekend)")

        return ", ".join(parts) if parts else "Not used"

    def _get_months_for_tou_period(self, period_index: int, weekday_schedule: List, weekend_schedule: List) -> str:
        """
        Determine which months a TOU period appears in for weekday and weekend schedules.
        
        Args:
            period_index (int): Index of the TOU period
            weekday_schedule (List): Weekday schedule from tariff
            weekend_schedule (List): Weekend schedule from tariff
            
        Returns:
            str: Formatted string describing when the period is used
        """
        weekday_months = []
        weekend_months = []

        # Get energy rates structure to check valid period indices
        energy_rates = self.tariff.get('energyratestructure', [])

        # Check weekday schedule
        for month_idx, month_schedule in enumerate(weekday_schedule):
            if month_idx < len(month_schedule) and period_index < len(energy_rates) and period_index in month_schedule:
                weekday_months.append(self.months[month_idx])

        # Check weekend schedule
        for month_idx, month_schedule in enumerate(weekend_schedule):
            if month_idx < len(month_schedule) and period_index < len(energy_rates) and period_index in month_schedule:
                weekend_months.append(self.months[month_idx])

        # Format the result
        parts = []
        if weekday_months:
            parts.append(f"{self._format_month_range(weekday_months)} (Weekday)")
        if weekend_months:
            parts.append(f"{self._format_month_range(weekend_months)} (Weekend)")

        return ", ".join(parts) if parts else "Not used"

    def _format_month_range(self, months: List[str]) -> str:
        """
        Format a list of months into a compact range (e.g., 'Jan-Jun' or 'Jan, Mar, Jun').
        
        Args:
            months (List[str]): List of month abbreviations
            
        Returns:
            str: Formatted month range string
        """
        if not months:
            return ""

        if len(months) == 1:
            return months[0]

        # Check if months form a consecutive range
        month_indices = [self.months.index(m) for m in months]
        month_indices.sort()

        if month_indices == list(range(month_indices[0], month_indices[-1] + 1)):
            # Consecutive range
            if month_indices[0] == month_indices[-1]:
                return months[0]
            else:
                return f"{months[0]}-{months[-1]}"
        else:
            # Non-consecutive, list them
            return ", ".join(months)


def create_temp_viewer_with_modified_tariff(modified_tariff_data: Dict) -> 'TempTariffViewer':
    """
    Create a temporary TariffViewer instance with modified tariff data.
    
    Args:
        modified_tariff_data (Dict): Modified tariff data
        
    Returns:
        TempTariffViewer: Temporary viewer instance
    """
    
    class TempTariffViewer(TariffViewer):
        """Temporary TariffViewer that works with in-memory data instead of files."""
        
        def __init__(self, tariff_data):
            # Skip file loading and work directly with data
            self.data = tariff_data
            
            # Handle both direct tariff data and wrapped in 'items'
            if 'items' in self.data:
                self.tariff = self.data['items'][0]
            else:
                self.tariff = self.data
                self.data = {'items': [self.data]}  # Wrap for consistency
                
            # Extract basic information with fallbacks
            self.utility_name = self.tariff.get('utility', 'Unknown Utility')
            self.rate_name = self.tariff.get('name', 'Unknown Rate')
            self.sector = self.tariff.get('sector', 'Unknown Sector')
            self.description = self.tariff.get('description', 'No description available')
            
            # Setup data structures
            self.months = MONTHS
            self.hours = HOURS
            self.update_rate_dataframes()
    
    return TempTariffViewer(modified_tariff_data)
