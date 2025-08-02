#!/usr/bin/env python3
"""
Simple test script to verify the web app upload functionality
"""

import requests
import os
import sys

def test_upload():
    """Test the upload endpoint directly."""
    print("🧪 Testing Power Bill Analysis Web App Upload")
    print("=" * 50)
    
    # Check if Flask app is running
    try:
        response = requests.get('http://127.0.0.1:5000/')
        if response.status_code != 200:
            print("❌ Flask app is not running or not accessible")
            print("   Please start the app first: python app.py")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Flask app is not running")
        print("   Please start the app first: python app.py")
        return False
    
    print("✅ Flask app is running")
    
    # Test with the sample CSV file
    csv_file = 'sample_data/GPC_Usage_2024-06-01-2025-07-14.csv'
    if not os.path.exists(csv_file):
        print(f"❌ Test CSV file not found: {csv_file}")
        return False
    
    print(f"📄 Testing upload with: {csv_file}")
    
    # Test upload
    try:
        with open(csv_file, 'rb') as f:
            files = {'file': f}
            response = requests.post('http://127.0.0.1:5000/upload', files=files)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Upload successful")
                filename = data.get('filename')
                
                # Test analysis
                print(f"🔍 Testing analysis...")
                analysis_response = requests.get(f'http://127.0.0.1:5000/api/analyze/{filename}')
                
                if analysis_response.status_code == 200:
                    analysis_data = analysis_response.json()
                    if analysis_data.get('success'):
                        monthly_results = analysis_data.get('monthly_results', [])
                        print(f"✅ Analysis successful: {len(monthly_results)} months processed")
                        
                        # Show summary
                        summary = analysis_data.get('summary', {})
                        costs = summary.get('annual_costs', {})
                        print(f"\n💰 Annual Cost Summary:")
                        print(f"   Traditional: ${costs.get('traditional', 0):,.2f}")
                        print(f"   TOU-RD-11:  ${costs.get('tou_rd', 0):,.2f}")
                        print(f"   TOU-REO-18: ${costs.get('tou_reo', 0):,.2f}")
                        
                        return True
                    else:
                        print(f"❌ Analysis failed: {analysis_data.get('error', 'Unknown error')}")
                        return False
                else:
                    print(f"❌ Analysis request failed: {analysis_response.status_code}")
                    print(f"   Response: {analysis_response.text}")
                    return False
            else:
                print(f"❌ Upload failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Upload request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

def main():
    if test_upload():
        print("\n🎉 All tests passed! The web app is working correctly.")
        print("\nIf you're getting 'string did not match expected pattern' in the browser:")
        print("1. Try a different browser (Chrome, Firefox, Safari)")
        print("2. Clear browser cache and cookies")
        print("3. Check browser developer tools (F12) for JavaScript errors")
        print("4. Ensure the CSV file is from Georgia Power in the correct format")
        print("5. Try opening: http://127.0.0.1:5000 directly")
    else:
        print("\n❌ Tests failed. Check the error messages above.")
        
if __name__ == "__main__":
    main()