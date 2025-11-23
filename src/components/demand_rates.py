"""
Demand rates tab component for URDB Tariff Viewer.

This module contains the UI components for the demand rates analysis tab.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any
from datetime import datetime
from io import BytesIO

from src.models.tariff import TariffViewer
from src.components.visualizations import create_heatmap
from src.utils.styling import create_custom_divider_html
from src.utils.helpers import clean_filename


def render_demand_rates_tab(tariff_viewer: TariffViewer, options: Dict[str, Any]) -> None:
    """
    Render the demand rates analysis tab matching the original app.py layout.
    
    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
        options (Dict[str, Any]): Display and analysis options
    """
    # Use the same modified tariff logic as energy rates
    if st.session_state.get('modified_tariff'):
        # Extract tariff data from modified structure
        if 'items' in st.session_state.modified_tariff:
            current_demand_tariff = st.session_state.modified_tariff['items'][0]
        else:
            current_demand_tariff = st.session_state.modified_tariff
    else:
        current_demand_tariff = tariff_viewer.tariff

    # Show current demand rate table first
    st.markdown("#### Time of Use Demand Rates Table")
    
    try:
        demand_table = tariff_viewer.create_demand_labels_table()
        
        if not demand_table.empty:
            st.dataframe(
                demand_table,
                width="stretch",
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
                    "Hours/Year": st.column_config.NumberColumn(
                        "Hours/Year",
                        width="small",
                        format="%d"
                    ),
                    "% of Year": st.column_config.TextColumn(
                        "% of Year",
                        width="small",
                    ),
                    "Days/Year": st.column_config.NumberColumn(
                        "Days/Year",
                        width="small",
                        format="%d"
                    ),
                    "Months Present": st.column_config.TextColumn(
                        "Months Present",
                        width="large",
                    )
                }
            )
            
            # Download button for the demand rate table
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                # Generate Excel file for download
                # Create a copy with numeric values for Excel export
                excel_table = demand_table.copy()
                
                # Convert formatted strings to numeric values
                # Remove $ and convert to float for rate columns
                for col in ['Base Rate ($/kW)', 'Adjustment ($/kW)', 'Total Rate ($/kW)']:
                    if col in excel_table.columns:
                        excel_table[col] = excel_table[col].str.replace('$', '').astype(float)
                
                # Remove % sign and convert to decimal for percentage column
                if '% of Year' in excel_table.columns:
                    excel_table['% of Year'] = excel_table['% of Year'].str.replace('%', '').astype(float) / 100
                
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    excel_table.to_excel(writer, sheet_name='Demand Rate Table', index=False)
                    
                    # Get the worksheet to apply formatting
                    worksheet = writer.sheets['Demand Rate Table']
                    
                    # Find column indices for formatting
                    headers = list(excel_table.columns)
                    rate_columns = ['Base Rate ($/kW)', 'Adjustment ($/kW)', 'Total Rate ($/kW)']
                    
                    # Apply formatting to columns
                    from openpyxl.styles import numbers
                    for col_idx, col_name in enumerate(headers, start=1):
                        if col_name in rate_columns:
                            for row_idx in range(2, len(excel_table) + 2):
                                cell = worksheet.cell(row=row_idx, column=col_idx)
                                cell.number_format = '_($* #,##0.00_);_($* (#,##0.00);_($* "-"??_);_(@_)'
                        elif col_name == '% of Year':
                            for row_idx in range(2, len(excel_table) + 2):
                                cell = worksheet.cell(row=row_idx, column=col_idx)
                                cell.number_format = '0.0%'
                
                excel_data = buffer.getvalue()
                
                # Create filename
                utility_clean = clean_filename(tariff_viewer.utility_name)
                rate_clean = clean_filename(tariff_viewer.rate_name)
                timestamp = datetime.now().strftime("%Y%m%d")
                filename = f"Demand_Rate_Table_{utility_clean}_{rate_clean}_{timestamp}.xlsx"
                
                st.download_button(
                    label="📥 Download Table",
                    data=excel_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Download the current demand rate table as an Excel file"
                )
        else:
            st.info("📝 **Note:** No demand rate structure found in this tariff JSON.")
            
    except Exception as e:
        st.error(f"❌ Error creating demand rate table: {str(e)}")
    
    st.markdown("---")
    
    # Demand Labels Table - Editable (moved above heatmaps to match original)
    st.markdown("#### 🏷️ Demand Period Labels & Rates (Editable)")
    
    # Get demand rates and labels for editing form
    demand_rates = current_demand_tariff.get('demandratestructure', [])
    demand_labels = current_demand_tariff.get('demandlabels', [])
    
    with st.expander("🔧 Edit Demand Rates", expanded=False):
        if demand_rates:
            _render_demand_editing_form(tariff_viewer, demand_rates, demand_labels)
        else:
            st.info("📝 **Note:** No demand rate structure found in this tariff JSON.")
    
    st.markdown("---")
    
    # Weekday Demand Rates - Full Width
    st.markdown("#### 📈 Weekday Demand Rates")
    
    # Create heatmap using the visualization function
    try:
        if st.session_state.get('has_modifications') and st.session_state.get('modified_tariff'):
            # Use modified tariff data for visualization
            from app import create_temp_viewer_with_modified_tariff
            temp_viewer = create_temp_viewer_with_modified_tariff(st.session_state.modified_tariff)
            fig = create_heatmap(
                tariff_viewer=temp_viewer,
                is_weekday=True,
                dark_mode=options.get('dark_mode', False),
                rate_type="demand",
                chart_height=options.get('chart_height', 700),
                text_size=options.get('text_size', 12)
            )
        else:
            fig = create_heatmap(
            tariff_viewer=tariff_viewer,
                is_weekday=True,
            dark_mode=options.get('dark_mode', False),
            rate_type="demand",
            chart_height=options.get('chart_height', 700),
                text_size=options.get('text_size', 12)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error creating weekday demand rates heatmap: {str(e)}")
        st.info("This may indicate missing or invalid demand rate data in the tariff file.")
    
    st.markdown("---")
    
    # Weekend Demand Rates - Full Width
    st.markdown("#### 📉 Weekend Demand Rates")
    
    try:
        if st.session_state.get('has_modifications') and st.session_state.get('modified_tariff'):
            # Use modified tariff data for visualization
            from app import create_temp_viewer_with_modified_tariff
            temp_viewer = create_temp_viewer_with_modified_tariff(st.session_state.modified_tariff)
            fig = create_heatmap(
                tariff_viewer=temp_viewer,
                is_weekday=False,
                dark_mode=options.get('dark_mode', False),
                rate_type="demand",
                chart_height=options.get('chart_height', 700),
                text_size=options.get('text_size', 12)
            )
        else:
            fig = create_heatmap(
            tariff_viewer=tariff_viewer,
                is_weekday=False,
                dark_mode=options.get('dark_mode', False),
                rate_type="demand",
                chart_height=options.get('chart_height', 700),
                text_size=options.get('text_size', 12)
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error creating weekend demand rates heatmap: {str(e)}")
        st.info("This may indicate missing or invalid demand rate data in the tariff file.")


def _render_demand_editing_form(tariff_viewer: TariffViewer, demand_rates: list, demand_labels: list) -> None:
    """Render the demand rate editing form matching the original app.py format."""
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
            if not st.session_state.get('modified_tariff'):
                st.session_state.modified_tariff = copy.deepcopy(tariff_viewer.data)
            
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
            
            
# End of file
