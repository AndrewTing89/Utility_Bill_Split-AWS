#!/usr/bin/env python3
"""
Set up email-to-SMS for Venmo notifications
"""

import json

def setup_email_sms():
    """Set up email-to-SMS configuration"""
    
    print("=== Email-to-SMS Setup ===")
    print()
    
    # Common carrier gateways
    carriers = {
        'verizon': '+19298884132@vtext.com',
        'att': '+19298884132@txt.att.net', 
        't-mobile': '+19298884132@tmomail.net',
        'sprint': '+19298884132@messaging.sprintpcs.com'
    }
    
    print("Carrier SMS Gateways:")
    for name, gateway in carriers.items():
        print(f"  {name.title()}: {gateway}")
    
    print()
    print("To test which carrier you're on:")
    print("1. Send a test email to each gateway address")
    print("2. See which one delivers to your phone as SMS")
    print()
    
    # Create SMS configuration for each carrier
    for carrier, gateway in carriers.items():
        config = {
            'carrier': carrier,
            'sms_gateway': gateway,
            'phone_number': '+19298884132'
        }
        
        filename = f'sms_config_{carrier}.json'
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Created config: {filename}")
    
    print()
    print("Next steps:")
    print("1. Get a Gmail App Password:")
    print("   - Go to https://myaccount.google.com/apppasswords")
    print("   - Generate password for 'Mail'")
    print()
    print("2. Test each carrier gateway by sending an email")
    print()
    print("3. Once you find your carrier, we'll integrate it into the app")
    
    # Create a test email function
    test_code = '''import smtplib
from email.mime.text import MIMEText

def send_venmo_sms(venmo_url, amount, carrier='verizon'):
    gateways = {
        'verizon': '+19298884132@vtext.com',
        'att': '+19298884132@txt.att.net',
        't-mobile': '+19298884132@tmomail.net',
        'sprint': '+19298884132@messaging.sprintpcs.com'
    }
    
    sms_gateway = gateways[carrier]
    message_body = f"💰 PG&E: ${amount}\\n{venmo_url}"
    
    msg = MIMEText(message_body)
    msg['From'] = 'andrewhting@gmail.com'
    msg['To'] = sms_gateway
    msg['Subject'] = ''
    
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('andrewhting@gmail.com', 'your_app_password_here')
    server.send_message(msg)
    server.quit()
    
    print(f"SMS sent to {sms_gateway}")

# Test it
venmo_url = "venmo://paycharge?txn=charge&recipients=UshiLo&amount=96.05"
send_venmo_sms(venmo_url, "96.05", carrier='verizon')  # Change carrier as needed'''
    
    with open('test_venmo_sms.py', 'w') as f:
        f.write(test_code)
    
    print()
    print("✅ Created test_venmo_sms.py")
    print("   Edit it with your Gmail app password and run to test")

if __name__ == '__main__':
    setup_email_sms()