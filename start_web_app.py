#!/usr/bin/env python3
"""
Simple startup script for the Power Bill Analysis Web App
"""

import sys
import subprocess
import webbrowser
import time
import os
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed."""
    required_packages = ['flask', 'pandas', 'numpy']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print(f"Please install them with: pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_analysis_files():
    """Check if required analysis files are present."""
    required_files = [
        'final_exact_analysis.py',
        'corrected_tou_calculator.py', 
        'tou_reo_calculator.py',
        'data_processor.py',
        'demand_calculator.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required analysis files: {', '.join(missing_files)}")
        return False
    
    return True

def main():
    print("🔌 Power Bill Analysis Web App Startup")
    print("=" * 50)
    
    # Check dependencies
    print("📦 Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    print("✅ All required packages are installed")
    
    # Check analysis files
    print("📁 Checking analysis files...")
    if not check_analysis_files():
        print("❌ Please ensure all analysis files are in the current directory")
        sys.exit(1)
    print("✅ All required analysis files are present")
    
    # Create uploads directory if it doesn't exist
    uploads_dir = Path('uploads')
    uploads_dir.mkdir(exist_ok=True)
    
    print("\n🚀 Starting web application...")
    print("📍 URL: http://127.0.0.1:5000")
    print("💡 The app will open in your default browser")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Start the Flask app
    try:
        # Give it a moment to start
        import threading
        import web_app
        
        def start_server():
            web_app.app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False)
        
        server_thread = threading.Thread(target=start_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Wait a moment for server to start
        time.sleep(2)
        
        # Open browser
        webbrowser.open('http://127.0.0.1:5000')
        
        print("🌐 Web app is running!")
        print("📤 Upload your Georgia Power CSV file to get started")
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Shutting down web app...")
            
    except Exception as e:
        print(f"❌ Error starting web app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()