import streamlit as st
import json
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from datetime import datetime, timedelta
import re
from calculate_utility_bill import calculate_utility_costs_for_app, InvalidTariffError, InvalidLoadProfileError


class TariffViewer:
    def __init__(self, json_file):
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
        self.months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        self.hours = list(range(24))
        self.update_rate_dataframes()
        
    def get_rate(self, period_index, rate_structure):
        if period_index < len(rate_structure):
            rate = rate_structure[period_index][0]['rate']
            adj = rate_structure[period_index][0].get('adj', 0)
            return rate + adj
        return 0
    
    def get_demand_rate(self, period_index, rate_structure):
        if period_index < len(rate_structure):
            rate = rate_structure[period_index][0]['rate']
            adj = rate_structure[period_index][0].get('adj', 0)
            return rate + adj
        return 0
    
    def update_rate_dataframes(self):
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
    

        
    def plot_heatmap(self, is_weekday=True, dark_mode=False, rate_type="energy", chart_height=700, text_size=12):
        if rate_type == "energy":
            df = self.weekday_df if is_weekday else self.weekend_df
            day_type = "Weekday" if is_weekday else "Weekend"
            title_suffix = "Energy Rates"
            colorbar_title = "Rate ($/kWh)"
            unit = "kWh"
            schedule_key = 'energyweekdayschedule' if is_weekday else 'energyweekendschedule'
            rate_structure = self.tariff.get('energyratestructure', [])
        else:  # demand
            df = self.demand_weekday_df if is_weekday else self.demand_weekend_df
            day_type = "Weekday" if is_weekday else "Weekend"
            title_suffix = "Demand Rates"
            colorbar_title = "Rate ($/kW)"
            unit = "kW"
            schedule_key = 'demandweekdayschedule' if is_weekday else 'demandweekendschedule'
            rate_structure = self.tariff.get('demandratestructure', [])
        
        # Get TOU labels for enhanced hover information
        energy_labels = self.tariff.get('energytoulabels', [])
        schedule = self.tariff.get(schedule_key, [])
        
        # Create enhanced heatmap with translucent tiles
        fig = go.Figure()
        
        # Green to red gradient (low to high rates)
        colors = [
            'rgba(34, 197, 94, 0.95)',   # Bright green (lowest rates)
            'rgba(74, 222, 128, 0.95)',  # Light green (low rates)
            'rgba(251, 191, 36, 0.95)',  # Yellow/amber (medium rates)
            'rgba(249, 115, 22, 0.95)',  # Orange (high rates)
            'rgba(239, 68, 68, 0.95)',   # Bright red (highest rates)
        ] if not dark_mode else [
            'rgba(34, 197, 94, 0.9)',    # Bright green (lowest rates)
            'rgba(74, 222, 128, 0.9)',   # Light green (low rates)
            'rgba(251, 191, 36, 0.9)',   # Yellow/amber (medium rates)
            'rgba(249, 115, 22, 0.9)',   # Orange (high rates)
            'rgba(239, 68, 68, 0.9)',    # Bright red (highest rates)
        ]
        
        # Create custom colorscale
        colorscale = [
            [0.0, colors[0]],    # Lowest rates - green
            [0.25, colors[1]],   # Low rates - light green
            [0.5, colors[2]],    # Medium rates - yellow/amber
            [0.75, colors[3]],   # High rates - orange
            [1.0, colors[4]]     # Highest rates - red
        ]
        
        # Create custom hover text with TOU period information
        hover_text = []
        custom_data = []
        
        for month_idx, month in enumerate(df.index):
            month_hover = []
            month_custom = []
            for hour_idx, hour in enumerate(df.columns):
                rate_value = df.iloc[month_idx, hour_idx]
                
                # Get TOU period information
                period_info = "N/A"
                if schedule and month_idx < len(schedule) and hour_idx < len(schedule[month_idx]):
                    period_idx = schedule[month_idx][hour_idx]
                    if energy_labels and period_idx < len(energy_labels):
                        period_info = energy_labels[period_idx]
                    else:
                        period_info = f"Period {period_idx}"
                
                # Create rich hover text
                hover_info = (
                    f"<b>{month}</b> - {hour:02d}:00<br>"
                    f"<b>TOU Period:</b> {period_info}<br>"
                    f"<b>Rate:</b> ${rate_value:.4f}/{unit}<br>"
                    f"<span style='font-size: 0.9em; color: #6b7280;'>Click tile for details</span>"
                )
                month_hover.append(hover_info)
                month_custom.append([month, hour, rate_value, period_info])
            
            hover_text.append(month_hover)
            custom_data.append(month_custom)
        
        # Create the enhanced heatmap
        heatmap = go.Heatmap(
            z=df.values,
            x=[f'{h:02d}:00' for h in self.hours],
            y=df.index,
            colorscale=colorscale,
            showscale=True,
            hoverongaps=False,
            text=df.values.round(4) if text_size > 0 else None,
            texttemplate="<b>%{text}</b>" if text_size > 0 else None,
            textfont={
                "size": text_size,
                "color": "#1f2937" if not dark_mode else "#f1f5f9",
                "family": "Inter, sans-serif"
            },
            hovertemplate="%{customdata[0]}<extra></extra>",
            customdata=hover_text,
            colorbar=dict(
                title=dict(
                    text=f"<b>{colorbar_title}</b>",
                    font=dict(size=14, family="Inter, sans-serif")
                ),
                thickness=25,
                len=0.7,
                outlinewidth=0,
                tickfont=dict(size=12, color='#0f172a' if not dark_mode else '#f1f5f9', family="Inter, sans-serif"),
                tickformat=".4f",
                bgcolor='rgba(255, 255, 255, 0.9)' if not dark_mode else 'rgba(15, 23, 42, 0.9)',
                bordercolor='#e5e7eb' if not dark_mode else '#374151',
                borderwidth=1
            ),
            opacity=0.9
        )
        
        fig.add_trace(heatmap)
        
        # Enhanced layout with modern styling
        fig.update_layout(
            title=dict(
                text=f'<b>{day_type} {title_suffix}</b><br><span style="font-size: 0.75em; color: #6b7280;">{self.utility_name} - {self.rate_name}</span>',
                font=dict(size=24, color='#0f172a' if not dark_mode else '#f1f5f9', family="Inter, sans-serif"),
                x=0.5,
                xanchor='center',
                y=0.95
            ),
            xaxis=dict(
                title=dict(
                    text="<b>Hour of Day</b>",
                    font=dict(size=16, color='#0f172a' if not dark_mode else '#f1f5f9', family="Inter, sans-serif")
                ),
                tickfont=dict(size=12, color='#1f2937' if not dark_mode else '#cbd5e1', family="Inter, sans-serif"),
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(229, 231, 235, 0.5)' if not dark_mode else 'rgba(75, 85, 99, 0.5)',
                zeroline=False,
                showline=True,
                linewidth=1,
                linecolor='#e5e7eb' if not dark_mode else '#4b5563',
                tickangle=0,
                dtick=2  # Show every 2 hours
            ),
            yaxis=dict(
                title=dict(
                    text="<b>Month</b>",
                    font=dict(size=16, color='#0f172a' if not dark_mode else '#f1f5f9', family="Inter, sans-serif")
                ),
                tickfont=dict(size=12, color='#1f2937' if not dark_mode else '#cbd5e1', family="Inter, sans-serif"),
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(229, 231, 235, 0.5)' if not dark_mode else 'rgba(75, 85, 99, 0.5)',
                zeroline=False,
                showline=True,
                linewidth=1,
                linecolor='#e5e7eb' if not dark_mode else '#4b5563'
            ),
            plot_bgcolor='rgba(248, 250, 252, 0.8)' if not dark_mode else 'rgba(15, 23, 42, 0.5)',
            paper_bgcolor='#ffffff' if not dark_mode else '#0f172a',
            margin=dict(l=80, r=100, t=120, b=80),
            height=chart_height,
            hoverlabel=dict(
                bgcolor='rgba(255, 255, 255, 0.95)' if not dark_mode else 'rgba(30, 41, 59, 0.95)',
                font_size=13,
                font_family="Inter, sans-serif",
                bordercolor='#e5e7eb' if not dark_mode else '#475569',
                align="left"
            ),
            font=dict(family="Inter, sans-serif"),
            # Add subtle animations
            transition=dict(duration=300, easing="cubic-in-out")
        )
        
        # Add subtle border around the heatmap
        fig.add_shape(
            type="rect",
            x0=-0.5, y0=-0.5, x1=23.5, y1=11.5,
            line=dict(color='#d1d5db' if not dark_mode else '#4b5563', width=2),
            fillcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    def plot_flat_demand_rates(self, dark_mode=False):
        """Plot flat demand rates (seasonal/monthly) as a modern bar chart"""
        # Create gradient colors for bars based on rate values
        rates = self.flat_demand_df['Rate ($/kW)'].values
        max_rate = rates.max()
        min_rate = rates.min()
        
        # Create color gradient from green to red based on rate values
        colors = []
        for rate in rates:
            if max_rate > min_rate:
                intensity = (rate - min_rate) / (max_rate - min_rate)
            else:
                intensity = 0.5

            # Interpolate between bright green and bright red for light theme
            r = int(34 + (239 - 34) * intensity)  # Green to red
            g = int(197 + (68 - 197) * intensity) # Green to red
            b = int(94 + (68 - 94) * intensity)   # Green to red
            colors.append(f'rgba({r}, {g}, {b}, 0.9)')
        
        fig = go.Figure(data=go.Bar(
            x=self.flat_demand_df.index,
            y=self.flat_demand_df['Rate ($/kW)'],
            text=[f'${rate:.4f}' for rate in rates],
            texttemplate="<b>%{text}</b>",
            textposition='outside',
            textfont=dict(
                size=12,
                color='#0f172a' if not dark_mode else '#f1f5f9',
                family='Inter, sans-serif'
            ),
            marker=dict(
                color=colors,
                line=dict(
                    color='rgba(255, 255, 255, 0.8)' if not dark_mode else 'rgba(15, 23, 42, 0.8)',
                    width=2
                ),
                opacity=0.9
            ),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "<b>Flat Demand Rate:</b> $%{y:.4f}/kW<br>"
                "<span style='font-size: 0.9em; color: #6b7280;'>Monthly fixed rate</span>"
                "<extra></extra>"
            )
        ))
        
        fig.update_layout(
            title=dict(
                text=f'<b>Seasonal/Monthly Demand Rates</b><br><span style="font-size: 0.75em; color: #6b7280;">{self.utility_name} - {self.rate_name}</span>',
                font=dict(size=24, color='#0f172a' if not dark_mode else '#f1f5f9', family="Inter, sans-serif"),
                x=0.5,
                xanchor='center',
                y=0.95
            ),
            xaxis=dict(
                title=dict(
                    text="<b>Month</b>",
                    font=dict(size=16, color='#0f172a' if not dark_mode else '#f1f5f9', family="Inter, sans-serif")
                ),
                tickfont=dict(size=12, color='#1f2937' if not dark_mode else '#cbd5e1', family="Inter, sans-serif"),
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(229, 231, 235, 0.5)' if not dark_mode else 'rgba(75, 85, 99, 0.5)',
                zeroline=False,
                showline=True,
                linewidth=1,
                linecolor='#e5e7eb' if not dark_mode else '#4b5563'
            ),
            yaxis=dict(
                title=dict(
                    text="<b>Demand Rate ($/kW)</b>",
                    font=dict(size=16, color='#0f172a' if not dark_mode else '#f1f5f9', family="Inter, sans-serif")
                ),
                tickfont=dict(size=12, color='#1f2937' if not dark_mode else '#cbd5e1', family="Inter, sans-serif"),
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(229, 231, 235, 0.5)' if not dark_mode else 'rgba(75, 85, 99, 0.5)',
                zeroline=False,
                showline=True,
                linewidth=1,
                linecolor='#e5e7eb' if not dark_mode else '#4b5563'
            ),
            plot_bgcolor='rgba(248, 250, 252, 0.8)' if not dark_mode else 'rgba(15, 23, 42, 0.5)',
            paper_bgcolor='#ffffff' if not dark_mode else '#0f172a',
            margin=dict(l=80, r=70, t=120, b=70),
            height=450,
            hoverlabel=dict(
                bgcolor='rgba(255, 255, 255, 0.95)' if not dark_mode else 'rgba(30, 41, 59, 0.95)',
                font_size=13,
                font_family="Inter, sans-serif",
                bordercolor='#e5e7eb' if not dark_mode else '#475569',
                align="left"
            ),
            font=dict(family="Inter, sans-serif"),
            transition=dict(duration=300, easing="cubic-in-out")
        )
        
        return fig
    
    def create_tou_labels_table(self):
        """Create a table showing TOU labels with their corresponding energy rates"""
        energy_labels = self.tariff.get('energytoulabels', None)
        energy_rates = self.tariff.get('energyratestructure', [])

        # If no energy rate structure, return empty DataFrame
        if not energy_rates:
            return pd.DataFrame()

        # Get weekday and weekend schedules
        weekday_schedule = self.tariff.get('energyweekdayschedule', [])
        weekend_schedule = self.tariff.get('energyweekendschedule', [])

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

                table_data.append({
                    'TOU Period': period_label,
                    'Base Rate ($/kWh)': f"${rate:.4f}",
                    'Adjustment ($/kWh)': f"${adj:.4f}",
                    'Total Rate ($/kWh)': f"${total_rate:.4f}",
                    'Months Present': months_present
                })

        return pd.DataFrame(table_data)

    def create_demand_labels_table(self):
        """Create a table showing demand charge labels with their corresponding rates"""
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

    def _get_months_for_demand_period(self, period_index, weekday_schedule, weekend_schedule):
        """Determine which months a demand period appears in for weekday and weekend schedules"""
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

    def _get_months_for_tou_period(self, period_index, weekday_schedule, weekend_schedule):
        """Determine which months a TOU period appears in for weekday and weekend schedules"""
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

    def _format_month_range(self, months):
        """Format a list of months into a compact range (e.g., 'Jan-Jun' or 'Jan, Mar, Jun')"""
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

