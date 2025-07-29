# AWS App Runner Setup Guide

## Quick Setup Instructions

### 1. Open AWS App Runner Console
Go to: https://console.aws.amazon.com/apprunner/

### 2. Create Service
Click **"Create service"**

### 3. Configure Source
- **Source type**: Source code repository
- **Connect to GitHub**: Click "Add new" and authorize AWS to access your GitHub
- **Repository**: Select `AndrewTing89/Utility_Bill_Split-AWS`
- **Branch**: `main`
- **Deployment trigger**: Manual (for now)

### 4. Configure Build
- **Configuration file**: Use configuration file (apprunner.yaml)
- **Configuration file path**: `web-ui/apprunner.yaml`

### 5. Configure Service
- **Service name**: `pge-bill-split-web`
- **CPU**: 0.25 vCPU
- **Memory**: 0.5 GB

### 6. Environment Variables
Add these environment variables:

```
PORT=8080
FLASK_ENV=production
AWS_REGION=us-west-2
BILLS_TABLE=pge-bill-automation-bills-dev
LAMBDA_FUNCTION=pge-bill-automation-automation-dev
```

### 7. Security (IAM Role)
- **Auto scaling**: 1 to 10 instances
- **Health check**: Default settings
- **Instance role**: Create new role with DynamoDB and Lambda permissions

### 8. Review and Create
- Review all settings
- Click **"Create & deploy"**

## Expected Results
- Deployment time: ~10-15 minutes
- Cost: ~$5-10/month
- URL: Will be provided after deployment (e.g., `https://abc123.us-west-2.awsapprunner.com`)

## IAM Permissions Needed
The App Runner service will need these permissions:
- DynamoDB: Read/Write to `pge-bill-automation-bills-dev`
- Lambda: Invoke `pge-bill-automation-automation-dev`
- Secrets Manager: Read configuration secrets

## Troubleshooting
If deployment fails:
1. Check CloudWatch logs in App Runner console
2. Verify environment variables are set correctly
3. Ensure IAM role has proper permissions
4. Check that the repository is accessible

## After Deployment
1. Test the web interface at the provided URL
2. Verify Lambda integration works
3. Check DynamoDB connectivity
4. Test bill processing functionality