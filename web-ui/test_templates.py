#!/usr/bin/env python3
"""
Template testing script - tests all templates without AWS dependencies
"""

import os
import sys
sys.path.append('/Users/ndting/Desktop/PGE Split AWS/web-ui')

from flask import Flask
from app_aws import app

# Mock data for testing
mock_bills = [
    {
        'id': 'test-1',
        'amount': 288.15,
        'due_date': '01/15/2025',
        'roommate_portion': 96.05,
        'my_portion': 192.10,
        'processed_date': '2025-01-01',
        'status': 'processed'
    }
]

mock_stats = {
    'total_bills': 1,
    'total_amount': 288.15,
    'total_roommate_portion': 96.05,
    'pending_bills': 0,
    'average_bill': 288.15
}

mock_settings = {
    'test_mode': True,
    'roommate_venmo': 'UshiLo',
    'my_phone': '+19298884132',
    'roommate_email': 'roommate@example.com',
    'my_email': 'your-email@gmail.com'
}

mock_schedule_status = {
    'loaded': True,
    'next_run': 'February 5, 2025 at 2:00 AM PT'
}

def test_all_templates():
    """Test all templates with mock data"""
    with app.test_client() as client:
        with app.app_context():
            
            print("🧪 Testing Templates...")
            
            # Test dashboard template
            try:
                from flask import render_template
                dashboard_html = render_template('dashboard.html', 
                                               bills=mock_bills[:5],
                                               stats=mock_stats,
                                               settings=mock_settings)
                print("✅ Dashboard template - OK")
            except Exception as e:
                print(f"❌ Dashboard template - ERROR: {e}")
            
            # Test bills template
            try:
                bills_html = render_template('bills.html',
                                           bills=mock_bills,
                                           settings=mock_settings)
                print("✅ Bills template - OK")
            except Exception as e:
                print(f"❌ Bills template - ERROR: {e}")
            
            # Test settings template
            try:
                settings_html = render_template('settings.html',
                                              settings=mock_settings,
                                              schedule_status=mock_schedule_status)
                print("✅ Settings template - OK")
            except Exception as e:
                print(f"❌ Settings template - ERROR: {e}")
            
            # Test error template
            try:
                error_html = render_template('error.html', error="Test error message")
                print("✅ Error template - OK")
            except Exception as e:
                print(f"❌ Error template - ERROR: {e}")
            
            print("\n🎉 Template testing complete!")

if __name__ == '__main__':
    test_all_templates()