# Debugging App Runner Internal Server Error

## Quick Steps to Find the Error

1. **In App Runner Console**:
   - Click on your service
   - Go to **"Logs"** tab
   - Look for **"Application logs"**
   - Find the most recent error message

2. **Common Issues**:
   - Missing environment variables
   - AWS credentials/permissions
   - Database connection errors
   - Import errors

## Quick Test Commands

```bash
# Test Lambda connection
aws lambda invoke \
  --function-name pge-bill-automation-automation-dev \
  --payload '{"test": true}' \
  /tmp/test.json \
  --profile pge-automation \
  --region us-west-2

# Check DynamoDB access
aws dynamodb describe-table \
  --table-name pge-bill-automation-bills-dev \
  --profile pge-automation \
  --region us-west-2
```

## If You Can't Find Application Logs

The error is likely one of these:
1. **IAM Role Issue** - App Runner can't access DynamoDB/Lambda
2. **Import Error** - Missing Python module
3. **Environment Variable** - Missing configuration

Share the application log error and I'll fix it immediately!