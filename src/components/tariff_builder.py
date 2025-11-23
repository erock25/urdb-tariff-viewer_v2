"""
Tariff Builder Component for URDB Tariff Viewer.

This module provides a GUI for creating new tariff JSON files from scratch.
"""

import streamlit as st
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from src.config.settings import Settings
from src.config.constants import MONTHS, HOURS
from src.utils.styling import create_section_header_html


def render_tariff_builder_tab() -> None:
    """
    Render the tariff builder tab for creating new tariffs from scratch.
    """
    st.markdown("""
    Create a new utility tariff from scratch. Fill in the required fields below and 
    optionally configure advanced rate structures. When finished, save your tariff 
    as a JSON file.
    """)
    
    # Performance tip
    st.info("""
    💡 **Performance Tip**: Each section uses forms to batch updates. Fill in all fields 
    in a section, then click the **"✅ Apply Changes"** button to save your entries without 
    constant screen refreshes.
    """)
    
    # Initialize session state for tariff builder if not exists
    if 'tariff_builder_data' not in st.session_state:
        st.session_state.tariff_builder_data = _create_empty_tariff_structure()
    
    # Create tabs for different sections
    builder_tabs = st.tabs([
        "📋 Basic Info",
        "⚡ Energy Rates",
        "📅 Energy Schedule",
        "🔌 Demand Charges",
        "📊 Flat Demand",
        "💰 Fixed Charges",
        "🔍 Preview & Save"
    ])
    
    with builder_tabs[0]:
        _render_basic_info_section()
    
    with builder_tabs[1]:
        _render_energy_rates_section()
    
    with builder_tabs[2]:
        _render_energy_schedule_section()
    
    with builder_tabs[3]:
        _render_demand_charges_section()
    
    with builder_tabs[4]:
        _render_flat_demand_section()
    
    with builder_tabs[5]:
        _render_fixed_charges_section()
    
    with builder_tabs[6]:
        _render_preview_and_save_section()


def _create_empty_tariff_structure() -> Dict[str, Any]:
    """
    Create an empty tariff structure with default values.
    
    Returns:
        Dict[str, Any]: Empty tariff structure
    """
    return {
        "items": [{
            # Basic information
            "utility": "",
            "name": "",
            "sector": "Commercial",
            "servicetype": "Bundled",
            "description": "",
            "source": "",
            "sourceparent": "",
            "country": "USA",
            
            # Voltage and service parameters
            "voltagecategory": "Secondary",
            "phasewiring": "Single Phase",
            "demandunits": "kW",
            
            # Energy rate structure
            "energyratestructure": [
                [{"unit": "kWh", "rate": 0.0, "adj": 0.0}]
            ],
            "energytoulabels": ["Period 0"],
            "energyweekdayschedule": [[0] * 24 for _ in range(12)],
            "energyweekendschedule": [[0] * 24 for _ in range(12)],
            "energycomments": "",
            
            # Demand rate structure (optional)
            "demandrateunit": "kW",
            "demandratestructure": [],
            "demandweekdayschedule": [],
            "demandweekendschedule": [],
            "demandcomments": "",
            
            # Flat demand structure (optional)
            "flatdemandunit": "kW",
            "flatdemandstructure": [[{"rate": 0.0, "adj": 0.0}]],
            "flatdemandmonths": [0] * 12,
            
            # Fixed charges
            "fixedchargefirstmeter": 0.0,
            "fixedchargeunits": "$/month",
            
            # Metadata
            "approved": True,
            "is_default": False,
            "startdate": int(datetime.now().timestamp()),
        }]
    }


