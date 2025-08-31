import streamlit as st
import json
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path


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
    
    st.markdown('<h1 class="main-header">URDB Tariff Viewer</h1>', unsafe_allow_html=True)
    # Sub-header tagline for modern look
    st.markdown('<p style="text-align: center; margin: -10px 0 24px 0; color: #64748b; font-size: 1.05rem;">Explore utility tariffs with beautiful, interactive visuals</p>', unsafe_allow_html=True)

    # Find JSON files
    script_dir = Path(__file__).parent
    
    # Look in tariffs subdirectory first
    tariffs_dir = script_dir / "tariffs"
    json_files = list(tariffs_dir.glob("*.json")) if tariffs_dir.exists() else []
    
    # If no files found in tariffs dir, check main directory
    if not json_files:
        json_files = list(script_dir.glob("*.json"))
    
    if not json_files:
        st.error("No JSON files found! Please make sure your JSON files are in the 'tariffs' subdirectory.")
        return

    # Load all tariff info for selection
    tariff_options = []
    for file_path in json_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                tariff = data['items'][0] if 'items' in data else data
                display_name = f"{tariff.get('utility', 'Unknown')} - {tariff.get('name', file_path.name)}"
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

    # Add a compact tariff selector in the main area as backup
    with st.expander("🔄 Quick Tariff Selector (if sidebar is hidden)", expanded=False):
        # Find current selection index
        current_index = 0
        for i, (path, name) in enumerate(tariff_options):
            if path == st.session_state.current_tariff:
                current_index = i
                break
        
        backup_selected = st.selectbox(
            "Select a tariff:",
            options=[option[0] for option in tariff_options],
            format_func=lambda x: next(name for path, name in tariff_options if path == x),
            key="backup_tariff_select",
            index=current_index
        )
        
        # Update session state when backup selector changes
        if backup_selected != st.session_state.current_tariff:
            st.session_state.tariff_viewer = TariffViewer(backup_selected)
            st.session_state.current_tariff = backup_selected
            st.success("✅ Tariff updated!")
            st.rerun()

    # Sidebar for controls
    with st.sidebar:
        st.markdown('<div class="sidebar-header">🎛️ Viewer Controls</div>', unsafe_allow_html=True)
        
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
        
        # Display preferences
        st.markdown("### 🎨 Display Preferences")
        dark_mode = st.checkbox("🌙 Dark Mode", value=True)
        
        # Helpful tip for better viewing
        st.info("💡 **Pro Tip**: Adjust visualization settings below for optimal viewing experience!")

        # Add a note about sidebar visibility
        with st.expander("📱 Having trouble seeing the sidebar?", expanded=False):
            st.write("If the sidebar is not visible:")
            st.write("1. Look for a **>** arrow on the top-left of the page")
            st.write("2. Click it to expand the sidebar")
            st.write("3. Or use the tariff selector in the main area below")

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

    # Main content area - Heatmaps
    st.markdown('<h2 class="section-header">📊 Rate Visualizations</h2>', unsafe_allow_html=True)
    
    # Add visualization configuration
    with st.expander("⚙️ Visualization Settings"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            show_text = st.checkbox("Show Rate Values", value=True, help="Display the actual rate values on the heatmap")
        
        with col2:
            chart_height_option = st.selectbox(
                "Chart Height",
                options=["Large (700px)", "Medium (600px)", "Small (500px)"],
                index=0,
                help="Choose the height of the heatmap charts for better readability"
            )
            
            # Extract the height value from the selected option
            if "700px" in chart_height_option:
                chart_height = 700
            elif "600px" in chart_height_option:
                chart_height = 600
            else:
                chart_height = 500
        
        with col3:
            text_size = st.slider("Text Size", min_value=10, max_value=16, value=12, help="Adjust the size of rate values on the heatmap")
    
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    
    # Create tabs for energy and demand rates with modern styling
    tab1, tab2, tab3, tab4 = st.tabs(["⚡ Energy Rates", "🔌 Demand Rates", "📊 Flat Demand", "📈 Combined View"])
    
    with tab1:
        st.markdown("### ⚡ Energy Rate Structure")
        
        # TOU Labels Table
        st.markdown("#### 🏷️ Time-of-Use Period Labels & Rates")
        tou_table = viewer.create_tou_labels_table()
        if not tou_table.empty:
            st.dataframe(
                tou_table,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "TOU Period": st.column_config.TextColumn(
                        "TOU Period",
                        help="Time-of-Use period name",
                        width="medium"
                    ),
                    "Base Rate ($/kWh)": st.column_config.TextColumn(
                        "Base Rate ($/kWh)",
                        help="Base energy rate before adjustments",
                        width="small"
                    ),
                    "Adjustment ($/kWh)": st.column_config.TextColumn(
                        "Adjustment ($/kWh)",
                        help="Rate adjustments (surcharges, credits, etc.)",
                        width="small"
                    ),
                    "Total Rate ($/kWh)": st.column_config.TextColumn(
                        "Total Rate ($/kWh)",
                        help="Final rate including all adjustments",
                        width="small"
                    ),
                    "Months Present": st.column_config.TextColumn(
                        "Months Present",
                        help="Which months this TOU period is active in weekday/weekend schedules",
                        width=300,  # Fixed pixel width to allow text wrapping
                        max_chars=None  # Allow unlimited characters for wrapping
                    )
                }
            )
        else:
            st.info("📝 **Note:** No energy rate structure found in this tariff JSON.")
        
        st.markdown("---")
        
        # Weekday Energy Rates - Full Width
        st.markdown("#### 📈 Weekday Energy Rates")
        st.plotly_chart(viewer.plot_heatmap(is_weekday=True, dark_mode=dark_mode, rate_type="energy", chart_height=chart_height, text_size=text_size), use_container_width=True)
        
        st.markdown("---")
        
        # Weekend Energy Rates - Full Width
        st.markdown("#### 📉 Weekend Energy Rates")
        st.plotly_chart(viewer.plot_heatmap(is_weekday=False, dark_mode=dark_mode, rate_type="energy", chart_height=chart_height, text_size=text_size), use_container_width=True)
        
    with tab2:
        st.markdown("### 🔌 Demand Charge Rate Structure")

        # Demand Labels Table
        st.markdown("#### 🏷️ Demand Period Labels & Rates")
        demand_table = viewer.create_demand_labels_table()
        if not demand_table.empty:
            st.dataframe(
                demand_table,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Demand Period": st.column_config.TextColumn(
                        "Demand Period",
                        help="Demand charge period name",
                        width="medium"
                    ),
                    "Base Rate ($/kW)": st.column_config.TextColumn(
                        "Base Rate ($/kW)",
                        help="Base demand rate before adjustments",
                        width="small"
                    ),
                    "Adjustment ($/kW)": st.column_config.TextColumn(
                        "Adjustment ($/kW)",
                        help="Rate adjustments (surcharges, credits, etc.)",
                        width="small"
                    ),
                    "Total Rate ($/kW)": st.column_config.TextColumn(
                        "Total Rate ($/kW)",
                        help="Final demand rate including all adjustments",
                        width="small"
                    ),
                    "Months Present": st.column_config.TextColumn(
                        "Months Present",
                        help="Which months this demand period is active in weekday/weekend schedules",
                        width=300,  # Fixed pixel width to allow text wrapping
                        max_chars=None  # Allow unlimited characters for wrapping
                    )
                }
            )
        else:
            st.info("📝 **Note:** No demand rate structure found in this tariff JSON.")

        st.markdown("---")

        # Weekday Demand Rates - Full Width
        st.markdown("#### 📈 Weekday Demand Rates")
        st.plotly_chart(viewer.plot_heatmap(is_weekday=True, dark_mode=dark_mode, rate_type="demand", chart_height=chart_height, text_size=text_size), use_container_width=True)
        
        st.markdown("---")
        
        # Weekend Demand Rates - Full Width
        st.markdown("#### 📉 Weekend Demand Rates")
        st.plotly_chart(viewer.plot_heatmap(is_weekday=False, dark_mode=dark_mode, rate_type="demand", chart_height=chart_height, text_size=text_size), use_container_width=True)
    
    with tab3:
        st.markdown("### 📊 Seasonal/Monthly Flat Demand Rates")
        st.plotly_chart(viewer.plot_flat_demand_rates(dark_mode=dark_mode), use_container_width=True)
        
    with tab4:
        st.markdown("### 📈 Combined Rate Analysis")
        st.markdown("**Energy vs Demand Rate Comparison**")
        # Create comparison chart
        comparison_data = pd.DataFrame({
            'Month': viewer.months,
            'Avg Energy Rate ($/kWh)': [viewer.weekday_df.iloc[i].mean() for i in range(12)],
            'Avg Demand Rate ($/kW)': [viewer.demand_weekday_df.iloc[i].mean() for i in range(12)]
        })
        fig = px.line(comparison_data, x='Month', y=['Avg Energy Rate ($/kWh)', 'Avg Demand Rate ($/kW)'],
                     title="Monthly Average Rates Comparison", markers=True)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

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
