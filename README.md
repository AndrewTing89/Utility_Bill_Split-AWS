# PG&E Bill Split Automation - AWS Version

An automated system for processing PG&E electricity bills, calculating roommate splits, and managing payment tracking. This AWS-deployed version uses serverless architecture for automatic monthly processing.

## Features

- **Automatic Bill Processing**: Scans Gmail for PG&E bills and extracts key information
- **Smart Bill Splitting**: Calculates roommate portions based on configurable ratios (default: 1/3 roommate, 2/3 owner)
- **Multi-Channel Notifications**:
  - SMS via email-to-SMS gateways (dual gateway redundancy)
  - Email notifications with HTML formatting and clickable Venmo links
- **Venmo Integration**: HTTPS links with pre-filled amount, recipient, and payment note
- **Payment Tracking**: Automatically detects Venmo payment confirmations and updates bill status
- **Web Dashboard**: Full-featured web interface for bill management and tracking
- **Scheduled Automation**: Runs automatically on the 5th of each month at 9 AM PST via EventBridge

## Architecture

- **AWS Lambda**: Serverless compute for bill processing logic (Python 3.9)
- **DynamoDB**: NoSQL database for bill and payment tracking
- **App Runner**: Managed web application hosting (auto-scaling)
- **EventBridge**: Scheduled automation triggers
- **Secrets Manager**: Secure credential storage
- **Gmail API**: Email monitoring and parsing
- **SMTP**: Email and SMS delivery via Gmail

## Web Dashboard Features

- View all processed bills with payment status
- Process new bills on-demand
- Check for Venmo payment confirmations
- Send SMS notifications with Venmo links
- Track SMS delivery status and timestamps
- Configure system settings

## Project Structure

```
.
├── src/                    # Core application logic
│   ├── bill_automation.py  # Main automation engine
│   ├── gmail_processor_aws.py  # Gmail API integration
│   ├── venmo_payment_detector.py  # Payment confirmation tracking
│   └── lambda_handler.py   # AWS Lambda entry point
├── web-ui/                 # Flask web application
│   ├── app_aws.py         # Main Flask app
│   ├── templates/         # HTML templates
│   └── requirements.txt   # Web app dependencies
├── terraform/             # Infrastructure as Code
│   └── main.tf           # AWS resource definitions
├── apprunner.yaml        # App Runner configuration
├── requirements.txt      # Lambda dependencies
└── clear_bills.py        # Utility to clear DynamoDB
```

## Setup

1. **Prerequisites**
   - AWS Account with appropriate IAM permissions
   - Gmail account with 2FA enabled
   - Python 3.8+ installed locally
   - AWS CLI configured
   - Terraform installed

2. **Gmail Configuration**
   - Enable 2-Factor Authentication
   - Generate App Password: Settings → Security → 2-Step Verification → App passwords
   - Enable Gmail API in Google Cloud Console
   - Download OAuth2 credentials JSON

3. **Infrastructure Deployment**
   ```bash
   cd terraform
   terraform init
   terraform plan
   terraform apply
   ```

4. **Configure Secrets**
   Update AWS Secrets Manager with your configuration:
   ```json
   {
     "gmail_user": "your-email@gmail.com",
     "gmail_app_password": "xxxx-xxxx-xxxx-xxxx",
     "roommate_email": "roommate@email.com",
     "my_email": "your-email@gmail.com",
     "roommate_venmo": "venmo-username",
     "my_venmo": "your-venmo",
     "my_phone": "+11234567890",
     "sms_gateway": "1234567890@vtext.com",
     "roommate_split_ratio": 0.333333,
     "my_split_ratio": 0.666667,
     "test_mode": false
   }
   ```

5. **Deploy Lambda Function**
   ```bash
   # Create deployment package
   mkdir lambda-package
   cp -r src/* lambda-package/
   cp requirements.txt lambda-package/
   pip install -r requirements.txt -t lambda-package/
   cd lambda-package
   zip -r ../lambda-function.zip .
   
   # Deploy to AWS
   aws lambda update-function-code \
     --function-name pge-bill-automation-automation-dev \
     --zip-file fileb://../lambda-function.zip \
     --region us-west-2
   ```

6. **Deploy Web Application**
   ```bash
   # App Runner will auto-deploy from apprunner.yaml
   # Access your unique URL from AWS Console
   ```

## Usage

### Web Dashboard
Access your App Runner URL to:
- **View Bills**: See all processed bills with amounts and payment status
- **Process New Bills**: Manually trigger Gmail scanning for new PG&E bills
- **Send Notifications**: Click "Send SMS with Venmo Link" to notify roommate
- **Check Payments**: Scan Gmail for Venmo payment confirmations
- **Update Settings**: Configure split ratios and notification preferences

### Notification Format

**SMS Message:**
```
PG&E August 2025
Total: $288.15
Pay: $96.05
https://venmo.com/username?txn=charge&amount=96.05&note=Balance--$96.05%0ATotal--$288.15%0ADue--08/08/2025
```

**Email Message:**
- HTML formatted with clickable "Charge on Venmo" button
- Shows total bill amount and roommate's share
- Includes due date and payment breakdown
- Venmo link opens with pre-filled amount and note

### Automatic Processing
- Runs automatically on the 5th of each month at 9 AM PST
- Processes new bills and sends notifications
- Updates payment tracking from Venmo confirmations

## Security

- Gmail App Password required (not regular password)
- All credentials stored in AWS Secrets Manager
- DynamoDB encryption at rest enabled
- App Runner URL should be kept private (security through obscurity)
- HTTPS only for all web traffic
- OAuth2 tokens encrypted and stored securely

## SMS Gateway Configuration

The system supports email-to-SMS gateways. Common carriers:
- **Verizon**: number@vtext.com or number@mypixmessages.com
- **AT&T**: number@txt.att.net
- **T-Mobile**: number@tmomail.net
- **Sprint**: number@messaging.sprintpcs.com

## Testing

1. **Clear existing data**: `python clear_bills.py`
2. **Process test bill**: Click "Process New Bills" in dashboard
3. **Verify notifications**: Check SMS and email delivery
4. **Test payment tracking**: Forward a Venmo payment confirmation to Gmail

## Troubleshooting

- **No bills found**: 
  - Check Gmail search query matches sender: `DoNotReply@billpay.pge.com`
  - Verify Gmail API credentials are valid
  - Check date range in search query

- **SMS not received**: 
  - Verify SMS gateway format for your carrier
  - Check phone number format in settings
  - Try alternate gateway (e.g., mypixmessages.com for Verizon)

- **Lambda errors**: 
  - Check CloudWatch logs: `/aws/lambda/pge-bill-automation-automation-dev`
  - Verify all environment variables are set
  - Check IAM permissions for Lambda role

- **Email classification issues**: 
  - Ensure bill detection filters out payment confirmations
  - Check email body parsing logic

## Monitoring

- **CloudWatch Logs**: Lambda execution logs
- **App Runner Logs**: Web application access and errors
- **DynamoDB Console**: View bill records directly
- **EventBridge Console**: Check scheduled rule status

## License

MIT License - See LICENSE file for details