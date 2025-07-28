# Deployment Guide

Complete guide for deploying the PG&E Bill Split Automation to AWS Lambda.

## 🏗️ Architecture Overview

The AWS deployment uses serverless architecture for 100% reliability:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   EventBridge   │───▶│   AWS Lambda    │───▶│   DynamoDB      │
│  (Monthly Cron) │    │  (Automation)   │    │  (Bill Data)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      SNS        │◀───│    Gmail API    │───▶│       S3        │
│ (SMS Alerts)    │    │ (Email Parser)  │    │ (PDF Storage)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │      SES        │
                       │ (Email Sending) │
                       └─────────────────┘
```

## 🚀 Deployment Steps

### 1. Prerequisites

Ensure you have:
- [x] AWS CLI installed and configured
- [x] Python 3.9+ installed
- [x] Gmail API credentials (`credentials.json`)
- [x] Completed initial authentication (`token.json`)

### 2. Configuration

**Update Settings**
Edit `config/settings.json`:

```json
{
  "gmail_user": "your-email@gmail.com",
  "roommate_email": "roommate@gmail.com",
  "my_email": "your-email@gmail.com", 
  "roommate_venmo": "roommate-venmo",
  "my_venmo": "your-venmo",
  "my_phone": "+1234567890",
  "roommate_split_ratio": 0.333333,
  "my_split_ratio": 0.666667,
  "test_mode": true
}
```

### 3. Deploy Infrastructure

```bash
cd deployment/
./deploy.sh dev
```

This will:
1. ✅ Create deployment package
2. ✅ Deploy CloudFormation stack
3. ✅ Update Lambda function
4. ✅ Test deployment
5. ✅ Display summary

### 4. Configure AWS Services

**Set up SES (Email)**
1. Go to AWS SES Console
2. Verify email addresses:
   - Your email
   - Roommate's email
3. Request production access (to send to unverified emails)

**Test Email Sending**
```bash
aws ses send-email \
  --source your-email@gmail.com \
  --destination ToAddresses=roommate@gmail.com \
  --message Subject={Data="Test"},Body={Text={Data="Test email"}}
```

### 5. Production Deployment

After testing thoroughly in dev:

```bash
# Update settings for production
vim config/settings.json  # Set test_mode: false

# Deploy to production
./deploy.sh prod
```

## 📅 Scheduling

The system runs automatically:
- **When**: 5th of each month
- **Time**: 9:00 AM PST (5:00 PM UTC)
- **Trigger**: EventBridge rule
- **Target**: Lambda function

**Manual Testing**
```bash
aws lambda invoke \
  --function-name pge-bill-automation-dev \
  --payload '{"test_mode": true}' \
  response.json
```

## 🔧 Management

### Update Code Only
```bash
./deploy.sh dev --code-only
```

### Update Configuration
```bash
# Update secrets in AWS
aws secretsmanager update-secret \
  --secret-id pge-bill-automation-config-dev \
  --secret-string file://config/settings.json
```

### View Logs
```bash
aws logs tail /aws/lambda/pge-bill-automation-dev --follow
```

### Check Bills Database
```bash
aws dynamodb scan \
  --table-name pge-bill-automation-bills-dev \
  --limit 10
```

## 💰 Cost Management

**Monthly cost breakdown:**
- Lambda: ~$0.50
- DynamoDB: ~$0.25
- S3: ~$0.02
- SES: ~$0.10
- SNS: ~$0.01
- Other: ~$0.12
- **Total: ~$1-2/month**

**Cost optimization:**
- Use on-demand DynamoDB billing
- Enable S3 lifecycle policies
- Monitor with AWS Cost Explorer

## 🛡️ Security

**Implemented security measures:**
- ✅ All secrets in AWS Secrets Manager
- ✅ S3 encryption at rest
- ✅ DynamoDB encryption at rest
- ✅ IAM least privilege access
- ✅ VPC endpoints (optional)
- ✅ CloudTrail logging

**Security checklist:**
- [ ] Rotate Gmail API credentials annually
- [ ] Review IAM permissions quarterly
- [ ] Monitor CloudWatch alarms
- [ ] Keep dependencies updated

## 📊 Monitoring

**CloudWatch Alarms:**
- Lambda errors
- DynamoDB throttling
- S3 access errors

**Metrics to watch:**
- Lambda duration (should be < 5 minutes)
- DynamoDB read/write capacity
- S3 storage costs
- SES bounce/complaint rates

**Set up monitoring:**
```bash
# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
  --dashboard-name PGE-Automation \
  --dashboard-body file://monitoring/dashboard.json
```

## 🆘 Troubleshooting

### Common Issues

**Gmail Authentication Errors**
```bash
# Re-authenticate
python setup/authenticate_gmail.py

# Update Lambda environment
cd deployment/
./setup-credentials.sh
./deploy.sh dev
```

**SES Email Not Sending**
```bash
# Check SES status
aws ses get-send-quota

# Verify email addresses
aws ses list-verified-email-addresses
```

**Lambda Timeout**
```bash
# Increase timeout (current: 15 minutes)
aws lambda update-function-configuration \
  --function-name pge-bill-automation-dev \
  --timeout 900
```

**DynamoDB Access Errors**
```bash
# Check IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn $(aws sts get-caller-identity --query Arn --output text) \
  --action-names dynamodb:PutItem \
  --resource-arns arn:aws:dynamodb:*:*:table/pge-bill-automation-bills-dev
```

### Debug Mode

Enable detailed logging:
```bash
aws lambda update-function-configuration \
  --function-name pge-bill-automation-dev \
  --environment Variables='{
    "LOG_LEVEL": "DEBUG",
    "BILLS_TABLE": "pge-bill-automation-bills-dev",
    "PROCESSING_LOG_TABLE": "pge-bill-automation-processing-log-dev",
    "PDF_BUCKET": "pge-bill-automation-pdfs-dev"
  }'
```

### Rollback Procedure

If deployment fails:
```bash
# Rollback CloudFormation stack
aws cloudformation cancel-update-stack \
  --stack-name pge-bill-automation-dev

# Or delete and redeploy
aws cloudformation delete-stack \
  --stack-name pge-bill-automation-dev
```

## 🔄 Disaster Recovery

**Backup strategy:**
- DynamoDB: Point-in-time recovery enabled
- S3: Versioning enabled
- Lambda: Code stored in Git
- Secrets: Export and store securely

**Recovery procedure:**
1. Redeploy infrastructure from Git
2. Restore DynamoDB from backup
3. Update secrets from secure backup
4. Test all functionality

## 📈 Scaling

The serverless architecture automatically scales, but for optimization:

**High volume usage:**
- Switch to DynamoDB provisioned capacity
- Enable S3 Transfer Acceleration
- Use CloudFront for PDF distribution
- Implement SQS for batch processing

**Multi-tenant support:**
- Separate tables per tenant
- Environment-based isolation
- Usage-based cost allocation

## 🔄 Migration

**From local system:**
1. Export local SQLite data
2. Import to DynamoDB
3. Test thoroughly in dev
4. Switch DNS/scheduling

**Between AWS accounts:**
1. Export CloudFormation template
2. Copy S3 data
3. Export/import DynamoDB
4. Update DNS records