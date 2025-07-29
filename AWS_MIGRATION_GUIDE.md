# AWS Migration Troubleshooting Guide

This guide documents the challenges encountered while migrating the PG&E Bill Split Automation from a local macOS environment to AWS, along with the solutions implemented.

## Overview

The original project was designed for local macOS execution using:
- Local SQLite database
- Mac Mail app for email sending
- Local PDF generation and storage
- Manual execution via Python scripts

The AWS migration required adapting to:
- DynamoDB for data storage
- Lambda for serverless execution
- App Runner for web hosting
- Email-to-SMS gateways instead of native messaging

## Major Challenges and Solutions

### 1. Lambda Import Errors

**Problem**: 
```
Runtime.ImportModuleError: Unable to import module 'lambda_handler': No module named 'lambda_handler'
```

**Root Cause**: Lambda expects a specific handler file structure that wasn't in the original project.

**Solution**:
- Created `lambda_handler.py` as the entry point
- Properly structured the deployment package with all dependencies
- Ensured the handler path matched Lambda configuration: `lambda_handler.lambda_handler`

### 2. App Runner Python Version Compatibility

**Problem**: 
```
The specified runtime version is not supported
```

**Root Cause**: App Runner has limited Python version support, and our initial attempts used unsupported versions.

**Solution**:
- Tried multiple Python versions (3.11, 3.9, 3.8)
- Final working configuration in `apprunner.yaml`:
```yaml
runtime: python3
run:
  runtime-version: 3.8
```

### 3. Email-to-SMS Gateway Reliability

**Problem**: SMS messages via email gateways were unreliable and sometimes delayed.

**Solution**:
- Implemented dual gateway support:
  - Primary: `number@vtext.com`
  - Backup: `number@mypixmessages.com`
- Both gateways are tried for each message

### 4. Venmo Deep Links in Email

**Problem**: Gmail blocks custom URL schemes like `venmo://` for security reasons.

**Solution**:
- Switched from deep links to HTTPS URLs: `https://venmo.com/username?txn=charge&amount=XX&note=YY`
- These URLs redirect to the app on mobile devices
- Added styled button in HTML emails for better UX

### 5. DynamoDB Decimal Type Handling

**Problem**: DynamoDB requires Decimal types for numeric values, causing type errors with Python floats.

**Solution**:
```python
from decimal import Decimal

# Convert floats to Decimal for DynamoDB
'amount': Decimal(str(round(bill_amount, 2)))
```

### 6. Gmail API Authentication in Lambda

**Problem**: OAuth2 flow doesn't work in serverless environment.

**Solution**:
- Pre-authenticated locally and stored credentials
- Used Gmail App Password for SMTP operations
- Stored all credentials in AWS Secrets Manager

### 7. Email Classification Logic

**Problem**: System was processing payment confirmation emails as new bills.

**Solution**:
- Added `_is_bill_statement()` method to filter emails
- Checks for specific indicators:
  - Must contain "Energy Statement is Ready"
  - Must NOT contain payment confirmation keywords

### 8. App Runner Build Failures

**Problem**: Flask wasn't being installed despite being in requirements.txt.

**Solution**:
- Moved pip install from pre-run to build phase
- Used Python 3.8 which has better build support
- Final working build command:
```yaml
build:
  commands:
    build:
      - pip install --no-cache-dir -r web-ui/requirements.txt
```

### 9. Lambda Package Size

**Problem**: Deployment package exceeded size limits with all dependencies.

**Solution**:
- Used Lambda Layers for large dependencies (Pillow)
- Removed unused imports and features (PDF generation)
- Compressed deployment package efficiently

### 10. Environment Variable Management

**Problem**: Inconsistent environment variables between local and AWS environments.

**Solution**:
- Centralized all config in AWS Secrets Manager
- Used environment variables in Lambda and App Runner
- Created consistent naming convention

## Migration Checklist

1. **Remove Mac-specific dependencies**:
   - ❌ Mac Mail integration
   - ❌ Local AppleScript
   - ❌ macOS-specific paths

2. **Adapt data storage**:
   - ✅ SQLite → DynamoDB
   - ✅ Local files → S3 (removed in final version)
   - ✅ File-based config → Secrets Manager

3. **Update authentication**:
   - ✅ Local OAuth → Pre-authenticated credentials
   - ✅ System keychain → AWS Secrets Manager
   - ✅ Gmail API + App Password hybrid approach

4. **Modify notification system**:
   - ✅ Mac notifications → Email notifications
   - ✅ iMessage → Email-to-SMS gateway
   - ✅ Local alerts → CloudWatch logs

5. **Adjust for serverless**:
   - ✅ Long-running processes → Quick Lambda executions
   - ✅ Local state → Stateless functions
   - ✅ File system → DynamoDB/S3

## Best Practices Learned

1. **Start with minimal functionality** - Get basic features working before adding complexity

2. **Use appropriate Python versions** - AWS services have specific version requirements

3. **Test locally with AWS services** - Use AWS CLI to test DynamoDB, Secrets Manager locally

4. **Log extensively** - CloudWatch logs are crucial for debugging Lambda issues

5. **Handle types carefully** - DynamoDB Decimal vs Python float conversions

6. **Plan for service limits** - Lambda timeout, package size, API rate limits

7. **Use managed services** - App Runner vs EC2, DynamoDB vs RDS

8. **Keep security simple** - URL obscurity can be sufficient for personal projects

## Common Commands

```bash
# Deploy Lambda function
aws lambda update-function-code --function-name pge-bill-automation-automation-dev --zip-file fileb://lambda-function.zip --region us-west-2

# Check Lambda logs
aws logs tail /aws/lambda/pge-bill-automation-automation-dev --region us-west-2 --since 5m

# Update App Runner
# (Automatic from GitHub push)

# Clear DynamoDB for testing
python clear_bills.py

# Test Lambda locally
python -c "from lambda_handler import lambda_handler; lambda_handler({'test_mode': False}, None)"
```

## Conclusion

The migration from local macOS to AWS required significant architectural changes but resulted in a more scalable, automated solution. Key lessons:

- Serverless requires different thinking about state and execution
- AWS managed services reduce operational overhead
- Email-to-SMS gateways are viable alternatives to native SMS
- Simple authentication (URL obscurity) can be appropriate for personal projects

The final solution successfully automates bill processing with minimal ongoing maintenance required.