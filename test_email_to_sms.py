#!/usr/bin/env python3
"""
Test email-to-SMS functionality
"""

import smtplib
from email.mime.text import MIMEText
import json
import boto3

def test_email_to_sms():
    """Test sending Venmo link via email-to-SMS"""
    
    print("=== Testing Email-to-SMS ===")
    print()
    
    # Common carrier gateways
    carriers = {
        'verizon': '+19298884132@vtext.com',
        'att': '+19298884132@txt.att.net', 
        't-mobile': '+19298884132@tmomail.net',
        'sprint': '+19298884132@messaging.sprintpcs.com',
        'us-cellular': '+19298884132@email.uscc.net'
    }
    
    print("Which carrier are you on?")
    for i, (name, gateway) in enumerate(carriers.items(), 1):
        print(f"{i}. {name.title()}: {gateway}")
    
    choice = input("\nEnter number (1-5): ")
    
    carrier_names = list(carriers.keys())
    if choice.isdigit() and 1 <= int(choice) <= len(carrier_names):
        carrier = carrier_names[int(choice) - 1]
        sms_gateway = carriers[carrier]
        print(f"Selected: {carrier.title()} -> {sms_gateway}")
    else:
        print("Invalid choice, using Verizon as default")
        carrier = 'verizon'
        sms_gateway = carriers['verizon']
    
    # Create test message
    venmo_url = "venmo://paycharge?txn=charge&recipients=UshiLo&amount=96.05&note=PG%26E%20bill%20split%20-%208/08/2025"
    message_body = f"💰 PG&E Bill Test\nAmount: $96.05\n{venmo_url}"
    
    print(f"\nSending test SMS to: {sms_gateway}")
    print("Message preview:")
    print(message_body)
    print()
    
    # Try to get Gmail credentials from AWS Secrets
    try:
        secrets_client = boto3.client('secretsmanager', region_name='us-west-2')
        response = secrets_client.get_secret_value(
            SecretId='arn:aws:secretsmanager:us-west-2:901398601400:secret:pge-bill-automation-secrets-dev-Oq01Wy'
        )
        settings = json.loads(response['SecretString'])
        gmail_user = settings.get('gmail_user', 'andrewhting@gmail.com')
        print(f"Using Gmail account: {gmail_user}")
        
        # Note: We'll need an app password for SMTP
        print("\n⚠️  You'll need a Gmail App Password for SMTP:")
        print("1. Go to https://myaccount.google.com/apppasswords")
        print("2. Generate an app password for 'Mail'")
        print("3. We'll store this in Secrets Manager")
        
        app_password = input("\nEnter your Gmail app password (or press Enter to skip test): ")
        
        if app_password:
            # Send the SMS via email
            msg = MIMEText(message_body)
            msg['From'] = gmail_user
            msg['To'] = sms_gateway
            msg['Subject'] = ''  # Empty subject for SMS
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(gmail_user, app_password)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Test SMS sent to {sms_gateway}!")
            print("Check your phone - you should receive the Venmo link as SMS")
            
            # Save the carrier info for later use
            with open('sms_config.json', 'w') as f:
                json.dump({
                    'carrier': carrier,
                    'sms_gateway': sms_gateway,
                    'phone_number': '+19298884132'
                }, f, indent=2)
            
            print(f"✅ SMS config saved to sms_config.json")
        else:
            print("Skipping test - no app password provided")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTo test manually:")
        print(f"Send an email to: {sms_gateway}")
        print(f"With body: {message_body}")

if __name__ == '__main__':
    test_email_to_sms()