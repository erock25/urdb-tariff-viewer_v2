"""
Energy rates tab component for URDB Tariff Viewer.

This module contains the UI components for the energy rates analysis tab.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime

from src.models.tariff import TariffViewer
from src.components.visualizations import create_heatmap, display_rate_statistics
from src.utils.styling import create_section_header_html, create_custom_divider_html
from src.utils.helpers import generate_energy_rates_excel, clean_filename


def render_energy_rates_tab(tariff_viewer: TariffViewer, options: Dict[str, Any]) -> None:
    """
    Render the energy rates analysis tab.
    
    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
        options (Dict[str, Any]): Display and analysis options
    """
    # Match original structure exactly
    st.markdown("### ⚡ Energy Rate Structure")
    
    # Show current table (read-only) first - matching original
    st.markdown("#### 📊 Current Rate Table")
    
    try:
        tou_table = tariff_viewer.create_tou_labels_table()
        
        if not tou_table.empty:
            st.dataframe(
                tou_table,
                width="stretch",
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
            
    except Exception as e:
        st.error(f"❌ Error creating rate table: {str(e)}")
    
    st.markdown("---")
    
    # Rate editing section
    st.markdown("#### ✏️ Rate Editing")
    
    with st.expander("🔧 Edit Energy Rates", expanded=False):
        _render_comprehensive_rate_editing_section(tariff_viewer, options)
    
    st.markdown("---")
    
    # Heatmap visualization section
    st.markdown("#### 🗓️ Time-of-Use Energy Rates Heatmap")
    
    # Controls for heatmap
    col1, col2 = st.columns(2)
    
    with col1:
        is_weekday = st.radio(
            "Day Type",
            options=[True, False],
            format_func=lambda x: "Weekday" if x else "Weekend",
            horizontal=True,
            help="Choose between weekday and weekend energy rates"
        )
    
    with col2:
        show_heatmap_text = st.checkbox(
            "Show Values on Heatmap",
            value=options.get('text_size', 12) > 0,
            help="Display rate values on heatmap tiles"
        )
    
    # Adjust text size based on checkbox
    text_size = options.get('text_size', 12) if show_heatmap_text else 0
    
    try:
        heatmap_fig = create_heatmap(
            tariff_viewer=tariff_viewer,
            is_weekday=is_weekday,
            dark_mode=options.get('dark_mode', False),
            rate_type="energy",
            chart_height=options.get('chart_height', 700),
            text_size=text_size
        )
        
        st.plotly_chart(heatmap_fig, width="stretch")
        
    except Exception as e:
        st.error(f"❌ Error creating energy rates heatmap: {str(e)}")
        st.info("This may indicate missing or invalid energy rate data in the tariff file.")
    
    st.markdown(create_custom_divider_html(), unsafe_allow_html=True)
    
    # Add Excel download section at the bottom
    _render_excel_download_section(tariff_viewer)


def _render_comprehensive_rate_editing_section(tariff_viewer: TariffViewer, options: Dict[str, Any]) -> None:
    """
    Render the comprehensive rate editing section (matching original app.py functionality).
    
    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
        options (Dict[str, Any]): Display options
    """
    # Use modified tariff if available, otherwise use original
    if st.session_state.get('modified_tariff'):
        # Extract tariff data from modified structure
        if 'items' in st.session_state.modified_tariff:
            current_tariff = st.session_state.modified_tariff['items'][0]
        else:
            current_tariff = st.session_state.modified_tariff
    else:
        current_tariff = tariff_viewer.tariff

    energy_labels = current_tariff.get('energytoulabels', [])
    energy_rates = current_tariff.get('energyratestructure', [])
    
    if not energy_rates:
        st.warning("⚠️ No energy rate structure found in this tariff.")
        return

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
            if not st.session_state.get('modified_tariff'):
                st.session_state.modified_tariff = copy.deepcopy(tariff_viewer.data)
            
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


def show_energy_rate_comparison(tariff_viewer: TariffViewer, options: Dict[str, Any]) -> None:
    """
    Show energy rate comparison between weekday and weekend.
    
    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
        options (Dict[str, Any]): Display options
    """
    st.markdown("#### 📊 Weekday vs Weekend Rate Comparison")
    
    # Calculate differences
    rate_diff = tariff_viewer.weekday_df - tariff_viewer.weekend_df
    
    # Show summary statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_weekday = tariff_viewer.weekday_df.values.mean()
        st.metric("Avg Weekday Rate", f"${avg_weekday:.4f}/kWh")
    
    with col2:
        avg_weekend = tariff_viewer.weekend_df.values.mean()
        st.metric("Avg Weekend Rate", f"${avg_weekend:.4f}/kWh")
    
    with col3:
        avg_difference = rate_diff.values.mean()
        st.metric(
            "Average Difference", 
            f"${avg_difference:.4f}/kWh",
            delta=f"Weekday {'higher' if avg_difference > 0 else 'lower'}"
        )
    
    # Show difference heatmap
    if st.checkbox("Show Rate Difference Heatmap"):
        import plotly.graph_objects as go
        
        fig = go.Figure(data=go.Heatmap(
            z=rate_diff.values,
            x=[f'{h:02d}:00' for h in range(24)],
            y=rate_diff.index,
            colorscale='RdBu_r',
            colorbar=dict(title="Rate Difference<br>($/kWh)"),
            hovertemplate="<b>%{y}</b> - %{x}<br>Difference: $%{z:.4f}/kWh<extra></extra>"
        ))
        
        fig.update_layout(
            title="Weekday vs Weekend Rate Differences",
            xaxis_title="Hour of Day",
            yaxis_title="Month",
            height=options.get('chart_height', 700)
        )
        
        st.plotly_chart(fig, width="stretch")


def _render_excel_download_section(tariff_viewer: TariffViewer) -> None:
    """
    Render the Excel download section with button.
    
    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
    """
    st.markdown("#### 📥 Download Energy Rates Data")
    
    col1, col2, col3 = st.columns([2, 2, 3])
    
    with col1:
        # Year selection for timeseries
        current_year = datetime.now().year
        year = st.number_input(
            "Year for Timeseries",
            min_value=2020,
            max_value=2050,
            value=current_year,
            step=1,
            help="Select the year for generating the full timeseries data"
        )
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        
        # Generate Excel file
        try:
            excel_data = generate_energy_rates_excel(tariff_viewer, year=year)
            
            # Create filename
            utility_clean = clean_filename(tariff_viewer.utility_name)
            rate_clean = clean_filename(tariff_viewer.rate_name)
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"Energy_Rates_{utility_clean}_{rate_clean}_{timestamp}.xlsx"
            
            # Download button
            st.download_button(
                label="📥 Download Excel File",
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Download Excel file with 4 sheets: Rate Table, Weekday Rates, Weekend Rates, and Timeseries"
            )
            
        except Exception as e:
            st.error(f"❌ Error generating Excel file: {str(e)}")
    
    with col3:
        st.info(
            """
            **Excel file contains 4 sheets:**
            - **Rate Table**: TOU periods with base rates and adjustments
            - **Weekday Rates**: 12x24 heatmap data (Month x Hour)
            - **Weekend Rates**: 12x24 heatmap data (Month x Hour)
            - **Timeseries**: Full year of 15-minute interval data with timestamps and rates
            """
        )
