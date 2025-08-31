import streamlit as st
import json
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import os

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
                
            self.original_tariff = self.tariff.copy()
            
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
    
    def update_rate(self, month_idx, hour, is_weekday, new_rate, rate_type="energy"):
        if rate_type == "energy":
            # Update energy rates
            schedule_key = 'energyweekdayschedule' if is_weekday else 'energyweekendschedule'
            if schedule_key in self.tariff and self.tariff[schedule_key]:
                period_idx = self.tariff[schedule_key][month_idx][hour]
                if 'energyratestructure' in self.tariff and self.tariff['energyratestructure']:
                    self.tariff['energyratestructure'][period_idx][0]['rate'] = new_rate
        elif rate_type == "demand":
            # Update demand rates
            schedule_key = 'demandweekdayschedule' if is_weekday else 'demandweekendschedule'
            if schedule_key in self.tariff and self.tariff[schedule_key]:
                period_idx = self.tariff[schedule_key][month_idx][hour]
                if 'demandratestructure' in self.tariff and self.tariff['demandratestructure']:
                    self.tariff['demandratestructure'][period_idx][0]['rate'] = new_rate
        
        # Update dataframes
        self.update_rate_dataframes()
        
    def update_flat_demand_rate(self, month_idx, new_rate):
        flat_demand_months = self.tariff.get('flatdemandmonths', [])
        if month_idx < len(flat_demand_months):
            period_idx = flat_demand_months[month_idx]
            flat_demand_rates = self.tariff.get('flatdemandstructure', [])
            if period_idx < len(flat_demand_rates) and flat_demand_rates[period_idx]:
                self.tariff['flatdemandstructure'][period_idx][0]['rate'] = new_rate
                self.update_rate_dataframes()
    
    def save_changes(self, filename):
        output_path = Path("modified_tariffs") / filename
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(self.data, f, indent=2)
        return str(output_path)
    
    def reset_changes(self):
        self.tariff = self.original_tariff.copy()
        self.data['items'][0] = self.tariff
        self.update_rate_dataframes()
        
    def plot_heatmap(self, is_weekday=True, dark_mode=False, rate_type="energy", chart_height=700, text_size=12):
        if rate_type == "energy":
            df = self.weekday_df if is_weekday else self.weekend_df
            day_type = "Weekday" if is_weekday else "Weekend"
            title_suffix = "Energy Rates"
            colorbar_title = "Rate ($/kWh)"
            hover_template = "<b>%{y}</b><br>Hour: <b>%{x}</b><br>Rate: <b>$%{z:.4f}/kWh</b><extra></extra>"
        else:  # demand
            df = self.demand_weekday_df if is_weekday else self.demand_weekend_df
            day_type = "Weekday" if is_weekday else "Weekend"
            title_suffix = "Demand Rates"
            colorbar_title = "Rate ($/kW)"
            hover_template = "<b>%{y}</b><br>Hour: <b>%{x}</b><br>Rate: <b>$%{z:.4f}/kW</b><extra></extra>"
        
        # Create Plotly heatmap with modern styling
        fig = go.Figure(data=go.Heatmap(
            z=df.values,
            x=[f'{h:02d}:00' for h in self.hours],
            y=df.index,
            text=df.values.round(4),
            texttemplate="%{text}",
            textfont={"size": text_size, "color": "#2c3e50" if not dark_mode else "#ffffff"},
            hoverongaps=False,
            colorscale=[
                [0, '#f0f9ff'],      # Very light blue
                [0.2, '#bae6fd'],    # Light blue
                [0.4, '#7dd3fc'],    # Medium blue
                [0.6, '#38bdf8'],    # Blue
                [0.8, '#0ea5e9'],    # Dark blue
                [1, '#0369a1']       # Very dark blue
            ] if not dark_mode else [
                [0, '#0f172a'],      # Very dark blue (dark mode)
                [0.2, '#1e293b'],    # Dark blue
                [0.4, '#334155'],    # Medium blue
                [0.6, '#475569'],    # Blue
                [0.8, '#64748b'],    # Light blue
                [1, '#94a3b8']       # Very light blue
            ],
            showscale=True,
            colorbar=dict(
                title=dict(text=colorbar_title),
                thickness=20,
                len=0.6,
                outlinewidth=0,
                tickfont=dict(size=13, color='#34495e' if not dark_mode else '#ffffff'),
                tickformat=".4f"
            )
        ))
        
        # Update layout for modern, clean appearance
        fig.update_layout(
            title=dict(
                text=f'{day_type} {title_suffix}<br><span style="font-size: 0.8em; color: #64748b;">{self.utility_name} - {self.rate_name}</span>',
                font=dict(size=22, color='#1e293b' if not dark_mode else '#ffffff'),
                x=0.5,
                xanchor='center',
                y=0.95
            ),
            xaxis=dict(
                title=dict(text="Hour of Day", font=dict(size=16, color='#475569' if not dark_mode else '#cbd5e1')),
                tickfont=dict(size=13, color='#64748b' if not dark_mode else '#94a3b8'),
                showgrid=True,
                gridwidth=1,
                gridcolor='#e2e8f0' if not dark_mode else '#334155',
                zeroline=False,
                showline=False,
                tickangle=0
            ),
            yaxis=dict(
                title=dict(text="Month", font=dict(size=16, color='#475569' if not dark_mode else '#cbd5e1')),
                tickfont=dict(size=13, color='#64748b' if not dark_mode else '#94a3b8'),
                showgrid=True,
                gridwidth=1,
                gridcolor='#e2e8f0' if not dark_mode else '#334155',
                zeroline=False,
                showline=False
            ),
            plot_bgcolor='#ffffff' if not dark_mode else '#0f172a',
            paper_bgcolor='#ffffff' if not dark_mode else '#0f172a',
            margin=dict(l=70, r=70, t=100, b=70),
            height=chart_height,
            width=900,
            hoverlabel=dict(
                bgcolor='#ffffff' if not dark_mode else '#1e293b',
                font_size=12,
                font_family="Inter, Arial, sans-serif",
                bordercolor='#e2e8f0' if not dark_mode else '#334155'
            ),
            font=dict(family="Inter, Arial, sans-serif")
        )
        
        # Add hover template for better information display
        fig.update_traces(hovertemplate=hover_template)
        
        return fig
    
    def plot_flat_demand_rates(self, dark_mode=False):
        """Plot flat demand rates (seasonal/monthly) as a bar chart"""
        fig = go.Figure(data=go.Bar(
            x=self.flat_demand_df.index,
            y=self.flat_demand_df['Rate ($/kW)'],
            text=self.flat_demand_df['Rate ($/kW)'].round(4),
            texttemplate="%{text}",
            textposition='outside',
            marker_color='#3b82f6',
            marker_line_color='#1e40af',
            marker_line_width=1,
            opacity=0.8
        ))
        
        fig.update_layout(
            title=dict(
                text=f'Seasonal/Monthly Demand Rates<br><span style="font-size: 0.8em; color: #64748b;">{self.utility_name} - {self.rate_name}</span>',
                font=dict(size=22, color='#1e293b' if not dark_mode else '#ffffff'),
                x=0.5,
                xanchor='center',
                y=0.95
            ),
            xaxis=dict(
                title=dict(text="Month", font=dict(size=14, color='#475569' if not dark_mode else '#cbd5e1')),
                tickfont=dict(size=11, color='#64748b' if not dark_mode else '#94a3b8'),
                showgrid=True,
                gridwidth=1,
                gridcolor='#e2e8f0' if not dark_mode else '#334155',
                zeroline=False,
                showline=False
            ),
            yaxis=dict(
                title=dict(text="Demand Rate ($/kW)", font=dict(size=14, color='#475569' if not dark_mode else '#cbd5e1')),
                tickfont=dict(size=11, color='#64748b' if not dark_mode else '#94a3b8'),
                showgrid=True,
                gridwidth=1,
                gridcolor='#e2e8f0' if not dark_mode else '#334155',
                zeroline=False,
                showline=False
            ),
            plot_bgcolor='#ffffff' if not dark_mode else '#0f172a',
            paper_bgcolor='#ffffff' if not dark_mode else '#0f172a',
            margin=dict(l=70, r=70, t=100, b=70),
            height=400,
            width=900,
            hoverlabel=dict(
                bgcolor='#ffffff' if not dark_mode else '#1e293b',
                font_size=12,
                font_family="Inter, Arial, sans-serif",
                bordercolor='#e2e8f0' if not dark_mode else '#334155'
            ),
            font=dict(family="Inter, Arial, sans-serif")
        )
        
        fig.update_traces(
            hovertemplate="<b>%{x}</b><br>Demand Rate: <b>$%{y:.4f}/kW</b><extra></extra>"
        )
        
        return fig
    
    def create_tou_labels_table(self):
        """Create a table showing TOU labels with their corresponding energy rates"""
        energy_labels = self.tariff.get('energytoulabels', None)
        energy_rates = self.tariff.get('energyratestructure', [])
        
        if not energy_labels:
            return None
        
        # Create table data
        table_data = []
        for i, label in enumerate(energy_labels):
            if i < len(energy_rates) and energy_rates[i]:
                rate_info = energy_rates[i][0]  # Get first tier
                rate = rate_info.get('rate', 0)
                adj = rate_info.get('adj', 0)
                total_rate = rate + adj
                unit = rate_info.get('unit', 'kWh')
                
                table_data.append({
                    'TOU Period': label,
                    'Base Rate ($/kWh)': f"${rate:.4f}",
                    'Adjustment ($/kWh)': f"${adj:.4f}",
                    'Total Rate ($/kWh)': f"${total_rate:.4f}",
                    'Unit': unit
                })
        
        return pd.DataFrame(table_data)

