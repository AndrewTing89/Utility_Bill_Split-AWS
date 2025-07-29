# PG&E Bill Automation - Final Setup Checklist

## ✅ Completed
- [x] Lambda function deployed
- [x] DynamoDB tables created
- [x] S3 bucket for PDFs
- [x] EventBridge scheduler (5th of month at 2 AM PT)
- [x] App Runner deployment started
- [x] IAM roles configured

## 📋 Required Actions

### 1. Verify Email Addresses in SES
```bash
# Verify your email
aws ses verify-email-identity \
  --email-address andrewhting@gmail.com \
  --profile pge-automation \
  --region us-west-2

# Verify roommate's email (for production)
aws ses verify-email-identity \
  --email-address [roommate-email] \
  --profile pge-automation \
  --region us-west-2
```

### 2. Test SMS Sending
```bash
# Quick SMS test
aws sns publish \
  --phone-number +19298884132 \
  --message "Test: PG&E automation is working!" \
  --profile pge-automation \
  --region us-west-2
```

### 3. Test Complete Automation
```bash
# Run full test
aws lambda invoke \
  --function-name pge-bill-automation-automation-dev \
  --payload '{"test_mode": true}' \
  response.json \
  --profile pge-automation \
  --region us-west-2

cat response.json
```

### 4. Switch to Production Mode
When ready to go live:
1. Update Lambda environment variable: `TEST_MODE=false`
2. Ensure roommate's email is verified in SES
3. Test one more time before the 5th!

## 🔍 Monitoring
- **CloudWatch Logs**: Check for Lambda execution logs
- **App Runner URL**: Access your dashboard (check App Runner console)
- **Next Scheduled Run**: February 5, 2025 at 2:00 AM PT