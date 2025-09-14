"""
Main entry point for URDB Tariff Viewer.

This is the new modular main application file that replaces the monolithic app.py.
"""

import streamlit as st
import sys
from pathlib import Path
from typing import Optional

# Add the parent directory to sys.path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import our modular components
from src.config.settings import Settings
from src.utils.styling import apply_custom_css, create_section_header_html, create_custom_divider_html
from src.services.file_service import FileService
from src.models.tariff import TariffViewer, create_temp_viewer_with_modified_tariff
from src.components.sidebar import create_sidebar
from src.components.energy_rates import render_energy_rates_tab
from src.components.demand_rates import render_demand_rates_tab
from src.components.flat_demand_rates import render_flat_demand_rates_tab
from src.components.cost_calculator import render_cost_calculator_tab
from src.components.load_generator import render_load_generator_tab
from src.components.visualizations import display_rate_statistics


def initialize_app(dark_mode: bool = False) -> None:
    """Initialize the Streamlit application.
    
    Args:
        dark_mode (bool): Whether to apply dark mode styling
    """
    # Set page configuration
    st.set_page_config(**Settings.get_streamlit_config())
    
    # Apply custom CSS styling with dark mode support
    apply_custom_css(dark_mode=dark_mode)
    
    # Ensure required directories exist
    Settings.ensure_directories_exist()
    
    # Initialize session state
    if 'modified_tariff' not in st.session_state:
        st.session_state.modified_tariff = None
    if 'has_modifications' not in st.session_state:
        st.session_state.has_modifications = False


def load_tariff_viewer(selected_file: Path) -> Optional[TariffViewer]:
    """
    Load a TariffViewer instance, handling both original and modified tariffs.
    
    Args:
        selected_file (Path): Path to the selected tariff file
        
    Returns:
        Optional[TariffViewer]: TariffViewer instance or None if loading fails
    """
    try:
        # Check if we have modifications for this tariff
        if (st.session_state.get('has_modifications', False) and 
            st.session_state.get('modified_tariff') is not None):
            
            # Use modified tariff data
            return create_temp_viewer_with_modified_tariff(st.session_state.modified_tariff)
        else:
            # Load original tariff
            return TariffViewer(selected_file)
            
    except Exception as e:
        st.error(f"❌ Error loading tariff: {str(e)}")
        st.info("💡 **Troubleshooting Tips:**")
        st.info("• Check that the JSON file is properly formatted")
        st.info("• Ensure the file contains valid URDB tariff data")
        st.info("• Try selecting a different tariff file")
        return None


def handle_tariff_switching(current_tariff_file: Path) -> None:
    """
    Handle switching between tariffs and clear modification state when needed.
    
    Args:
        current_tariff_file (Path): Currently selected tariff file
    """
    # Check if tariff has changed
    if ('last_tariff_file' not in st.session_state or 
        st.session_state.last_tariff_file != current_tariff_file):
        
        st.session_state.last_tariff_file = current_tariff_file
        
        # Clear form states when switching tariffs
        form_state_keys = [
            'form_labels', 'form_rates', 'form_adjustments',
            'demand_form_labels', 'demand_form_rates', 'demand_form_adjustments',
            'flat_demand_form_rates', 'flat_demand_form_adjustments'
        ]
        
        for key in form_state_keys:
            if key in st.session_state:
                del st.session_state[key]
        
        # Clear modification state when switching tariffs (unless it's a user-generated tariff)
        if not str(current_tariff_file).startswith(str(Settings.USER_DATA_DIR)):
            st.session_state.modified_tariff = None
            st.session_state.has_modifications = False


