# 📱 PG&E Bill Split Workflow Summary

## 🔄 Automated Monthly Flow (5th of each month at 9 AM):

1. **Gmail Search** 📧
   - Searches for PG&E bill emails from the last 30 days
   - Extracts: Total amount, due date, calculates split (33%/67%)
   - Saves new bills to DynamoDB

2. **SMS Notification** 📲
   - For each new bill found:
     - Creates Venmo deep link with roommate's portion
     - Sends SMS to your phone (9298884132) via Gmail SMTP
     - Logs timestamp of when SMS was sent
   
3. **Payment Tracking** ✅
   - Checks Gmail for Venmo payment confirmation emails
   - Automatically marks bills as paid when payment is detected

## 🎯 Manual Controls:

### From Dashboard:
- **"Process New Bills"** - Manually trigger the full flow above
- **"Check for Payments"** - Only check for Venmo payment confirmations

### From Bill Details:
- **"Send SMS with Venmo Link"** - Resend SMS for a specific bill
  - Useful if you didn't receive the first SMS
  - Shows timestamp of last SMS sent

## 📊 What Gets Tracked:

For each bill:
- `amount` - Total PG&E bill amount
- `roommate_portion` - 33% split amount
- `due_date` - When payment is due
- `sms_sent` - Whether SMS was sent (true/false)
- `sms_sent_at` - Timestamp of when SMS was sent
- `payment_confirmed` - Whether roommate has paid

## 💬 SMS Format:

```
💰 PG&E Bill - [Month Year]
Amount: $XX.XX
venmo://paycharge?txn=charge&recipients=UshiLo&amount=XX.XX
```

Tapping the link opens Venmo app with:
- Recipient: UshiLo
- Amount: Pre-filled with roommate's portion
- Type: Charge request
- You just need to add a note and send!

## 🚀 Testing Locally:

1. Run `python run_local_dev.py`
2. Access http://localhost:8080
3. Click "Process New Bills" to test the full flow

## ⚙️ Settings:

All settings are stored in AWS Secrets Manager and loaded automatically:
- Gmail credentials for searching bills
- SMS gateway (9298884132@vtext.com for Verizon)
- Split ratios (33% roommate, 67% you)
- Venmo usernames

The system is fully automated - it will run every month on the 5th and handle everything!