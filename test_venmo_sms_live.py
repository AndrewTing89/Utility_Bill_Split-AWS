#!/usr/bin/env python3
"""
Test live Venmo SMS sending
"""

import smtplib
from email.mime.text import MIMEText
from datetime import datetime

def send_venmo_sms_test():
    """Send a test Venmo SMS"""
    
    print("=== Testing Live Venmo SMS ===")
    print()
    
    # Your settings
    gmail_user = 'andrewhting@gmail.com'
    gmail_app_password = 'pgcv uphl aqrm rlqe'  # Your app password
    sms_gateway = '+19298884132@vtext.com'  # Xfinity/Verizon gateway
    
    # Test Venmo URL (same format as your real bills)
    venmo_url = "venmo://paycharge?txn=charge&recipients=UshiLo&amount=96.05&note=PG%26E%20bill%20split%20-%208/08/2025"
    
    # Create SMS message
    message_body = f"💰 PG&E Bill - August 2025\nAmount: $96.05\n{venmo_url}"
    
    print(f"Sending to: {sms_gateway}")
    print("Message:")
    print(message_body)
    print()
    
    try:
        # Create email message
        msg = MIMEText(message_body)
        msg['From'] = gmail_user
        msg['To'] = sms_gateway
        msg['Subject'] = ''  # Empty subject for SMS
        
        # Send via Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_app_password)
        server.send_message(msg)
        server.quit()
        
        print("✅ SMS sent successfully!")
        print("📱 Check your phone - you should receive:")
        print("   1. The Venmo link as SMS")
        print("   2. Tap the link to open Venmo")
        print("   3. It should be pre-filled to charge UshiLo $96.05")
        
    except Exception as e:
        print(f"❌ Error sending SMS: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure your Gmail app password is correct")
        print("2. Try different SMS gateways if this one doesn't work")

if __name__ == '__main__':
    send_venmo_sms_test()