def render_tariff_info_chips(tariff_viewer: TariffViewer) -> None:
    """
    Render the tariff information chips (matches original layout).
    
    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
    """
    # Context chips for quick reference (matching original)
    st.markdown(
        f"""
        <div class="chips">
            <div class="chip">🏢 {tariff_viewer.utility_name}</div>
            <div class="chip">⚡ {tariff_viewer.rate_name}</div>
            <div class="chip">🏭 {tariff_viewer.sector}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_load_profile_analysis_tab(selected_load_profile: Optional[Path], options: dict) -> None:
    """
    Render the load profile analysis tab.
    
    Args:
        selected_load_profile (Optional[Path]): Selected load profile file
        options (dict): Display options
    """
    st.markdown(create_section_header_html("📊 Load Profile Analysis"), unsafe_allow_html=True)
    
    if not selected_load_profile:
        st.info("ℹ️ Select a load profile from the sidebar to analyze.")
        return
    
    try:
        # Load and analyze the profile
        from src.services.calculation_service import CalculationService
        
        validation_results = CalculationService.validate_load_profile(selected_load_profile)
        
        if validation_results['is_valid']:
            # Load the profile data
            profile_df = FileService.load_csv_file(selected_load_profile)
            
            # Show analysis
            from src.components.load_generator import show_load_profile_analysis
            show_load_profile_analysis(profile_df, options)
            
        else:
            st.error("❌ Invalid load profile file")
            for error in validation_results.get('errors', []):
                st.error(f"• {error}")
                
    except Exception as e:
        st.error(f"❌ Error analyzing load profile: {str(e)}")


def render_tariff_information_section(tariff_viewer: TariffViewer) -> None:
    """
    Render the tariff information section.
    
    Args:
        tariff_viewer (TariffViewer): TariffViewer instance
    """
    st.markdown(create_custom_divider_html(), unsafe_allow_html=True)
    st.markdown(create_section_header_html("📋 Tariff Information"), unsafe_allow_html=True)
    
    # Basic information metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Utility Company</h3>
            <p>{tariff_viewer.utility_name}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Rate Schedule</h3>
            <p>{tariff_viewer.rate_name}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Customer Sector</h3>
            <p>{tariff_viewer.sector}</p>
        </div>
        """, unsafe_allow_html=True)
    
    
    # Description
    st.markdown(create_section_header_html("📝 Description"), unsafe_allow_html=True)
    st.markdown(tariff_viewer.description)
    
    # Raw JSON data viewer
    with st.expander("🔍 View Raw JSON Data"):
        st.json(tariff_viewer.data)


def main() -> None:
    """Main application function."""
    # Initialize the application with basic CSS first
    initialize_app(dark_mode=False)
    
    # Create sidebar and get selections
    selected_tariff_file, selected_load_profile, sidebar_options = create_sidebar()
    
    # Apply dark mode CSS if enabled
    if sidebar_options.get('dark_mode', False):
        from src.utils.styling import get_dark_mode_css
        st.markdown(get_dark_mode_css(), unsafe_allow_html=True)
    
    # Handle case where no tariff file is selected
    if not selected_tariff_file:
        st.error("❌ No tariff file selected. Please select a tariff from the sidebar.")
        st.stop()
    
    # Handle tariff switching
    handle_tariff_switching(selected_tariff_file)
    
    # Load tariff viewer
    tariff_viewer = load_tariff_viewer(selected_tariff_file)
    
    if not tariff_viewer:
        st.error("❌ Failed to load tariff data.")
        st.stop()
    
    # Render tariff info chips (matches original layout)
    render_tariff_info_chips(tariff_viewer)
    
    # Create main tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "⚡ Energy Rates", 
        "🔌 Demand Rates", 
        "📊 Flat Demand", 
        "💰 Utility Cost Calculator", 
        "🔧 Load Profile Generator", 
        "📊 LP Analysis"
    ])
    
    # Render each tab
    with tab1:
        render_energy_rates_tab(tariff_viewer, sidebar_options)
    
    with tab2:
        render_demand_rates_tab(tariff_viewer, sidebar_options)
    
    with tab3:
        render_flat_demand_rates_tab(tariff_viewer, sidebar_options)
    
    with tab4:
        render_cost_calculator_tab(tariff_viewer, selected_load_profile, sidebar_options)
    
    with tab5:
        render_load_generator_tab(tariff_viewer, sidebar_options)
    
    with tab6:
        render_load_profile_analysis_tab(selected_load_profile, sidebar_options)
    
    # Render tariff information section at the bottom
    render_tariff_information_section(tariff_viewer)


if __name__ == "__main__":
    main()
