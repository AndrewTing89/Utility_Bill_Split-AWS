#!/usr/bin/env python3
"""
Test all possible SMS gateways for Xfinity Mobile
"""

import smtplib
from email.mime.text import MIMEText
import time

def test_all_xfinity_gateways():
    """Test multiple SMS gateways to find the right one for Xfinity Mobile"""
    
    print("=== Testing All Xfinity Mobile SMS Gateways ===")
    print()
    
    # Your settings
    gmail_user = 'andrewhting@gmail.com'
    gmail_app_password = 'pgcv uphl aqrm rlqe'
    phone_number = '+19298884132'
    
    # All possible gateways for Xfinity Mobile
    gateways = [
        # Verizon network (Xfinity uses Verizon)
        f'{phone_number}@vtext.com',
        f'{phone_number}@vzwpix.com',
        
        # Xfinity specific (less common but possible)
        f'{phone_number}@mobile.xfinity.com',
        f'{phone_number}@xfinity.com',
        f'{phone_number}@comcastpcs.textmsg.com',
        
        # Other major carriers (just in case)
        f'{phone_number}@txt.att.net',
        f'{phone_number}@tmomail.net',
        f'{phone_number}@messaging.sprintpcs.com',
        f'{phone_number}@page.nextel.com',
        
        # Alternative formats
        f'{phone_number}@mms.att.net',
        f'{phone_number}@mymetropcs.com',
        
        # Just the number without +1
        f'9298884132@vtext.com',
        f'9298884132@vzwpix.com',
    ]
    
    print(f"Testing {len(gateways)} different gateways...")
    print("Each will send a numbered test message so you know which one worked.")
    print()
    
    successful_gateways = []
    
    for i, gateway in enumerate(gateways, 1):
        print(f"Testing {i}/{len(gateways)}: {gateway}")
        
        # Create unique test message
        message_body = f"Test #{i}: {gateway.split('@')[1]} gateway"
        
        try:
            msg = MIMEText(message_body)
            msg['From'] = gmail_user
            msg['To'] = gateway
            msg['Subject'] = ''  # Empty for SMS
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(gmail_user, gmail_app_password)
            server.send_message(msg)
            server.quit()
            
            print(f"   ✅ Sent to {gateway}")
            successful_gateways.append((i, gateway))
            
            # Small delay between sends
            time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ Failed: {gateway} - {e}")
    
    print()
    print("=" * 50)
    print("TEST COMPLETE!")
    print()
    print("Now check your phone for SMS messages.")
    print("Whichever message(s) you receive, note the test number.")
    print()
    print("Sent successfully to:")
    for test_num, gateway in successful_gateways:
        print(f"  Test #{test_num}: {gateway}")
    
    print()
    print("Once you know which test number worked, we'll use that gateway!")

if __name__ == '__main__':
    test_all_xfinity_gateways()