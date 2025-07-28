# PG&E Bill Split Automation - AWS Lambda

![AWS](https://img.shields.io/badge/AWS-Lambda-orange) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![License](https://img.shields.io/badge/License-MIT-green)

**Serverless automation for splitting PG&E utility bills between roommates**

Automatically processes PG&E bills from Gmail, calculates splits, generates professional PDFs, and sends Venmo payment requests. Runs entirely on AWS Lambda for 100% reliability at $2-5/month.

## ✨ Features

- 📧 **Gmail Integration**: Automatically parses PG&E bill emails
- 💰 **Smart Bill Splitting**: Configurable ratios (default: 1/3 roommate, 2/3 you)
- 📄 **Professional PDFs**: Generates official-looking bill summaries
- 💳 **Venmo Integration**: Creates one-click payment request links
- 📱 **SMS Notifications**: Sends Venmo links to your phone
- ✉️ **Email Notifications**: Sends PDFs to roommate automatically
- 🗄️ **Cloud Storage**: Tracks all bills and payments in DynamoDB
- ⏰ **Monthly Automation**: Runs automatically on the 5th of each month
- 🛡️ **Test Mode**: Safe testing without bothering roommates
- 📊 **Monitoring**: CloudWatch alerts and comprehensive logging
- 🌐 **Web Interface**: AWS App Runner hosted dashboard for bill tracking

## 🏗️ Architecture

- **AWS Lambda**: Serverless automation logic
- **DynamoDB**: Bill storage and processing history  
- **S3**: PDF storage with encryption
- **SES**: Email notifications
- **SNS**: SMS notifications
- **EventBridge**: Monthly scheduling
- **Secrets Manager**: Secure configuration
- **CloudFormation**: Infrastructure as code
- **App Runner**: Web UI hosting

## 💰 Cost

**~$2-5 per month** for typical usage:
- Lambda: ~$0.50/month
- DynamoDB: ~$0.25/month  
- S3: ~$0.02/month
- SES: ~$0.10/month
- SNS: ~$0.01/month
- App Runner: ~$2-3/month
- Other: ~$0.12/month

## 🚀 Quick Start

### Prerequisites

1. **AWS Account** with CLI configured
2. **Gmail Account** with API access
3. **Python 3.9+** and pip

### 1. Clone Repository

```bash
git clone https://github.com/AndrewTing89/Utility_Bill_Split-AWS.git
cd Utility_Bill_Split-AWS
```

### 2. Set Up Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create credentials (OAuth 2.0)
5. Download credentials as `credentials.json`

### 3. Initial Authentication

```bash
# Install dependencies locally for setup
pip install -r requirements.txt

# Run initial Gmail authentication
python setup/authenticate_gmail.py
```

This creates a `token.json` file needed for AWS deployment.

### 4. Configure Settings

Edit `config/settings.json`:

```json
{
  "gmail_user": "your-email@gmail.com",
  "roommate_email": "roommate@gmail.com", 
  "my_email": "your-email@gmail.com",
  "roommate_venmo": "roommate-venmo-username",
  "my_venmo": "your-venmo-username",
  "my_phone": "+1234567890",
  "roommate_split_ratio": 0.333333,
  "my_split_ratio": 0.666667,
  "test_mode": true
}
```

### 5. Deploy to AWS

```bash
cd deployment/
./deploy.sh dev
```

### 6. Deploy Web Interface

```bash
cd web-ui/
./deploy-web.sh
```

### 7. Verify SES Email

1. Go to AWS SES Console
2. Verify your email addresses
3. Test email sending

### 8. Test the System

```bash
# Manual test run
aws lambda invoke \
  --function-name pge-bill-automation-dev \
  --payload '{"test_mode": true}' \
  response.json
```

## 📅 How It Works

1. **Monthly Trigger**: EventBridge triggers Lambda on 5th of each month
2. **Gmail Processing**: Searches for new PG&E bills from `DoNotReply@billpay.pge.com`
3. **Bill Analysis**: Extracts amount, due date, and bill details
4. **Split Calculation**: Calculates roommate and your portions
5. **PDF Generation**: Creates professional bill summary PDF
6. **Notifications**: 
   - Emails PDF to roommate
   - Sends Venmo link to your phone
7. **Storage**: Saves everything to DynamoDB for tracking
8. **Web Dashboard**: Track bills and payments via hosted interface

## 🔧 Configuration

### Environment Settings

The system uses AWS Secrets Manager for configuration. Update via AWS Console:

```json
{
  "gmail_user": "your-email@gmail.com",
  "roommate_email": "roommate@gmail.com",
  "roommate_venmo": "venmo-username", 
  "my_phone": "+1234567890",
  "roommate_split_ratio": 0.333333,
  "test_mode": false
}
```

### Test Mode

- **Enabled**: Simulates all actions, no actual emails/SMS sent
- **Disabled**: Full automation with real notifications
- Always test in development environment first!

## 📊 Monitoring

### CloudWatch Logs
```bash
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/pge-bill-automation
```

### Manual Testing
```bash
aws lambda invoke \
  --function-name pge-bill-automation-dev \
  --payload '{"test_mode": true, "manual_trigger": true}' \
  response.json
```

### View Bills Database
```bash
aws dynamodb scan --table-name pge-bill-automation-bills-dev --limit 10
```

## 🛠️ Development

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run local tests
python -m pytest tests/

# Test Gmail integration
python src/test_gmail.py

# Test web interface locally
cd web-ui/
python simple_test.py
```

### Update Lambda Code

```bash
cd deployment/
./deploy.sh dev --code-only
```

### Infrastructure Changes

```bash
# Full infrastructure update
./deploy.sh dev
```

## 🔒 Security

- All credentials stored in AWS Secrets Manager
- S3 and DynamoDB encrypted at rest
- IAM roles with least privilege access
- VPC deployment option available
- No hardcoded secrets in code

## 🆘 Troubleshooting

### Common Issues

**Gmail Authentication Errors**
```bash
# Re-authenticate locally first
python setup/authenticate_gmail.py
cd deployment/
./setup-credentials.sh
./deploy.sh dev
```

**SES Email Not Working**
- Verify email addresses in SES Console
- Check if account is in sandbox mode
- Ensure region supports SES

**Lambda Timeout**
- Check CloudWatch logs for specific errors
- Current timeout is 15 minutes
- Consider increasing memory if needed

### Debug Mode

Enable detailed logging:
```bash
aws lambda update-function-configuration \
  --function-name pge-bill-automation-dev \
  --environment Variables='{"LOG_LEVEL":"DEBUG",...}'
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for reliable utility bill management
- Uses Gmail API for email processing
- Leverages AWS serverless architecture
- ReportLab for PDF generation
- Inspired by the need for automated roommate billing

## 📞 Support

- 📖 **Documentation**: Check this README and `docs/` folder
- 🐛 **Issues**: Open an issue on GitHub
- 💬 **Discussions**: Use GitHub Discussions for questions

---

**Note**: This is a personal automation tool. Always test thoroughly in development mode before using in production. Ensure compliance with your local laws and PG&E terms of service.
