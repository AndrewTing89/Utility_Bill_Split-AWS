#!/usr/bin/env python3
"""
Simple SMS sending using Twilio (much easier than AWS SNS)
"""

def setup_twilio_sms():
    """Set up Twilio for SMS - much simpler than AWS"""
    
    print("=== Twilio SMS Setup (Much Easier!) ===")
    print()
    print("Twilio is way easier than AWS for SMS. Here's how:")
    print()
    print("1. Sign up at https://www.twilio.com/try-twilio")
    print("   - You get $15 free credit")
    print("   - No origination number needed for trial")
    print()
    print("2. Get your credentials:")
    print("   - Account SID")
    print("   - Auth Token")
    print("   - Twilio phone number (they give you one)")
    print()
    print("3. Install Twilio Python library:")
    print("   pip install twilio")
    print()
    print("4. Code is super simple:")
    print()
    
    code = '''from twilio.rest import Client

# Your Twilio credentials
account_sid = 'your_account_sid'
auth_token = 'your_auth_token'
twilio_number = '+1234567890'  # They give you this

client = Client(account_sid, auth_token)

message = client.messages.create(
    body='💰 PG&E Bill - August 2025\\nAmount: $96.05\\nVenmo: venmo://paycharge...',
    from_=twilio_number,
    to='+19298884132'
)

print(f"SMS sent! Message SID: {message.sid}")'''
    
    print(code)
    print()
    print("Benefits over AWS:")
    print("✅ No origination number setup needed")
    print("✅ Works immediately after signup")
    print("✅ $15 free credit = ~500 SMS messages")
    print("✅ Much simpler API")
    print("✅ Better for low-volume personal use")
    print()
    print("Cost: ~$0.0075 per SMS (AWS is similar)")

def alternative_email_approach():
    """Alternative: Send Venmo link via email to your phone"""
    
    print("\n=== Alternative: Email-to-SMS Gateway ===")
    print()
    print("Most carriers have email-to-SMS gateways:")
    print()
    print("Verizon: +19298884132@vtext.com")
    print("AT&T: +19298884132@txt.att.net") 
    print("T-Mobile: +19298884132@tmomail.net")
    print("Sprint: +19298884132@messaging.sprintpcs.com")
    print()
    print("You can send an email to your phone number @ carrier domain")
    print("and it arrives as SMS!")
    print()
    
    code = '''import smtplib
from email.mime.text import MIMEText

# Send via Gmail SMTP (you already have this set up)
def send_sms_via_email(venmo_url, amount):
    msg = MIMEText(f"💰 PG&E: ${amount}\\n{venmo_url}")
    msg['From'] = 'andrewhting@gmail.com'
    msg['To'] = '+19298884132@vtext.com'  # Your carrier's SMS gateway
    msg['Subject'] = ''  # Keep empty for SMS
    
    # Use your existing Gmail SMTP setup
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('andrewhting@gmail.com', 'your_app_password')
    server.send_message(msg)
    server.quit()'''
    
    print(code)
    print()
    print("✅ No new accounts needed")
    print("✅ Uses your existing Gmail setup")
    print("✅ Works immediately")
    print("✅ Completely free")

if __name__ == '__main__':
    setup_twilio_sms()
    alternative_email_approach()
    
    print("\n" + "="*50)
    print("RECOMMENDATION:")
    print("Try the email-to-SMS approach first - it's free and uses")
    print("your existing Gmail setup. If that doesn't work well,")
    print("go with Twilio (super easy and cheap).")