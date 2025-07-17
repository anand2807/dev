#!/usr/bin/env python3
"""
Launch the Renaissance Options Trading Dashboard
"""

import subprocess
import sys
import os

def main():
    """Launch the Streamlit dashboard"""
    
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    # Set the dashboard file path
    dashboard_file = os.path.join(current_dir, 'src', 'monitoring', 'dashboard.py')
    
    print("🚀 Launching Renaissance Options Trading Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:8501")
    print("🛑 Press Ctrl+C to stop the dashboard")
    print("=" * 60)
    
    try:
        # Launch Streamlit
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 
            dashboard_file,
            '--server.port=8501',
            '--server.address=0.0.0.0',
            '--server.allowRunOnSave=true',
            '--server.runOnSave=true'
        ])
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")
        print("💡 Make sure Streamlit is installed: pip install streamlit")

if __name__ == "__main__":
    main()