def create_temp_viewer_with_modified_tariff(modified_tariff_data):
    """Create a temporary TariffViewer instance with modified tariff data"""
    class TempTariffViewer(TariffViewer):
        def __init__(self, modified_data):
            try:
                self.data = modified_data
                
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
                self.months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                self.hours = list(range(24))
                self.update_rate_dataframes()
                
            except Exception as e:
                st.error(f"Error creating temporary viewer: {str(e)}")
                raise
    
    return TempTariffViewer(modified_tariff_data)

def generate_load_profile(tariff, avg_load, load_factor, tou_percentages, year, 
                         seasonal_variation=0.1, weekend_factor=0.8, 
                         daily_variation=0.15, noise_level=0.05):
    """Generate a synthetic load profile with specified characteristics
    
    Parameters:
    -----------
    tariff : dict
        The tariff data containing TOU schedules
    avg_load : float
        Average load in kW across the year
    load_factor : float
        Load factor (average/peak ratio)
    tou_percentages : dict
        Percentage of energy in each TOU period
    year : int
        Year for the timestamps
    seasonal_variation : float
        Seasonal variation factor (0-0.5)
    weekend_factor : float
        Weekend load as fraction of weekday (0.1-1.5)
    daily_variation : float
        Daily variation factor (0-0.3)
    noise_level : float
        Random noise level (0-0.2)
        
    Returns:
    --------
    pd.DataFrame
        Load profile with timestamp, load_kW, kWh, month, energy_period columns
    """
    
    # Create 15-minute intervals for the entire year
    start_date = datetime(year, 1, 1)
    end_date = datetime(year + 1, 1, 1)
    timestamps = []
    current = start_date
    while current < end_date:
        timestamps.append(current)
        current += timedelta(minutes=15)
    
    df = pd.DataFrame({'timestamp': timestamps})
    df['month'] = df['timestamp'].dt.month
    df['hour'] = df['timestamp'].dt.hour
    df['weekday'] = df['timestamp'].dt.weekday
    df['is_weekend'] = df['weekday'] >= 5
    
    # Calculate peak load from average and load factor
    peak_load = avg_load / load_factor
    
    # Get TOU schedules from tariff
    weekday_schedule = tariff.get('energyweekdayschedule', [])
    weekend_schedule = tariff.get('energyweekendschedule', [])
    
    # Assign TOU periods
    energy_periods = []
    for _, row in df.iterrows():
        month_idx = row['month'] - 1
        hour = row['hour']
        
        if row['is_weekend'] and weekend_schedule and month_idx < len(weekend_schedule):
            if hour < len(weekend_schedule[month_idx]):
                period = weekend_schedule[month_idx][hour]
            else:
                period = 0
        elif weekday_schedule and month_idx < len(weekday_schedule):
            if hour < len(weekday_schedule[month_idx]):
                period = weekday_schedule[month_idx][hour]
            else:
                period = 0
        else:
            period = 0
            
        energy_periods.append(int(period))
    
    df['energy_period'] = energy_periods
    
    # Create base load profile with seasonal variation
    seasonal_multiplier = 1 + seasonal_variation * np.sin(2 * np.pi * (df['month'] - 1) / 12)
    
    # Weekend factor
    weekend_multiplier = np.where(df['is_weekend'], weekend_factor, 1.0)
    
    # Daily variation (higher during certain hours)
    daily_multiplier = 1 + daily_variation * np.sin(2 * np.pi * df['hour'] / 24)
    
    # Random noise
    np.random.seed(42)  # For reproducibility
    noise = 1 + noise_level * np.random.normal(0, 1, len(df))
    
    # Calculate target energy for each TOU period
    total_annual_kwh = avg_load * 8760  # kW * hours in year
    target_energy_by_period = {}
    
    for period, percentage in tou_percentages.items():
        target_energy_by_period[period] = total_annual_kwh * (percentage / 100.0)
    
    # Initialize load array
    load_kw = np.full(len(df), avg_load)
    
    # Apply multipliers
    load_kw *= seasonal_multiplier * weekend_multiplier * daily_multiplier * noise
    
    # Adjust to meet TOU energy targets
    for period in tou_percentages.keys():
        period_mask = df['energy_period'] == period
        if period_mask.sum() > 0:
            current_energy = (load_kw[period_mask] * 0.25).sum()  # 15-min intervals = 0.25 hours
            target_energy = target_energy_by_period[period]
            
            if current_energy > 0:
                adjustment_factor = target_energy / current_energy
                load_kw[period_mask] *= adjustment_factor
    
    # Scale to meet overall average load target
    actual_avg = load_kw.mean()
    if actual_avg > 0:
        load_kw *= (avg_load / actual_avg)
    
    # Apply load factor constraint by scaling peaks
    actual_peak = load_kw.max()
    target_peak = avg_load / load_factor
    
    if actual_peak > target_peak:
        # Compress peaks to meet load factor
        excess_mask = load_kw > target_peak
        load_kw[excess_mask] = target_peak + (load_kw[excess_mask] - target_peak) * 0.1
    
    # Ensure non-negative loads
    load_kw = np.maximum(load_kw, 0)
    
    # Calculate kWh for 15-minute intervals
    df['load_kW'] = load_kw
    df['kWh'] = df['load_kW'] * 0.25  # 15 minutes = 0.25 hours
    
    return df[['timestamp', 'load_kW', 'kWh', 'month', 'energy_period']]

