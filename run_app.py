#!/usr/bin/env python3
"""
Launcher script for the URDB Tariff Viewer application.

This script provides a simple way to run the modular application.
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run the URDB Tariff Viewer application."""
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    main_module = script_dir / "src" / "main.py"
    
    if not main_module.exists():
        print("❌ Error: src/main.py not found!")
        print("Make sure you're running this script from the project root directory.")
        sys.exit(1)
    
    print("🚀 Starting URDB Tariff Viewer v2.0...")
    print(f"📁 Running from: {script_dir}")
    print(f"🎯 Main module: {main_module}")
    print("-" * 50)
    
    try:
        # Run streamlit with the main module
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(main_module),
            "--server.headless", "true",
            "--server.enableCORS", "false",
            "--browser.gatherUsageStats", "false"
        ], cwd=script_dir, check=True)
    
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running application: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Error: Streamlit not found!")
        print("Please install streamlit: pip install streamlit")
        sys.exit(1)

if __name__ == "__main__":
    main()