def main():
    st.set_page_config(page_title="URDB Tariff Viewer", layout="wide", initial_sidebar_state="expanded")
    
    # Custom CSS for modern styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem 0;
        border-bottom: 3px solid #3b82f6;
        background: linear-gradient(90deg, #f8fafc 0%, #e2e8f0 100%);
        border-radius: 10px;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .sidebar-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0px 0px;
        background-color: #f1f5f9;
        border: 1px solid #e2e8f0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6;
        color: white;
    }
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
    }
    .stSelectbox > div > div {
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">⚡ URDB Tariff Viewer & Editor</h1>', unsafe_allow_html=True)

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

    # Sidebar for controls
    with st.sidebar:
        st.markdown('<div class="sidebar-header">🎛️ Controls</div>', unsafe_allow_html=True)
        
        # Dark mode toggle
        dark_mode = st.checkbox("🌙 Dark Mode", value=False)
        
        # Helpful tip for better viewing
        st.info("💡 **Tip**: Use the '⚙️ Visualization Settings' below to adjust chart height and text size for better readability!")
        
        # Tariff selection
        selected_file = st.selectbox(
            "📊 Select a tariff",
            options=[option[0] for option in tariff_options],
            format_func=lambda x: next(name for path, name in tariff_options if path == x)
        )

        if "tariff_viewer" not in st.session_state or st.session_state.current_tariff != selected_file:
            try:
                st.session_state.tariff_viewer = TariffViewer(selected_file)
                st.session_state.current_tariff = selected_file
            except Exception as e:
                st.error(f"Error loading tariff: {str(e)}")
                st.exception(e)
                return

        viewer = st.session_state.tariff_viewer

        # Rate editing controls
        st.markdown("### ✏️ Edit Rates")
        
        # Rate type selection
        rate_type = st.selectbox("Rate Type", options=["Energy", "Demand"], help="Choose between energy rates ($/kWh) or demand rates ($/kW)")
        
        month_idx = st.selectbox("Month", options=list(enumerate(viewer.months)), format_func=lambda x: x[1])[0]
        hour = st.selectbox("Hour", options=[(f"{h:02d}:00", h) for h in viewer.hours], format_func=lambda x: x[0])[1]
        is_weekday = st.radio("Day Type", options=["Weekday", "Weekend"]) == "Weekday"
        
        # Get current rate for selected time
        if rate_type == "Energy":
            df = viewer.weekday_df if is_weekday else viewer.weekend_df
            current_rate = df.iloc[month_idx, hour]
            rate_unit = "$/kWh"
        else:  # Demand
            df = viewer.demand_weekday_df if is_weekday else viewer.demand_weekend_df
            current_rate = df.iloc[month_idx, hour]
            rate_unit = "$/kW"
        
        new_rate = st.number_input(f"Rate ({rate_unit})", value=float(current_rate), format="%.4f", step=0.0001)
        
        if st.button("🔄 Update Rate", type="primary"):
            viewer.update_rate(month_idx, hour, is_weekday, new_rate, rate_type.lower())
            st.success("✅ Rate updated successfully!")
        
        # Flat demand rate editing
        st.markdown("### 🔌 Edit Flat Demand Rates")
        flat_month_idx = st.selectbox("Month for Flat Demand", options=list(enumerate(viewer.months)), format_func=lambda x: x[1], key="flat_demand")[0]
        current_flat_rate = viewer.flat_demand_df.iloc[flat_month_idx, 0]
        new_flat_rate = st.number_input("Flat Demand Rate ($/kW)", value=float(current_flat_rate), format="%.4f", step=0.0001, key="flat_demand_rate")
        
        if st.button("🔄 Update Flat Demand Rate", type="secondary"):
            viewer.update_flat_demand_rate(flat_month_idx, new_flat_rate)
            st.success("✅ Flat demand rate updated successfully!")

        # Save and Reset buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Changes", type="secondary"):
                new_file = viewer.save_changes(f"modified_{selected_file.name}")
                st.success(f"💾 Saved to {new_file}")
        with col2:
            if st.button("🔄 Reset", type="secondary"):
                viewer.reset_changes()
                st.success("🔄 Rates reset to original")

    # Main content area - Heatmaps
    st.markdown("## 📊 Rate Visualizations")
    
    # Add summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📈 Highest Energy Rate",
            value=f"${viewer.weekday_df.max().max():.4f}/kWh",
            delta=f"Hour {viewer.weekday_df.max().idxmax()}:00"
        )
    
    with col2:
        st.metric(
            label="📉 Lowest Energy Rate", 
            value=f"${viewer.weekday_df.min().min():.4f}/kWh",
            delta=f"Hour {viewer.weekday_df.min().idxmin()}:00"
        )
    
    with col3:
        st.metric(
            label="📊 Average Energy Rate",
            value=f"${viewer.weekday_df.mean().mean():.4f}/kWh",
            delta="All periods"
        )
    
    with col4:
        st.metric(
            label="🕐 Peak Energy Hours",
            value=f"{len(viewer.weekday_df[viewer.weekday_df > viewer.weekday_df.mean().mean()])} periods",
            delta="Above average"
        )
    
    # Demand charge statistics
    st.markdown("### 🔌 Demand Charge Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📈 Highest Demand Rate",
            value=f"${viewer.demand_weekday_df.max().max():.4f}/kW",
            delta=f"Hour {viewer.demand_weekday_df.max().idxmax()}:00"
        )
    
    with col2:
        st.metric(
            label="📉 Lowest Demand Rate", 
            value=f"${viewer.demand_weekday_df.min().min():.4f}/kW",
            delta=f"Hour {viewer.demand_weekday_df.min().idxmin()}:00"
        )
    
    with col3:
        st.metric(
            label="📊 Average Demand Rate",
            value=f"${viewer.demand_weekday_df.mean().mean():.4f}/kW",
            delta="All periods"
        )
    
    with col4:
        st.metric(
            label="🔌 Flat Demand Rate",
            value=f"${viewer.flat_demand_df['Rate ($/kW)'].max():.4f}/kW",
            delta="Highest monthly rate"
        )
    
    st.markdown("---")
    
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
    
    st.markdown("---")
    
    # Create tabs for energy and demand rates with modern styling
    tab1, tab2, tab3, tab4 = st.tabs(["⚡ Energy Rates", "🔌 Demand Rates", "📊 Flat Demand", "📈 Combined View"])
    
    with tab1:
        st.markdown("### ⚡ Energy Rate Structure")
        
        # TOU Labels Table
        st.markdown("#### 🏷️ Time-of-Use Period Labels & Rates")
        tou_table = viewer.create_tou_labels_table()
        if tou_table is not None:
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
                        help="Base energy rate before adjustments"
                    ),
                    "Adjustment ($/kWh)": st.column_config.TextColumn(
                        "Adjustment ($/kWh)",
                        help="Rate adjustments (surcharges, credits, etc.)"
                    ),
                    "Total Rate ($/kWh)": st.column_config.TextColumn(
                        "Total Rate ($/kWh)",
                        help="Final rate including all adjustments"
                    ),
                    "Unit": st.column_config.TextColumn(
                        "Unit",
                        help="Rate unit (typically kWh)"
                    )
                }
            )
        else:
            st.info("📝 **Note:** TOU labels not present in this tariff JSON. The tariff uses period-based rates without descriptive labels.")
        
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
        col1, col2 = st.columns(2)
        with col1:
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
        
        with col2:
            st.markdown("**Rate Distribution**")
            # Create histogram of rates
            energy_rates = viewer.weekday_df.values.flatten()
            demand_rates = viewer.demand_weekday_df.values.flatten()
            
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=energy_rates, name="Energy Rates", nbinsx=20, opacity=0.7))
            fig.add_trace(go.Histogram(x=demand_rates, name="Demand Rates", nbinsx=20, opacity=0.7))
            fig.update_layout(title="Rate Distribution", height=400, barmode='overlay')
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Display tariff details in modern cards
    st.markdown("## 📋 Tariff Information")
    
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
    
    # Additional demand charge information
    st.markdown("### 🔌 Demand Charge Details")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🔌 Demand Unit</h3>
            <p style="font-size: 1.2rem; margin: 0;">{viewer.tariff.get('demandrateunit', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-card">
            <h3>📊 Flat Demand Unit</h3>
            <p style="font-size: 1.2rem; margin: 0;">{viewer.tariff.get('flatdemandunit', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🕐 Demand Window</h3>
            <p style="font-size: 1.2rem; margin: 0;">{viewer.tariff.get('demandwindow', 'N/A')} min</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-card">
            <h3>⚡ Reactive Power</h3>
            <p style="font-size: 1.2rem; margin: 0;">${viewer.tariff.get('demandreactivepowercharge', 'N/A')}/kVAR</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📈 Demand Ratchet</h3>
            <p style="font-size: 1.2rem; margin: 0;">{viewer.tariff.get('demandratchetpercentage', ['N/A'])[0] if viewer.tariff.get('demandratchetpercentage') else 'N/A'}%</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-card">
            <h3>🔌 Coincident Unit</h3>
            <p style="font-size: 1.2rem; margin: 0;">{viewer.tariff.get('coincidentrateunit', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("## 📝 Description")
    st.info(viewer.description)
    
    # Show full JSON data in an expandable section
    with st.expander("🔍 View Raw JSON Data"):
        st.json(viewer.data)

if __name__ == "__main__":
    main()
