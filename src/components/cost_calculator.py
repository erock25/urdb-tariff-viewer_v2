"""
Cost calculator tab component for URDB Tariff Viewer.

This module contains the UI components for the utility cost calculator tab.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, Optional, Union
from pathlib import Path

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
    Render the utility cost calculator tab.
    
    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
        load_profile_path (Optional[Path]): Path to selected load profile
        options (Dict[str, Any]): Display and analysis options
    """
    st.markdown(create_section_header_html("💰 Utility Cost Calculator"), unsafe_allow_html=True)
    
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


def _render_load_factor_analysis_tool(tariff_viewer: TariffViewer, options: Dict[str, Any]) -> None:
    """
    Render the load factor analysis tool.
    
    This tool allows users to calculate effective utility rates ($/kWh) at different load factors
    by specifying demand assumptions and energy distribution percentages.
    
    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
        options (Dict[str, Any]): Display options
    """
    
    with st.expander("🔍 Load Factor Rate Analysis Tool", expanded=False):
        st.markdown("""
        This tool calculates the **effective utility rate in $/kWh** for different load factors.
        
        **How it works:**
        - Specify the maximum demand for each applicable demand period
        - Specify the energy distribution across all energy rate periods
        - Select the month of interest
        - View effective rates for load factors: 1%, 5%, 10%, 20%, 30%, 50%, and 100%
        """)
        
        tariff_data = tariff_viewer.tariff  # Use .tariff for actual tariff data
        
        # Month selection
        month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        selected_month = st.selectbox(
            "📅 Select Month of Interest",
            options=list(range(12)),
            format_func=lambda x: month_names[x],
            help="Select the month for which to calculate effective rates"
        )
        
        st.markdown("---")
        
        # Get demand rate structure
        has_tou_demand = 'demandratestructure' in tariff_data and tariff_data.get('demandratestructure')
        has_flat_demand = 'flatdemandstructure' in tariff_data and tariff_data.get('flatdemandstructure')
        
        demand_inputs = {}
        
        # TOU Demand inputs
        if has_tou_demand:
            st.markdown("##### ⚡ TOU Demand Charges")
            st.markdown("Specify the maximum demand (kW) for each TOU demand period:")
            
            # Get demand period labels if available
            demand_labels = tariff_data.get('demandtoulabels', [])
            num_demand_periods = len(tariff_data['demandratestructure'])
            
            cols = st.columns(min(num_demand_periods, 3))
            for i in range(num_demand_periods):
                label = demand_labels[i] if i < len(demand_labels) else f"Demand Period {i}"
                rate = tariff_data['demandratestructure'][i][0].get('rate', 0)
                adj = tariff_data['demandratestructure'][i][0].get('adj', 0)
                total_rate = rate + adj
                
                with cols[i % 3]:
                    demand_inputs[f'tou_demand_{i}'] = st.number_input(
                        f"{label}\n(${total_rate:.2f}/kW)",
                        min_value=0.0,
                        value=0.0,
                        step=1.0,
                        key=f"lf_tou_demand_{i}",
                        help=f"Base rate: ${rate:.2f}/kW" + (f" + Adjustment: ${adj:.2f}/kW" if adj != 0 else "")
                    )
        
        # Flat demand input
        if has_flat_demand:
            st.markdown("##### 📊 Flat Monthly Demand Charge")
            
            # Get the correct flat demand structure based on selected month
            flatdemandmonths = tariff_data.get('flatdemandmonths', [0]*12)
            flat_tier = flatdemandmonths[selected_month] if selected_month < len(flatdemandmonths) else 0
            
            # Get rate structure for this tier
            flat_structure = tariff_data['flatdemandstructure']
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
                tou_demands = [v for k, v in demand_inputs.items() if k.startswith('tou_demand_') and v > 0]
                if tou_demands:
                    max_tou_demand = max(tou_demands)
                    # Use the greater of entered flat demand or max TOU demand
                    if flat_demand_value == 0:
                        # User didn't enter anything, auto-set to max TOU demand
                        st.info(f"ℹ️ Note: Flat demand automatically set to {max_tou_demand:.1f} kW to match the highest TOU demand.")
                        demand_inputs['flat_demand'] = max_tou_demand
                    elif flat_demand_value < max_tou_demand:
                        # User entered a value but it's too low
                        st.info(f"ℹ️ Note: Flat demand ({flat_demand_value:.1f} kW) is less than highest TOU demand ({max_tou_demand:.1f} kW). Using {max_tou_demand:.1f} kW for calculations.")
                        demand_inputs['flat_demand'] = max_tou_demand
                    else:
                        # User entered a valid value
                        demand_inputs['flat_demand'] = flat_demand_value
                else:
                    demand_inputs['flat_demand'] = flat_demand_value
            else:
                demand_inputs['flat_demand'] = flat_demand_value
        
        st.markdown("---")
        
        # Energy rate structure inputs
        st.markdown("##### 💡 Energy Distribution")
        st.markdown("Specify the percentage of energy consumption in each rate period (must sum to 100%):")
        
        energy_structure = tariff_data.get('energyratestructure', [])
        energy_labels = tariff_data.get('energytoulabels', [])
        num_energy_periods = len(energy_structure)
        
        energy_percentages = {}
        total_percentage = 0.0
        
        # Create columns for energy inputs
        cols = st.columns(min(num_energy_periods, 3))
        for i in range(num_energy_periods):
            label = energy_labels[i] if i < len(energy_labels) else f"Energy Period {i}"
            rate = energy_structure[i][0].get('rate', 0)
            adj = energy_structure[i][0].get('adj', 0)
            total_rate = rate + adj
            
            with cols[i % 3]:
                energy_percentages[i] = st.number_input(
                    f"{label}\n(${total_rate:.4f}/kWh)",
                    min_value=0.0,
                    max_value=100.0,
                    value=0.0 if i > 0 else 100.0,  # Default first period to 100%
                    step=1.0,
                    key=f"lf_energy_pct_{i}",
                    help=f"Base rate: ${rate:.4f}/kWh" + (f" + Adjustment: ${adj:.4f}/kWh" if adj != 0 else "")
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
                results = _calculate_load_factor_rates(
                    tariff_data=tariff_data,
                    demand_inputs=demand_inputs,
                    energy_percentages=energy_percentages,
                    selected_month=selected_month,
                    has_tou_demand=has_tou_demand,
                    has_flat_demand=has_flat_demand
                )
                _display_load_factor_results(results, options)


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
    
    # Load factors to analyze
    load_factors = [0.01, 0.05, 0.10, 0.20, 0.30, 0.50, 1.00]
    
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
        all_demands = [v for k, v in demand_inputs.items() if v > 0]
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
            for period_idx, percentage in energy_percentages.items():
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


def _display_load_factor_results(results: pd.DataFrame, options: Dict[str, Any]) -> None:
    """
    Display load factor analysis results.
    
    Args:
        results: DataFrame with analysis results
        options: Display options
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
    
    # Visualization
    st.markdown("#### 📈 Effective Rate vs Load Factor")
    
    dark_mode = options.get('dark_mode', False)
    
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
    
    # Cost breakdown as stacked bar
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
