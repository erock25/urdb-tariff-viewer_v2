"""
Cost calculator tab component for URDB Tariff Viewer.

This module contains the UI components for the utility cost analysis tab.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, Optional
from pathlib import Path
from io import BytesIO

from src.models.tariff import TariffViewer
from src.services.calculation_service import CalculationService
from src.services.file_service import FileService
from src.utils.styling import create_section_header_html, create_custom_divider_html
from src.config.settings import Settings


def render_cost_calculator_tab(
    tariff_viewer: TariffViewer, 
    load_profile_path: Optional[Path], 
    options: Dict[str, Any]
) -> None:
    """
    Render the utility cost analysis tab.
    
    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
        load_profile_path (Optional[Path]): Path to selected load profile
        options (Dict[str, Any]): Display and analysis options
    """
    st.markdown(create_section_header_html("💰 Utility Cost Analysis"), unsafe_allow_html=True)
    
    # Load Factor Analysis Tool - Always available
    st.markdown("#### 📊 Load Factor Rate Analysis")
    _render_load_factor_analysis_tool(tariff_viewer, options)
    
    st.markdown(create_custom_divider_html(), unsafe_allow_html=True)
    
    # Rest of the calculator (requires load profile)
    if not load_profile_path:
        _show_no_load_profile_message()
        return
    
    # Load profile validation
    st.markdown("#### 📋 Load Profile Validation")
    
    try:
        validation_results = CalculationService.validate_load_profile(load_profile_path)
        _display_validation_results(validation_results)
        
        if not validation_results['is_valid']:
            st.error("❌ Cannot proceed with cost calculation due to validation errors.")
            return
            
    except Exception as e:
        st.error(f"❌ Error validating load profile: {str(e)}")
        return
    
    st.markdown(create_custom_divider_html(), unsafe_allow_html=True)
    
    # Calculate button
    if st.button("🧮 Calculate Utility Costs", type="primary", width="stretch"):
        # Use default customer voltage from options
        customer_voltage = options.get('customer_voltage', 480.0)
        _perform_cost_calculation(tariff_viewer, load_profile_path, customer_voltage, options)
    
    # Show existing results if available
    if 'calculation_results' in st.session_state:
        st.markdown(create_custom_divider_html(), unsafe_allow_html=True)
        _display_calculation_results(st.session_state.calculation_results, options)


def render_load_factor_analysis_tab(tariff_viewer: TariffViewer, options: Dict[str, Any]) -> None:
    """
    Render the load factor analysis tool tab.
    
    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
        options (Dict[str, Any]): Display and analysis options
    """
    _render_load_factor_analysis_tool(tariff_viewer, options)


def render_utility_cost_calculation_tab(
    tariff_viewer: TariffViewer, 
    load_profile_path: Optional[Path], 
    options: Dict[str, Any]
) -> None:
    """
    Render the utility cost calculation tool tab.
    
    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
        load_profile_path (Optional[Path]): Path to selected load profile
        options (Dict[str, Any]): Display and analysis options
    """
    # Rest of the calculator (requires load profile)
    if not load_profile_path:
        _show_no_load_profile_message()
        return
    
    # Load profile validation
    st.markdown("#### 📋 Load Profile Validation")
    
    try:
        validation_results = CalculationService.validate_load_profile(load_profile_path)
        _display_validation_results(validation_results)
        
        if not validation_results['is_valid']:
            st.error("❌ Cannot proceed with cost calculation due to validation errors.")
            return
            
    except Exception as e:
        st.error(f"❌ Error validating load profile: {str(e)}")
        return
    
    st.markdown(create_custom_divider_html(), unsafe_allow_html=True)
    
    # Calculate button
    if st.button("🧮 Calculate Utility Costs", type="primary", width="stretch"):
        # Use default customer voltage from options
        customer_voltage = options.get('customer_voltage', 480.0)
        _perform_cost_calculation(tariff_viewer, load_profile_path, customer_voltage, options)
    
    # Show existing results if available
    if 'calculation_results' in st.session_state:
        st.markdown(create_custom_divider_html(), unsafe_allow_html=True)
        _display_calculation_results(st.session_state.calculation_results, options)


def _show_no_load_profile_message() -> None:
    """Show message when no load profile is selected."""
    st.info("ℹ️ **No Load Profile Selected**")
    st.markdown("""
    To calculate utility costs, you need to:
    
    1. **Select a load profile** from the sidebar dropdown, or
    2. **Upload a CSV file** with your load data, or  
    3. **Generate a synthetic profile** using the Load Profile Generator tab
    
    **Required CSV Format:**
    - `timestamp`: Date and time in YYYY-MM-DD HH:MM:SS format
    - `load_kW`: Load values in kilowatts
    - Optional: `kWh` column (will be calculated if missing)
    """)
    
    # Show available load profiles
    csv_files = FileService.find_csv_files()
    if csv_files:
        st.markdown("**Available Load Profiles:**")
        for file_path in csv_files[:5]:  # Show first 5
            file_info = FileService.get_file_info(file_path)
            st.markdown(f"- `{file_info['name']}` ({file_info['size_mb']:.1f} MB)")
        
        if len(csv_files) > 5:
            st.markdown(f"... and {len(csv_files) - 5} more files")


def _display_validation_results(validation_results: Dict[str, Any]) -> None:
    """Display load profile validation results."""
    if validation_results['is_valid']:
        st.success("✅ Load profile validation passed")
        
        # Show file info
        info = validation_results.get('info', {})
        if info:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Data Points", f"{info.get('row_count', 0):,}")
            
            with col2:
                load_range = info.get('load_range', {})
                if load_range.get('avg'):
                    st.metric("Avg Load", f"{load_range['avg']:.1f} kW")
            
            with col3:
                if load_range.get('max'):
                    st.metric("Peak Load", f"{load_range['max']:.1f} kW")
            
            with col4:
                date_range = info.get('date_range', {})
                if date_range.get('start') and date_range.get('end'):
                    st.metric("Date Range", f"{date_range['start']} to {date_range['end']}")
    
    else:
        st.error("❌ Load profile validation failed")
        
        # Show errors
        for error in validation_results.get('errors', []):
            st.error(f"• {error}")
    
    # Show warnings
    for warning in validation_results.get('warnings', []):
        st.warning(f"⚠️ {warning}")


def _perform_cost_calculation(
    tariff_viewer: TariffViewer, 
    load_profile_path: Path, 
    customer_voltage: float,
    options: Dict[str, Any]
) -> None:
    """Perform the utility cost calculation."""
    
    with st.spinner("🧮 Calculating utility costs..."):
        try:
            # Check if we have modified tariff data and use it directly
            if (st.session_state.get('has_modifications', False) and 
                st.session_state.get('modified_tariff') is not None):
                # Use modified tariff data directly
                from src.services.calculation_engine import calculate_utility_costs_for_app
                
                # Extract the actual tariff data from the wrapper structure
                modified_tariff = st.session_state.modified_tariff
                if 'items' in modified_tariff:
                    tariff_data = modified_tariff['items'][0]
                else:
                    tariff_data = modified_tariff
                
                results = calculate_utility_costs_for_app(
                    tariff_data=tariff_data,
                    load_profile_path=str(load_profile_path),
                    default_voltage=customer_voltage
                )
            else:
                # Use the calculation service with original tariff
                results = CalculationService.calculate_utility_bill(
                    tariff_viewer=tariff_viewer,
                    load_profile_path=load_profile_path,
                    customer_voltage=customer_voltage
                )
            
            # Store results in session state
            st.session_state.calculation_results = results
            st.session_state.calculation_tariff = {
                'utility': tariff_viewer.utility_name,
                'rate': tariff_viewer.rate_name,
                'sector': tariff_viewer.sector
            }
            
            st.success("✅ Cost calculation completed successfully!")
            st.rerun()  # Refresh to show results
            
        except Exception as e:
            st.error(f"❌ Calculation failed: {str(e)}")
            st.info("💡 **Troubleshooting Tips:**")
            st.info("• Ensure your load profile has the correct format")
            st.info("• Check that the tariff file contains valid rate structures")
            st.info("• Verify that timestamps in your load profile are properly formatted")


def _display_calculation_results(results: pd.DataFrame, options: Dict[str, Any]) -> None:
    """Display the calculation results."""
    st.markdown("#### 💰 Cost Calculation Results")
    
    tariff_info = st.session_state.get('calculation_tariff', {})
    if tariff_info:
        st.info(f"**Tariff:** {tariff_info.get('utility', 'Unknown')} - {tariff_info.get('rate', 'Unknown')}")
    
    # Calculate summary metrics from DataFrame (matching original app.py)
    total_annual_cost = results['total_charge'].sum()
    total_annual_kwh = results['total_kwh'].sum()
    avg_monthly_cost = results['total_charge'].mean()
    effective_rate_per_kwh = total_annual_cost / total_annual_kwh if total_annual_kwh > 0 else 0
    
    # Main cost metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Annual Total Cost", f"${total_annual_cost:,.0f}")
    
    with col2:
        st.metric("Annual Total kWh", f"{total_annual_kwh:,.0f}")
    
    with col3:
        st.metric("Average Monthly Cost", f"${avg_monthly_cost:,.0f}")
    
    with col4:
        st.metric("Effective Rate $/kWh", f"${effective_rate_per_kwh:.4f}")
    
    st.markdown("---")
    
    # Display detailed monthly breakdown (matching original app.py)
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
    _create_cost_breakdown_chart(results, options)
    
    # Load profile chart
    st.markdown("#### ⚡ Load Profile Overview")
    _create_load_profile_chart(results, options)


def _create_cost_breakdown_chart(results: pd.DataFrame, options: Dict[str, Any]) -> None:
    """Create a monthly cost breakdown chart."""
    dark_mode = options.get('dark_mode', False)
    
    # Create monthly bar chart instead of annual donut chart
    fig = go.Figure()
    
    # Add grouped bar chart for monthly cost breakdown
    fig.add_trace(go.Bar(
        x=results['month_name'],
        y=results['total_energy_cost'],
        name='Energy Costs',
        marker_color='rgba(59, 130, 246, 0.8)',
        hovertemplate="<b>%{x}</b><br>Energy Cost: $%{y:.2f}<extra></extra>"
    ))
    
    fig.add_trace(go.Bar(
        x=results['month_name'],
        y=results['total_demand_cost'],
        name='Demand Costs',
        marker_color='rgba(249, 115, 22, 0.8)',
        hovertemplate="<b>%{x}</b><br>Demand Cost: $%{y:.2f}<extra></extra>"
    ))
    
    fig.add_trace(go.Bar(
        x=results['month_name'],
        y=results['fixed_charge'],
        name='Fixed Charges',
        marker_color='rgba(34, 197, 94, 0.8)',
        hovertemplate="<b>%{x}</b><br>Fixed Charge: $%{y:.2f}<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(
            text="Monthly Cost Breakdown by Month",
            font=dict(
                size=18,
                color='#1f2937' if not dark_mode else '#f1f5f9',
                family="Inter, sans-serif"
            )
        ),
        barmode='stack',
        xaxis_title="Month",
        yaxis_title="Cost ($)",
        height=500,
        showlegend=True,
        plot_bgcolor='rgba(248, 250, 252, 0.8)' if not dark_mode else 'rgba(15, 23, 42, 0.5)',
        paper_bgcolor='#ffffff' if not dark_mode else '#0f172a',
        font=dict(
            family="Inter, sans-serif",
            color='#1f2937' if not dark_mode else '#f1f5f9'
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _create_load_profile_chart(results: pd.DataFrame, options: Dict[str, Any]) -> None:
    """Create a load profile overview chart."""
    dark_mode = options.get('dark_mode', False)
    
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


def _display_monthly_breakdown(monthly_costs: Dict[str, Any], options: Dict[str, Any]) -> None:
    """Display monthly cost breakdown."""
    dark_mode = options.get('dark_mode', False)
    
    # Convert to DataFrame for easier handling
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Extract monthly data (assuming it exists in results)
    monthly_data = []
    for i, month in enumerate(months):
        # This is a placeholder - actual structure depends on calculation service
        total = monthly_costs.get(f'month_{i+1}', {}).get('total', 0)
        energy = monthly_costs.get(f'month_{i+1}', {}).get('energy', 0)
        demand = monthly_costs.get(f'month_{i+1}', {}).get('demand', 0)
        
        monthly_data.append({
            'Month': month,
            'Total': total,
            'Energy': energy,
            'Demand': demand
        })
    
    df = pd.DataFrame(monthly_data)
    
    # Create stacked bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Energy Charges',
        x=df['Month'],
        y=df['Energy'],
        marker_color='#1e40af' if not dark_mode else '#3b82f6',
        hovertemplate='<b>Energy Charges</b><br>Month: %{x}<br>Cost: $%{y:,.2f}<extra></extra>'
    ))
    
    fig.add_trace(go.Bar(
        name='Demand Charges',
        x=df['Month'],
        y=df['Demand'],
        marker_color='#7c3aed' if not dark_mode else '#8b5cf6',
        hovertemplate='<b>Demand Charges</b><br>Month: %{x}<br>Cost: $%{y:,.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text='Monthly Cost Breakdown',
            font=dict(
                size=18,
                color='#1f2937' if not dark_mode else '#f1f5f9',
                family="Inter, sans-serif"
            )
        ),
        xaxis=dict(
            title='Month',
            titlefont=dict(
                color='#1f2937' if not dark_mode else '#f1f5f9'
            ),
            tickfont=dict(
                color='#1f2937' if not dark_mode else '#f1f5f9'
            )
        ),
        yaxis=dict(
            title='Cost ($)',
            titlefont=dict(
                color='#1f2937' if not dark_mode else '#f1f5f9'
            ),
            tickfont=dict(
                color='#1f2937' if not dark_mode else '#f1f5f9'
            )
        ),
        barmode='stack',
        height=400,
        font=dict(
            family="Inter, sans-serif",
            color='#1f2937' if not dark_mode else '#f1f5f9'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            font=dict(
                color='#1f2937' if not dark_mode else '#f1f5f9'
            )
        )
    )
    
    st.plotly_chart(fig, width="stretch")
    
    # Show data table
    st.dataframe(df.round(2), width="stretch", hide_index=True)


def _display_load_statistics(load_stats: Dict[str, Any]) -> None:
    """Display load profile statistics."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        peak_kw = load_stats.get('peak_kw', 0)
        st.metric("Peak Demand", f"{peak_kw:.1f} kW")
    
    with col2:
        avg_kw = load_stats.get('avg_kw', 0)
        st.metric("Average Load", f"{avg_kw:.1f} kW")
    
    with col3:
        total_kwh = load_stats.get('total_kwh', 0)
        st.metric("Total Energy", f"{total_kwh:,.0f} kWh")
    
    with col4:
        load_factor = load_stats.get('load_factor', 0)
        st.metric("Load Factor", f"{load_factor:.1%}")


