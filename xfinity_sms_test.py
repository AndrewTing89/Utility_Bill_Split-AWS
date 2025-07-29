#!/usr/bin/env python3
"""
Test Xfinity Mobile SMS gateways
"""

def test_xfinity_gateways():
    """Test different gateways for Xfinity Mobile"""
    
    print("=== Xfinity Mobile SMS Gateways ===")
    print()
    print("Xfinity Mobile uses Verizon's network, so try these:")
    print()
    
    gateways = [
        '+19298884132@vtext.com',      # Verizon (most likely)
        '+19298884132@txt.att.net',    # Sometimes works
        '+19298884132@mobile.xfinity.com',  # Possible Xfinity gateway
        '+19298884132@xfinity.com',    # Another possibility
    ]
    
    for i, gateway in enumerate(gateways, 1):
        print(f"{i}. {gateway}")
    
    print()
    print("Quick test method:")
    print("1. Send a test email from your Gmail to each address above")
    print("2. Subject: (leave blank)")
    print("3. Body: 'Test SMS from email'")
    print("4. See which one arrives on your phone as SMS")
    print()
    
    # Create test script
    test_code = '''import smtplib
from email.mime.text import MIMEText

def test_sms_gateway(gateway, app_password):
    """Test if a gateway works"""
    
    msg = MIMEText("🧪 Test SMS from email - if you got this, it works!")
    msg['From'] = 'andrewhting@gmail.com'
    msg['To'] = gateway
    msg['Subject'] = ''  # Empty for SMS
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('andrewhting@gmail.com', app_password)
        server.send_message(msg)
        server.quit()
        print(f"✅ Sent test to {gateway}")
        return True
    except Exception as e:
        print(f"❌ Failed to send to {gateway}: {e}")
        return False

# Test all gateways
app_password = "your_gmail_app_password_here"  # Replace with real password

gateways = [
    '+19298884132@vtext.com',
    '+19298884132@txt.att.net', 
    '+19298884132@mobile.xfinity.com',
    '+19298884132@xfinity.com'
]

print("Testing all gateways...")
for gateway in gateways:
    test_sms_gateway(gateway, app_password)
    
print("\\nCheck your phone - whichever gateway delivered SMS is the right one!")'''
    
    with open('test_xfinity_sms.py', 'w') as f:
        f.write(test_code)
    
    print("✅ Created test_xfinity_sms.py")
    print("   Add your Gmail app password and run it to test all gateways")
    print()
    print("Most likely winner: +19298884132@vtext.com (Verizon network)")
    print()
    print("Once you find the working gateway, I'll integrate it into your app!")

if __name__ == '__main__':
    test_xfinity_gateways()