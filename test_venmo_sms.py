import smtplib
from email.mime.text import MIMEText

def send_venmo_sms(venmo_url, amount, carrier='verizon'):
    gateways = {
        'verizon': '+19298884132@vtext.com',
        'att': '+19298884132@txt.att.net',
        't-mobile': '+19298884132@tmomail.net',
        'sprint': '+19298884132@messaging.sprintpcs.com'
    }
    
    sms_gateway = gateways[carrier]
    message_body = f"💰 PG&E: ${amount}\n{venmo_url}"
    
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
send_venmo_sms(venmo_url, "96.05", carrier='verizon')  # Change carrier as needed