def _display_detailed_breakdown(results: Dict[str, Any]) -> None:
    """Display detailed cost breakdown."""
    st.json(results)


def _create_export_section(results: Dict[str, Any]) -> None:
    """Create export options for results."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Export as JSON
        if st.button("📄 Export as JSON"):
            import json
            json_str = json.dumps(results, indent=2, default=str)
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name="utility_cost_calculation.json",
                mime="application/json"
            )
    
    with col2:
        # Export summary as CSV
        if st.button("📊 Export Summary as CSV"):
            # Convert values to float in case they're pandas Series
            def safe_float_convert(value):
                if hasattr(value, 'iloc'):
                    return float(value.iloc[0]) if len(value) > 0 else 0.0
                else:
                    return float(value) if value is not None else 0.0
            
            summary_data = {
                'Metric': ['Total Annual Cost', 'Energy Charges', 'Demand Charges', 'Fixed Charges'],
                'Amount ($)': [
                    safe_float_convert(results.get('total_annual_cost', 0)),
                    safe_float_convert(results.get('total_energy_cost', 0)),
                    safe_float_convert(results.get('total_demand_cost', 0)),
                    safe_float_convert(results.get('total_fixed_cost', 0))
                ]
            }
            
            df = pd.DataFrame(summary_data)
            csv_str = df.to_csv(index=False)
            
            st.download_button(
                label="Download CSV",
                data=csv_str,
                file_name="utility_cost_summary.csv",
                mime="text/csv"
            )
    
    with col3:
        # Generate report
        if st.button("📋 Generate Report"):
            st.info("📋 Report generation feature coming soon!")


def show_cost_comparison(tariff_viewers: list, load_profile_path: Path, options: Dict[str, Any]) -> None:
    """
    Show cost comparison between multiple tariffs.
    
    Args:
        tariff_viewers (list): List of TariffViewer instances
        load_profile_path (Path): Path to load profile
        options (Dict[str, Any]): Display options
    """
    st.markdown("#### 🔄 Tariff Comparison")
    
    if len(tariff_viewers) < 2:
        st.info("Select multiple tariffs to compare costs.")
        return
    
    with st.spinner("Comparing tariffs..."):
        try:
            comparison_results = CalculationService.compare_tariffs(
                tariff_viewers=tariff_viewers,
                load_profile_path=load_profile_path,
                customer_voltage=options.get('customer_voltage', 480.0)
            )
            
            # Display comparison results
            _display_comparison_results(comparison_results, options)
            
        except Exception as e:
            st.error(f"❌ Comparison failed: {str(e)}")


def _display_comparison_results(comparison_results: Dict[str, Any], options: Dict[str, Any]) -> None:
    """Display tariff comparison results."""
    tariff_results = comparison_results.get('tariff_results', [])
    summary = comparison_results.get('summary', {})
    
    if not tariff_results:
        st.error("No comparison results available.")
        return
    
    # Summary metrics
    if summary:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Lowest Cost", f"${summary.get('lowest_cost', 0):,.2f}")
        
        with col2:
            st.metric("Highest Cost", f"${summary.get('highest_cost', 0):,.2f}")
        
        with col3:
            savings = summary.get('highest_cost', 0) - summary.get('lowest_cost', 0)
            st.metric("Potential Savings", f"${savings:,.2f}")
    
    # Comparison table
    comparison_df = pd.DataFrame([
        {
            'Utility': result['utility_name'],
            'Rate': result['rate_name'],
            'Total Cost ($)': result['total_cost'],
            'Energy Cost ($)': result['energy_cost'],
            'Demand Cost ($)': result['demand_cost'],
            'Status': '✅ Success' if result['calculation_successful'] else '❌ Failed'
        }
        for result in tariff_results
    ])
    
    st.dataframe(comparison_df, width="stretch", hide_index=True)
    
    # Comparison chart
    successful_results = [r for r in tariff_results if r['calculation_successful']]
    
    if len(successful_results) > 1:
        fig = px.bar(
            x=[f"{r['utility_name']}\n{r['rate_name']}" for r in successful_results],
            y=[r['total_cost'] for r in successful_results],
            title="Annual Cost Comparison",
            labels={'x': 'Tariff', 'y': 'Annual Cost ($)'}
        )
        
        fig.update_layout(
            height=400,
            font=dict(family="Inter, sans-serif")
        )
        
        st.plotly_chart(fig, width="stretch")


def _get_active_energy_periods_for_month(tariff_data: Dict[str, Any], month: int) -> set:
    """
    Determine which energy periods are actually present in a given month.
    
    Args:
        tariff_data: Tariff data dictionary
        month: Month index (0-11)
    
    Returns:
        Set of period indices that appear in the selected month
    """
    active_periods = set()
    
    # Get schedules
    weekday_schedule = tariff_data.get('energyweekdayschedule', [])
    weekend_schedule = tariff_data.get('energyweekendschedule', [])
    
    # Check if month is valid and schedules exist
    if month < len(weekday_schedule):
        # Add all periods from weekday schedule for this month
        active_periods.update(weekday_schedule[month])
    
    if month < len(weekend_schedule):
        # Add all periods from weekend schedule for this month
        active_periods.update(weekend_schedule[month])
    
    return active_periods


def _get_active_demand_periods_for_month(tariff_data: Dict[str, Any], month: int) -> set:
    """
    Determine which demand periods are actually present in a given month.
    
    Args:
        tariff_data: Tariff data dictionary
        month: Month index (0-11)
    
    Returns:
        Set of period indices that appear in the selected month
    """
    active_periods = set()
    
    # Get schedules
    weekday_schedule = tariff_data.get('demandweekdayschedule', [])
    weekend_schedule = tariff_data.get('demandweekendschedule', [])
    
    # Check if month is valid and schedules exist
    if month < len(weekday_schedule):
        # Add all periods from weekday schedule for this month
        active_periods.update(weekday_schedule[month])
    
    if month < len(weekend_schedule):
        # Add all periods from weekend schedule for this month
        active_periods.update(weekend_schedule[month])
    
    return active_periods


def _get_active_demand_periods_for_year(tariff_data: Dict[str, Any]) -> Dict[int, int]:
    """
    Determine which demand periods are present in the year and count months of activity.
    
    Args:
        tariff_data: Tariff data dictionary
    
    Returns:
        Dictionary mapping period index to number of months it's active
    """
    period_month_counts = {}
    
    for month in range(12):
        active_periods = _get_active_demand_periods_for_month(tariff_data, month)
        for period in active_periods:
            period_month_counts[period] = period_month_counts.get(period, 0) + 1
    
    return period_month_counts


def _get_active_energy_periods_for_year(tariff_data: Dict[str, Any]) -> Dict[int, int]:
    """
    Determine which energy periods are present in the year and count months of activity.
    
    Args:
        tariff_data: Tariff data dictionary
    
    Returns:
        Dictionary mapping period index to number of months it's active
    """
    period_month_counts = {}
    
    for month in range(12):
        active_periods = _get_active_energy_periods_for_month(tariff_data, month)
        for period in active_periods:
            period_month_counts[period] = period_month_counts.get(period, 0) + 1
    
    return period_month_counts


def _calculate_annual_period_hour_percentages(tariff_data: Dict[str, Any], year: int = 2024) -> Dict[int, float]:
    """
    Calculate what percentage of the year's hours each energy period is present.
    
    Args:
        tariff_data: Tariff data dictionary
        year: Year for calendar calculation (default 2024)
    
    Returns:
        Dictionary mapping period index to percentage of year (0-100)
    """
    import calendar
    
    # Get schedules
    weekday_schedule = tariff_data.get('energyweekdayschedule', [])
    weekend_schedule = tariff_data.get('energyweekendschedule', [])
    
    if len(weekday_schedule) < 12 or len(weekend_schedule) < 12:
        return {}
    
    # Count hours per period across the year
    period_hours = {}
    total_hours = 0
    
    for month in range(12):
        # Get the calendar for this month
        cal = calendar.monthcalendar(year, month + 1)  # calendar uses 1-12 for months
        
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
    
    # Convert to percentages
    period_percentages = {}
    for period, hours in period_hours.items():
        period_percentages[period] = (hours / total_hours * 100) if total_hours > 0 else 0
    
    return period_percentages


def _calculate_period_hour_percentages(tariff_data: Dict[str, Any], month: int, year: int = 2024) -> Dict[int, float]:
    """
    Calculate what percentage of the month's hours each energy period is present.
    
    Args:
        tariff_data: Tariff data dictionary
        month: Month index (0-11)
        year: Year for calendar calculation (default 2024)
    
    Returns:
        Dictionary mapping period index to percentage of month (0-100)
    """
    import calendar
    
    # Get schedules
    weekday_schedule = tariff_data.get('energyweekdayschedule', [])
    weekend_schedule = tariff_data.get('energyweekendschedule', [])
    
    if month >= len(weekday_schedule) or month >= len(weekend_schedule):
        return {}
    
    # Get the calendar for this month
    cal = calendar.monthcalendar(year, month + 1)  # calendar uses 1-12 for months
    
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
    
    # Count hours per period
    period_hours = {}
    
    # Count from weekday schedule
    for hour in range(24):
        period = weekday_schedule[month][hour]
        period_hours[period] = period_hours.get(period, 0) + weekday_count
    
    # Count from weekend schedule
    for hour in range(24):
        period = weekend_schedule[month][hour]
        period_hours[period] = period_hours.get(period, 0) + weekend_count
    
    # Calculate total hours in month
    total_hours = (weekday_count + weekend_count) * 24
    
    # Convert to percentages
    period_percentages = {}
    for period, hours in period_hours.items():
        period_percentages[period] = (hours / total_hours * 100) if total_hours > 0 else 0
    
    return period_percentages


def _render_load_factor_analysis_tool(tariff_viewer: TariffViewer, options: Dict[str, Any]) -> None:
    """
    Render the load factor analysis tool.
    
    This tool allows users to calculate effective utility rates ($/kWh) at different load factors
    by specifying demand assumptions and energy distribution percentages.
    
    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
        options (Dict[str, Any]): Display options
    """
    
    st.markdown("""
    This tool calculates the **effective utility rate in $/kWh** for different load factors.
    
    **How it works:**
    - Select single month or full year analysis
    - Specify the maximum demand for each applicable demand period
    - Specify the energy distribution across all energy rate periods
    - View effective rates from 1% up to the maximum physically possible load factor (in 1% increments), plus 100%
    
    **Note:** The maximum physically possible load factor is determined by your energy distribution. 
    For each period: LF ≤ (hour %) / (energy %). The tool uses the most restrictive constraint.
    Example: if a period is 20% of hours but you allocate 40% of energy there, max LF = 50%.
    """)
    
    tariff_data = tariff_viewer.tariff  # Use .tariff for actual tariff data
    
    # Show what rate structures are present in this tariff
    has_tou_demand_check = bool(tariff_data.get('demandratestructure'))
    has_flat_demand_check = bool(tariff_data.get('flatdemandstructure'))
    has_energy_structure = bool(tariff_data.get('energyratestructure'))
    
    rate_structure_info = []
    if has_tou_demand_check:
        rate_structure_info.append("Time-of-Use Demand Charges")
    if has_flat_demand_check:
        rate_structure_info.append("Flat Monthly Demand Charges")
    if has_energy_structure:
        num_energy_periods = len(tariff_data.get('energyratestructure', []))
        if num_energy_periods == 1:
            rate_structure_info.append("Flat Energy Rate (no time-of-use periods)")
        else:
            rate_structure_info.append(f"{num_energy_periods} Time-of-Use Energy Periods")
    
    if rate_structure_info:
        st.info(f"📊 **This tariff includes:** {', '.join(rate_structure_info)}")
    else:
        st.warning("⚠️ No rate structure information found in this tariff.")
    
    # Analysis period selection
    month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
    
    analysis_period = st.radio(
        "📅 Analysis Period",
        options=["Single Month", "Full Year"],
        horizontal=True,
        help="Choose whether to analyze a single month or calculate annual effective rates"
    )
    
    # Month selection (only shown for single month analysis)
    if analysis_period == "Single Month":
        selected_month = st.selectbox(
            "Select Month",
            options=list(range(12)),
            format_func=lambda x: month_names[x],
            help="Select the month for which to calculate effective rates"
        )
    else:
        # For full year, we'll use all months, but need a reference month for UI purposes
        selected_month = 0  # Reference month for determining which periods to show
    
    st.markdown("---")
    
    # Get demand rate structure
    has_tou_demand = 'demandratestructure' in tariff_data and tariff_data.get('demandratestructure')
    has_flat_demand = 'flatdemandstructure' in tariff_data and tariff_data.get('flatdemandstructure')
    
    demand_inputs = {}
    
    # Initialize period month count variables (will be populated based on tariff structure)
    demand_period_month_counts = {}
    energy_period_month_counts = {}
        
    # TOU Demand inputs
    if has_tou_demand:
        st.markdown("##### ⚡ TOU Demand Charges")
        st.markdown("Specify the maximum demand (kW) for each TOU demand period:")
        
        # Get demand period labels if available
        demand_labels = tariff_data.get('demandtoulabels', [])
        num_demand_periods = len(tariff_data['demandratestructure'])
        
        # Get active demand periods based on analysis period
        if analysis_period == "Single Month":
            active_demand_periods = _get_active_demand_periods_for_month(tariff_data, selected_month)
            demand_period_month_counts = {p: 1 for p in active_demand_periods}
            
            # Show info about which periods are active
            if len(active_demand_periods) < num_demand_periods:
                inactive_periods = set(range(num_demand_periods)) - active_demand_periods
                inactive_labels = [demand_labels[i] if i < len(demand_labels) else f"Period {i}" 
                                 for i in sorted(inactive_periods)]
                st.info(f"ℹ️ Only showing demand periods present in {month_names[selected_month]}. "
                       f"The following demand periods are not scheduled this month: {', '.join(inactive_labels)}")
        else:
            # Full year - get all periods active in any month
            demand_period_month_counts = _get_active_demand_periods_for_year(tariff_data)
            active_demand_periods = set(demand_period_month_counts.keys())
            
            if len(active_demand_periods) < num_demand_periods:
                st.info(f"ℹ️ Showing all demand periods active during the year.")
        
        # Only show active periods
        active_demand_periods_list = sorted(list(active_demand_periods))
        
        if not active_demand_periods_list:
            st.warning("⚠️ No demand periods found in the schedule. Please check the tariff data.")
        else:
            cols = st.columns(min(len(active_demand_periods_list), 3))
            for idx, i in enumerate(active_demand_periods_list):
                label = demand_labels[i] if i < len(demand_labels) else f"Demand Period {i}"
                rate = tariff_data['demandratestructure'][i][0].get('rate', 0)
                adj = tariff_data['demandratestructure'][i][0].get('adj', 0)
                total_rate = rate + adj
                
                # Show month count for annual analysis
                month_info = ""
                if analysis_period == "Full Year":
                    month_count = demand_period_month_counts.get(i, 0)
                    month_info = f"\n({month_count} months)"
                
                with cols[idx % min(len(active_demand_periods_list), 3)]:
                    demand_inputs[f'tou_demand_{i}'] = st.number_input(
                        f"{label}{month_info}\n(${total_rate:.2f}/kW)",
                        min_value=0.0,
                        value=0.0,
                        step=1.0,
                        key=f"lf_tou_demand_{i}_{analysis_period}",
                        help=f"Base rate: ${rate:.2f}/kW" + (f" + Adjustment: ${adj:.2f}/kW" if adj != 0 else "") +
                             (f"\n\nActive in {month_count} months" if analysis_period == "Full Year" else "")
                    )
        
        # Flat demand input
        if has_flat_demand:
            st.markdown("##### 📊 Flat Monthly Demand Charge")
            
            flatdemandmonths = tariff_data.get('flatdemandmonths', [0]*12)
            flat_structure = tariff_data['flatdemandstructure']
            
            if analysis_period == "Single Month":
                # Single month - show one input
                flat_tier = flatdemandmonths[selected_month] if selected_month < len(flatdemandmonths) else 0
                
                # Get rate structure for this tier
                if flat_tier < len(flat_structure):
                    flat_rate = flat_structure[flat_tier][0].get('rate', 0)
                    flat_adj = flat_structure[flat_tier][0].get('adj', 0)
                else:
                    flat_rate = flat_structure[0][0].get('rate', 0)
                    flat_adj = flat_structure[0][0].get('adj', 0)
                
                total_flat_rate = flat_rate + flat_adj
                
                # Build help text
                help_text = f"Base rate: ${flat_rate:.2f}/kW" + (f" + Adjustment: ${flat_adj:.2f}/kW" if flat_adj != 0 else "")
                if len(flat_structure) > 1:
                    help_text += f"\n\n(Rate for {month_names[selected_month]} - tier {flat_tier})"
                if has_tou_demand:
                    help_text += "\n\nNote: If entered value is less than highest TOU demand, it will be auto-adjusted upward"
                
                flat_demand_value = st.number_input(
                    f"Maximum Monthly Demand (${total_flat_rate:.2f}/kW)",
                    min_value=0.0,
                    value=0.0,
                    step=1.0,
                    key="lf_flat_demand",
                    help=help_text
                )
                
                # Auto-adjust flat demand to be at least max TOU demand
                if has_tou_demand:
                    tou_demands = [v for k, v in demand_inputs.items() if k.startswith('tou_demand_') and isinstance(v, (int, float)) and v > 0]
                    if tou_demands:
                        max_tou_demand = max(tou_demands)
                        if flat_demand_value == 0:
                            st.info(f"ℹ️ Note: Flat demand automatically set to {max_tou_demand:.1f} kW to match the highest TOU demand.")
                            demand_inputs['flat_demand'] = max_tou_demand
                        elif flat_demand_value < max_tou_demand:
                            st.info(f"ℹ️ Note: Flat demand ({flat_demand_value:.1f} kW) is less than highest TOU demand ({max_tou_demand:.1f} kW). Using {max_tou_demand:.1f} kW for calculations.")
                            demand_inputs['flat_demand'] = max_tou_demand
                        else:
                            demand_inputs['flat_demand'] = flat_demand_value
                    else:
                        demand_inputs['flat_demand'] = flat_demand_value
                else:
                    demand_inputs['flat_demand'] = flat_demand_value
            else:
                # Full year - count how many months each tier applies
                tier_month_counts = {}
                for month_tier in flatdemandmonths:
                    tier_month_counts[month_tier] = tier_month_counts.get(month_tier, 0) + 1
                
                # Show info about tier distribution
                if len(tier_month_counts) > 1:
                    st.info(f"ℹ️ This tariff has {len(tier_month_counts)} different flat demand rate tiers across the year. Enter the same demand value for all tiers (will be applied to appropriate months).")
                
                # Single input for flat demand (applies to all tiers)
                flat_demand_value = st.number_input(
                    f"Maximum Monthly Demand (kW)",
                    min_value=0.0,
                    value=0.0,
                    step=1.0,
                    key="lf_flat_demand_annual",
                    help="This demand value will be applied to all months, but charged at the appropriate rate for each month"
                )
                
                # Auto-adjust flat demand to be at least max TOU demand
                if has_tou_demand:
                    tou_demands = [v for k, v in demand_inputs.items() if k.startswith('tou_demand_') and isinstance(v, (int, float)) and v > 0]
                    if tou_demands:
                        max_tou_demand = max(tou_demands)
                        if flat_demand_value == 0:
                            st.info(f"ℹ️ Note: Flat demand automatically set to {max_tou_demand:.1f} kW to match the highest TOU demand.")
                            demand_inputs['flat_demand'] = max_tou_demand
                        elif flat_demand_value < max_tou_demand:
                            st.info(f"ℹ️ Note: Flat demand ({flat_demand_value:.1f} kW) is less than highest TOU demand ({max_tou_demand:.1f} kW). Using {max_tou_demand:.1f} kW for calculations.")
                            demand_inputs['flat_demand'] = max_tou_demand
                        else:
                            demand_inputs['flat_demand'] = flat_demand_value
                    else:
                        demand_inputs['flat_demand'] = flat_demand_value
                else:
                    demand_inputs['flat_demand'] = flat_demand_value
                
                # Store tier information for later use in calculations
                demand_inputs['_flat_tier_month_counts'] = tier_month_counts
        
        st.markdown("---")
        
        # Energy rate structure inputs
        st.markdown("##### 💡 Energy Distribution")
        
        energy_structure = tariff_data.get('energyratestructure', [])
        energy_labels = tariff_data.get('energytoulabels', [])
        num_energy_periods = len(energy_structure)
        
        # Get active periods and hour percentages based on analysis period
        if analysis_period == "Single Month":
            active_periods = _get_active_energy_periods_for_month(tariff_data, selected_month)
            period_hour_percentages = _calculate_period_hour_percentages(tariff_data, selected_month)
            energy_period_month_counts = {p: 1 for p in active_periods}
            time_label = f"{month_names[selected_month]}'s hours"
            
            # Show info about which periods are active
            if len(active_periods) < num_energy_periods:
                inactive_periods = set(range(num_energy_periods)) - active_periods
                inactive_labels = [energy_labels[i] if i < len(energy_labels) else f"Period {i}" 
                                 for i in sorted(inactive_periods)]
                st.info(f"ℹ️ Only showing periods present in {month_names[selected_month]}. "
                       f"The following periods are not scheduled this month: {', '.join(inactive_labels)}")
        else:
            # Full year - get all periods active in any month
            energy_period_month_counts = _get_active_energy_periods_for_year(tariff_data)
            active_periods = set(energy_period_month_counts.keys())
            period_hour_percentages = _calculate_annual_period_hour_percentages(tariff_data)
            time_label = "year's hours"
            
            if len(active_periods) < num_energy_periods:
                st.info(f"ℹ️ Showing all energy periods active during the year.")
        
        st.markdown("Specify the percentage of energy consumption in each rate period (must sum to 100%):")
        st.caption("💡 **Note:** Your energy distribution determines the maximum **physically possible** load factor. For each period, the constraint is: LF ≤ (hour %) / (energy %). Example: if a period represents 20% of hours but you allocate 40% of energy there, max LF = 50% (otherwise power would exceed peak demand). Beyond the max physical LF, calculations use hour percentages (representing constant 24/7 operation at 100% LF).")
        
        energy_percentages = {}
        total_percentage = 0.0
        
        # Only show active periods
        active_periods_list = sorted(list(active_periods))
        
        # Fallback: if no periods found in schedule, use all periods from energy structure
        if not active_periods_list and num_energy_periods > 0:
            st.warning(f"⚠️ No energy periods found in the schedule. Using all {num_energy_periods} period(s) from energy rate structure.")
            active_periods_list = list(range(num_energy_periods))
            # Calculate hour percentages assuming equal distribution
            if not period_hour_percentages:
                period_hour_percentages = {i: 100.0 / num_energy_periods for i in range(num_energy_periods)}
        
        if not active_periods_list:
            st.error(f"⚠️ No energy rate structure found in this tariff.")
            st.write("This tariff does not appear to have energy rate information configured.")
        else:
            # Create columns for energy inputs
            cols = st.columns(min(len(active_periods_list), 3))
            for idx, i in enumerate(active_periods_list):
                label = energy_labels[i] if i < len(energy_labels) else f"Energy Period {i}"
                rate = energy_structure[i][0].get('rate', 0)
                adj = energy_structure[i][0].get('adj', 0)
                total_rate = rate + adj
                
                # Get the hour percentage for this period
                hour_pct = period_hour_percentages.get(i, 0)
                
                with cols[idx % min(len(active_periods_list), 3)]:
                    # Show period presence percentage
                    st.caption(f"📊 {hour_pct:.1f}% of {time_label}")
                    
                    # Default first active period to 100%, others to 0
                    default_value = 100.0 if idx == 0 else 0.0
                    
                    help_text = f"Base rate: ${rate:.4f}/kWh" + (f" + Adjustment: ${adj:.4f}/kWh" if adj != 0 else "")
                    help_text += f"\n\nThis period is present for {hour_pct:.1f}% of {time_label}"
                    if analysis_period == "Full Year":
                        month_count = energy_period_month_counts.get(i, 0)
                        help_text += f"\nActive in {month_count} months"
                    
                    energy_percentages[i] = st.number_input(
                        f"{label}\n(${total_rate:.4f}/kWh)",
                        min_value=0.0,
                        max_value=100.0,
                        value=default_value,
                        step=1.0,
                        key=f"lf_energy_pct_{i}_{analysis_period}",
                        help=help_text
                    )
                    total_percentage += energy_percentages[i]
        
        # Show percentage total
        percentage_color = "green" if abs(total_percentage - 100.0) < 0.01 else "red"
        st.markdown(f"**Total: <span style='color:{percentage_color}'>{total_percentage:.1f}%</span>**", unsafe_allow_html=True)
        
        if abs(total_percentage - 100.0) >= 0.01:
            st.warning("⚠️ Energy percentages must sum to 100%")
        
        st.markdown("---")
        
        # Calculate button
        if st.button("🧮 Calculate Effective Rates", type="primary", key="calc_load_factor"):
            # Validation checks
            validation_passed = True
            
            # Check energy percentages sum to 100%
            if abs(total_percentage - 100.0) >= 0.01:
                st.error("❌ Energy percentages must sum to 100% before calculating")
                validation_passed = False
            
            # Proceed with calculation if validation passed
            if validation_passed:
                # Calculate max valid LF to inform the user (use already calculated period_hour_percentages)
                max_valid_lf_for_msg = 1.0
                for period_idx, energy_pct in energy_percentages.items():
                    if energy_pct > 0 and period_idx in period_hour_percentages:
                        hour_pct = period_hour_percentages[period_idx]
                        if hour_pct > 0:
                            period_max_lf = hour_pct / energy_pct
                            max_valid_lf_for_msg = min(max_valid_lf_for_msg, period_max_lf)
                        else:
                            max_valid_lf_for_msg = 0.0
                max_valid_lf_for_msg = min(max_valid_lf_for_msg, 1.0)
                
                # Show info about load factor range
                num_points = int(max_valid_lf_for_msg * 100)
                time_context = "month" if analysis_period == "Single Month" else "year"
                if max_valid_lf_for_msg < 1.0:
                    st.info(f"ℹ️ Maximum physically possible load factor: **{max_valid_lf_for_msg*100:.1f}%** (based on your energy distribution). "
                           f"Calculations from 1% to {max_valid_lf_for_msg*100:.1f}% LF use your specified energy distribution ({num_points} data points). "
                           f"Additionally, 100% LF is calculated using hour percentages (constant 24/7 operation at full power).")
                else:
                    st.info(f"ℹ️ Your energy distribution allows calculations up to 100% load factor ({num_points} data points). "
                           f"At 100% LF, energy distribution matches hour percentages (constant 24/7 operation).")
                
                if analysis_period == "Single Month":
                    results = _calculate_load_factor_rates(
                        tariff_data=tariff_data,
                        demand_inputs=demand_inputs,
                        energy_percentages=energy_percentages,
                        selected_month=selected_month,
                        has_tou_demand=has_tou_demand,
                        has_flat_demand=has_flat_demand
                    )
                    _display_load_factor_results(
                        results, 
                        options, 
                        tariff_data=tariff_data,
                        demand_inputs=demand_inputs,
                        energy_percentages=energy_percentages,
                        selected_month=selected_month,
                        has_tou_demand=has_tou_demand,
                        has_flat_demand=has_flat_demand,
                        analysis_period=analysis_period
                    )
                else:
                    # Full year analysis
                    results = _calculate_annual_load_factor_rates(
                        tariff_data=tariff_data,
                        demand_inputs=demand_inputs,
                        energy_percentages=energy_percentages,
                        has_tou_demand=has_tou_demand,
                        has_flat_demand=has_flat_demand,
                        demand_period_month_counts=demand_period_month_counts,
                        energy_period_month_counts=energy_period_month_counts
                    )
                    _display_load_factor_results(
                        results, 
                        options, 
                        tariff_data=tariff_data,
                        demand_inputs=demand_inputs,
                        energy_percentages=energy_percentages,
                        selected_month=None,  # Not applicable for annual
                        has_tou_demand=has_tou_demand,
                        has_flat_demand=has_flat_demand,
                        analysis_period=analysis_period,
                        demand_period_month_counts=demand_period_month_counts,
                        energy_period_month_counts=energy_period_month_counts
                    )


def _calculate_load_factor_rates(
    tariff_data: Dict[str, Any],
    demand_inputs: Dict[str, float],
    energy_percentages: Dict[int, float],
    selected_month: int,
    has_tou_demand: bool,
    has_flat_demand: bool
) -> pd.DataFrame:
    """
    Calculate effective utility rates for different load factors.
    
    Args:
        tariff_data: Tariff data dictionary
        demand_inputs: Dictionary of demand values for each period
        energy_percentages: Dictionary of energy percentages for each period
        selected_month: Month index (0-11)
        has_tou_demand: Whether tariff has TOU demand charges
        has_flat_demand: Whether tariff has flat demand charges
    
    Returns:
        DataFrame with load factor analysis results
    """
    
    # Calculate the maximum physically possible load factor based on user's energy distribution
    # For each period: power_required = (energy_pct / hour_pct) * avg_load
    # This can't exceed peak_demand, so: LF <= hour_pct / energy_pct for each period
    # Maximum LF is the minimum of these ratios across all periods with energy
    period_hour_pcts = _calculate_period_hour_percentages(tariff_data, selected_month)
    
    max_valid_lf = 1.0  # Start at 100%
    for period_idx, energy_pct in energy_percentages.items():
        if energy_pct > 0 and period_idx in period_hour_pcts:
            hour_pct = period_hour_pcts[period_idx]
            if hour_pct > 0:
                # This period constrains max LF to hour_pct / energy_pct
                period_max_lf = hour_pct / energy_pct
                max_valid_lf = min(max_valid_lf, period_max_lf)
            else:
                # Period has energy but 0 hours - physically impossible
                max_valid_lf = 0.0
    
    # Cap at 100% (in case user under-allocates energy everywhere)
    max_valid_lf = min(max_valid_lf, 1.0)
    
    # Generate load factors from 1% up to (but not exceeding) max_valid_lf in 1% increments
    load_factors = []
    for i in range(1, 101):  # 1% to 100%
        lf = i / 100.0
        if lf <= max_valid_lf:
            load_factors.append(lf)
        elif lf == 1.00:
            # Always include 100% as final point (uses hour percentages)
            load_factors.append(1.00)
            break
        else:
            # Exceeded max_valid_lf, add 100% and stop
            load_factors.append(1.00)
            break
    
    # Hours in the selected month (approximate)
    hours_in_month = [744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744]
    hours = hours_in_month[selected_month]
    
    # Get fixed charge
    fixed_charge = tariff_data.get('fixedchargefirstmeter', 0)
    
    # Get energy rate structure
    energy_structure = tariff_data.get('energyratestructure', [])
    
    results = []
    
    for lf in load_factors:
        # Calculate peak demand (use the maximum of all specified demands)
        all_demands = [v for k, v in demand_inputs.items() if not k.startswith('_') and isinstance(v, (int, float)) and v > 0]
        peak_demand = max(all_demands) if all_demands else 0
        
        if peak_demand == 0:
            # If no demand specified, can't calculate
            avg_load = 0
            total_energy = 0
        else:
            # Calculate average load from load factor
            # Load Factor = Average Load / Peak Load
            avg_load = peak_demand * lf
            
            # Calculate total energy
            total_energy = avg_load * hours
        
        # Calculate demand charges
        total_demand_cost = 0
        
        # TOU demand charges
        if has_tou_demand:
            demand_structure = tariff_data.get('demandratestructure', [])
            for i, structure in enumerate(demand_structure):
                demand_key = f'tou_demand_{i}'
                if demand_key in demand_inputs and demand_inputs[demand_key] > 0:
                    rate = structure[0].get('rate', 0)
                    adj = structure[0].get('adj', 0)
                    # Demand charge is based on the specified demand for this period
                    total_demand_cost += demand_inputs[demand_key] * (rate + adj)
        
        # Flat demand charge
        if has_flat_demand:
            if 'flat_demand' in demand_inputs and demand_inputs['flat_demand'] > 0:
                # Get the correct flat demand structure based on selected month
                flatdemandmonths = tariff_data.get('flatdemandmonths', [0]*12)
                flat_tier = flatdemandmonths[selected_month] if selected_month < len(flatdemandmonths) else 0
                
                flat_structure_list = tariff_data['flatdemandstructure']
                if flat_tier < len(flat_structure_list):
                    flat_structure = flat_structure_list[flat_tier][0]
                else:
                    flat_structure = flat_structure_list[0][0]
                
                rate = flat_structure.get('rate', 0)
                adj = flat_structure.get('adj', 0)
                total_demand_cost += demand_inputs['flat_demand'] * (rate + adj)
        
        # Calculate energy charges
        total_energy_cost = 0
        if total_energy > 0:
            # At load factors above max_valid_lf, energy distribution must match the TOU schedule
            # (facility must operate during periods where user allocated 0% energy)
            # Below max_valid_lf, use user-specified distribution (operational flexibility exists)
            if lf > max_valid_lf + 0.005:  # Small tolerance for floating point
                # Use period hour percentages (forced operation in all periods)
                effective_energy_pcts = period_hour_pcts
            else:
                # Use user-specified energy percentages (operational flexibility)
                effective_energy_pcts = energy_percentages
            
            for period_idx, percentage in effective_energy_pcts.items():
                if percentage > 0 and period_idx < len(energy_structure):
                    # Energy in this period
                    period_energy = total_energy * (percentage / 100.0)
                    
                    # Get rate for this period (tier 0 for simplicity)
                    rate = energy_structure[period_idx][0].get('rate', 0)
                    adj = energy_structure[period_idx][0].get('adj', 0)
                    
                    total_energy_cost += period_energy * (rate + adj)
        
        # Total cost
        total_cost = total_demand_cost + total_energy_cost + fixed_charge
        
        # Effective rate ($/kWh)
        effective_rate = total_cost / total_energy if total_energy > 0 else 0
        
        results.append({
            'Load Factor': f"{lf * 100:.0f}%",
            'Load Factor Value': lf,
            'Peak Demand (kW)': peak_demand,
            'Average Load (kW)': avg_load,
            'Total Energy (kWh)': total_energy,
            'Demand Charges ($)': total_demand_cost,
            'Energy Charges ($)': total_energy_cost,
            'Fixed Charges ($)': fixed_charge,
            'Total Cost ($)': total_cost,
            'Effective Rate ($/kWh)': effective_rate
        })
    
    return pd.DataFrame(results)


def _calculate_annual_load_factor_rates(
    tariff_data: Dict[str, Any],
    demand_inputs: Dict[str, float],
    energy_percentages: Dict[int, float],
    has_tou_demand: bool,
    has_flat_demand: bool,
    demand_period_month_counts: Dict[int, int],
    energy_period_month_counts: Dict[int, int]
) -> pd.DataFrame:
    """
    Calculate effective utility rates for different load factors over a full year.
    
    Args:
        tariff_data: Tariff data dictionary
        demand_inputs: Dictionary of demand values for each period
        energy_percentages: Dictionary of energy percentages for each period
        has_tou_demand: Whether tariff has TOU demand charges
        has_flat_demand: Whether tariff has flat demand charges
        demand_period_month_counts: Dict mapping demand period index to # months active
        energy_period_month_counts: Dict mapping energy period index to # months active
    
    Returns:
        DataFrame with annual load factor analysis results
    """
    import calendar
    
    # Calculate the maximum physically possible load factor using annual hour percentages
    period_hour_pcts_annual = _calculate_annual_period_hour_percentages(tariff_data)
    
    max_valid_lf = 1.0  # Start at 100%
    for period_idx, energy_pct in energy_percentages.items():
        if energy_pct > 0 and period_idx in period_hour_pcts_annual:
            hour_pct = period_hour_pcts_annual[period_idx]
            if hour_pct > 0:
                period_max_lf = hour_pct / energy_pct
                max_valid_lf = min(max_valid_lf, period_max_lf)
            else:
                max_valid_lf = 0.0
    
    max_valid_lf = min(max_valid_lf, 1.0)
    
    # Generate load factors from 1% up to max_valid_lf in 1% increments
    load_factors = []
    for i in range(1, 101):  # 1% to 100%
        lf = i / 100.0
        if lf <= max_valid_lf:
            load_factors.append(lf)
        elif lf == 1.00:
            load_factors.append(1.00)
            break
        else:
            load_factors.append(1.00)
            break
    
    # Get fixed charge (annual total)
    fixed_charge_monthly = tariff_data.get('fixedchargefirstmeter', 0)
    fixed_charge_annual = fixed_charge_monthly * 12
    
    # Get rate structures
    energy_structure = tariff_data.get('energyratestructure', [])
    flatdemandmonths = tariff_data.get('flatdemandmonths', [0]*12)
    flat_structure_list = tariff_data.get('flatdemandstructure', []) if has_flat_demand else []
    demand_structure = tariff_data.get('demandratestructure', []) if has_tou_demand else []
    
    # Calculate peak demand
    all_demands = [v for k, v in demand_inputs.items() if (k.startswith('tou_demand_') or k == 'flat_demand') and isinstance(v, (int, float))]
    all_demands = [v for v in all_demands if v > 0]
    peak_demand = max(all_demands) if all_demands else 0
    
    results = []
    
    for lf in load_factors:
        if peak_demand == 0:
            avg_load = 0
            total_energy_annual = 0
        else:
            avg_load = peak_demand * lf
        
        # Aggregate annual values
        total_energy_annual = 0
        total_demand_cost_annual = 0
        total_energy_cost_annual = 0
        
        # Calculate for each month and aggregate
        for month in range(12):
            # Hours in this month (approximate)
            hours_in_month = [744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744]
            hours = hours_in_month[month]
            
            # Monthly energy
            month_energy = avg_load * hours if peak_demand > 0 else 0
            total_energy_annual += month_energy
            
            # Get active periods for this month
            active_demand_periods = _get_active_demand_periods_for_month(tariff_data, month)
            active_energy_periods = _get_active_energy_periods_for_month(tariff_data, month)
            period_hour_pcts_month = _calculate_period_hour_percentages(tariff_data, month)
            
            # TOU demand charges (only for active periods in this month)
            if has_tou_demand:
                for i, structure in enumerate(demand_structure):
                    if i in active_demand_periods:
                        demand_key = f'tou_demand_{i}'
                        if demand_key in demand_inputs and demand_inputs[demand_key] > 0:
                            rate = structure[0].get('rate', 0)
                            adj = structure[0].get('adj', 0)
                            total_demand_cost_annual += demand_inputs[demand_key] * (rate + adj)
            
            # Flat demand charge
            if has_flat_demand and 'flat_demand' in demand_inputs and demand_inputs['flat_demand'] > 0:
                flat_tier = flatdemandmonths[month] if month < len(flatdemandmonths) else 0
                if flat_tier < len(flat_structure_list):
                    flat_structure = flat_structure_list[flat_tier][0]
                else:
                    flat_structure = flat_structure_list[0][0]
                
                rate = flat_structure.get('rate', 0)
                adj = flat_structure.get('adj', 0)
                total_demand_cost_annual += demand_inputs['flat_demand'] * (rate + adj)
            
            # Energy charges for this month
            if month_energy > 0:
                # Determine effective energy percentages
                if lf > max_valid_lf + 0.005:
                    effective_energy_pcts = period_hour_pcts_month
                else:
                    # Use user-specified, but only for active periods this month
                    effective_energy_pcts = {k: v for k, v in energy_percentages.items() if k in active_energy_periods}
                    # Renormalize to 100% for active periods only
                    total_active_pct = sum(effective_energy_pcts.values())
                    if total_active_pct > 0:
                        effective_energy_pcts = {k: (v / total_active_pct * 100) for k, v in effective_energy_pcts.items()}
                    else:
                        # Fallback to hour percentages if no active periods have energy
                        effective_energy_pcts = period_hour_pcts_month
                
                for period_idx, percentage in effective_energy_pcts.items():
                    if percentage > 0 and period_idx < len(energy_structure):
                        period_energy = month_energy * (percentage / 100.0)
                        rate = energy_structure[period_idx][0].get('rate', 0)
                        adj = energy_structure[period_idx][0].get('adj', 0)
                        total_energy_cost_annual += period_energy * (rate + adj)
        
        # Total annual cost
        total_cost_annual = total_demand_cost_annual + total_energy_cost_annual + fixed_charge_annual
        
        # Effective rate ($/kWh)
        effective_rate = total_cost_annual / total_energy_annual if total_energy_annual > 0 else 0
        
        results.append({
            'Load Factor': f"{lf * 100:.0f}%",
            'Load Factor Value': lf,
            'Peak Demand (kW)': peak_demand,
            'Average Load (kW)': avg_load,
            'Total Energy (kWh)': total_energy_annual,
            'Demand Charges ($)': total_demand_cost_annual,
            'Energy Charges ($)': total_energy_cost_annual,
            'Fixed Charges ($)': fixed_charge_annual,
            'Total Cost ($)': total_cost_annual,
            'Effective Rate ($/kWh)': effective_rate
        })
    
    return pd.DataFrame(results)


def _calculate_comprehensive_load_factor_breakdown(
    results: pd.DataFrame,
    tariff_data: Dict[str, Any],
    demand_inputs: Dict[str, float],
    energy_percentages: Dict[int, float],
    selected_month: int,
    has_tou_demand: bool,
    has_flat_demand: bool,
    analysis_period: str = "Single Month",
    demand_period_month_counts: Dict[int, int] = None,
    energy_period_month_counts: Dict[int, int] = None
) -> pd.DataFrame:
    """
    Calculate comprehensive breakdown table with all load factors and detailed rate components.
    
    Args:
        results: Original results DataFrame
        tariff_data: Tariff data dictionary
        demand_inputs: Dictionary of demand values for each period
        energy_percentages: Dictionary of energy percentages for each period
        selected_month: Month index (0-11, or None for annual)
        has_tou_demand: Whether tariff has TOU demand charges
        has_flat_demand: Whether tariff has flat demand charges
        analysis_period: "Single Month" or "Full Year"
        demand_period_month_counts: Dict mapping demand period to # months active (for annual)
        energy_period_month_counts: Dict mapping energy period to # months active (for annual)
    
    Returns:
        DataFrame with comprehensive breakdown for all load factors
    """
    
    # Calculate the maximum physically possible load factor based on user's energy distribution
    if analysis_period == "Single Month":
        period_hour_pcts = _calculate_period_hour_percentages(tariff_data, selected_month)
    else:
        period_hour_pcts = _calculate_annual_period_hour_percentages(tariff_data)
    
    max_valid_lf = 1.0
    for period_idx, energy_pct in energy_percentages.items():
        if energy_pct > 0 and period_idx in period_hour_pcts:
            hour_pct = period_hour_pcts[period_idx]
            if hour_pct > 0:
                period_max_lf = hour_pct / energy_pct
                max_valid_lf = min(max_valid_lf, period_max_lf)
            else:
                max_valid_lf = 0.0
    max_valid_lf = min(max_valid_lf, 1.0)
    
    # Get all energy and demand structures
    energy_structure = tariff_data.get('energyratestructure', [])
    energy_labels = tariff_data.get('energyweekdaylabels', [])
    
    # Calculate peak demand (filter out metadata keys starting with underscore)
    all_demands = [v for k, v in demand_inputs.items() if not k.startswith('_') and isinstance(v, (int, float)) and v > 0]
    peak_demand = max(all_demands) if all_demands else 0
    
    # Build comprehensive rows
    comprehensive_rows = []
    
    for idx, row in results.iterrows():
        load_factor = row['Load Factor Value']
        avg_load = row['Average Load (kW)']
        total_energy = row['Total Energy (kWh)']
        
        # Start with base columns
        comprehensive_row = {
            'Load Factor': row['Load Factor'],
            'Average Load (kW)': avg_load,
            'Total Energy (kWh)': total_energy
        }
        
        # Determine which energy distribution to use
        if load_factor > max_valid_lf + 0.005:  # Small tolerance for floating point
            # Use period hour percentages (forced operation in all periods)
            effective_energy_pcts = period_hour_pcts
        else:
            # Use user-specified energy percentages (operational flexibility)
            effective_energy_pcts = energy_percentages
        
        # Add energy period columns (include ALL periods, not just active ones)
        for period_idx in range(len(energy_structure)):
            period_label = energy_labels[period_idx] if period_idx < len(energy_labels) else f"Period {period_idx}"
            
            # Get rate for this period (always show rate even if not used)
            rate = energy_structure[period_idx][0].get('rate', 0)
            adj = energy_structure[period_idx][0].get('adj', 0)
            total_rate = rate + adj
            
            # Get percentage for this period (0 if not present)
            percentage = effective_energy_pcts.get(period_idx, 0)
            period_energy = total_energy * (percentage / 100.0) if percentage > 0 else 0
            
            if period_energy > 0:
                period_cost = period_energy * total_rate
            else:
                period_cost = 0
            
            comprehensive_row[f'{period_label} (kWh)'] = period_energy
            comprehensive_row[f'{period_label} Rate ($/kWh)'] = total_rate
            comprehensive_row[f'{period_label} Cost ($)'] = period_cost
        
        # Add TOU demand columns (include ALL periods)
        if has_tou_demand:
            demand_structure = tariff_data.get('demandratestructure', [])
            demand_labels = tariff_data.get('demandtoulabels', [])
            
            for i in range(len(demand_structure)):
                period_label = demand_labels[i] if i < len(demand_labels) else f"TOU Period {i}"
                demand_key = f'tou_demand_{i}'
                
                # Get rate for this period (always show rate even if not used)
                rate = demand_structure[i][0].get('rate', 0)
                adj = demand_structure[i][0].get('adj', 0)
                total_rate = rate + adj
                
                if demand_key in demand_inputs:
                    demand_value = demand_inputs[demand_key]
                    if demand_value > 0:
                        # For annual, multiply cost by number of months active
                        if analysis_period == "Full Year" and demand_period_month_counts:
                            num_months = demand_period_month_counts.get(i, 0)
                            demand_cost = demand_value * total_rate * num_months
                        else:
                            demand_cost = demand_value * total_rate
                    else:
                        demand_cost = 0
                else:
                    demand_value = 0
                    demand_cost = 0
                
                # For annual analysis, add # Months column
                if analysis_period == "Full Year" and demand_period_month_counts:
                    num_months = demand_period_month_counts.get(i, 0)
                    comprehensive_row[f'{period_label} # Months'] = num_months
                
                comprehensive_row[f'{period_label} Demand (kW)'] = demand_value
                comprehensive_row[f'{period_label} Rate ($/kW)'] = total_rate
                comprehensive_row[f'{period_label} Demand Cost ($)'] = demand_cost
        
        # Add flat demand columns
        if has_flat_demand:
            flatdemandmonths = tariff_data.get('flatdemandmonths', [0]*12)
            flat_structure_list = tariff_data['flatdemandstructure']
            
            if analysis_period == "Single Month":
                # Single month - one set of columns
                flat_tier = flatdemandmonths[selected_month] if selected_month < len(flatdemandmonths) else 0
                
                if flat_tier < len(flat_structure_list):
                    flat_structure = flat_structure_list[flat_tier][0]
                else:
                    flat_structure = flat_structure_list[0][0]
                
                rate = flat_structure.get('rate', 0)
                adj = flat_structure.get('adj', 0)
                total_rate = rate + adj
                
                if 'flat_demand' in demand_inputs:
                    demand_value = demand_inputs['flat_demand']
                    if demand_value > 0:
                        demand_cost = demand_value * total_rate
                    else:
                        demand_cost = 0
                else:
                    demand_value = 0
                    demand_cost = 0
                
                comprehensive_row['Flat Demand (kW)'] = demand_value
                comprehensive_row['Flat Demand Rate ($/kW)'] = total_rate
                comprehensive_row['Flat Demand Cost ($)'] = demand_cost
            else:
                # Annual - separate columns for each unique tier
                # Count months per tier
                tier_month_counts = {}
                for month_tier in flatdemandmonths:
                    tier_month_counts[month_tier] = tier_month_counts.get(month_tier, 0) + 1
                
                # Create columns for each tier
                for tier_idx in sorted(tier_month_counts.keys()):
                    if tier_idx < len(flat_structure_list):
                        flat_structure = flat_structure_list[tier_idx][0]
                    else:
                        flat_structure = flat_structure_list[0][0]
                    
                    rate = flat_structure.get('rate', 0)
                    adj = flat_structure.get('adj', 0)
                    total_rate = rate + adj
                    num_months = tier_month_counts[tier_idx]
                    
                    if 'flat_demand' in demand_inputs:
                        demand_value = demand_inputs['flat_demand']
                        if demand_value > 0:
                            demand_cost = demand_value * total_rate * num_months
                        else:
                            demand_cost = 0
                    else:
                        demand_value = 0
                        demand_cost = 0
                    
                    # Create tier-specific column names
                    tier_label = f"Flat Demand (Tier {tier_idx})"
                    comprehensive_row[f'{tier_label} # Months'] = num_months
                    comprehensive_row[f'{tier_label} Demand (kW)'] = demand_value
                    comprehensive_row[f'{tier_label} Rate ($/kW)'] = total_rate
                    comprehensive_row[f'{tier_label} Cost ($)'] = demand_cost
        
        # Add summary columns
        comprehensive_row['Total Demand Charges ($)'] = row['Demand Charges ($)']
        comprehensive_row['Total Energy Charges ($)'] = row['Energy Charges ($)']
        comprehensive_row['Fixed Charges ($)'] = row['Fixed Charges ($)']
        comprehensive_row['Total Cost ($)'] = row['Total Cost ($)']
        comprehensive_row['Effective Rate ($/kWh)'] = row['Effective Rate ($/kWh)']
        
        comprehensive_rows.append(comprehensive_row)
    
    return pd.DataFrame(comprehensive_rows)


def _display_load_factor_results(
    results: pd.DataFrame, 
    options: Dict[str, Any],
    tariff_data: Dict[str, Any] = None,
    demand_inputs: Dict[str, float] = None,
    energy_percentages: Dict[int, float] = None,
    selected_month: int = 0,
    has_tou_demand: bool = False,
    has_flat_demand: bool = False,
    analysis_period: str = "Single Month",
    demand_period_month_counts: Dict[int, int] = None,
    energy_period_month_counts: Dict[int, int] = None
) -> None:
    """
    Display load factor analysis results.
    
    Args:
        results: DataFrame with analysis results
        options: Display options
        tariff_data: Tariff data dictionary (optional, for detailed breakdown)
        demand_inputs: Dictionary of demand values for each period (optional)
        energy_percentages: Dictionary of energy percentages for each period (optional)
        selected_month: Month index 0-11 (optional, None for annual analysis)
        has_tou_demand: Whether tariff has TOU demand charges (optional)
        has_flat_demand: Whether tariff has flat demand charges (optional)
        analysis_period: "Single Month" or "Full Year"
        demand_period_month_counts: Dict mapping demand period to # months active (for annual)
        energy_period_month_counts: Dict mapping energy period to # months active (for annual)
    """
    
    st.markdown("### 📊 Load Factor Analysis Results")
    
    if results['Peak Demand (kW)'].iloc[0] == 0:
        st.warning("⚠️ No demand values specified. Please enter at least one demand value to calculate effective rates.")
        return
    
    # Display summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        peak_demand = results['Peak Demand (kW)'].iloc[0]
        st.metric("Peak Demand", f"{peak_demand:.1f} kW")
    
    with col2:
        min_rate = results['Effective Rate ($/kWh)'].min()
        st.metric("Lowest Effective Rate", f"${min_rate:.4f}/kWh", 
                 delta=f"at {results.loc[results['Effective Rate ($/kWh)'].idxmin(), 'Load Factor']}")
    
    with col3:
        max_rate = results['Effective Rate ($/kWh)'].max()
        st.metric("Highest Effective Rate", f"${max_rate:.4f}/kWh",
                 delta=f"at {results.loc[results['Effective Rate ($/kWh)'].idxmax(), 'Load Factor']}")
    
    st.markdown("---")
    
    # Display results table
    st.markdown("#### 📋 Detailed Results Table")
    
    display_df = results[[
        'Load Factor', 'Average Load (kW)', 'Total Energy (kWh)', 
        'Demand Charges ($)', 'Energy Charges ($)', 'Fixed Charges ($)', 
        'Total Cost ($)', 'Effective Rate ($/kWh)'
    ]].copy()
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Load Factor": st.column_config.TextColumn("Load Factor", width="small"),
            "Average Load (kW)": st.column_config.NumberColumn("Avg Load (kW)", format="%.2f"),
            "Total Energy (kWh)": st.column_config.NumberColumn("Total Energy (kWh)", format="%.0f"),
            "Demand Charges ($)": st.column_config.NumberColumn("Demand ($)", format="$%.2f"),
            "Energy Charges ($)": st.column_config.NumberColumn("Energy ($)", format="$%.2f"),
            "Fixed Charges ($)": st.column_config.NumberColumn("Fixed ($)", format="$%.2f"),
            "Total Cost ($)": st.column_config.NumberColumn("Total ($)", format="$%.2f"),
            "Effective Rate ($/kWh)": st.column_config.NumberColumn("Effective Rate", format="$%.4f")
        }
    )
    
    # Add download button for Detailed Results Table
    buffer = BytesIO()
    
    # Create a copy for Excel with load factor as percentage
    excel_df = display_df.copy()
    if 'Load Factor' in excel_df.columns:
        # Convert load factor string to numeric percentage (e.g., "50%" -> 0.50)
        excel_df['Load Factor'] = excel_df['Load Factor'].str.replace('%', '').astype(float) / 100
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        excel_df.to_excel(writer, sheet_name='Load Factor Analysis', index=False)
        
        # Get the worksheet to apply formatting
        worksheet = writer.sheets['Load Factor Analysis']
        
        # Apply formatting to columns
        from openpyxl.styles import numbers
        headers = list(excel_df.columns)
        
        for col_idx, col_name in enumerate(headers, start=1):
            for row_idx in range(2, len(excel_df) + 2):
                cell = worksheet.cell(row=row_idx, column=col_idx)
                
                # Percentage format for Load Factor
                if col_name == 'Load Factor':
                    cell.number_format = '0%'
                # Accounting format for currency columns (whole numbers)
                elif col_name in ['Demand Charges ($)', 'Energy Charges ($)', 'Fixed Charges ($)', 'Total Cost ($)']:
                    cell.number_format = '_($* #,##0_);_($* (#,##0);_($* "-"_);_(@_)'
                elif col_name == 'Effective Rate ($/kWh)':
                    cell.number_format = '_($* #,##0.0000_);_($* (#,##0.0000);_($* "-"????_);_(@_)'
                elif col_name == 'Total Energy (kWh)':
                    cell.number_format = '#,##0'
                elif col_name == 'Average Load (kW)':
                    cell.number_format = '#,##0'
    
    buffer.seek(0)
    
    st.download_button(
        label="📥 Download Detailed Results as Excel",
        data=buffer,
        file_name="load_factor_detailed_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_detailed_results"
    )
    
    # Visualization
    st.markdown("#### 📈 Effective Rate vs Load Factor")
    
    dark_mode = options.get('dark_mode', False)
    
    # Get comprehensive breakdown for energy period details
    if tariff_data is not None and demand_inputs is not None and energy_percentages is not None:
        comprehensive_df = _calculate_comprehensive_load_factor_breakdown(
            results=results,
            tariff_data=tariff_data,
            demand_inputs=demand_inputs,
            energy_percentages=energy_percentages,
            selected_month=selected_month,
            has_tou_demand=has_tou_demand,
            has_flat_demand=has_flat_demand,
            analysis_period=analysis_period,
            demand_period_month_counts=demand_period_month_counts,
            energy_period_month_counts=energy_period_month_counts
        )
    else:
        comprehensive_df = None
    
    # Create dual-axis chart
    fig = go.Figure()
    
    # Effective rate line
    fig.add_trace(go.Scatter(
        x=results['Load Factor Value'] * 100,
        y=results['Effective Rate ($/kWh)'],
        mode='lines+markers',
        name='Effective Rate ($/kWh)',
        line=dict(color='rgba(59, 130, 246, 0.8)', width=3),
        marker=dict(size=10),
        yaxis='y1',
        hovertemplate="<b>Load Factor: %{x:.0f}%</b><br>Effective Rate: $%{y:.4f}/kWh<extra></extra>"
    ))
    
    # Cost breakdown as stacked bars - break down energy by period
    if comprehensive_df is not None and tariff_data is not None:
        # Get energy period labels and structure
        energy_structure = tariff_data.get('energyratestructure', [])
        energy_labels = tariff_data.get('energyweekdaylabels', [])
        
        # Define color palette for energy periods (green shades)
        energy_colors = [
            'rgba(34, 197, 94, 0.9)',   # Green
            'rgba(16, 185, 129, 0.8)',  # Emerald
            'rgba(5, 150, 105, 0.7)',   # Dark green
            'rgba(132, 204, 22, 0.7)',  # Lime
            'rgba(101, 163, 13, 0.7)',  # Olive
            'rgba(74, 222, 128, 0.6)',  # Light green
            'rgba(22, 163, 74, 0.6)',   # Forest green
            'rgba(187, 247, 208, 0.7)', # Very light green
        ]
        
        # Add energy period traces
        for period_idx in range(len(energy_structure)):
            period_label = energy_labels[period_idx] if period_idx < len(energy_labels) else f"Period {period_idx}"
            cost_col = f'{period_label} Cost ($)'
            
            if cost_col in comprehensive_df.columns:
                color_idx = period_idx % len(energy_colors)
                fig.add_trace(go.Bar(
                    x=results['Load Factor Value'] * 100,
                    y=comprehensive_df[cost_col],
                    name=f'{period_label} Energy',
                    marker_color=energy_colors[color_idx],
                    yaxis='y2',
                    hovertemplate=f"<b>Load Factor: %{{x:.0f}}%</b><br>{period_label}: $%{{y:.2f}}<extra></extra>"
                ))
    else:
        # Fallback to aggregate energy charges if breakdown not available
        fig.add_trace(go.Bar(
            x=results['Load Factor Value'] * 100,
            y=results['Energy Charges ($)'],
            name='Energy Charges',
            marker_color='rgba(34, 197, 94, 0.7)',
            yaxis='y2',
            hovertemplate="<b>Load Factor: %{x:.0f}%</b><br>Energy: $%{y:.2f}<extra></extra>"
        ))
    
    fig.add_trace(go.Bar(
        x=results['Load Factor Value'] * 100,
        y=results['Demand Charges ($)'],
        name='Demand Charges',
        marker_color='rgba(249, 115, 22, 0.7)',
        yaxis='y2',
        hovertemplate="<b>Load Factor: %{x:.0f}%</b><br>Demand: $%{y:.2f}<extra></extra>"
    ))
    
    fig.add_trace(go.Bar(
        x=results['Load Factor Value'] * 100,
        y=results['Fixed Charges ($)'],
        name='Fixed Charges',
        marker_color='rgba(156, 163, 175, 0.7)',
        yaxis='y2',
        hovertemplate="<b>Load Factor: %{x:.0f}%</b><br>Fixed: $%{y:.2f}<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(
            text="Effective Rate and Cost Breakdown by Load Factor",
            font=dict(size=18, color='#1f2937' if not dark_mode else '#f1f5f9')
        ),
        xaxis=dict(
            title=dict(
                text="Load Factor (%)",
                font=dict(color='#1f2937' if not dark_mode else '#f1f5f9')
            ),
            tickfont=dict(color='#1f2937' if not dark_mode else '#f1f5f9'),
            tickmode='array',
            tickvals=[1, 5, 10, 20, 30, 50, 100]
        ),
        yaxis=dict(
            title=dict(
                text="Effective Rate ($/kWh)",
                font=dict(color='rgba(59, 130, 246, 0.8)')
            ),
            tickfont=dict(color='rgba(59, 130, 246, 0.8)'),
            side='left'
        ),
        yaxis2=dict(
            title=dict(
                text="Cost ($)",
                font=dict(color='#1f2937' if not dark_mode else '#f1f5f9')
            ),
            tickfont=dict(color='#1f2937' if not dark_mode else '#f1f5f9'),
            overlaying='y',
            side='right'
        ),
        barmode='stack',
        height=500,
        showlegend=True,
        legend=dict(
            font=dict(color='#1f2937' if not dark_mode else '#f1f5f9'),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        plot_bgcolor='rgba(248, 250, 252, 0.8)' if not dark_mode else 'rgba(15, 23, 42, 0.5)',
        paper_bgcolor='#ffffff' if not dark_mode else '#0f172a',
        font=dict(family="Inter, sans-serif", color='#1f2937' if not dark_mode else '#f1f5f9')
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add comprehensive breakdown table if data is available
    if comprehensive_df is not None:
        st.markdown("---")
        st.markdown("#### 📊 Comprehensive Breakdown Table")
        if analysis_period == "Single Month":
            st.caption("This table shows all load factors with detailed breakdowns by energy rate period and demand period. Periods not active in the selected month show 0 kWh or 0 kW.")
        else:
            st.caption("This table shows all load factors with detailed breakdowns by energy rate period and demand period for the full year. The '# Months' columns indicate how many months each period/tier is active.")
        
        # Build column configuration dynamically
        column_config = {
            "Load Factor": st.column_config.TextColumn("Load Factor", width="small"),
            "Average Load (kW)": st.column_config.NumberColumn("Avg Load (kW)", format="%.2f"),
            "Total Energy (kWh)": st.column_config.NumberColumn("Total Energy (kWh)", format="%.0f")
        }
        
        # Add energy period columns
        energy_structure = tariff_data.get('energyratestructure', [])
        energy_labels = tariff_data.get('energyweekdaylabels', [])
        for period_idx in range(len(energy_structure)):
            period_label = energy_labels[period_idx] if period_idx < len(energy_labels) else f"Period {period_idx}"
            column_config[f'{period_label} (kWh)'] = st.column_config.NumberColumn(
                f'{period_label} (kWh)', format="%.0f", width="small"
            )
            column_config[f'{period_label} Rate ($/kWh)'] = st.column_config.NumberColumn(
                f'{period_label} Rate ($/kWh)', format="$%.4f", width="small"
            )
            column_config[f'{period_label} Cost ($)'] = st.column_config.NumberColumn(
                f'{period_label} Cost ($)', format="$%.2f", width="small"
            )
        
        # Add TOU demand columns
        if has_tou_demand:
            demand_structure = tariff_data.get('demandratestructure', [])
            demand_labels = tariff_data.get('demandtoulabels', [])
            for i in range(len(demand_structure)):
                period_label = demand_labels[i] if i < len(demand_labels) else f"TOU Period {i}"
                column_config[f'{period_label} Demand (kW)'] = st.column_config.NumberColumn(
                    f'{period_label} Demand (kW)', format="%.2f", width="small"
                )
                column_config[f'{period_label} Rate ($/kW)'] = st.column_config.NumberColumn(
                    f'{period_label} Rate ($/kW)', format="$%.2f", width="small"
                )
                column_config[f'{period_label} Demand Cost ($)'] = st.column_config.NumberColumn(
                    f'{period_label} Demand Cost ($)', format="$%.2f", width="small"
                )
        
        # Add flat demand columns
        if has_flat_demand:
            column_config['Flat Demand (kW)'] = st.column_config.NumberColumn(
                'Flat Demand (kW)', format="%.2f", width="small"
            )
            column_config['Flat Demand Rate ($/kW)'] = st.column_config.NumberColumn(
                'Flat Demand Rate ($/kW)', format="$%.2f", width="small"
            )
            column_config['Flat Demand Cost ($)'] = st.column_config.NumberColumn(
                'Flat Demand Cost ($)', format="$%.2f", width="small"
            )
        
        # Add summary columns
        column_config['Total Demand Charges ($)'] = st.column_config.NumberColumn(
            'Total Demand ($)', format="$%.2f"
        )
        column_config['Total Energy Charges ($)'] = st.column_config.NumberColumn(
            'Total Energy ($)', format="$%.2f"
        )
        column_config['Fixed Charges ($)'] = st.column_config.NumberColumn(
            'Fixed ($)', format="$%.2f"
        )
        column_config['Total Cost ($)'] = st.column_config.NumberColumn(
            'Total Cost ($)', format="$%.2f"
        )
        column_config['Effective Rate ($/kWh)'] = st.column_config.NumberColumn(
            'Effective Rate ($/kWh)', format="$%.4f"
        )
        
        # Display the comprehensive table
        st.dataframe(
            comprehensive_df,
            use_container_width=True,
            hide_index=True,
            column_config=column_config,
            height=min(400, 35 * len(comprehensive_df) + 38)  # Dynamic height based on rows
        )
        
        # Add download button for Comprehensive Breakdown Table
        buffer_comprehensive = BytesIO()
        
        # Create a copy for Excel with load factor as percentage
        excel_comprehensive_df = comprehensive_df.copy()
        if 'Load Factor' in excel_comprehensive_df.columns:
            # Convert load factor string to numeric percentage (e.g., "50%" -> 0.50)
            excel_comprehensive_df['Load Factor'] = excel_comprehensive_df['Load Factor'].str.replace('%', '').astype(float) / 100
        
        with pd.ExcelWriter(buffer_comprehensive, engine='openpyxl') as writer:
            excel_comprehensive_df.to_excel(writer, sheet_name='Comprehensive Breakdown', index=False)
            
            # Get the worksheet to apply formatting
            worksheet = writer.sheets['Comprehensive Breakdown']
            
            # Apply formatting to columns
            from openpyxl.styles import numbers
            headers = list(excel_comprehensive_df.columns)
            
            for col_idx, col_name in enumerate(headers, start=1):
                for row_idx in range(2, len(excel_comprehensive_df) + 2):
                    cell = worksheet.cell(row=row_idx, column=col_idx)
                    
                    # Apply appropriate formatting based on column name
                    if col_name == 'Load Factor':
                        # Percentage format for Load Factor
                        cell.number_format = '0%'
                    elif col_name.endswith('Rate ($/kW)') or '($/kW)' in col_name:
                        # Accounting format with 2 decimal places for demand rates
                        cell.number_format = '_($* #,##0.00_);_($* (#,##0.00);_($* "-"??_);_(@_)'
                    elif col_name.endswith('Rate ($/kWh)') or col_name == 'Effective Rate ($/kWh)':
                        # Accounting format with 4 decimal places for energy rates
                        cell.number_format = '_($* #,##0.0000_);_($* (#,##0.0000);_($* "-"????_);_(@_)'
                    elif col_name.endswith('Cost ($)') or col_name.endswith('Charges ($)') or col_name == 'Total Cost ($)':
                        # Accounting format with no decimals for costs
                        cell.number_format = '_($* #,##0_);_($* (#,##0);_($* "-"_);_(@_)'
                    elif col_name.endswith('(kWh)') or col_name == 'Total Energy (kWh)':
                        # Number format with commas for energy
                        cell.number_format = '#,##0'
                    elif col_name.endswith('(kW)') or col_name == 'Average Load (kW)':
                        # Number format with no decimals for load
                        cell.number_format = '#,##0'
        
        buffer_comprehensive.seek(0)
        
        st.download_button(
            label="📥 Download Comprehensive Breakdown as Excel",
            data=buffer_comprehensive,
            file_name="load_factor_comprehensive_breakdown.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_comprehensive_breakdown"
        )
