"""
Flat demand rates tab component for URDB Tariff Viewer.

This module contains the UI components for the flat demand rates analysis tab.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any

from src.models.tariff import TariffViewer
from src.components.visualizations import create_flat_demand_chart


def render_flat_demand_rates_tab(tariff_viewer: TariffViewer, options: Dict[str, Any]) -> None:
    """
    Render the flat demand rates analysis tab matching the original app.py layout.
    
    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
        options (Dict[str, Any]): Display and analysis options
    """
    st.markdown("### 📊 Seasonal/Monthly Flat Demand Rates")
    
    # Use the same modified tariff logic as other rate types
    if st.session_state.get('modified_tariff'):
        # Extract tariff data from modified structure
        if 'items' in st.session_state.modified_tariff:
            current_flat_demand_tariff = st.session_state.modified_tariff['items'][0]
        else:
            current_flat_demand_tariff = st.session_state.modified_tariff
    else:
        current_flat_demand_tariff = tariff_viewer.tariff

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
    
    with st.expander("🔧 Edit Flat Demand Rates", expanded=False):
        if flat_demand_rates and flat_demand_months:
            _render_flat_demand_editing_form(tariff_viewer, flat_demand_rates, flat_demand_months)
        else:
            st.info("📝 **Note:** No flat demand rate structure found in this tariff JSON.")
    
    st.markdown("---")
    
    # Flat Demand Rates Chart
    st.markdown("#### 📈 Monthly Flat Demand Rates Visualization")
    
    try:
        # Use modified tariff for chart if available
        if st.session_state.get('has_modifications') and st.session_state.get('modified_tariff'):
            from app import create_temp_viewer_with_modified_tariff
            temp_viewer = create_temp_viewer_with_modified_tariff(st.session_state.modified_tariff)
            fig = create_flat_demand_chart(
                tariff_viewer=temp_viewer,
                dark_mode=options.get('dark_mode', False)
            )
        else:
            fig = create_flat_demand_chart(
                tariff_viewer=tariff_viewer,
                dark_mode=options.get('dark_mode', False)
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error creating flat demand rates chart: {str(e)}")
        st.info("This may indicate missing or invalid flat demand rate data in the tariff file.")


def _render_flat_demand_editing_form(tariff_viewer: TariffViewer, flat_demand_rates: list, flat_demand_months: list) -> None:
    """Render the flat demand rate editing form matching the original app.py format."""
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
            if not st.session_state.get('modified_tariff'):
                st.session_state.modified_tariff = copy.deepcopy(tariff_viewer.data)
            
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