def main():
    st.set_page_config(
        page_title="URDB Tariff Viewer", 
        layout="wide", 
        initial_sidebar_state="expanded",
        page_icon="⚡"
    )
    
    # Modern CSS styling with clean design
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #ffffff;
        color: #1f2937;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Main header styling */
    .main-header {
        font-family: 'Inter', sans-serif;
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin: 0 0 3rem 0;
        padding: 2rem 0;
        position: relative;
    }

    .main-header::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 120px;
        height: 4px;
        background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
        border-radius: 2px;
    }
    
    /* Modern metric cards */
    .metric-card {
        background: #ffffff;
        border: 2px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.75rem 0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15), 0 2px 8px rgba(0, 0, 0, 0.1);
        border-color: #cbd5e1;
    }

    .metric-card h3 {
        color: #1f2937;
        font-size: 0.875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin: 0 0 0.5rem 0;
    }

    .metric-card p {
        color: #0f172a;
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
    }
    
    /* Sidebar styling */
    .stSidebar {
        background-color: #f8fafc !important;
        border-right: 2px solid #cbd5e1 !important;
    }

    .stSidebar > div {
        padding-top: 2rem !important;
    }

    .sidebar-header {
        background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        text-align: center;
        font-weight: 600;
        font-size: 1.1rem;
    }

    /* Ensure sidebar is visible */
    .stSidebar[data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
        width: 300px !important;
        min-width: 300px !important;
    }

    /* Sidebar content styling */
    .stSidebar .stSelectbox label {
        font-weight: 500 !important;
        color: #1f2937 !important;
        font-size: 0.9rem !important;
    }

    .stSidebar .stCheckbox label {
        font-weight: 500 !important;
        color: #1f2937 !important;
    }

    /* Ensure all sidebar text has proper contrast */
    .stSidebar .stSelectbox div,
    .stSidebar .stCheckbox div,
    .stSidebar p,
    .stSidebar span {
        color: #1f2937 !important;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.75rem;
        font-weight: 700;
        color: #0f172a;
        margin: 2.5rem 0 1.5rem 0;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #e5e7eb;
        position: relative;
    }

    .section-header::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 60px;
        height: 2px;
        background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: #f8fafc;
        padding: 6px;
        border-radius: 12px;
        margin-bottom: 2rem;
        border: 1px solid #cbd5e1;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        background-color: transparent;
        border: none;
        color: #374151;
        font-weight: 500;
        padding: 12px 24px;
        transition: all 0.2s ease;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
        color: white !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }

    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        border: 2px solid #1e40af;
        background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
        color: white;
        padding: 0.75rem 1.5rem;
        transition: all 0.2s ease;
        font-family: 'Inter', sans-serif;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        border-color: #1e3a8a;
    }
    
                /* Form controls */
            .stSelectbox > div > div,
            .stNumberInput > div > div > input,
            .stCheckbox > label {
                border-radius: 8px;
                border: 2px solid #cbd5e1;
                font-family: 'Inter', sans-serif;
                background-color: #ffffff !important;
                color: #1f2937 !important;
            }

            .stSelectbox > div > div:focus-within,
            .stNumberInput > div > div > input:focus {
                border-color: #1e40af;
                box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.1);
            }

            /* Light mode selectbox dropdown styling */
            .stSelectbox [data-baseweb="select"] {
                background-color: #ffffff !important;
                border-color: #cbd5e1 !important;
                color: #1f2937 !important;
            }

            .stSelectbox [data-baseweb="select"] * {
                color: #1f2937 !important;
                background-color: inherit !important;
            }

            /* Light mode selectbox dropdown options */
            .stSelectbox [data-baseweb="popover"] {
                background-color: #ffffff !important;
                border: 1px solid #cbd5e1 !important;
                border-radius: 8px !important;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
            }

            .stSelectbox [data-baseweb="menu"] [data-baseweb="menu-item"] {
                color: #1f2937 !important;
                background-color: #ffffff !important;
            }

            .stSelectbox [data-baseweb="menu"] [data-baseweb="menu-item"]:hover {
                background-color: #f8fafc !important;
                color: #1f2937 !important;
            }

            .stSelectbox [data-baseweb="menu"] [data-baseweb="menu-item"][data-baseweb="menu-item--selected"] {
                background-color: #eff6ff !important;
                color: #1e40af !important;
            }

    /* Info boxes */
    .stInfo {
        background-color: #eff6ff;
        border: 2px solid #bfdbfe;
        border-radius: 8px;
        padding: 1rem;
    }

    /* Statistics cards container */
    .stats-container {
        background: #f8fafc;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border: 2px solid #e2e8f0;
    }

    /* Ensure proper spacing for metric columns */
    .stats-container .stColumn {
        padding: 0.5rem;
    }

    /* Additional fallback styling for metric text */
    .stMetric {
        color: inherit !important;
    }

    .stMetric div {
        color: inherit !important;
    }

    .stMetric span {
        color: inherit !important;
    }

    /* Base dataframe styling */
    .stDataFrame {
        color: #1f2937 !important; /* Default to readable dark gray */
        border-radius: 6px !important;
        overflow: hidden !important;
    }

    .stDataFrame div {
        color: inherit !important;
    }

    .stDataFrame span {
        color: inherit !important;
    }

    .stDataFrame td {
        color: inherit !important;
        padding: 8px 12px !important;
        border-bottom: 1px solid #f3f4f6 !important;
    }

    .stDataFrame th {
        color: #1f2937 !important;
        font-weight: 600 !important;
        padding: 12px 12px 8px 12px !important;
        border-bottom: 2px solid #e5e7eb !important;
    }

    /* Improve metric layout */
    [data-testid="metric-container"] {
        background: #ffffff !important;
        border: 2px solid #e5e7eb !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin: 0.5rem 0 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06) !important;
        min-height: 100px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
    }

    [data-testid="metric-container"] [data-testid="metric-label"],
    [data-testid="metric-container"] .stMetricLabel,
    .stMetric [data-testid="metric-label"] {
        color: #1f2937 !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        margin-bottom: 0.5rem !important;
        line-height: 1.2 !important;
    }

    [data-testid="metric-container"] [data-testid="metric-value"],
    [data-testid="metric-container"] .stMetricValue,
    .stMetric [data-testid="metric-value"] {
        color: #000000 !important; /* Pure black for maximum contrast */
        font-weight: 700 !important;
        font-size: 1.5rem !important;
        margin: 0 !important;
        line-height: 1.2 !important;
    }

    [data-testid="metric-container"] [data-testid="metric-delta"],
    [data-testid="metric-container"] .stMetricDelta,
    .stMetric [data-testid="metric-delta"] {
        color: #374151 !important; /* Darker gray for better contrast */
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        margin-top: 0.25rem !important;
        line-height: 1.2 !important;
    }
    




    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f8fafc;
        border-radius: 8px;
        font-weight: 500;
        border: 1px solid #cbd5e1;
    }

    /* Custom divider */
    .custom-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent 0%, #1e40af 50%, transparent 100%);
        border: none;
        margin: 2rem 0;
    }


    </style>
    """, unsafe_allow_html=True)
    

    # Find JSON files from both directories
    script_dir = Path(__file__).parent

    # Look in tariffs subdirectory for original tariffs
    tariffs_dir = script_dir / "tariffs"
    original_files = list(tariffs_dir.glob("*.json")) if tariffs_dir.exists() else []
    
    # Look in user_tariffs subdirectory for user-generated tariffs
    user_tariffs_dir = script_dir / "user_tariffs"
    user_files = list(user_tariffs_dir.glob("*.json")) if user_tariffs_dir.exists() else []

    # If no files found in tariffs dir, check main directory for backward compatibility
    if not original_files:
        original_files = list(script_dir.glob("*.json"))

    # Combine and sort files for consistent ordering
    json_files = original_files + user_files
    json_files.sort()
    
    if not json_files:
        st.error("No JSON files found! Please make sure your JSON files are in the 'tariffs/' or 'user_tariffs/' subdirectories.")
        return

    # Load all tariff info for selection with tags
    tariff_options = []
    
    # Process original tariffs
    for file_path in original_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                tariff = data['items'][0] if 'items' in data else data
                base_name = f"{tariff.get('utility', 'Unknown')} - {tariff.get('name', file_path.name)}"
                display_name = f"📋 {base_name}"  # Original tariff tag
                tariff_options.append((file_path, display_name))
        except Exception as e:
            st.error(f"Error loading {file_path.name}: {str(e)}")
            continue
    
    # Process user-generated tariffs
    for file_path in user_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                tariff = data['items'][0] if 'items' in data else data
                base_name = f"{tariff.get('utility', 'Unknown')} - {tariff.get('name', file_path.name)}"
                display_name = f"👤 {base_name} (User Generated)"  # User-generated tariff tag
                tariff_options.append((file_path, display_name))
        except Exception as e:
            st.error(f"Error loading {file_path.name}: {str(e)}")
            continue

    if not tariff_options:
        st.error("No valid tariff files found!")
        return

    # Initialize current tariff if not exists
    if 'current_tariff' not in st.session_state:
        st.session_state.current_tariff = tariff_options[0][0]
        st.session_state.tariff_viewer = TariffViewer(st.session_state.current_tariff)

    # Initialize modified tariff session state early (before sidebar)
    if 'modified_tariff' not in st.session_state:
        st.session_state.modified_tariff = None
        st.session_state.has_modifications = False

    # Sidebar for controls
    with st.sidebar:
        
        # Tariff selection with modern styling
        st.markdown("### 📊 Select Tariff")
        
        # Find current selection index for sidebar
        sidebar_current_index = 0
        for i, (path, name) in enumerate(tariff_options):
            if path == st.session_state.current_tariff:
                sidebar_current_index = i
                break
        
        selected_file = st.selectbox(
            "Choose a tariff to analyze:",
            options=[option[0] for option in tariff_options],
            format_func=lambda x: next(name for path, name in tariff_options if path == x),
            label_visibility="collapsed",
            key="sidebar_tariff_select",
            index=sidebar_current_index
        )
        
        st.markdown("---")
        
        # Load profile selection
        st.markdown("### 📈 Select Load Profile")
        
        # Find load profile files
        load_profiles_dir = script_dir / "load_profiles"
        sidebar_load_profile_files = []
        if load_profiles_dir.exists():
            sidebar_load_profile_files = list(load_profiles_dir.glob("*.csv"))
        
        if sidebar_load_profile_files:
            # Create load profile options
            sidebar_load_profile_options = []
            for file_path in sidebar_load_profile_files:
                display_name = file_path.stem.replace('_', ' ').title()
                sidebar_load_profile_options.append((file_path, display_name))
            
            # Sort options by display name
            sidebar_load_profile_options.sort(key=lambda x: x[1])
            
            # Initialize current load profile if not exists
            if 'current_load_profile' not in st.session_state:
                st.session_state.current_load_profile = sidebar_load_profile_options[0][0]
            
            # Find current selection index for sidebar
            sidebar_lp_current_index = 0
            for i, (path, name) in enumerate(sidebar_load_profile_options):
                if path == st.session_state.current_load_profile:
                    sidebar_lp_current_index = i
                    break
            
            selected_load_profile = st.selectbox(
                "Choose a load profile:",
                options=[option[0] for option in sidebar_load_profile_options],
                format_func=lambda x: next(name for path, name in sidebar_load_profile_options if path == x),
                label_visibility="collapsed",
                key="sidebar_load_profile_select",
                index=sidebar_lp_current_index
            )
            
            # Update session state when sidebar load profile selector changes
            if selected_load_profile != st.session_state.current_load_profile:
                st.session_state.current_load_profile = selected_load_profile
                st.success("✅ Load profile updated!")
                
            # Show current load profile info
            current_lp_name = next(name for path, name in sidebar_load_profile_options if path == selected_load_profile)
            st.caption(f"📊 **Current**: {current_lp_name}")
            
        else:
            st.info("📁 No load profile files found in 'load_profiles' directory")
            st.session_state.current_load_profile = None
        
        st.markdown("---")
        
        # Tariff save functionality
        if st.session_state.has_modifications:
            st.markdown("### 💾 Save Modified Tariff")
            st.success("✏️ **Modified tariff** - Changes are not saved to original file")
            
            if st.button("🔄 Reset to Original", help="Discard all changes and restore original tariff", use_container_width=True):
                st.session_state.modified_tariff = None
                st.session_state.has_modifications = False
                # Clear energy form state to reload original values
                if 'form_labels' in st.session_state:
                    del st.session_state.form_labels
                if 'form_rates' in st.session_state:
                    del st.session_state.form_rates
                if 'form_adjustments' in st.session_state:
                    del st.session_state.form_adjustments
                # Clear demand form state to reload original values
                if 'demand_form_labels' in st.session_state:
                    del st.session_state.demand_form_labels
                if 'demand_form_rates' in st.session_state:
                    del st.session_state.demand_form_rates
                if 'demand_form_adjustments' in st.session_state:
                    del st.session_state.demand_form_adjustments
                # Clear flat demand form state to reload original values
                if 'flat_demand_form_rates' in st.session_state:
                    del st.session_state.flat_demand_form_rates
                if 'flat_demand_form_adjustments' in st.session_state:
                    del st.session_state.flat_demand_form_adjustments
                st.rerun()
            
            if st.button("💾 Save As New File", type="primary", help="Save modified tariff as a new JSON file", use_container_width=True):
                st.session_state.show_save_dialog = True
            
            # Save dialog in sidebar
            if st.session_state.get('show_save_dialog', False):
                st.markdown("#### 💾 Save File")
                
                with st.form("sidebar_save_tariff_form"):
                    # Generate default filename
                    default_name = f"{st.session_state.tariff_viewer.utility_name}_{st.session_state.tariff_viewer.rate_name}_Modified".replace(" ", "_").replace("-", "_")
                    # Clean filename by replacing invalid characters
                    clean_default = "".join(c if c.isalnum() or c in "._-" else "_" for c in default_name)
                    
                    new_filename = st.text_input(
                        "Filename:",
                        value=clean_default,
                        help="Enter a name for the new tariff file (without .json extension)"
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Save", type="primary"):
                            if new_filename.strip():
                                try:
                                    # Clean filename
                                    clean_filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in new_filename.strip())
                                    if not clean_filename.endswith('.json'):
                                        clean_filename += '.json'
                                    
                                    # Create user_tariffs directory if it doesn't exist
                                    script_dir = Path(__file__).parent
                                    user_tariffs_dir = script_dir / "user_tariffs"
                                    user_tariffs_dir.mkdir(exist_ok=True)
                                    
                                    filepath = user_tariffs_dir / clean_filename
                                    
                                    # Save the modified tariff
                                    with open(filepath, 'w') as f:
                                        json.dump(st.session_state.modified_tariff, f, indent=2, ensure_ascii=False)
                                    
                                    # Use toast notifications instead of sidebar messages
                                    st.toast(f"✅ Saved as '{clean_filename}'!", icon="✅")
                                    st.toast("🔄 Refresh to see in dropdown", icon="🔄")
                                    st.session_state.show_save_dialog = False
                                    
                                except Exception as e:
                                    st.toast(f"❌ Error: {str(e)}", icon="❌")
                            else:
                                st.toast("❌ Please enter a filename.", icon="❌")
                    
                    with col2:
                        if st.form_submit_button("❌ Cancel"):
                            st.session_state.show_save_dialog = False
                            st.rerun()
            
            st.markdown("---")
        
        # Tariff upload section
        st.markdown("### 📁 Upload New Tariff")
        
        uploaded_file = st.file_uploader(
            "Upload Tariff JSON File",
            type=['json'],
            accept_multiple_files=False,
            help="Upload a URDB tariff JSON file (max 1MB) - will be saved to user_tariffs/ directory",
            key="tariff_upload"
        )
        
        # Display file size limit info
        st.caption("📏 **File size limit**: 1MB maximum | 📁 **Saved to**: user_tariffs/ directory")
        
        if uploaded_file is not None:
            # Validate file size (1MB = 1,048,576 bytes)
            if uploaded_file.size > 1048576:
                st.error("❌ File size exceeds 1MB limit. Please upload a smaller file.")
            else:
                try:
                    # Try to parse the JSON to validate it
                    file_content = uploaded_file.read()
                    json_data = json.loads(file_content.decode('utf-8'))
                    
                    # Basic validation - check if it looks like a URDB tariff
                    is_valid_tariff = False
                    if isinstance(json_data, dict):
                        # Check for URDB tariff structure
                        if 'items' in json_data and isinstance(json_data['items'], list) and len(json_data['items']) > 0:
                            tariff_item = json_data['items'][0]
                            if isinstance(tariff_item, dict) and ('utility' in tariff_item or 'name' in tariff_item):
                                is_valid_tariff = True
                        # Also accept direct tariff objects (not wrapped in 'items')
                        elif 'utility' in json_data or 'name' in json_data:
                            is_valid_tariff = True
                    
                    if is_valid_tariff:
                        # Create user_tariffs directory if it doesn't exist (uploaded files go to user_tariffs)
                        user_tariffs_dir = script_dir / "user_tariffs"
                        user_tariffs_dir.mkdir(exist_ok=True)
                        
                        # Generate filename (clean the uploaded filename)
                        original_name = uploaded_file.name
                        if not original_name.endswith('.json'):
                            original_name += '.json'
                        
                        # Clean filename to remove special characters
                        import re
                        clean_name = re.sub(r'[^\w\-_\.]', '_', original_name)
                        filepath = user_tariffs_dir / clean_name
                        
                        # Check if file already exists
                        if filepath.exists():
                            if st.button("⚠️ File exists! Click to overwrite", type="secondary"):
                                # Save the file
                                with open(filepath, 'wb') as f:
                                    f.write(file_content)
                                st.success(f"✅ Tariff file '{clean_name}' uploaded and saved successfully!")
                                st.info("🔄 Please refresh the page or reselect the tariff to see the new file in the dropdown.")
                        else:
                            # Save the file
                            with open(filepath, 'wb') as f:
                                f.write(file_content)
                            st.success(f"✅ Tariff file '{clean_name}' uploaded and saved successfully!")
                            st.info("🔄 Please refresh the page or reselect the tariff to see the new file in the dropdown.")
                    else:
                        st.error("❌ Invalid tariff format. Please upload a valid URDB tariff JSON file.")
                        st.info("💡 The file should contain either:\n- An 'items' array with tariff objects\n- A direct tariff object with 'utility' or 'name' fields")
                
                except json.JSONDecodeError as e:
                    st.error(f"❌ Invalid JSON file: {str(e)}")
                except UnicodeDecodeError:
                    st.error("❌ File encoding error. Please ensure the file is saved in UTF-8 format.")
                except Exception as e:
                    st.error(f"❌ Error processing file: {str(e)}")
        
        st.markdown("---")
        
        # Tariff download section
        st.markdown("### 📥 Download Current Tariff")
        
        # Get current tariff data
        if 'tariff_viewer' in st.session_state and st.session_state.tariff_viewer:
            current_tariff_data = st.session_state.tariff_viewer.data
            current_tariff_name = f"{st.session_state.tariff_viewer.utility_name}_{st.session_state.tariff_viewer.rate_name}".replace(" ", "_").replace("-", "_")
            
            # Clean the filename
            import re
            clean_filename = re.sub(r'[^\w\-_]', '_', current_tariff_name)
            download_filename = f"{clean_filename}.json"
            
            # Convert to JSON string with proper formatting
            json_string = json.dumps(current_tariff_data, indent=2, ensure_ascii=False)
            
            st.download_button(
                label="📄 Download Tariff JSON",
                data=json_string,
                file_name=download_filename,
                mime="application/json",
                help=f"Download the currently selected tariff: {st.session_state.tariff_viewer.utility_name} - {st.session_state.tariff_viewer.rate_name}",
                use_container_width=True
            )
            
            # Show file info
            st.caption(f"📋 **Current tariff**: {st.session_state.tariff_viewer.utility_name} - {st.session_state.tariff_viewer.rate_name}")
        else:
            st.info("🔄 No tariff selected. Please select a tariff to enable download.")
        
        st.markdown("---")
        
        # Display preferences
        st.markdown("### 🎨 Display Preferences")
        dark_mode = st.checkbox("🌙 Dark Mode", value=True)

        # Update session state when sidebar selector changes
        if selected_file != st.session_state.current_tariff:
            try:
                st.session_state.tariff_viewer = TariffViewer(selected_file)
                st.session_state.current_tariff = selected_file
                st.rerun()
            except Exception as e:
                st.error(f"Error loading tariff: {str(e)}")
                st.exception(e)
                return

        viewer = st.session_state.tariff_viewer



    # Apply additional theme overrides and modern polish (after we know dark_mode)
    if 'dark_mode' in locals() and dark_mode:
        st.markdown(
            """
            <style>
            .stApp {
                background: #0f172a !important;
                color: #f1f5f9;
            }
            .metric-card, .stats-container {
                background: #1e293b !important;
                border-color: #334155 !important;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3), 0 1px 2px rgba(0, 0, 0, 0.2) !important;
            }
            .metric-card h3, .section-header {
                color: #f1f5f9 !important;
            }
            .metric-card p {
                color: #e2e8f0 !important;
            }
            .stTabs [data-baseweb="tab-list"] {
                background: #1e293b !important;
                border-color: #334155 !important;
            }
            .stTabs [data-baseweb="tab"] {
                color: #cbd5e1 !important;
            }
            .stTabs [aria-selected="true"] {
                box-shadow: 0 2px 10px rgba(0,0,0,0.5) !important;
            }
            .stSidebar {
                background: #0f172a !important;
                border-right: 2px solid #334155 !important;
            }
            .stSidebar .stSelectbox label,
            .stSidebar .stCheckbox label {
                color: #f1f5f9 !important;
            }
            .stButton > button {
                border-color: #3b82f6 !important;
                box-shadow: 0 4px 16px rgba(59,130,246,0.3) !important;
            }
            .chips {
                display: flex;
                gap: 8px;
                justify-content: center;
                flex-wrap: wrap;
                margin: 8px 0 20px 0;
            }
            .chip {
                background: rgba(51, 65, 85, 0.8);
                border: 1px solid #475569;
                color: #f1f5f9;
                padding: 8px 12px;
                border-radius: 9999px;
                font-weight: 600;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            }
            .main-header {
                background: none !important;
                -webkit-background-clip: initial !important;
                -webkit-text-fill-color: initial !important;
                background-clip: initial !important;
                color: #ffffff !important;
            }
            .section-header {
                color: #f1f5f9 !important;
                border-bottom-color: #334155 !important;
            }
            .custom-divider {
                background: linear-gradient(90deg, transparent 0%, #3b82f6 50%, transparent 100%) !important;
            }
            .stInfo {
                background-color: #1e293b !important;
                border-color: #334155 !important;
                color: #f1f5f9 !important;
            }
            .streamlit-expanderHeader {
                background-color: #1e293b !important;
                border-color: #334155 !important;
                color: #f1f5f9 !important;
            }
            /* Dark mode metric styling */
            [data-testid="metric-container"] {
                background: #1e293b !important;
                border-color: #334155 !important;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3), 0 1px 2px rgba(0, 0, 0, 0.2) !important;
            }
            [data-testid="metric-container"] [data-testid="metric-label"] {
                color: #cbd5e1 !important;
            }
            [data-testid="metric-container"] [data-testid="metric-value"] {
                color: #f1f5f9 !important;
            }
            [data-testid="metric-container"] [data-testid="metric-delta"] {
                color: #94a3b8 !important;
            }
            .stats-container {
                background: #0f172a !important;
                border-color: #334155 !important;
            }

            /* Dark mode app and sidebar styling for better text readability */
            .stApp {
                background-color: #0f172a !important;
                color: #f1f5f9 !important;
            }

            .stSidebar {
                background-color: #0f172a !important;
                border-right: 2px solid #334155 !important;
                color: #f1f5f9 !important;
            }

            .stSidebar .sidebar-header {
                background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important;
                color: #ffffff !important;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
            }

            /* Dark mode sidebar text colors for optimal contrast */
            .stSidebar .stSelectbox label,
            .stSidebar .stCheckbox label {
                color: #f1f5f9 !important;
                font-weight: 500 !important;
            }

            .stSidebar .stSelectbox div,
            .stSidebar .stCheckbox div,
            .stSidebar p,
            .stSidebar span,
            .stSidebar .stSelectbox,
            .stSidebar .stCheckbox {
                color: #f1f5f9 !important;
            }

            /* Dark mode sidebar interactive elements */
            .stSidebar .stSelectbox [data-baseweb="select"] {
                background-color: #1e293b !important;
                border-color: #334155 !important;
            }

            .stSidebar .stSelectbox [data-baseweb="select"] *,
            .stSidebar .stSelectbox [data-baseweb="select"] span,
            .stSidebar .stSelectbox [data-baseweb="select"] div {
                color: #f1f5f9 !important;
            }

            .stSidebar .stCheckbox [data-baseweb="checkbox"] {
                background-color: #1e293b !important;
            }

            /* Dark mode info boxes in sidebar */
            .stSidebar .stInfo {
                background-color: #1e293b !important;
                border-color: #334155 !important;
                color: #f1f5f9 !important;
            }

            .stSidebar .stInfo *,
            .stSidebar .stInfo p,
            .stSidebar .stInfo span {
                color: #f1f5f9 !important;
            }

            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            .stApp {
                background: #ffffff !important;
                color: #1f2937;
            }
            .metric-card, .stats-container {
                background: #ffffff !important;
                border-color: #e5e7eb !important;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06) !important;
            }
            .section-header { color: #0f172a !important; }
            .stTabs [data-baseweb="tab-list"] {
                background: #f8fafc !important;
                border-color: #cbd5e1 !important;
            }
            .stSidebar {
                background: #f8fafc !important;
                border-right: 2px solid #cbd5e1 !important;
            }
            .chips {
                display: flex;
                gap: 8px;
                justify-content: center;
                flex-wrap: wrap;
                margin: 8px 0 20px 0;
            }
            .chip {
                background: rgba(59, 130, 246, 0.08);
                border: 1px solid #cbd5e1;
                color: #1f2937;
                padding: 8px 12px;
                border-radius: 9999px;
                font-weight: 600;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
            }
            .stInfo {
                color: #1f2937 !important;
            }
            .streamlit-expanderHeader {
                color: #1f2937 !important;
            }

            /* Light mode metric styling */
            [data-testid="metric-container"] {
                background: #ffffff !important;
                border-color: #e5e7eb !important;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06) !important;
            }

            /* Comprehensive metric text styling for light mode */
            [data-testid="metric-container"] [data-testid="metric-label"],
            [data-testid="metric-container"] .stMetricLabel,
            .stMetric [data-testid="metric-label"] {
                color: #1f2937 !important; /* Darker gray for better contrast */
                font-weight: 600 !important;
                font-size: 0.875rem !important;
                margin-bottom: 0.5rem !important;
                line-height: 1.2 !important;
            }

            [data-testid="metric-container"] [data-testid="metric-value"],
            [data-testid="metric-container"] .stMetricValue,
            .stMetric [data-testid="metric-value"] {
                color: #000000 !important; /* Pure black for maximum contrast */
                font-weight: 700 !important;
                font-size: 1.5rem !important;
                margin: 0 !important;
                line-height: 1.2 !important;
            }

            [data-testid="metric-container"] [data-testid="metric-delta"],
            [data-testid="metric-container"] .stMetricDelta,
            .stMetric [data-testid="metric-delta"] {
                color: #374151 !important; /* Darker gray for delta text */
                font-weight: 500 !important;
                font-size: 0.875rem !important;
                margin-top: 0.25rem !important;
                line-height: 1.2 !important;
            }
            .stats-container {
                background: #f8fafc !important;
                border-color: #e2e8f0 !important;
                border: 2px solid #e2e8f0 !important;
                border-radius: 8px !important;
                padding: 1.5rem !important;
                margin: 1rem 0 !important;
            }

            /* Light mode sidebar styling */
            .stSidebar {
                background-color: #f8fafc !important;
                border-right: 2px solid #cbd5e1 !important;
                color: #1f2937 !important;
            }

            .stSidebar .sidebar-header {
                background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%) !important;
                color: white !important;
            }

            /* Sidebar text colors for light mode */
            .stSidebar .stSelectbox label {
                color: #1f2937 !important;
                font-weight: 500 !important;
            }

            .stSidebar .stCheckbox label {
                color: #1f2937 !important;
                font-weight: 500 !important;
            }

            .stSidebar .stSelectbox div {
                color: #1f2937 !important;
            }

            .stSidebar .stCheckbox div {
                color: #1f2937 !important;
            }

            .stSidebar p, .stSidebar span, .stSidebar div {
                color: #1f2937 !important;
            }

            /* Info box styling in sidebar for light mode */
            .stSidebar .stInfo {
                background-color: #eff6ff !important;
                border: 2px solid #bfdbfe !important;
                border-radius: 8px !important;
                color: #1f2937 !important;
            }

            /* Light mode dataframe styling - force text visibility */
            .stDataFrame {
                color: #000000 !important; /* Force black text for maximum visibility */
                background-color: #ffffff !important;
                border: 1px solid #e5e7eb !important;
                border-radius: 8px !important;
            }

            /* Force all dataframe content to be visible */
            .stDataFrame * {
                color: #000000 !important; /* Force black text on all elements */
                background-color: transparent !important;
            }

            /* Specific styling for table cells */
            .stDataFrame td {
                color: #000000 !important;
                background-color: #ffffff !important;
                border-bottom: 1px solid #f3f4f6 !important;
                padding: 8px 12px !important;
            }

            .stDataFrame th {
                color: #000000 !important; /* Force black for headers too */
                background-color: #f9fafb !important;
                font-weight: 600 !important;
                border-bottom: 2px solid #e5e7eb !important;
                padding: 12px 12px 8px 12px !important;
            }

            /* Target Streamlit's specific dataframe structure */
            .stDataFrame [data-testid="stDataFrame"] {
                color: #000000 !important;
                background-color: #ffffff !important;
            }

            .stDataFrame [data-testid="stDataFrame"] * {
                color: #000000 !important;
            }

            /* Ensure table content is visible */
            .stDataFrame table,
            .stDataFrame table * {
                color: #000000 !important;
                background-color: transparent !important;
            }

            /* Light mode sidebar selectbox styling */
            .stSidebar .stSelectbox [data-baseweb="select"] {
                background-color: #f8fafc !important;
                border-color: #cbd5e1 !important;
                color: #1f2937 !important;
            }

            .stSidebar .stSelectbox [data-baseweb="select"] * {
                color: #1f2937 !important;
                background-color: inherit !important;
            }

            /* Light mode sidebar selectbox dropdown options */
            .stSidebar .stSelectbox [data-baseweb="popover"] {
                background-color: #ffffff !important;
                border: 1px solid #cbd5e1 !important;
                border-radius: 8px !important;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
            }

            .stSidebar .stSelectbox [data-baseweb="menu"] [data-baseweb="menu-item"] {
                color: #1f2937 !important;
                background-color: #ffffff !important;
            }

            .stSidebar .stSelectbox [data-baseweb="menu"] [data-baseweb="menu-item"]:hover {
                background-color: #f8fafc !important;
                color: #1f2937 !important;
            }

            .stSidebar .stSelectbox [data-baseweb="menu"] [data-baseweb="menu-item"][data-baseweb="menu-item--selected"] {
                background-color: #eff6ff !important;
                color: #1e40af !important;
            }

            </style>
            """,
            unsafe_allow_html=True,
        )

    # Context chips for quick reference
    st.markdown(
        f"""
        <div class="chips">
            <div class="chip">🏢 {viewer.utility_name}</div>
            <div class="chip">⚡ {viewer.rate_name}</div>
            <div class="chip">🏭 {viewer.sector}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Set default visualization settings since controls were removed
    show_text = True
    chart_height = 700
    text_size = 12
    
    # Session state already initialized earlier
    
    # Track current tariff file to detect changes
    current_tariff_file = str(st.session_state.current_tariff)
    if 'last_tariff_file' not in st.session_state or st.session_state.last_tariff_file != current_tariff_file:
        # Tariff has changed, clear all form states to force re-initialization
        st.session_state.last_tariff_file = current_tariff_file
        
        # Clear energy form state
        if 'form_labels' in st.session_state:
            del st.session_state.form_labels
        if 'form_rates' in st.session_state:
            del st.session_state.form_rates
        if 'form_adjustments' in st.session_state:
            del st.session_state.form_adjustments
            
        # Clear demand form state
        if 'demand_form_labels' in st.session_state:
            del st.session_state.demand_form_labels
        if 'demand_form_rates' in st.session_state:
            del st.session_state.demand_form_rates
        if 'demand_form_adjustments' in st.session_state:
            del st.session_state.demand_form_adjustments
            
        # Clear flat demand form state
        if 'flat_demand_form_rates' in st.session_state:
            del st.session_state.flat_demand_form_rates
        if 'flat_demand_form_adjustments' in st.session_state:
            del st.session_state.flat_demand_form_adjustments
            
        # Clear modification state when switching tariffs (unless it's a user-generated tariff)
        if not current_tariff_file.startswith(str(Path(__file__).parent / "user_tariffs")):
            st.session_state.modified_tariff = None
            st.session_state.has_modifications = False
    
    
    # Create tabs for energy and demand rates with modern styling
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["⚡ Energy Rates", "🔌 Demand Rates", "📊 Flat Demand", "💰 Utility Cost Calculator", "🔧 Load Profile Generator", "📊 LP Analysis"])
    
    with tab1:
        st.markdown("### ⚡ Energy Rate Structure")
        
        # Use modified tariff if available, otherwise use original
        if st.session_state.modified_tariff:
            # Extract tariff data from modified structure
            if 'items' in st.session_state.modified_tariff:
                current_tariff = st.session_state.modified_tariff['items'][0]
            else:
                current_tariff = st.session_state.modified_tariff
        else:
            current_tariff = viewer.tariff
        
        
        # Show current table (read-only) first
        st.markdown("#### 📊 Current Rate Table")
        
        energy_labels = current_tariff.get('energytoulabels', [])
        energy_rates = current_tariff.get('energyratestructure', [])
        
        
        # Create table data for display
        table_data = []
        weekday_schedule = current_tariff.get('energyweekdayschedule', [])
        weekend_schedule = current_tariff.get('energyweekendschedule', [])
        
        current_energy_labels = current_tariff.get('energytoulabels', [])
        current_energy_rates = current_tariff.get('energyratestructure', [])
        
        for i, rate_structure in enumerate(current_energy_rates):
            if rate_structure:
                rate_info = rate_structure[0]
                rate = rate_info.get('rate', 0)
                adj = rate_info.get('adj', 0)
                total_rate = rate + adj

                if current_energy_labels and i < len(current_energy_labels):
                    period_label = current_energy_labels[i]
                else:
                    period_label = f"Period {i}"

                # Determine which months this TOU period appears in
                months_present = viewer._get_months_for_tou_period(i, weekday_schedule, weekend_schedule)

                table_data.append({
                    'TOU Period': period_label,
                    'Base Rate ($/kWh)': f"${rate:.4f}",
                    'Adjustment ($/kWh)': f"${adj:.4f}",
                    'Total Rate ($/kWh)': f"${total_rate:.4f}",
                    'Months Present': months_present
                })

        if table_data:
            display_df = pd.DataFrame(table_data)
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "TOU Period": st.column_config.TextColumn(
                        "TOU Period",
                        width="medium",
                    ),
                    "Base Rate ($/kWh)": st.column_config.TextColumn(
                        "Base Rate ($/kWh)",
                        width="small",
                    ),
                    "Adjustment ($/kWh)": st.column_config.TextColumn(
                        "Adjustment ($/kWh)", 
                        width="small",
                    ),
                    "Total Rate ($/kWh)": st.column_config.TextColumn(
                        "Total Rate ($/kWh)",
                        width="small",
                    ),
                    "Months Present": st.column_config.TextColumn(
                        "Months Present",
                        width="large",
                    )
                }
            )
        else:
            st.info("📝 **Note:** No energy rate structure found in this tariff JSON.")
        
        st.markdown("---")
        
        # TOU Labels Table - Editable
        st.markdown("#### 🏷️ Time-of-Use Period Labels & Rates (Editable)")
        
        if energy_rates:
            # Initialize form values in session state if not exists or if we need to refresh from current tariff
            form_needs_init = (
                'form_labels' not in st.session_state or 
                len(st.session_state.get('form_labels', [])) != len(energy_rates) or
                len(st.session_state.get('form_rates', [])) != len(energy_rates)
            )
            
            if form_needs_init:
                st.session_state.form_labels = energy_labels.copy() if energy_labels else []
                st.session_state.form_rates = []
                st.session_state.form_adjustments = []
                
                for i, rate_structure in enumerate(energy_rates):
                    if rate_structure:
                        rate_info = rate_structure[0]
                        st.session_state.form_rates.append(float(rate_info.get('rate', 0)))
                        st.session_state.form_adjustments.append(float(rate_info.get('adj', 0)))
                    else:
                        st.session_state.form_rates.append(0.0)
                        st.session_state.form_adjustments.append(0.0)
                
                # Ensure we have labels for all periods
                while len(st.session_state.form_labels) < len(energy_rates):
                    st.session_state.form_labels.append(f"Period {len(st.session_state.form_labels)}")
            
            # Create editable form
            with st.form("energy_rates_form"):
                st.markdown("**Edit the rates below and click 'Apply Changes' to update:**")
                
                edited_labels = []
                edited_rates = []
                
                # Create columns for the form
                col_headers = st.columns([3, 2, 2, 1])
                col_headers[0].write("**TOU Period Name**")
                col_headers[1].write("**Base Rate ($/kWh)**")
                col_headers[2].write("**Adjustment ($/kWh)**")
                col_headers[3].write("**Total**")
                
                for i, rate_structure in enumerate(energy_rates):
                    if rate_structure:  # Ensure rate structure exists
                        rate_info = rate_structure[0]  # Get first tier
                        
                        # Use session state values if available, otherwise use original values
                        if i < len(st.session_state.form_labels):
                            current_label = st.session_state.form_labels[i]
                        elif energy_labels and i < len(energy_labels):
                            current_label = energy_labels[i]
                        else:
                            current_label = f"Period {i}"
                        
                        if i < len(st.session_state.form_rates):
                            base_rate = st.session_state.form_rates[i]
                        else:
                            base_rate = float(rate_info.get('rate', 0))
                        
                        if i < len(st.session_state.form_adjustments):
                            adjustment = st.session_state.form_adjustments[i]
                        else:
                            adjustment = float(rate_info.get('adj', 0))
                        
                        # Create input fields
                        cols = st.columns([3, 2, 2, 1])
                        
                        with cols[0]:
                            new_label = st.text_input(
                                f"Label {i}",
                                value=current_label,
                                key=f"label_{i}",
                                label_visibility="collapsed"
                            )
                            edited_labels.append(new_label)
                        
                        with cols[1]:
                            new_base_rate = st.number_input(
                                f"Base Rate {i}",
                                value=base_rate,
                                step=0.0001,
                                format="%.4f",
                                key=f"base_rate_{i}",
                                label_visibility="collapsed"
                            )
                        
                        with cols[2]:
                            new_adjustment = st.number_input(
                                f"Adjustment {i}",
                                value=adjustment,
                                step=0.0001,
                                format="%.4f",
                                key=f"adjustment_{i}",
                                label_visibility="collapsed"
                            )
                        
                        with cols[3]:
                            total_rate = new_base_rate + new_adjustment
                            st.write(f"${total_rate:.4f}")
                        
                        # Store the edited rate structure
                        edited_rate_info = rate_info.copy()
                        edited_rate_info['rate'] = new_base_rate
                        edited_rate_info['adj'] = new_adjustment
                        edited_rates.append([edited_rate_info])
                    else:
                        edited_rates.append([])
                        edited_labels.append(f"Period {i}")
                
                # Apply changes button
                if st.form_submit_button("✅ Apply Changes", type="primary"):
                    # Update session state with new values
                    st.session_state.form_labels = edited_labels.copy()
                    st.session_state.form_rates = [edited_rates[i][0]['rate'] if edited_rates[i] else 0.0 for i in range(len(edited_rates))]
                    st.session_state.form_adjustments = [edited_rates[i][0]['adj'] if edited_rates[i] else 0.0 for i in range(len(edited_rates))]
                    
                    # Create modified tariff - use deep copy to avoid reference issues
                    import copy
                    if not st.session_state.modified_tariff:
                        st.session_state.modified_tariff = copy.deepcopy(viewer.data)
                    
                    # Update the tariff data
                    if 'items' in st.session_state.modified_tariff:
                        tariff_data = st.session_state.modified_tariff['items'][0]
                    else:
                        tariff_data = st.session_state.modified_tariff
                    
                    # Update energy rate structure
                    tariff_data['energyratestructure'] = edited_rates
                    
                    # Update energy TOU labels
                    tariff_data['energytoulabels'] = edited_labels
                    
                    st.session_state.has_modifications = True
                    st.success("✅ Changes applied! The visualizations will update to reflect your changes.")
                    st.rerun()
            
        
        st.markdown("---")

        
        # Weekday Energy Rates - Full Width
        st.markdown("#### 📈 Weekday Energy Rates")
        
        # Create a temporary viewer with modified tariff if needed
        if st.session_state.has_modifications and st.session_state.modified_tariff:
            temp_viewer = create_temp_viewer_with_modified_tariff(st.session_state.modified_tariff)
            st.plotly_chart(temp_viewer.plot_heatmap(is_weekday=True, dark_mode=dark_mode, rate_type="energy", chart_height=chart_height, text_size=text_size), use_container_width=True)
        else:
            st.plotly_chart(viewer.plot_heatmap(is_weekday=True, dark_mode=dark_mode, rate_type="energy", chart_height=chart_height, text_size=text_size), use_container_width=True)
        
        st.markdown("---")
        
        # Weekend Energy Rates - Full Width
        st.markdown("#### 📉 Weekend Energy Rates")
        
        if st.session_state.has_modifications and st.session_state.modified_tariff:
            temp_viewer = create_temp_viewer_with_modified_tariff(st.session_state.modified_tariff)
            st.plotly_chart(temp_viewer.plot_heatmap(is_weekday=False, dark_mode=dark_mode, rate_type="energy", chart_height=chart_height, text_size=text_size), use_container_width=True)
        else:
            st.plotly_chart(viewer.plot_heatmap(is_weekday=False, dark_mode=dark_mode, rate_type="energy", chart_height=chart_height, text_size=text_size), use_container_width=True)
        
    with tab2:
        st.markdown("### 🔌 Demand Charge Rate Structure")
        
        # Use the same modified tariff logic as energy rates
        if st.session_state.modified_tariff:
            # Extract tariff data from modified structure
            if 'items' in st.session_state.modified_tariff:
                current_demand_tariff = st.session_state.modified_tariff['items'][0]
            else:
                current_demand_tariff = st.session_state.modified_tariff
        else:
            current_demand_tariff = viewer.tariff

        # Show current demand rate table first
        st.markdown("#### 📊 Current Demand Rate Table")
        
        demand_labels = current_demand_tariff.get('demandlabels', [])
        demand_rates = current_demand_tariff.get('demandratestructure', [])
        
        # Create table data for display
        demand_table_data = []
        demand_weekday_schedule = current_demand_tariff.get('demandweekdayschedule', [])
        demand_weekend_schedule = current_demand_tariff.get('demandweekendschedule', [])
        
        current_demand_labels = current_demand_tariff.get('demandlabels', [])
        current_demand_rates = current_demand_tariff.get('demandratestructure', [])
        
        if current_demand_rates:
            # If we have labels, use them; otherwise create generic labels
            if current_demand_labels:
                labels_to_use = current_demand_labels
            else:
                labels_to_use = ["Demand Label Not In Tariff JSON"] * len(current_demand_rates)
            
            for i, label in enumerate(labels_to_use):
                if i < len(current_demand_rates) and current_demand_rates[i]:
                    rate_info = current_demand_rates[i][0]  # Get first tier
                    rate = rate_info.get('rate', 0)
                    adj = rate_info.get('adj', 0)
                    total_rate = rate + adj
                    
                    # Determine which months this demand period appears in
                    months_present = viewer._get_months_for_tou_period(i, demand_weekday_schedule, demand_weekend_schedule)
                    
                    demand_table_data.append({
                        'Demand Period': label,
                        'Base Rate ($/kW)': f"${rate:.4f}",
                        'Adjustment ($/kW)': f"${adj:.4f}",
                        'Total Rate ($/kW)': f"${total_rate:.4f}",
                        'Months Present': months_present
                    })
            
            if demand_table_data:
                display_demand_df = pd.DataFrame(demand_table_data)
                st.dataframe(
                    display_demand_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Demand Period": st.column_config.TextColumn(
                            "Demand Period",
                            width="medium",
                        ),
                        "Base Rate ($/kW)": st.column_config.TextColumn(
                            "Base Rate ($/kW)",
                            width="small",
                        ),
                        "Adjustment ($/kW)": st.column_config.TextColumn(
                            "Adjustment ($/kW)", 
                            width="small",
                        ),
                        "Total Rate ($/kW)": st.column_config.TextColumn(
                            "Total Rate ($/kW)",
                            width="small",
                        ),
                        "Months Present": st.column_config.TextColumn(
                            "Months Present",
                            width="large",
                        )
                    }
                )
        else:
            st.info("📝 **Note:** No demand rate structure found in this tariff JSON.")
        
        st.markdown("---")
        
        # Demand Labels Table - Editable
        st.markdown("#### 🏷️ Demand Period Labels & Rates (Editable)")
        
        if demand_rates:
            # Initialize demand form values in session state if not exists or if we need to refresh from current tariff
            demand_form_needs_init = (
                'demand_form_labels' not in st.session_state or 
                len(st.session_state.get('demand_form_labels', [])) != len(demand_rates) or
                len(st.session_state.get('demand_form_rates', [])) != len(demand_rates)
            )
            
            if demand_form_needs_init:
                st.session_state.demand_form_labels = demand_labels.copy() if demand_labels else []
                st.session_state.demand_form_rates = []
                st.session_state.demand_form_adjustments = []
                
                for i, rate_structure in enumerate(demand_rates):
                    if rate_structure:
                        rate_info = rate_structure[0]
                        st.session_state.demand_form_rates.append(float(rate_info.get('rate', 0)))
                        st.session_state.demand_form_adjustments.append(float(rate_info.get('adj', 0)))
                    else:
                        st.session_state.demand_form_rates.append(0.0)
                        st.session_state.demand_form_adjustments.append(0.0)
                
                # Ensure we have labels for all periods
                while len(st.session_state.demand_form_labels) < len(demand_rates):
                    st.session_state.demand_form_labels.append(f"Demand Period {len(st.session_state.demand_form_labels)}")
            
            # Create editable form for demand rates
            with st.form("demand_rates_form"):
                st.markdown("**Edit the demand rates below and click 'Apply Changes' to update:**")
                
                edited_demand_labels = []
                edited_demand_rates = []
                
                # Create columns for the form
                col_headers = st.columns([3, 2, 2, 1])
                col_headers[0].write("**Demand Period Name**")
                col_headers[1].write("**Base Rate ($/kW)**")
                col_headers[2].write("**Adjustment ($/kW)**")
                col_headers[3].write("**Total**")
                
                for i, rate_structure in enumerate(demand_rates):
                    if rate_structure:  # Ensure rate structure exists
                        rate_info = rate_structure[0]  # Get first tier
                        
                        # Use session state values if available, otherwise use original values
                        if i < len(st.session_state.demand_form_labels):
                            current_label = st.session_state.demand_form_labels[i]
                        elif demand_labels and i < len(demand_labels):
                            current_label = demand_labels[i]
                        else:
                            current_label = f"Demand Period {i}"
                        
                        if i < len(st.session_state.demand_form_rates):
                            base_rate = st.session_state.demand_form_rates[i]
                        else:
                            base_rate = float(rate_info.get('rate', 0))
                        
                        if i < len(st.session_state.demand_form_adjustments):
                            adjustment = st.session_state.demand_form_adjustments[i]
                        else:
                            adjustment = float(rate_info.get('adj', 0))
                        
                        # Create input fields
                        cols = st.columns([3, 2, 2, 1])
                        
                        with cols[0]:
                            new_label = st.text_input(
                                f"Demand Label {i}",
                                value=current_label,
                                key=f"demand_label_{i}",
                                label_visibility="collapsed"
                            )
                            edited_demand_labels.append(new_label)
                        
                        with cols[1]:
                            new_base_rate = st.number_input(
                                f"Demand Base Rate {i}",
                                value=base_rate,
                                step=0.0001,
                                format="%.4f",
                                key=f"demand_base_rate_{i}",
                                label_visibility="collapsed"
                            )
                        
                        with cols[2]:
                            new_adjustment = st.number_input(
                                f"Demand Adjustment {i}",
                                value=adjustment,
                                step=0.0001,
                                format="%.4f",
                                key=f"demand_adjustment_{i}",
                                label_visibility="collapsed"
                            )
                        
                        with cols[3]:
                            total_rate = new_base_rate + new_adjustment
                            st.write(f"${total_rate:.4f}")
                        
                        # Store the edited rate structure
                        edited_rate_info = rate_info.copy()
                        edited_rate_info['rate'] = new_base_rate
                        edited_rate_info['adj'] = new_adjustment
                        edited_demand_rates.append([edited_rate_info])
                    else:
                        edited_demand_rates.append([])
                        edited_demand_labels.append(f"Demand Period {i}")
                
                # Apply changes button for demand rates
                if st.form_submit_button("✅ Apply Changes", type="primary"):
                    # Update session state with new values
                    st.session_state.demand_form_labels = edited_demand_labels.copy()
                    st.session_state.demand_form_rates = [edited_demand_rates[i][0]['rate'] if edited_demand_rates[i] else 0.0 for i in range(len(edited_demand_rates))]
                    st.session_state.demand_form_adjustments = [edited_demand_rates[i][0]['adj'] if edited_demand_rates[i] else 0.0 for i in range(len(edited_demand_rates))]
                    
                    # Create modified tariff - use deep copy to avoid reference issues
                    import copy
                    if not st.session_state.modified_tariff:
                        st.session_state.modified_tariff = copy.deepcopy(viewer.data)
                    
                    # Update the tariff data
                    if 'items' in st.session_state.modified_tariff:
                        tariff_data = st.session_state.modified_tariff['items'][0]
                    else:
                        tariff_data = st.session_state.modified_tariff
                    
                    # Update demand rate structure
                    tariff_data['demandratestructure'] = edited_demand_rates
                    
                    # Update demand labels
                    tariff_data['demandlabels'] = edited_demand_labels
                    
                    st.session_state.has_modifications = True
                    st.success("✅ Demand rate changes applied! The visualizations will update to reflect your changes.")
                    st.rerun()
            
        else:
            st.info("📝 **Note:** No demand rate structure found in this tariff JSON.")
        
        st.markdown("---")
        
        # Weekday Demand Rates - Full Width
        st.markdown("#### 📈 Weekday Demand Rates")
        
        # Create a temporary viewer with modified tariff if needed
        if st.session_state.has_modifications and st.session_state.modified_tariff:
            temp_viewer = create_temp_viewer_with_modified_tariff(st.session_state.modified_tariff)
            st.plotly_chart(temp_viewer.plot_heatmap(is_weekday=True, dark_mode=dark_mode, rate_type="demand", chart_height=chart_height, text_size=text_size), use_container_width=True)
        else:
            st.plotly_chart(viewer.plot_heatmap(is_weekday=True, dark_mode=dark_mode, rate_type="demand", chart_height=chart_height, text_size=text_size), use_container_width=True)
        
        st.markdown("---")
        
        # Weekend Demand Rates - Full Width
        st.markdown("#### 📉 Weekend Demand Rates")
        
        if st.session_state.has_modifications and st.session_state.modified_tariff:
            temp_viewer = create_temp_viewer_with_modified_tariff(st.session_state.modified_tariff)
            st.plotly_chart(temp_viewer.plot_heatmap(is_weekday=False, dark_mode=dark_mode, rate_type="demand", chart_height=chart_height, text_size=text_size), use_container_width=True)
        else:
            st.plotly_chart(viewer.plot_heatmap(is_weekday=False, dark_mode=dark_mode, rate_type="demand", chart_height=chart_height, text_size=text_size), use_container_width=True)
    
    with tab3:
        st.markdown("### 📊 Seasonal/Monthly Flat Demand Rates")
        
        # Use the same modified tariff logic as other rate types
        if st.session_state.modified_tariff:
            # Extract tariff data from modified structure
            if 'items' in st.session_state.modified_tariff:
                current_flat_demand_tariff = st.session_state.modified_tariff['items'][0]
            else:
                current_flat_demand_tariff = st.session_state.modified_tariff
        else:
            current_flat_demand_tariff = viewer.tariff

        # Show current flat demand table first
        st.markdown("#### 📊 Current Monthly Flat Demand Rates")
        
        flat_demand_rates = current_flat_demand_tariff.get('flatdemandstructure', [])
        flat_demand_months = current_flat_demand_tariff.get('flatdemandmonths', [])
        
        # Create table data for display
        flat_demand_table_data = []
        month_names_short = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        current_flat_demand_rates = current_flat_demand_tariff.get('flatdemandstructure', [])
        current_flat_demand_months = current_flat_demand_tariff.get('flatdemandmonths', [])
        
        for month_idx in range(12):
            period_idx = current_flat_demand_months[month_idx] if month_idx < len(current_flat_demand_months) else 0
            if period_idx < len(current_flat_demand_rates) and current_flat_demand_rates[period_idx]:
                rate = current_flat_demand_rates[period_idx][0].get('rate', 0)
                adj = current_flat_demand_rates[period_idx][0].get('adj', 0)
            else:
                rate = 0
                adj = 0
            
            total_rate = rate + adj
            
            flat_demand_table_data.append({
                'Month': month_names_short[month_idx],
                'Base Rate ($/kW)': f"${rate:.4f}",
                'Adjustment ($/kW)': f"${adj:.4f}",
                'Total Rate ($/kW)': f"${total_rate:.4f}"
            })
        
        if flat_demand_table_data:
            display_flat_demand_df = pd.DataFrame(flat_demand_table_data)
            st.dataframe(
                display_flat_demand_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Month": st.column_config.TextColumn(
                        "Month",
                        width="small",
                    ),
                    "Base Rate ($/kW)": st.column_config.TextColumn(
                        "Base Rate ($/kW)",
                        width="medium",
                    ),
                    "Adjustment ($/kW)": st.column_config.TextColumn(
                        "Adjustment ($/kW)", 
                        width="medium",
                    ),
                    "Total Rate ($/kW)": st.column_config.TextColumn(
                        "Total Rate ($/kW)",
                        width="medium",
                    )
                }
            )
        else:
            st.info("📝 **Note:** No flat demand rate structure found in this tariff JSON.")
        
        st.markdown("---")
        
        # Flat Demand Rates - Editable
        st.markdown("#### 🏷️ Monthly Flat Demand Rates (Editable)")
        
        if flat_demand_rates and flat_demand_months:
            # Initialize flat demand form values in session state
            flat_demand_form_needs_init = (
                'flat_demand_form_rates' not in st.session_state or 
                len(st.session_state.get('flat_demand_form_rates', [])) != 12
            )
            
            if flat_demand_form_needs_init:
                st.session_state.flat_demand_form_rates = []
                st.session_state.flat_demand_form_adjustments = []
                
                # Initialize rates for all 12 months
                for month_idx in range(12):
                    period_idx = flat_demand_months[month_idx] if month_idx < len(flat_demand_months) else 0
                    if period_idx < len(flat_demand_rates) and flat_demand_rates[period_idx]:
                        rate = flat_demand_rates[period_idx][0].get('rate', 0)
                        adj = flat_demand_rates[period_idx][0].get('adj', 0)
                        st.session_state.flat_demand_form_rates.append(float(rate))
                        st.session_state.flat_demand_form_adjustments.append(float(adj))
                    else:
                        st.session_state.flat_demand_form_rates.append(0.0)
                        st.session_state.flat_demand_form_adjustments.append(0.0)
            
            # Create editable form for flat demand rates
            with st.form("flat_demand_rates_form"):
                st.markdown("**Edit the monthly flat demand rates below and click 'Apply Changes' to update:**")
                
                edited_flat_demand_rates = []
                edited_flat_demand_adjustments = []
                
                # Create columns for the form
                col_headers = st.columns([2, 2, 2, 1])
                col_headers[0].write("**Month**")
                col_headers[1].write("**Base Rate ($/kW)**")
                col_headers[2].write("**Adjustment ($/kW)**")
                col_headers[3].write("**Total**")
                
                month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                             'July', 'August', 'September', 'October', 'November', 'December']
                
                for month_idx in range(12):
                    # Use session state values if available
                    if month_idx < len(st.session_state.flat_demand_form_rates):
                        base_rate = st.session_state.flat_demand_form_rates[month_idx]
                    else:
                        base_rate = 0.0
                    
                    if month_idx < len(st.session_state.flat_demand_form_adjustments):
                        adjustment = st.session_state.flat_demand_form_adjustments[month_idx]
                    else:
                        adjustment = 0.0
                    
                    # Create input fields
                    cols = st.columns([2, 2, 2, 1])
                    
                    with cols[0]:
                        st.write(f"**{month_names[month_idx]}**")
                    
                    with cols[1]:
                        new_base_rate = st.number_input(
                            f"Base Rate {month_idx}",
                            value=base_rate,
                            step=0.0001,
                            format="%.4f",
                            key=f"flat_demand_base_rate_{month_idx}",
                            label_visibility="collapsed"
                        )
                        edited_flat_demand_rates.append(new_base_rate)
                    
                    with cols[2]:
                        new_adjustment = st.number_input(
                            f"Adjustment {month_idx}",
                            value=adjustment,
                            step=0.0001,
                            format="%.4f",
                            key=f"flat_demand_adjustment_{month_idx}",
                            label_visibility="collapsed"
                        )
                        edited_flat_demand_adjustments.append(new_adjustment)
                    
                    with cols[3]:
                        total_rate = new_base_rate + new_adjustment
                        st.write(f"${total_rate:.4f}")
                
                # Apply changes button for flat demand rates
                if st.form_submit_button("✅ Apply Changes", type="primary"):
                    # Update session state with new values
                    st.session_state.flat_demand_form_rates = edited_flat_demand_rates.copy()
                    st.session_state.flat_demand_form_adjustments = edited_flat_demand_adjustments.copy()
                    
                    # Create modified tariff - use deep copy to avoid reference issues
                    import copy
                    if not st.session_state.modified_tariff:
                        st.session_state.modified_tariff = copy.deepcopy(viewer.data)
                    
                    # Update the tariff data
                    if 'items' in st.session_state.modified_tariff:
                        tariff_data = st.session_state.modified_tariff['items'][0]
                    else:
                        tariff_data = st.session_state.modified_tariff
                    
                    # Rebuild flat demand structure
                    # For simplicity, create one rate structure per month
                    new_flat_demand_structure = []
                    new_flat_demand_months = []
                    
                    for month_idx in range(12):
                        rate_structure = [{
                            'rate': edited_flat_demand_rates[month_idx],
                            'adj': edited_flat_demand_adjustments[month_idx],
                            'unit': 'kW'
                        }]
                        new_flat_demand_structure.append(rate_structure)
                        new_flat_demand_months.append(month_idx)
                    
                    # Update flat demand structure
                    tariff_data['flatdemandstructure'] = new_flat_demand_structure
                    tariff_data['flatdemandmonths'] = new_flat_demand_months
                    
                    st.session_state.has_modifications = True
                    st.success("✅ Flat demand rate changes applied! The visualizations will update to reflect your changes.")
                    st.rerun()
            
        
        st.markdown("---")
        
        # Flat Demand Rates Chart
        st.markdown("#### 📈 Monthly Flat Demand Rates Visualization")
        
        # Use modified tariff for chart if available
        if st.session_state.has_modifications and st.session_state.modified_tariff:
            temp_viewer = create_temp_viewer_with_modified_tariff(st.session_state.modified_tariff)
            st.plotly_chart(temp_viewer.plot_flat_demand_rates(dark_mode=dark_mode), use_container_width=True)
        else:
            st.plotly_chart(viewer.plot_flat_demand_rates(dark_mode=dark_mode), use_container_width=True)
        
    with tab4:
        st.markdown("### 💰 Utility Cost Calculator")
        st.markdown("Calculate monthly utility bills by applying the selected tariff to a load profile.")
        
        # Check if load profile is selected in sidebar
        if 'current_load_profile' not in st.session_state or st.session_state.current_load_profile is None:
            st.warning("⚠️ Please select a load profile from the sidebar to calculate utility costs.")
            st.stop()
        
        selected_load_profile = st.session_state.current_load_profile
        
        # Show current load profile info
        load_profile_name = selected_load_profile.stem.replace('_', ' ').title()
        st.info(f"📊 **Using load profile**: {load_profile_name}")
        st.markdown("*To change the load profile, use the selector in the sidebar.*")
        
        if st.button("🧮 Calculate Utility Costs", type="primary"):
            try:
                with st.spinner("Calculating utility costs..."):
                    # Use modified tariff if available
                    if st.session_state.has_modifications and st.session_state.modified_tariff:
                        if 'items' in st.session_state.modified_tariff:
                            tariff_for_calc = st.session_state.modified_tariff['items'][0]
                        else:
                            tariff_for_calc = st.session_state.modified_tariff
                    else:
                        tariff_for_calc = viewer.tariff
                    
                    # Calculate costs using the current tariff and selected load profile
                    results = calculate_utility_costs_for_app(tariff_for_calc, str(selected_load_profile))
                    
                    st.success("✅ Calculation completed successfully!")
                    
                    # Display results summary
                    st.markdown("#### 📊 Monthly Utility Cost Summary")

                    # Create summary metrics for monthly focus
                    total_annual_cost = results['total_charge'].sum()
                    total_annual_kwh = results['total_kwh'].sum()
                    avg_monthly_cost = results['total_charge'].mean()
                    max_monthly_cost = results['total_charge'].max()
                    min_monthly_cost = results['total_charge'].min()
                    effective_rate_per_kwh = total_annual_cost / total_annual_kwh if total_annual_kwh > 0 else 0

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Average Monthly Cost", f"${avg_monthly_cost:,.0f}")
                    with col2:
                        st.metric("Highest Monthly Cost", f"${max_monthly_cost:,.0f}")
                    with col3:
                        st.metric("Lowest Monthly Cost", f"${min_monthly_cost:,.0f}")
                    with col4:
                        st.metric("Effective Rate $/kWh", f"${effective_rate_per_kwh:.4f}")
                    
                    st.markdown("---")
                    
                    # Display detailed monthly breakdown
                    st.markdown("#### 📅 Detailed Monthly Breakdown")
                    
                    # Prepare display dataframe
                    display_df = results[[
                        'month_name', 'total_kwh', 'peak_kw', 'avg_load', 'load_factor',
                        'total_energy_cost', 'total_demand_cost', 'fixed_charge', 'total_charge'
                    ]].copy()
                    
                    # Format the dataframe for better display
                    st.dataframe(
                            display_df,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "month_name": st.column_config.TextColumn(
                                    "Month",
                                    help="Month of the year",
                                    width="small"
                                ),
                                "total_kwh": st.column_config.NumberColumn(
                                    "Total kWh",
                                    help="Total energy consumption for the month",
                                    format="%.0f"
                                ),
                                "peak_kw": st.column_config.NumberColumn(
                                    "Peak Load (kW)",
                                    help="Maximum demand during the month",
                                    format="%.2f"
                                ),
                                "avg_load": st.column_config.NumberColumn(
                                    "Avg Load (kW)",
                                    help="Average load during the month",
                                    format="%.2f"
                                ),
                                "load_factor": st.column_config.NumberColumn(
                                    "Load Factor",
                                    help="Load factor (average/peak)",
                                    format="%.3f"
                                ),
                                "total_energy_cost": st.column_config.NumberColumn(
                                    "Energy Cost ($)",
                                    help="Total energy charges including adjustments",
                                    format="$%.2f"
                                ),
                                "total_demand_cost": st.column_config.NumberColumn(
                                    "Demand Cost ($)",
                                    help="Total demand charges including adjustments",
                                    format="$%.2f"
                                ),
                                "fixed_charge": st.column_config.NumberColumn(
                                    "Fixed Charge ($)",
                                    help="Monthly fixed charges",
                                    format="$%.2f"
                                ),
                                "total_charge": st.column_config.NumberColumn(
                                    "Total Cost ($)",
                                    help="Total monthly utility bill",
                                    format="$%.2f"
                                )
                            }
                        )
                    
                    # Cost breakdown chart
                    st.markdown("#### 📈 Monthly Cost Visualization")
                    
                    fig_costs = go.Figure()
                    
                    # Add grouped bar chart for cost breakdown
                    fig_costs.add_trace(go.Bar(
                        x=results['month_name'],
                        y=results['total_energy_cost'],
                        name='Energy Costs',
                        marker_color='rgba(59, 130, 246, 0.8)',
                        hovertemplate="<b>%{x}</b><br>Energy Cost: $%{y:.2f}<extra></extra>"
                    ))
                    
                    fig_costs.add_trace(go.Bar(
                        x=results['month_name'],
                        y=results['total_demand_cost'],
                        name='Demand Costs',
                        marker_color='rgba(249, 115, 22, 0.8)',
                        hovertemplate="<b>%{x}</b><br>Demand Cost: $%{y:.2f}<extra></extra>"
                    ))
                    
                    fig_costs.add_trace(go.Bar(
                        x=results['month_name'],
                        y=results['fixed_charge'],
                        name='Fixed Charges',
                        marker_color='rgba(34, 197, 94, 0.8)',
                        hovertemplate="<b>%{x}</b><br>Fixed Charge: $%{y:.2f}<extra></extra>"
                    ))
                    
                    fig_costs.update_layout(
                        title=dict(
                            text=f'<b>Monthly Cost Breakdown by Month</b><br><span style="font-size: 0.75em; color: #6b7280;">{viewer.utility_name} - {viewer.rate_name}</span>',
                            font=dict(size=20, color='#0f172a' if not dark_mode else '#f1f5f9'),
                            x=0.5,
                            xanchor='center'
                        ),
                        barmode='stack',
                        xaxis_title="Month",
                        yaxis_title="Cost ($)",
                        height=500,
                        showlegend=True,
                        plot_bgcolor='rgba(248, 250, 252, 0.8)' if not dark_mode else 'rgba(15, 23, 42, 0.5)',
                        paper_bgcolor='#ffffff' if not dark_mode else '#0f172a',
                        font=dict(color='#0f172a' if not dark_mode else '#f1f5f9')
                    )
                    
                    st.plotly_chart(fig_costs, use_container_width=True)
                    
                    # Load profile chart
                    st.markdown("#### ⚡ Load Profile Overview")
                    
                    # Show monthly peak and average loads
                    fig_load = go.Figure()
                    
                    fig_load.add_trace(go.Scatter(
                        x=results['month_name'],
                        y=results['peak_kw'],
                        mode='lines+markers',
                        name='Peak Load (kW)',
                        line=dict(color='rgba(239, 68, 68, 0.8)', width=3),
                        marker=dict(size=8),
                        hovertemplate="<b>%{x}</b><br>Peak Load: %{y:.2f} kW<extra></extra>"
                    ))
                    
                    fig_load.add_trace(go.Scatter(
                        x=results['month_name'],
                        y=results['avg_load'],
                        mode='lines+markers',
                        name='Average Load (kW)',
                        line=dict(color='rgba(59, 130, 246, 0.8)', width=3),
                        marker=dict(size=8),
                        hovertemplate="<b>%{x}</b><br>Average Load: %{y:.2f} kW<extra></extra>"
                    ))
                    
                    fig_load.update_layout(
                        title=dict(
                            text='<b>Monthly Load Profile Summary</b>',
                            font=dict(size=20, color='#0f172a' if not dark_mode else '#f1f5f9'),
                            x=0.5,
                            xanchor='center'
                        ),
                        xaxis_title="Month",
                        yaxis_title="Load (kW)",
                        height=400,
                        showlegend=True,
                        plot_bgcolor='rgba(248, 250, 252, 0.8)' if not dark_mode else 'rgba(15, 23, 42, 0.5)',
                        paper_bgcolor='#ffffff' if not dark_mode else '#0f172a',
                        font=dict(color='#0f172a' if not dark_mode else '#f1f5f9')
                    )
                    
                    st.plotly_chart(fig_load, use_container_width=True)
                    
            except InvalidTariffError as e:
                st.error(f"❌ Tariff validation error: {str(e)}")
            except InvalidLoadProfileError as e:
                st.error(f"❌ Load profile error: {str(e)}")
            except Exception as e:
                st.error(f"❌ Calculation error: {str(e)}")
                st.exception(e)
                    
    with tab5:
        st.markdown("### 🔧 Load Profile Generator")
        st.markdown("Create custom load profiles with specified characteristics and TOU energy distribution.")
        
        # Load profile parameters
        st.markdown("#### ⚙️ Load Profile Parameters")
        
        col1, col2 = st.columns(2)
        with col1:
            avg_load = st.number_input(
                "Average Load (kW)", 
                min_value=0.1, 
                max_value=10000.0, 
                value=100.0, 
                step=1.0,
                help="The average load across the entire year"
            )
            
            load_factor = st.slider(
                "Load Factor", 
                min_value=0.1, 
                max_value=1.0, 
                value=0.6, 
                step=0.01,
                help="Ratio of average load to peak load (0.1 = highly variable, 1.0 = constant load)"
            )
        
        with col2:
            profile_name = st.text_input(
                "Load Profile Name",
                value="Custom_Load_Profile",
                help="Name for the load profile file (will be saved as CSV)"
            )
            
            year = st.selectbox(
                "Year",
                options=list(range(2024, 2031)),
                index=1,  # Default to 2025
                help="Year for the load profile timestamps"
            )
        
        # TOU Energy Distribution
        st.markdown("#### 📊 Energy Distribution by TOU Period")
        st.markdown("Specify what percentage of total annual energy falls into each TOU period for the selected tariff.")
        
        # Get TOU periods from current tariff (use modified if available)
        if st.session_state.has_modifications and st.session_state.modified_tariff:
            if 'items' in st.session_state.modified_tariff:
                current_tariff_for_gen = st.session_state.modified_tariff['items'][0]
            else:
                current_tariff_for_gen = st.session_state.modified_tariff
        else:
            current_tariff_for_gen = viewer.tariff
            
        energy_labels = current_tariff_for_gen.get('energytoulabels', [])
        energy_rates = current_tariff_for_gen.get('energyratestructure', [])
        
        if not energy_rates:
            st.error("❌ The selected tariff does not have energy rate structure. Please select a different tariff.")
        else:
            # Create TOU period inputs
            tou_percentages = {}
            total_percentage = 0
            
            st.markdown("##### Weekday Energy Distribution")
            weekday_cols = st.columns(min(len(energy_rates), 4))
            
            for i, rate_structure in enumerate(energy_rates):
                col_idx = i % len(weekday_cols)
                with weekday_cols[col_idx]:
                    if energy_labels and i < len(energy_labels):
                        period_name = energy_labels[i]
                    else:
                        period_name = f"Period {i}"
                    
                    # Get the rate for display
                    rate = rate_structure[0].get('rate', 0) if rate_structure else 0
                    adj = rate_structure[0].get('adj', 0) if rate_structure else 0
                    total_rate = rate + adj
                    
                    percentage = st.number_input(
                        f"{period_name}\n(${total_rate:.4f}/kWh)",
                        min_value=0.0,
                        max_value=100.0,
                        value=100.0 / len(energy_rates),  # Equal distribution by default
                        step=0.1,
                        key=f"tou_pct_{i}",
                        help=f"Percentage of annual energy in {period_name}"
                    )
                    tou_percentages[i] = percentage
                    total_percentage += percentage
            
            # Show total percentage
            if abs(total_percentage - 100.0) > 0.1:
                st.warning(f"⚠️ Total percentage is {total_percentage:.1f}%. It should equal 100%.")
            else:
                st.success(f"✅ Total percentage: {total_percentage:.1f}%")
            
            # Advanced options
            with st.expander("🔧 Advanced Options"):
                col1, col2 = st.columns(2)
                with col1:
                    seasonal_variation = st.slider(
                        "Seasonal Variation",
                        min_value=0.0,
                        max_value=0.5,
                        value=0.1,
                        step=0.01,
                        help="How much the load varies seasonally (0 = no variation, 0.5 = ±50% variation)"
                    )
                    
                    weekend_factor = st.slider(
                        "Weekend Load Factor",
                        min_value=0.1,
                        max_value=1.5,
                        value=0.8,
                        step=0.01,
                        help="Weekend load as a fraction of weekday load"
                    )
                
                with col2:
                    daily_variation = st.slider(
                        "Daily Variation",
                        min_value=0.0,
                        max_value=0.3,
                        value=0.15,
                        step=0.01,
                        help="How much the load varies within each day"
                    )
                    
                    noise_level = st.slider(
                        "Random Noise Level",
                        min_value=0.0,
                        max_value=0.2,
                        value=0.05,
                        step=0.01,
                        help="Amount of random variation in the load profile"
                    )
            
            # Generate button
            if st.button("🚀 Generate Load Profile", type="primary"):
                if abs(total_percentage - 100.0) > 0.1:
                    st.error("❌ Please ensure TOU percentages sum to 100% before generating.")
                elif not profile_name.strip():
                    st.error("❌ Please provide a name for the load profile.")
                else:
                    try:
                        with st.spinner("Generating load profile..."):
                            # Generate the load profile
                            load_profile_df = generate_load_profile(
                                tariff=current_tariff_for_gen,
                                avg_load=avg_load,
                                load_factor=load_factor,
                                tou_percentages=tou_percentages,
                                year=year,
                                seasonal_variation=seasonal_variation,
                                weekend_factor=weekend_factor,
                                daily_variation=daily_variation,
                                noise_level=noise_level
                            )
                            
                            # Save to load_profiles directory
                            load_profiles_dir = script_dir / "load_profiles"
                            load_profiles_dir.mkdir(exist_ok=True)
                            
                            # Clean filename
                            clean_name = re.sub(r'[^\w\-_]', '_', profile_name.strip())
                            filename = f"{clean_name}_{year}.csv"
                            filepath = load_profiles_dir / filename
                            
                            # Save the file
                            load_profile_df.to_csv(filepath, index=False)
                            
                            st.success(f"✅ Load profile generated successfully!")
                            st.success(f"📁 Saved as: `{filename}` in the load_profiles directory")
                            
                            # Display summary statistics
                            st.markdown("#### 📊 Generated Load Profile Summary")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Total Annual kWh", f"{load_profile_df['kWh'].sum():,.0f}")
                            with col2:
                                st.metric("Peak Load (kW)", f"{load_profile_df['load_kW'].max():.2f}")
                            with col3:
                                st.metric("Average Load (kW)", f"{load_profile_df['load_kW'].mean():.2f}")
                            with col4:
                                actual_load_factor = load_profile_df['load_kW'].mean() / load_profile_df['load_kW'].max()
                                st.metric("Actual Load Factor", f"{actual_load_factor:.3f}")
                            
                            # Show monthly summary
                            monthly_summary = load_profile_df.groupby('month').agg({
                                'load_kW': ['mean', 'max'],
                                'kWh': 'sum'
                            }).round(2)
                            monthly_summary.columns = ['Avg Load (kW)', 'Peak Load (kW)', 'Total kWh']
                            monthly_summary.index = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                            
                            st.markdown("#### 📅 Monthly Summary")
                            st.dataframe(monthly_summary, use_container_width=True)
                            
                            # Plot the load profile
                            st.markdown("#### 📈 Load Profile Visualization")
                            
                            # Sample data for plotting (show first week)
                            sample_data = load_profile_df.head(672)  # First week (7 days * 96 intervals)
                            
                            fig_profile = go.Figure()
                            fig_profile.add_trace(go.Scatter(
                                x=sample_data['timestamp'],
                                y=sample_data['load_kW'],
                                mode='lines',
                                name='Load (kW)',
                                line=dict(color='rgba(59, 130, 246, 0.8)', width=2),
                                hovertemplate="<b>%{x}</b><br>Load: %{y:.2f} kW<extra></extra>"
                            ))
                            
                            fig_profile.update_layout(
                                title=dict(
                                    text=f'<b>Generated Load Profile - First Week Sample</b><br><span style="font-size: 0.75em; color: #6b7280;">{profile_name} - {year}</span>',
                                    font=dict(size=20, color='#0f172a' if not dark_mode else '#f1f5f9'),
                                    x=0.5,
                                    xanchor='center'
                                ),
                                xaxis_title="Date/Time",
                                yaxis_title="Load (kW)",
                                height=400,
                                showlegend=False,
                                plot_bgcolor='rgba(248, 250, 252, 0.8)' if not dark_mode else 'rgba(15, 23, 42, 0.5)',
                                paper_bgcolor='#ffffff' if not dark_mode else '#0f172a',
                                font=dict(color='#0f172a' if not dark_mode else '#f1f5f9')
                            )
                            
                            st.plotly_chart(fig_profile, use_container_width=True)
                            
                            # TOU distribution verification
                            st.markdown("#### 🔍 TOU Distribution Verification")
                            
                            # Calculate actual TOU distribution
                            actual_distribution = {}
                            total_kwh = load_profile_df['kWh'].sum()
                            
                            for period in range(len(energy_rates)):
                                period_mask = load_profile_df['energy_period'] == period
                                period_kwh = load_profile_df[period_mask]['kWh'].sum()
                                actual_percentage = (period_kwh / total_kwh * 100) if total_kwh > 0 else 0
                                
                                period_name = energy_labels[period] if energy_labels and period < len(energy_labels) else f"Period {period}"
                                actual_distribution[period_name] = {
                                    'target': tou_percentages.get(period, 0),
                                    'actual': actual_percentage,
                                    'kwh': period_kwh
                                }
                            
                            # Display comparison
                            comparison_data = []
                            for period_name, data in actual_distribution.items():
                                comparison_data.append({
                                    'TOU Period': period_name,
                                    'Target %': f"{data['target']:.1f}%",
                                    'Actual %': f"{data['actual']:.1f}%",
                                    'Difference': f"{data['actual'] - data['target']:+.1f}%",
                                    'Energy (kWh)': f"{data['kwh']:,.0f}"
                                })
                            
                            comparison_df = pd.DataFrame(comparison_data)
                            st.dataframe(comparison_df, use_container_width=True, hide_index=True)
                            
                    except Exception as e:
                        st.error(f"❌ Error generating load profile: {str(e)}")
                        st.exception(e)
                        
    with tab6:
        st.markdown("### 📊 Load Profile Analysis")
        st.markdown("Analyze existing load profiles to understand consumption patterns and characteristics.")
        
        # Check if load profile is selected in sidebar
        if 'current_load_profile' not in st.session_state or st.session_state.current_load_profile is None:
            st.warning("⚠️ Please select a load profile from the sidebar to analyze.")
            st.stop()
        
        selected_analysis_profile = st.session_state.current_load_profile
        
        # Show current load profile info
        analysis_load_profile_name = selected_analysis_profile.stem.replace('_', ' ').title()
        st.info(f"📊 **Analyzing load profile**: {analysis_load_profile_name}")
        st.markdown("*To change the load profile, use the selector in the sidebar.*")
        
        if st.button("🔍 Analyze Load Profile", type="primary"):
            try:
                with st.spinner("Analyzing load profile..."):
                    # Load the CSV file
                    df = pd.read_csv(selected_analysis_profile)
                    
                    # Validate required columns
                    required_columns = ['timestamp', 'load_kW']
                    missing_columns = [col for col in required_columns if col not in df.columns]
                    
                    if missing_columns:
                        st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
                        st.info("Required columns: timestamp, load_kW")
                    else:
                        # Parse timestamp and add derived columns
                        df['timestamp'] = pd.to_datetime(df['timestamp'])
                        df['month'] = df['timestamp'].dt.month
                        df['hour'] = df['timestamp'].dt.hour
                        df['weekday'] = df['timestamp'].dt.weekday  # 0=Monday, 6=Sunday
                        df['day_name'] = df['timestamp'].dt.day_name()
                        
                        # Calculate kWh if not present (assuming 15-minute intervals)
                        if 'kWh' not in df.columns:
                            df['kWh'] = df['load_kW'] * 0.25  # 15 minutes = 0.25 hours
                        
                        st.success("✅ Load profile analyzed successfully!")
                        
                        # Display basic statistics
                        st.markdown("#### 📊 Load Profile Overview")
                        
                        total_kwh = df['kWh'].sum()
                        peak_kw = df['load_kW'].max()
                        avg_kw = df['load_kW'].mean()
                        load_factor = avg_kw / peak_kw if peak_kw > 0 else 0
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Energy", f"{total_kwh:,.0f} kWh")
                        with col2:
                            st.metric("Peak Demand", f"{peak_kw:.2f} kW")
                        with col3:
                            st.metric("Average Load", f"{avg_kw:.2f} kW")
                        with col4:
                            st.metric("Load Factor", f"{load_factor:.3f}")
                        
                        st.markdown("---")
                        
                        # Monthly Analysis Table
                        st.markdown("#### 📅 Monthly Peak Demand and Energy Analysis")
                        
                        monthly_stats = df.groupby('month').agg({
                            'load_kW': ['max', 'mean'],
                            'kWh': 'sum'
                        }).round(2)
                        
                        # Flatten column names
                        monthly_stats.columns = ['Peak Demand (kW)', 'Avg Load (kW)', 'Total Energy (kWh)']
                        
                        # Add month names
                        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                        monthly_stats.index = [month_names[i-1] for i in monthly_stats.index]
                        
                        # Add totals row
                        totals_row = pd.DataFrame({
                            'Peak Demand (kW)': [peak_kw],
                            'Avg Load (kW)': [avg_kw],
                            'Total Energy (kWh)': [total_kwh]
                        }, index=['TOTAL'])
                        
                        monthly_stats_with_totals = pd.concat([monthly_stats, totals_row])
                        
                        st.dataframe(
                            monthly_stats_with_totals,
                            use_container_width=True,
                            column_config={
                                "Peak Demand (kW)": st.column_config.NumberColumn(
                                    "Peak Demand (kW)",
                                    help="Maximum demand for the month",
                                    format="%.2f"
                                ),
                                "Avg Load (kW)": st.column_config.NumberColumn(
                                    "Avg Load (kW)",
                                    help="Average load for the month",
                                    format="%.2f"
                                ),
                                "Total Energy (kWh)": st.column_config.NumberColumn(
                                    "Total Energy (kWh)",
                                    help="Total energy consumption for the month",
                                    format="%.0f"
                                )
                            }
                        )
                        
                        st.markdown("---")
                        
                        # Demand Level Analysis Table
                        st.markdown("#### ⚡ Energy Above Demand Level Analysis")
                        st.markdown("Shows cumulative energy (kWh) consumed at or above various demand levels.")
                        
                        # Create demand level analysis
                        demand_levels = []
                        kwh_above_levels = []
                        
                        current_level = peak_kw
                        while current_level >= 0:
                            # Count kWh where load is at or above this level
                            kwh_above = df[df['load_kW'] >= current_level]['kWh'].sum()
                            demand_levels.append(current_level)
                            kwh_above_levels.append(kwh_above)
                            current_level -= 50
                            
                            if current_level < 0:
                                break
                        
                        # Create demand analysis DataFrame
                        demand_analysis_df = pd.DataFrame({
                            'Demand Level (kW)': [f"≥ {level:.0f}" for level in demand_levels],
                            'Energy Above Level (kWh)': kwh_above_levels,
                            'Percentage of Total': [(kwh / total_kwh * 100) if total_kwh > 0 else 0 for kwh in kwh_above_levels]
                        })
                        
                        st.dataframe(
                            demand_analysis_df,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Demand Level (kW)": st.column_config.TextColumn(
                                    "Demand Level (kW)",
                                    help="Demand threshold level",
                                    width="small"
                                ),
                                "Energy Above Level (kWh)": st.column_config.NumberColumn(
                                    "Energy Above Level (kWh)",
                                    help="Total energy consumed at or above this demand level",
                                    format="%.0f"
                                ),
                                "Percentage of Total": st.column_config.NumberColumn(
                                    "Percentage of Total",
                                    help="Percentage of total energy above this demand level",
                                    format="%.1f%%"
                                )
                            }
                        )
                        
                        st.markdown("---")
                        
                        # Day of Week Analysis
                        st.markdown("#### 📅 Energy Consumption by Day of Week")
                        
                        # Group by day of week
                        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        daily_kwh = df.groupby('day_name')['kWh'].sum().reindex(day_order)
                        
                        # Create bar chart for day of week
                        fig_daily = go.Figure(data=go.Bar(
                            x=daily_kwh.index,
                            y=daily_kwh.values,
                            text=[f'{val:,.0f}' for val in daily_kwh.values],
                            textposition='outside',
                            textfont=dict(
                                size=12,
                                color='#0f172a' if not dark_mode else '#f1f5f9',
                                family='Inter, sans-serif'
                            ),
                            marker=dict(
                                color=['rgba(59, 130, 246, 0.8)' if day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'] 
                                      else 'rgba(34, 197, 94, 0.8)' for day in daily_kwh.index],
                                line=dict(
                                    color='rgba(255, 255, 255, 0.8)' if not dark_mode else 'rgba(15, 23, 42, 0.8)',
                                    width=2
                                )
                            ),
                            hovertemplate="<b>%{x}</b><br>Total Energy: %{y:,.0f} kWh<extra></extra>"
                        ))
                        
                        fig_daily.update_layout(
                            title=dict(
                                text='<b>Total Energy Consumption by Day of Week</b>',
                                font=dict(size=20, color='#0f172a' if not dark_mode else '#f1f5f9', family="Inter, sans-serif"),
                                x=0.5,
                                xanchor='center'
                            ),
                            xaxis=dict(
                                title="Day of Week",
                                tickfont=dict(size=12, color='#1f2937' if not dark_mode else '#cbd5e1'),
                                showgrid=True,
                                gridcolor='rgba(229, 231, 235, 0.5)' if not dark_mode else 'rgba(75, 85, 99, 0.5)'
                            ),
                            yaxis=dict(
                                title="Energy (kWh)",
                                tickfont=dict(size=12, color='#1f2937' if not dark_mode else '#cbd5e1'),
                                showgrid=True,
                                gridcolor='rgba(229, 231, 235, 0.5)' if not dark_mode else 'rgba(75, 85, 99, 0.5)'
                            ),
                            plot_bgcolor='rgba(248, 250, 252, 0.8)' if not dark_mode else 'rgba(15, 23, 42, 0.5)',
                            paper_bgcolor='#ffffff' if not dark_mode else '#0f172a',
                            height=400,
                            font=dict(color='#0f172a' if not dark_mode else '#f1f5f9')
                        )
                        
                        st.plotly_chart(fig_daily, use_container_width=True)
                        
                        st.markdown("---")
                        
                        # Hour of Day Analysis
                        st.markdown("#### 🕐 Energy Consumption by Hour of Day")
                        
                        # Group by hour of day
                        hourly_kwh = df.groupby('hour')['kWh'].sum()
                        
                        # Create line chart for hour of day
                        fig_hourly = go.Figure(data=go.Scatter(
                            x=hourly_kwh.index,
                            y=hourly_kwh.values,
                            mode='lines+markers',
                            line=dict(color='rgba(59, 130, 246, 0.8)', width=3),
                            marker=dict(size=6, color='rgba(59, 130, 246, 1.0)'),
                            fill='tonexty' if len(hourly_kwh) > 1 else None,
                            fillcolor='rgba(59, 130, 246, 0.1)',
                            hovertemplate="<b>Hour %{x}:00</b><br>Total Energy: %{y:,.0f} kWh<extra></extra>"
                        ))
                        
                        fig_hourly.update_layout(
                            title=dict(
                                text='<b>Total Energy Consumption by Hour of Day</b>',
                                font=dict(size=20, color='#0f172a' if not dark_mode else '#f1f5f9', family="Inter, sans-serif"),
                                x=0.5,
                                xanchor='center'
                            ),
                            xaxis=dict(
                                title="Hour of Day",
                                tickfont=dict(size=12, color='#1f2937' if not dark_mode else '#cbd5e1'),
                                showgrid=True,
                                gridcolor='rgba(229, 231, 235, 0.5)' if not dark_mode else 'rgba(75, 85, 99, 0.5)',
                                tickmode='linear',
                                dtick=2
                            ),
                            yaxis=dict(
                                title="Energy (kWh)",
                                tickfont=dict(size=12, color='#1f2937' if not dark_mode else '#cbd5e1'),
                                showgrid=True,
                                gridcolor='rgba(229, 231, 235, 0.5)' if not dark_mode else 'rgba(75, 85, 99, 0.5)'
                            ),
                            plot_bgcolor='rgba(248, 250, 252, 0.8)' if not dark_mode else 'rgba(15, 23, 42, 0.5)',
                            paper_bgcolor='#ffffff' if not dark_mode else '#0f172a',
                            height=400,
                            showlegend=False,
                            font=dict(color='#0f172a' if not dark_mode else '#f1f5f9')
                        )
                        
                        st.plotly_chart(fig_hourly, use_container_width=True)
                        
            except Exception as e:
                st.error(f"❌ Error analyzing load profile: {str(e)}")
                st.exception(e)

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    # Display tariff details in modern cards
    st.markdown('<h2 class="section-header">📋 Tariff Information</h2>', unsafe_allow_html=True)
    
    # Create metric cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🏢 Utility</h3>
            <p style="font-size: 1.2rem; margin: 0;">{viewer.utility_name}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-card">
            <h3>⚡ Rate Name</h3>
            <p style="font-size: 1.2rem; margin: 0;">{viewer.rate_name}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🏭 Sector</h3>
            <p style="font-size: 1.2rem; margin: 0;">{viewer.sector}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-card">
            <h3>🔌 Min Demand</h3>
            <p style="font-size: 1.2rem; margin: 0;">{viewer.tariff.get('peakkwcapacitymin', 'N/A')} kW</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>💰 Fixed Charge</h3>
            <p style="font-size: 1.2rem; margin: 0;">${viewer.tariff.get('fixedchargefirstmeter', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-card">
            <h3>📅 Rate Type</h3>
            <p style="font-size: 1.2rem; margin: 0;">Time-of-Use</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<h2 class="section-header">📝 Description</h2>', unsafe_allow_html=True)
    st.info(viewer.description)
    
    # Show full JSON data in an expandable section
    with st.expander("🔍 View Raw JSON Data"):
        st.json(viewer.data)

if __name__ == "__main__":
    main()
