#!/usr/bin/env python3
"""
Test the web app SMS functionality
"""

import requests
import json

def test_web_app_sms():
    """Test SMS sending via the web app"""
    
    print("=== Testing Web App SMS Integration ===")
    print()
    
    # Your web app URL
    web_url = "https://kyf5cqt8ci.us-west-2.awsapprunner.com"
    
    # Test with your existing bill
    bill_id = "pge_8_08_2025_28814"
    
    print(f"Testing with bill: {bill_id}")
    print(f"Web app: {web_url}")
    print()
    
    try:
        # Make request to create Venmo request (which will send SMS)
        response = requests.post(
            f"{web_url}/api/create-venmo-request",
            json={"bill_id": bill_id},
            headers={"Content-Type": "application/json"}
        )
        
        result = response.json()
        
        print("Response:")
        print(json.dumps(result, indent=2))
        
        if result.get('success') and result.get('sms_sent'):
            print()
            print("🎉 SUCCESS!")
            print("📱 Check your phone - you should receive SMS with Venmo link!")
            print("💰 Tap the link to open Venmo with the charge request ready")
        elif result.get('success'):
            print()
            print("⚠️  Venmo URL created but SMS not sent")
            print(f"Error: {result.get('sms_error', 'Unknown error')}")
        else:
            print()
            print("❌ Request failed")
            print(f"Error: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"❌ Error testing web app: {e}")

if __name__ == '__main__':
    test_web_app_sms()