def _render_basic_info_section() -> None:
    """Render the basic information section of the tariff builder."""
    st.markdown("### 📋 Basic Tariff Information")
    st.markdown("Enter the essential details about this utility rate.")
    
    data = st.session_state.tariff_builder_data['items'][0]
    
    # Use a form to batch updates and prevent reruns on every keystroke
    # Add timestamp to ensure unique key
    form_key = f"basic_info_form_{id(data)}"
    with st.form(form_key, clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            utility = st.text_input(
                "Utility Company Name *",
                value=data.get('utility', ''),
                help="e.g., 'Pacific Gas & Electric Co'"
            )
            
            name = st.text_input(
                "Rate Schedule Name *",
                value=data.get('name', ''),
                help="e.g., 'TOU-EV-9 (below 2kV)'"
            )
            
            sector = st.selectbox(
                "Customer Sector *",
                options=["Commercial", "Residential", "Industrial", "Agricultural", "Lighting"],
                index=["Commercial", "Residential", "Industrial", "Agricultural", "Lighting"].index(
                    data.get('sector', 'Commercial')
                ),
                help="Type of customer this rate applies to"
            )
            
            servicetype = st.selectbox(
                "Service Type",
                options=["Bundled", "Energy Only", "Delivery Only"],
                index=["Bundled", "Energy Only", "Delivery Only"].index(
                    data.get('servicetype', 'Bundled')
                ),
                help="Type of service provided"
            )
        
        with col2:
            voltagecategory = st.selectbox(
                "Voltage Category",
                options=["Secondary", "Primary", "Transmission"],
                index=["Secondary", "Primary", "Transmission"].index(
                    data.get('voltagecategory', 'Secondary')
                ),
                help="Voltage level of service"
            )
            
            phasewiring = st.selectbox(
                "Phase Wiring",
                options=["Single Phase", "Three Phase"],
                index=["Single Phase", "Three Phase"].index(
                    data.get('phasewiring', 'Single Phase')
                ),
                help="Electrical phase configuration"
            )
            
            country = st.text_input(
                "Country",
                value=data.get('country', 'USA'),
                help="Country where this tariff applies"
            )
        
        # Description and sources
        st.markdown("---")
        
        description = st.text_area(
            "Description *",
            value=data.get('description', ''),
            height=100,
            help="Detailed description of the rate, applicability, and any special conditions"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            source = st.text_input(
                "Tariff Source URL (optional)",
                value=data.get('source', ''),
                help="URL to the official tariff document"
            )
        
        with col2:
            sourceparent = st.text_input(
                "Utility Tariff Page URL (optional)",
                value=data.get('sourceparent', ''),
                help="URL to the utility's main tariff page"
            )
        
        # Form submit button
        submitted = st.form_submit_button("✅ Apply Changes", type="primary", use_container_width=True)
        
        if submitted:
            # Update data only when form is submitted
            data['utility'] = utility
            data['name'] = name
            data['sector'] = sector
            data['servicetype'] = servicetype
            data['voltagecategory'] = voltagecategory
            data['phasewiring'] = phasewiring
            data['country'] = country
            data['description'] = description
            data['source'] = source
            data['sourceparent'] = sourceparent
            st.success("✓ Basic information updated!")
    
    # Show validation (outside form)
    _show_section_validation("basic_info", data)


def _render_energy_rates_section() -> None:
    """Render the energy rates section of the tariff builder."""
    st.markdown("### ⚡ Energy Rate Structure")
    st.markdown("""
    Define your Time-of-Use (TOU) energy rate periods. Each period represents a different 
    energy rate (e.g., Summer/Winter On-Peak, Off-Peak, Super Off-Peak).
    """)
    
    data = st.session_state.tariff_builder_data['items'][0]
    
    # Number of TOU periods (outside form, as it restructures data)
    num_periods = st.number_input(
        "Number of TOU Periods",
        min_value=1,
        max_value=12,
        value=len(data.get('energyratestructure', [{}])),
        help="How many different rate periods do you have? (e.g., 3 for Peak/Mid-Peak/Off-Peak)"
    )
    
    # Adjust arrays based on number of periods
    if len(data['energyratestructure']) != num_periods:
        data['energyratestructure'] = [
            [{"unit": "kWh", "rate": 0.0, "adj": 0.0}] 
            for _ in range(num_periods)
        ]
        data['energytoulabels'] = [f"Period {i}" for i in range(num_periods)]
    
    st.markdown("---")
    
    # Use form to batch updates for all periods
    # Add unique identifier to prevent duplicate key errors
    form_key = f"energy_rates_form_{num_periods}_{id(data)}"
    with st.form(form_key, clear_on_submit=False):
        # Create input fields for each period
        period_data = []
        for i in range(num_periods):
            st.markdown(f"#### ⚡ TOU Period {i}")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                label = st.text_input(
                    "Period Label",
                    value=data['energytoulabels'][i],
                    help="e.g., 'Peak', 'Off-Peak', 'Super Off-Peak'",
                    key=f"energy_label_{i}"
                )
            
            with col2:
                rate = st.number_input(
                    "Base Rate ($/kWh)",
                    min_value=0.0,
                    max_value=10.0,
                    value=data['energyratestructure'][i][0].get('rate', 0.0),
                    format="%.5f",
                    step=0.001,
                    help="Base energy rate in dollars per kWh",
                    key=f"energy_rate_{i}"
                )
            
            with col3:
                adj = st.number_input(
                    "Adjustment ($/kWh)",
                    min_value=-1.0,
                    max_value=1.0,
                    value=data['energyratestructure'][i][0].get('adj', 0.0),
                    format="%.5f",
                    step=0.001,
                    help="Rate adjustment (can be negative)",
                    key=f"energy_adj_{i}"
                )
            
            # Show total rate
            total_rate = rate + adj
            st.caption(f"**Total Rate:** ${total_rate:.5f}/kWh")
            
            period_data.append({'label': label, 'rate': rate, 'adj': adj})
            
            if i < num_periods - 1:
                st.markdown("---")
        
        # Comments
        st.markdown("---")
        comments = st.text_area(
            "Energy Rate Comments (optional)",
            value=data.get('energycomments', ''),
            help="Additional notes about energy rates, adjustments, or special conditions"
        )
        
        # Form submit button
        submitted = st.form_submit_button("✅ Apply Changes", type="primary", use_container_width=True)
        
        if submitted:
            # Update data only when form is submitted
            for i, pd in enumerate(period_data):
                data['energytoulabels'][i] = pd['label']
                data['energyratestructure'][i][0]['rate'] = pd['rate']
                data['energyratestructure'][i][0]['adj'] = pd['adj']
            data['energycomments'] = comments
            st.success("✓ Energy rates updated!")
    
    _show_section_validation("energy_rates", data)


def _render_energy_schedule_section() -> None:
    """Render the energy schedule section of the tariff builder."""
    st.markdown("### 📅 Energy TOU Schedule")
    st.markdown("""
    Define when each TOU period applies throughout the year. You can set different 
    schedules for weekdays and weekends.
    """)
    
    data = st.session_state.tariff_builder_data['items'][0]
    num_periods = len(data['energyratestructure'])
    
    # Schedule editing mode
    st.markdown("#### Schedule Configuration")
    
    schedule_mode = st.radio(
        "How would you like to set the schedule?",
        options=["Simple (same for all months)", "Advanced (different by month)"],
        help="Simple mode applies the same daily pattern to all months"
    )
    
    if schedule_mode == "Simple (same for all months)":
        _render_simple_schedule_editor(data, num_periods)
    else:
        _render_advanced_schedule_editor(data, num_periods)
    
    # Show schedule preview
    st.markdown("---")
    st.markdown("#### 📊 Schedule Preview")
    
    tab1, tab2 = st.tabs(["Weekday Schedule", "Weekend Schedule"])
    
    with tab1:
        _show_schedule_heatmap(data['energyweekdayschedule'], "Weekday", data['energytoulabels'],
                              rate_structure=data.get('energyratestructure'),
                              rate_type='energy')
    
    with tab2:
        _show_schedule_heatmap(data['energyweekendschedule'], "Weekend", data['energytoulabels'],
                              rate_structure=data.get('energyratestructure'),
                              rate_type='energy')


def _render_simple_schedule_editor(data: Dict, num_periods: int) -> None:
    """Render a simple schedule editor that applies the same pattern to all months."""
    st.markdown("#### Weekday Schedule")
    st.info("💡 **Tip**: Fill in all hours, then click 'Apply Schedule' at the bottom to update.")
    
    # Use a form to batch all 24+ hour selections
    # Add unique identifier to prevent duplicate key errors
    form_key = f"simple_schedule_form_{num_periods}_{id(data)}"
    with st.form(form_key, clear_on_submit=False):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("**Set hourly rates for a typical weekday:**")
            weekday_pattern = []
            
            # Create 24 hour selections
            for hour in range(24):
                period = st.selectbox(
                    f"Hour {hour}:00",
                    options=list(range(num_periods)),
                    format_func=lambda x: f"{data['energytoulabels'][x]} (Period {x})",
                    key=f"simple_weekday_{hour}",
                    index=data['energyweekdayschedule'][0][hour] if hour < len(data['energyweekdayschedule'][0]) else 0
                )
                weekday_pattern.append(period)
        
        with col2:
            st.markdown("**Current Schedule:**")
            # Show current schedule from data
            current_schedule_df = pd.DataFrame({
                'Hour': [f"{h}:00" for h in range(24)],
                'Period': [data['energytoulabels'][data['energyweekdayschedule'][0][h]] for h in range(24)]
            })
            st.dataframe(current_schedule_df, use_container_width=True, height=600)
        
        st.markdown("---")
        st.markdown("#### Weekend Schedule")
        
        weekend_same = st.checkbox(
            "Use same schedule for weekends",
            value=True,
            help="If checked, weekend will use the same schedule as weekdays"
        )
        
        weekend_pattern = []
        if not weekend_same:
            st.markdown("**Set hourly rates for a typical weekend:**")
            cols = st.columns(4)
            
            for hour in range(24):
                with cols[hour % 4]:
                    period = st.selectbox(
                        f"Hr {hour}",
                        options=list(range(num_periods)),
                        format_func=lambda x: f"P{x}",
                        key=f"simple_weekend_{hour}",
                        index=data['energyweekendschedule'][0][hour] if hour < len(data['energyweekendschedule'][0]) else 0,
                        label_visibility="visible"
                    )
                    weekend_pattern.append(period)
        
        # Form submit button
        submitted = st.form_submit_button("✅ Apply Schedule", type="primary", use_container_width=True)
        
        if submitted:
            # Apply pattern to all months
            data['energyweekdayschedule'] = [weekday_pattern for _ in range(12)]
            
            if weekend_same:
                data['energyweekendschedule'] = [weekday_pattern for _ in range(12)]
            else:
                data['energyweekendschedule'] = [weekend_pattern for _ in range(12)]
            
            st.success("✓ Schedule updated for all months!")


def _initialize_default_templates(data: Dict, schedule_key: str, num_periods: int) -> Dict:
    """Initialize default templates from existing schedule data."""
    templates = {
        'Template 1': {
            'name': 'Template 1',
            'schedule': data[schedule_key][0].copy() if data[schedule_key] else [0] * 24,
            'assigned_months': [0]  # January by default
        }
    }
    return templates


def _get_template_key(schedule_type: str, rate_type: str) -> str:
    """Get the session state key for templates."""
    return f"{rate_type}_schedule_templates"


def _get_schedule_key(schedule_type: str, rate_type: str) -> str:
    """Get the data key for the schedule (weekday or weekend)."""
    prefix = 'energy' if rate_type == 'energy' else 'demand'
    return f"{prefix}{schedule_type}schedule"


def _render_template_manager(schedule_type: str, rate_type: str, num_periods: int, data: Dict) -> None:
    """Render the template management UI (add, delete, rename templates)."""
    template_key = _get_template_key(schedule_type, rate_type)
    templates = st.session_state[template_key][schedule_type]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"**Current {schedule_type.title()} Templates:**")
        if templates:
            for template_id, template in templates.items():
                num_months = len(template.get('assigned_months', []))
                st.write(f"• **{template['name']}** ({num_months} months assigned)")
        else:
            st.info("No templates yet. Add one below!")
    
    with col2:
        st.markdown("**Add New Template:**")
        new_template_name = st.text_input(
            "Template Name",
            placeholder="e.g., Summer Peak",
            key=f"new_template_name_{rate_type}_{schedule_type}"
        )
        
        if st.button("➕ Add Template", key=f"add_template_{rate_type}_{schedule_type}"):
            if new_template_name and new_template_name not in templates:
                templates[new_template_name] = {
                    'name': new_template_name,
                    'schedule': [0] * 24,  # Default all zeros
                    'assigned_months': []
                }
                st.success(f"✓ Added template '{new_template_name}'")
                st.rerun()
            elif new_template_name in templates:
                st.error("Template name already exists!")
            else:
                st.warning("Please enter a template name.")
    
    # Delete template option
    if templates:
        st.markdown("**Delete Template:**")
        template_to_delete = st.selectbox(
            "Select template to delete",
            options=list(templates.keys()),
            key=f"delete_template_select_{rate_type}_{schedule_type}"
        )
        
        if st.button("🗑️ Delete", key=f"delete_template_{rate_type}_{schedule_type}"):
            if len(templates) > 1:
                del templates[template_to_delete]
                st.success(f"✓ Deleted template '{template_to_delete}'")
                st.rerun()
            else:
                st.error("Cannot delete the last template! Add another one first.")


def _render_template_editor(schedule_type: str, rate_type: str, num_periods: int, data: Dict) -> None:
    """Render the template editor UI for defining the 24-hour schedule."""
    template_key = _get_template_key(schedule_type, rate_type)
    templates = st.session_state[template_key][schedule_type]
    
    if not templates:
        st.warning("No templates available. Add a template in Step 1.")
        return
    
    selected_template = st.selectbox(
        "Select template to edit:",
        options=list(templates.keys()),
        key=f"edit_template_select_{rate_type}_{schedule_type}"
    )
    
    template = templates[selected_template]
    
    st.markdown(f"#### Editing: **{template['name']}**")
    st.markdown("**Set the TOU period for each hour:**")
    
    # Create a form to batch updates
    with st.form(f"template_editor_{rate_type}_{schedule_type}_{selected_template}"):
        cols = st.columns(6)
        new_schedule = []
        
        for hour in range(24):
            with cols[hour % 6]:
                if rate_type == 'energy':
                    format_func = lambda x: f"{data['energytoulabels'][x]}" if x < len(data.get('energytoulabels', [])) else f"P{x}"
                else:  # demand
                    demand_labels = data.get('demandlabels', [f"Period {i}" for i in range(num_periods)])
                    format_func = lambda x: f"{demand_labels[x]}" if x < len(demand_labels) else f"P{x}"
                
                period = st.selectbox(
                    f"{hour}:00",
                    options=list(range(num_periods)),
                    format_func=format_func,
                    index=template['schedule'][hour] if hour < len(template['schedule']) else 0,
                    key=f"template_hour_{rate_type}_{schedule_type}_{selected_template}_{hour}",
                    label_visibility="visible"
                )
                new_schedule.append(period)
        
        submitted = st.form_submit_button("✅ Save Template", type="primary", use_container_width=True)
        
        if submitted:
            template['schedule'] = new_schedule
            st.success(f"✓ Saved template '{template['name']}'")
    
    # Show template preview
    st.markdown("**Template Preview:**")
    preview_df = pd.DataFrame({
        'Hour': [f"{h}:00" for h in range(24)],
        'Period': [template['schedule'][h] for h in range(24)]
    })
    st.dataframe(preview_df, use_container_width=True, height=300)


def _render_month_assignment(schedule_type: str, rate_type: str, data: Dict) -> None:
    """Render the month assignment UI for assigning templates to months."""
    template_key = _get_template_key(schedule_type, rate_type)
    templates = st.session_state[template_key][schedule_type]
    
    if not templates:
        st.warning("No templates available. Add a template in Step 1.")
        return
    
    st.markdown("**Assign each month to a template:**")
    st.info("💡 **Tip**: Typically there are 2-3 unique schedules per year (e.g., Summer, Winter, Shoulder).")
    
    # Initialize month assignments if not present
    for template in templates.values():
        if 'assigned_months' not in template:
            template['assigned_months'] = []
    
    # Create a form for batch updates
    with st.form(f"month_assignment_{rate_type}_{schedule_type}"):
        cols = st.columns(4)
        month_assignments = {}
        
        # Get current assignments
        current_assignments = {}
        for template_name, template in templates.items():
            for month in template.get('assigned_months', []):
                current_assignments[month] = template_name
        
        for month_idx in range(12):
            with cols[month_idx % 4]:
                current_template = current_assignments.get(month_idx, list(templates.keys())[0])
                
                selected = st.selectbox(
                    MONTHS[month_idx],
                    options=list(templates.keys()),
                    index=list(templates.keys()).index(current_template) if current_template in templates else 0,
                    key=f"month_assign_{rate_type}_{schedule_type}_{month_idx}"
                )
                month_assignments[month_idx] = selected
        
        submitted = st.form_submit_button("✅ Apply Month Assignments", type="primary", use_container_width=True)
        
        if submitted:
            # Clear all existing assignments
            for template in templates.values():
                template['assigned_months'] = []
            
            # Apply new assignments
            for month_idx, template_name in month_assignments.items():
                if template_name in templates:
                    templates[template_name]['assigned_months'].append(month_idx)
            
            st.success("✓ Month assignments updated!")
    
    # Show assignment summary
    st.markdown("---")
    st.markdown("**Assignment Summary:**")
    for template_name, template in templates.items():
        assigned_months = template.get('assigned_months', [])
        if assigned_months:
            month_names = [MONTHS[m] for m in sorted(assigned_months)]
            st.write(f"**{template_name}**: {', '.join(month_names)}")
        else:
            st.write(f"**{template_name}**: No months assigned")


def _apply_templates_to_schedule(data: Dict, rate_type: str, same_schedule: bool = False) -> None:
    """Apply templates to generate the final schedule arrays."""
    template_key_weekday = _get_template_key('weekday', rate_type)
    template_key_weekend = _get_template_key('weekend', rate_type)
    
    # Apply weekday templates
    weekday_templates = st.session_state[template_key_weekday]['weekday']
    schedule_key_weekday = _get_schedule_key('weekday', rate_type)
    
    for month_idx in range(12):
        # Find which template is assigned to this month
        assigned_template = None
        for template in weekday_templates.values():
            if month_idx in template.get('assigned_months', []):
                assigned_template = template
                break
        
        if assigned_template:
            data[schedule_key_weekday][month_idx] = assigned_template['schedule'].copy()
    
    # Apply weekend templates
    schedule_key_weekend = _get_schedule_key('weekend', rate_type)
    
    if same_schedule:
        # If schedules are the same, copy weekday templates to weekend
        for month_idx in range(12):
            data[schedule_key_weekend][month_idx] = data[schedule_key_weekday][month_idx].copy()
    else:
        # Apply weekend templates normally
        weekend_templates = st.session_state[template_key_weekend]['weekend']
        
        for month_idx in range(12):
            # Find which template is assigned to this month
            assigned_template = None
            for template in weekend_templates.values():
                if month_idx in template.get('assigned_months', []):
                    assigned_template = template
                    break
            
            if assigned_template:
                data[schedule_key_weekend][month_idx] = assigned_template['schedule'].copy()


def _render_advanced_schedule_editor(data: Dict, num_periods: int) -> None:
    """Render an advanced schedule editor with template-based customization."""
    st.markdown("Configure schedules using templates. Define 2-3 unique schedules and assign them to months.")
    
    # Initialize templates in session state if not present
    if 'energy_schedule_templates' not in st.session_state:
        st.session_state.energy_schedule_templates = {
            'weekday': _initialize_default_templates(data, 'energyweekdayschedule', num_periods),
            'weekend': _initialize_default_templates(data, 'energyweekendschedule', num_periods)
        }
    
    # Initialize same schedule flag if not present
    if 'energy_schedule_same_for_weekday_weekend' not in st.session_state:
        st.session_state.energy_schedule_same_for_weekday_weekend = False
    
    # Add checkbox to indicate same schedule for weekday and weekend
    same_schedule = st.checkbox(
        "Weekday and weekend schedules are the same",
        value=st.session_state.energy_schedule_same_for_weekday_weekend,
        key="energy_same_schedule_checkbox",
        help="Check this box if your tariff has the same time-of-use schedule for weekdays and weekends. You'll only need to configure the weekday schedule."
    )
    st.session_state.energy_schedule_same_for_weekday_weekend = same_schedule
    
    # If schedules are the same, only allow editing weekday
    if same_schedule:
        schedule_type_lower = 'weekday'
        st.info("ℹ️ You are editing the schedule for both weekdays and weekends. The weekend schedule will automatically match the weekday schedule.")
    else:
        schedule_type = st.radio("Schedule to edit:", ["Weekday", "Weekend"], horizontal=True, key="energy_schedule_type")
        schedule_type_lower = schedule_type.lower()
    
    # Three-step process
    st.markdown("---")
    st.markdown("### Step 1: Manage Templates")
    if same_schedule:
        st.info("💡 **Tip**: Create a template for each unique schedule that will occur in the tariff over a given year. For example, if your tariff has different rates for Summer, Winter, and Shoulder seasons, create three templates.")
    else:
        st.info("💡 **Tip**: Create a template for each unique schedule that will occur in the tariff over a given year. For example, if your tariff has different rates for Summer, Winter, and Shoulder seasons, create three templates. **Remember to do this separately for Weekdays and Weekends** using the toggle button above.")
    _render_template_manager(schedule_type_lower, 'energy', num_periods, data)
    
    st.markdown("---")
    st.markdown("### Step 2: Edit Templates")
    _render_template_editor(schedule_type_lower, 'energy', num_periods, data)
    
    st.markdown("---")
    st.markdown("### Step 3: Assign Templates to Months")
    _render_month_assignment(schedule_type_lower, 'energy', data)
    
    # Apply templates to generate final schedules
    _apply_templates_to_schedule(data, 'energy', same_schedule)


def _render_simple_demand_schedule_editor(data: Dict, num_periods: int) -> None:
    """Render a simple demand schedule editor that applies the same pattern to all months."""
    st.markdown("#### Weekday Demand Schedule")
    st.info("💡 **Tip**: Fill in all hours, then click 'Apply Demand Schedule' at the bottom to update.")
    
    # Get demand labels
    demand_labels = data.get('demandlabels', [f"Period {i}" for i in range(num_periods)])
    
    # Use a form to batch all 24+ hour selections
    form_key = f"simple_demand_schedule_form_{num_periods}_{id(data)}"
    with st.form(form_key, clear_on_submit=False):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("**Set demand periods for a typical weekday:**")
            weekday_pattern = []
            
            # Create 24 hour selections
            for hour in range(24):
                period = st.selectbox(
                    f"Hour {hour}:00",
                    options=list(range(num_periods)),
                    format_func=lambda x: f"{demand_labels[x]} (Period {x})",
                    key=f"simple_demand_weekday_{hour}",
                    index=data['demandweekdayschedule'][0][hour] if hour < len(data['demandweekdayschedule'][0]) else 0
                )
                weekday_pattern.append(period)
        
        with col2:
            st.markdown("**Current Schedule:**")
            # Show current schedule from data
            current_schedule_df = pd.DataFrame({
                'Hour': [f"{h}:00" for h in range(24)],
                'Period': [demand_labels[data['demandweekdayschedule'][0][h]] for h in range(24)]
            })
            st.dataframe(current_schedule_df, use_container_width=True, height=600)
        
        st.markdown("---")
        st.markdown("#### Weekend Demand Schedule")
        
        weekend_same = st.checkbox(
            "Use same schedule for weekends",
            value=True,
            help="If checked, weekend will use the same schedule as weekdays",
            key="demand_weekend_same"
        )
        
        weekend_pattern = []
        if not weekend_same:
            st.markdown("**Set demand periods for a typical weekend:**")
            cols = st.columns(4)
            
            for hour in range(24):
                with cols[hour % 4]:
                    period = st.selectbox(
                        f"Hr {hour}",
                        options=list(range(num_periods)),
                        format_func=lambda x: f"P{x}",
                        key=f"simple_demand_weekend_{hour}",
                        index=data['demandweekendschedule'][0][hour] if hour < len(data['demandweekendschedule'][0]) else 0,
                        label_visibility="visible"
                    )
                    weekend_pattern.append(period)
        
        # Form submit button
        submitted = st.form_submit_button("✅ Apply Demand Schedule", type="primary", use_container_width=True)
        
        if submitted:
            # Apply pattern to all months
            data['demandweekdayschedule'] = [weekday_pattern for _ in range(12)]
            
            if weekend_same:
                data['demandweekendschedule'] = [weekday_pattern for _ in range(12)]
            else:
                data['demandweekendschedule'] = [weekend_pattern for _ in range(12)]
            
            st.success("✓ Demand schedule updated for all months!")


def _render_advanced_demand_schedule_editor(data: Dict, num_periods: int) -> None:
    """Render an advanced demand schedule editor with template-based customization."""
    st.markdown("Configure demand schedules using templates. Define 2-3 unique schedules and assign them to months.")
    
    # Initialize templates in session state if not present
    if 'demand_schedule_templates' not in st.session_state:
        st.session_state.demand_schedule_templates = {
            'weekday': _initialize_default_templates(data, 'demandweekdayschedule', num_periods),
            'weekend': _initialize_default_templates(data, 'demandweekendschedule', num_periods)
        }
    
    # Initialize same schedule flag if not present
    if 'demand_schedule_same_for_weekday_weekend' not in st.session_state:
        st.session_state.demand_schedule_same_for_weekday_weekend = False
    
    # Add checkbox to indicate same schedule for weekday and weekend
    same_schedule = st.checkbox(
        "Weekday and weekend schedules are the same",
        value=st.session_state.demand_schedule_same_for_weekday_weekend,
        key="demand_same_schedule_checkbox",
        help="Check this box if your tariff has the same time-of-use schedule for weekdays and weekends. You'll only need to configure the weekday schedule."
    )
    st.session_state.demand_schedule_same_for_weekday_weekend = same_schedule
    
    # If schedules are the same, only allow editing weekday
    if same_schedule:
        schedule_type_lower = 'weekday'
        st.info("ℹ️ You are editing the schedule for both weekdays and weekends. The weekend schedule will automatically match the weekday schedule.")
    else:
        schedule_type = st.radio("Schedule to edit:", ["Weekday", "Weekend"], horizontal=True, key="demand_schedule_type")
        schedule_type_lower = schedule_type.lower()
    
    # Three-step process
    st.markdown("---")
    st.markdown("### Step 1: Manage Templates")
    if same_schedule:
        st.info("💡 **Tip**: Create a template for each unique schedule that will occur in the tariff over a given year. For example, if your tariff has different rates for Summer, Winter, and Shoulder seasons, create three templates.")
    else:
        st.info("💡 **Tip**: Create a template for each unique schedule that will occur in the tariff over a given year. For example, if your tariff has different rates for Summer, Winter, and Shoulder seasons, create three templates. **Remember to do this separately for Weekdays and Weekends** using the toggle button above.")
    _render_template_manager(schedule_type_lower, 'demand', num_periods, data)
    
    st.markdown("---")
    st.markdown("### Step 2: Edit Templates")
    _render_template_editor(schedule_type_lower, 'demand', num_periods, data)
    
    st.markdown("---")
    st.markdown("### Step 3: Assign Templates to Months")
    _render_month_assignment(schedule_type_lower, 'demand', data)
    
    # Apply templates to generate final schedules
    _apply_templates_to_schedule(data, 'demand', same_schedule)


def _show_schedule_heatmap(schedule: List[List[int]], schedule_type: str, labels: List[str], 
                          rate_structure: List[List[Dict]] = None, rate_type: str = 'energy') -> None:
    """Display a heatmap visualization of the schedule.
    
    Args:
        schedule: 12x24 array of period indices
        schedule_type: Description of schedule (e.g., "Weekday", "Demand Weekday")
        labels: Period labels
        rate_structure: Optional rate structure to display actual values instead of periods
        rate_type: Type of rate ('energy' or 'demand') for formatting
    """
    # Create DataFrame for the heatmap
    if rate_structure is not None:
        # Map period indices to actual rate values
        rate_values = []
        for month_schedule in schedule:
            month_rates = []
            for period_idx in month_schedule:
                if period_idx < len(rate_structure):
                    rate = rate_structure[period_idx][0].get('rate', 0.0)
                    adj = rate_structure[period_idx][0].get('adj', 0.0)
                    total_rate = rate + adj
                    month_rates.append(total_rate)
                else:
                    month_rates.append(0.0)
            rate_values.append(month_rates)
        
        schedule_df = pd.DataFrame(rate_values, index=MONTHS, columns=HOURS)
        value_label = "Rate ($/kW)" if rate_type == 'demand' else "Rate ($/kWh)"
    else:
        # Display period indices
        schedule_df = pd.DataFrame(schedule, index=MONTHS, columns=HOURS)
        value_label = "Period Index"
    
    # Display as styled dataframe with fallback if matplotlib not available
    try:
        st.dataframe(
            schedule_df.style.background_gradient(cmap='RdYlGn_r', axis=None).format("{:.4f}" if rate_structure else "{:.0f}"),
            use_container_width=True
        )
    except ImportError:
        # Fallback to plain dataframe if matplotlib not available
        st.dataframe(schedule_df, use_container_width=True)
        st.caption("⚠️ Install matplotlib for color-coded heatmap visualization")
    
    # Show legend
    st.markdown("**Period Legend:**")
    legend_cols = st.columns(min(len(labels), 4))
    for i, label in enumerate(labels):
        with legend_cols[i % 4]:
            if rate_structure is not None and i < len(rate_structure):
                rate = rate_structure[i][0].get('rate', 0.0)
                adj = rate_structure[i][0].get('adj', 0.0)
                total_rate = rate + adj
                if rate_type == 'demand':
                    st.markdown(f"**{i}:** {label} (${total_rate:.4f}/kW)")
                else:
                    st.markdown(f"**{i}:** {label} (${total_rate:.5f}/kWh)")
            else:
                st.markdown(f"**{i}:** {label}")


def _render_demand_charges_section() -> None:
    """Render the demand charges section of the tariff builder."""
    st.markdown("### 🔌 Demand Charge Structure (Optional)")
    st.markdown("""
    Define Time-of-Use demand charges if your tariff has them. Leave this section 
    empty if your tariff only has flat demand charges or no demand charges.
    """)
    
    data = st.session_state.tariff_builder_data['items'][0]
    
    has_demand = st.checkbox(
        "This tariff has TOU demand charges",
        value=len(data.get('demandratestructure', [])) > 0,
        help="Check if this tariff has time-varying demand charges"
    )
    
    if not has_demand:
        data['demandratestructure'] = []
        data['demandweekdayschedule'] = []
        data['demandweekendschedule'] = []
        st.info("ℹ️ No TOU demand charges configured. You can still set flat demand charges in the next tab.")
        return
    
    # Number of demand periods
    num_periods = st.number_input(
        "Number of Demand Periods",
        min_value=1,
        max_value=12,
        value=max(1, len(data.get('demandratestructure', []))),
        help="How many different demand rate periods?"
    )
    
    st.info("💡 **Tip**: If your tariff has hours when no TOU-based demand charge applies (separate from flat monthly demands), include a period with a $0.00 rate. This allows you to schedule those zero-charge hours in the demand schedule below.")
    
    # Adjust arrays
    if len(data['demandratestructure']) != num_periods:
        data['demandratestructure'] = [
            [{"rate": 0.0, "adj": 0.0}] 
            for _ in range(num_periods)
        ]
        data['demandweekdayschedule'] = [[0] * 24 for _ in range(12)]
        data['demandweekendschedule'] = [[0] * 24 for _ in range(12)]
        data['demandlabels'] = [f"Period {i}" for i in range(num_periods)]
    
    # Ensure demandlabels exists and has correct length
    if 'demandlabels' not in data or len(data['demandlabels']) != num_periods:
        data['demandlabels'] = [f"Period {i}" for i in range(num_periods)]
    
    st.markdown("---")
    
    # Create input fields for each period
    for i in range(num_periods):
        with st.expander(f"🔌 Demand Period {i}", expanded=(i == 0)):
            # Label input
            label = st.text_input(
                "Period Label",
                value=data['demandlabels'][i] if i < len(data['demandlabels']) else f"Period {i}",
                help="e.g., 'Peak', 'Mid-Peak', 'Off-Peak', 'No Charge'",
                key=f"demand_label_{num_periods}_{i}"
            )
            data['demandlabels'][i] = label
            
            col1, col2 = st.columns(2)
            
            with col1:
                rate = st.number_input(
                    "Base Rate ($/kW)",
                    min_value=0.0,
                    max_value=100.0,
                    value=data['demandratestructure'][i][0].get('rate', 0.0),
                    format="%.4f",
                    step=0.1,
                    help="Base demand rate in dollars per kW",
                    key=f"demand_rate_{i}"
                )
                data['demandratestructure'][i][0]['rate'] = rate
            
            with col2:
                adj = st.number_input(
                    "Adjustment ($/kW)",
                    min_value=-10.0,
                    max_value=10.0,
                    value=data['demandratestructure'][i][0].get('adj', 0.0),
                    format="%.4f",
                    step=0.1,
                    help="Rate adjustment (can be negative)",
                    key=f"demand_adj_{i}"
                )
                data['demandratestructure'][i][0]['adj'] = adj
            
            total_rate = rate + adj
            st.info(f"**Total Rate:** ${total_rate:.4f}/kW")
    
    # Comments
    st.markdown("---")
    data['demandcomments'] = st.text_area(
        "Demand Charge Comments (optional)",
        value=data.get('demandcomments', ''),
        help="Additional notes about demand charges"
    )
    
    # Demand Schedule Configuration
    st.markdown("---")
    st.markdown("### 📅 Demand Charge Schedule")
    st.markdown("""
    Configure when each demand charge period applies throughout the year.
    """)
    
    demand_schedule_mode = st.radio(
        "Schedule Configuration",
        options=["Simple (same for all months)", "Advanced (different by month)"],
        help="Simple mode applies the same daily pattern to all months",
        key="demand_schedule_mode"
    )
    
    if demand_schedule_mode == "Simple (same for all months)":
        _render_simple_demand_schedule_editor(data, num_periods)
    else:
        _render_advanced_demand_schedule_editor(data, num_periods)
    
    # Show schedule preview
    st.markdown("---")
    st.markdown("#### 📊 Demand Schedule Preview")
    
    tab1, tab2 = st.tabs(["Weekday Schedule", "Weekend Schedule"])
    
    with tab1:
        _show_schedule_heatmap(data['demandweekdayschedule'], "Demand Weekday", 
                              data.get('demandlabels', [f"Period {i}" for i in range(num_periods)]),
                              rate_structure=data.get('demandratestructure'),
                              rate_type='demand')
    
    with tab2:
        _show_schedule_heatmap(data['demandweekendschedule'], "Demand Weekend",
                              data.get('demandlabels', [f"Period {i}" for i in range(num_periods)]),
                              rate_structure=data.get('demandratestructure'),
                              rate_type='demand')


def _render_flat_demand_section() -> None:
    """Render the flat demand charges section."""
    st.markdown("### 📊 Flat Demand Charges")
    st.markdown("""
    Define monthly flat demand charges. These are demand charges that don't vary by time of day.
    """)
    
    data = st.session_state.tariff_builder_data['items'][0]
    
    # Seasonal or monthly
    demand_type = st.radio(
        "Flat Demand Structure",
        options=["Same for all months", "Seasonal (different rates for different months)"],
        help="How do flat demand charges vary?"
    )
    
    if demand_type == "Same for all months":
        col1, col2 = st.columns(2)
        
        with col1:
            rate = st.number_input(
                "Flat Demand Rate ($/kW)",
                min_value=0.0,
                max_value=100.0,
                value=data['flatdemandstructure'][0][0].get('rate', 0.0),
                format="%.4f",
                step=0.1,
                help="Monthly demand charge per kW"
            )
            data['flatdemandstructure'][0][0]['rate'] = rate
        
        with col2:
            adj = st.number_input(
                "Adjustment ($/kW)",
                min_value=-10.0,
                max_value=10.0,
                value=data['flatdemandstructure'][0][0].get('adj', 0.0),
                format="%.4f",
                step=0.1,
                help="Rate adjustment"
            )
            data['flatdemandstructure'][0][0]['adj'] = adj
        
        # Apply to all months
        data['flatdemandmonths'] = [0] * 12
        
        total_rate = rate + adj
        st.info(f"**Total Flat Demand Rate:** ${total_rate:.4f}/kW for all months")
    
    else:
        st.markdown("#### Define Seasonal Demand Rates")
        
        num_seasons = st.number_input(
            "Number of Seasons",
            min_value=1,
            max_value=12,
            value=max(1, len(data.get('flatdemandstructure', [[]]))),
            help="e.g., 2 for summer/winter, 4 for quarterly"
        )
        
        # Adjust structure
        if len(data['flatdemandstructure']) != num_seasons:
            data['flatdemandstructure'] = [
                [{"rate": 0.0, "adj": 0.0}] 
                for _ in range(num_seasons)
            ]
        
        # Rate inputs for each season
        for i in range(num_seasons):
            with st.expander(f"Season {i}", expanded=(i == 0)):
                col1, col2 = st.columns(2)
                
                with col1:
                    rate = st.number_input(
                        "Rate ($/kW)",
                        min_value=0.0,
                        value=data['flatdemandstructure'][i][0].get('rate', 0.0),
                        format="%.4f",
                        key=f"flat_demand_rate_{i}"
                    )
                    data['flatdemandstructure'][i][0]['rate'] = rate
                
                with col2:
                    adj = st.number_input(
                        "Adjustment ($/kW)",
                        min_value=-10.0,
                        max_value=10.0,
                        value=data['flatdemandstructure'][i][0].get('adj', 0.0),
                        format="%.4f",
                        key=f"flat_demand_adj_{i}"
                    )
                    data['flatdemandstructure'][i][0]['adj'] = adj
        
        # Month assignments
        st.markdown("#### Assign Months to Seasons")
        st.markdown("Select which season applies to each month:")
        
        cols = st.columns(4)
        for month_idx, month in enumerate(MONTHS):
            with cols[month_idx % 4]:
                season = st.selectbox(
                    month,
                    options=list(range(num_seasons)),
                    format_func=lambda x: f"Season {x}",
                    key=f"flat_demand_month_{month_idx}",
                    index=data['flatdemandmonths'][month_idx] if month_idx < len(data['flatdemandmonths']) else 0
                )
                data['flatdemandmonths'][month_idx] = season


def _render_fixed_charges_section() -> None:
    """Render the fixed charges section."""
    st.markdown("### 💰 Fixed Monthly Charges")
    st.markdown("Define fixed charges that are applied regardless of usage.")
    
    data = st.session_state.tariff_builder_data['items'][0]
    
    col1, col2 = st.columns(2)
    
    with col1:
        fixed_charge = st.number_input(
            "Fixed Monthly Charge ($)",
            min_value=0.0,
            max_value=10000.0,
            value=data.get('fixedchargefirstmeter', 0.0),
            format="%.2f",
            step=1.0,
            help="Monthly customer charge or service charge"
        )
        data['fixedchargefirstmeter'] = fixed_charge
    
    with col2:
        charge_units = st.selectbox(
            "Charge Units",
            options=["$/month", "$/day", "$/year"],
            index=["$/month", "$/day", "$/year"].index(data.get('fixedchargeunits', '$/month')),
            help="How is the fixed charge billed?"
        )
        data['fixedchargeunits'] = charge_units
    
    st.info(f"**Total Fixed Charge:** ${fixed_charge:.2f} {charge_units}")


def _render_preview_and_save_section() -> None:
    """Render the preview and save section."""
    st.markdown("### 🔍 Preview & Save Tariff")
    st.markdown("Review your tariff configuration and save it as a JSON file.")
    
    data = st.session_state.tariff_builder_data
    
    # Validation
    is_valid, validation_messages = _validate_tariff(data['items'][0])
    
    if not is_valid:
        st.error("❌ **Validation Issues:**")
        for msg in validation_messages:
            st.error(f"• {msg}")
        st.warning("⚠️ Please fix the issues above before saving.")
    else:
        st.success("✅ Tariff configuration is valid!")
    
    # Preview JSON
    with st.expander("📄 Preview JSON", expanded=False):
        st.json(data)
    
    # Summary
    st.markdown("---")
    st.markdown("#### 📊 Tariff Summary")
    
    tariff_data = data['items'][0]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Utility", tariff_data.get('utility', 'N/A'))
        st.metric("Rate Name", tariff_data.get('name', 'N/A'))
    
    with col2:
        st.metric("Sector", tariff_data.get('sector', 'N/A'))
        st.metric("Energy Periods", len(tariff_data.get('energyratestructure', [])))
    
    with col3:
        st.metric("Fixed Charge", f"${tariff_data.get('fixedchargefirstmeter', 0):.2f}")
        has_tou_demand = len(tariff_data.get('demandratestructure', [])) > 0
        st.metric("TOU Demand", "Yes" if has_tou_demand else "No")
    
    # Save section
    st.markdown("---")
    st.markdown("#### 💾 Save Tariff")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        filename = st.text_input(
            "Filename",
            value=_generate_filename(tariff_data),
            help="Name for the JSON file (without .json extension)"
        )
    
    with col2:
        st.markdown("")  # Spacing
        st.markdown("")  # Spacing
        
        if st.button("💾 Save Tariff", type="primary", disabled=not is_valid, use_container_width=True):
            _save_tariff(data, filename)
    
    # Reset button
    if st.button("🔄 Reset Form", help="Clear all data and start over"):
        st.session_state.tariff_builder_data = _create_empty_tariff_structure()
        st.rerun()


def _show_section_validation(section: str, data: Dict) -> None:
    """Show validation status for a section."""
    if section == "basic_info":
        missing = []
        if not data.get('utility'):
            missing.append("Utility Company Name")
        if not data.get('name'):
            missing.append("Rate Schedule Name")
        if not data.get('description'):
            missing.append("Description")
        
        if missing:
            st.warning(f"⚠️ Required fields missing: {', '.join(missing)}")
        else:
            st.success("✅ All required fields completed!")
    
    elif section == "energy_rates":
        has_rates = any(
            rate[0].get('rate', 0) > 0 
            for rate in data.get('energyratestructure', [])
        )
        if not has_rates:
            st.warning("⚠️ At least one energy rate should be greater than 0")
        else:
            st.success("✅ Energy rates configured!")


def _validate_tariff(tariff_data: Dict) -> tuple[bool, List[str]]:
    """
    Validate the tariff configuration.
    
    Returns:
        tuple: (is_valid, list of validation messages)
    """
    messages = []
    
    # Required fields
    if not tariff_data.get('utility'):
        messages.append("Utility company name is required")
    
    if not tariff_data.get('name'):
        messages.append("Rate schedule name is required")
    
    if not tariff_data.get('description'):
        messages.append("Description is required")
    
    # Energy rates validation
    if not tariff_data.get('energyratestructure'):
        messages.append("At least one energy rate period is required")
    else:
        # Check if at least one rate is non-zero
        has_nonzero = any(
            rate[0].get('rate', 0) != 0 
            for rate in tariff_data['energyratestructure']
        )
        if not has_nonzero:
            messages.append("At least one energy rate should be non-zero")
    
    # Check schedules match rate structure
    num_energy_periods = len(tariff_data.get('energyratestructure', []))
    for month_schedule in tariff_data.get('energyweekdayschedule', []):
        if any(period >= num_energy_periods for period in month_schedule):
            messages.append("Energy schedule references non-existent period")
            break
    
    return (len(messages) == 0, messages)


def _generate_filename(tariff_data: Dict) -> str:
    """Generate a filename based on tariff data."""
    utility = tariff_data.get('utility', 'Unknown').replace(' ', '_')
    name = tariff_data.get('name', 'Tariff').replace(' ', '_')
    
    # Clean filename
    filename = f"{utility}_{name}"
    filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
    
    return filename


def _save_tariff(data: Dict, filename: str) -> None:
    """Save the tariff to a JSON file."""
    try:
        # Clean filename
        clean_filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename.strip())
        if not clean_filename.endswith('.json'):
            clean_filename += '.json'
        
        # Create user_data directory if it doesn't exist
        Settings.USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        filepath = Settings.USER_DATA_DIR / clean_filename
        
        # Save the tariff
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        st.success(f"✅ Tariff saved successfully as '{clean_filename}'!")
        st.info("🔄 Refresh the page or reselect from the sidebar to view your new tariff.")
        
        # Offer download button
        json_string = json.dumps(data, indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 Download JSON File",
            data=json_string,
            file_name=clean_filename,
            mime="application/json"
        )
        
    except Exception as e:
        st.error(f"❌ Error saving tariff: {str(e)}")

