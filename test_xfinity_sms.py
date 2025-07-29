import smtplib
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
    
print("\nCheck your phone - whichever gateway delivered SMS is the right one!")