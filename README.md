# PG&E Bill Split Automation - AWS Version

An automated system for processing PG&E electricity bills, calculating roommate splits, and managing payment tracking. This AWS-deployed version uses serverless architecture for automatic monthly processing.

## Features

- **Automatic Bill Processing**: Scans Gmail for PG&E bills and extracts key information
- **Smart Bill Splitting**: Calculates roommate portions based on configurable ratios
- **PDF Generation**: Creates professional bill summaries with payment details
- **Email Notifications**: Sends bill notifications with PDF attachments via AWS SES
- **Venmo Integration**: Generates payment request links for easy roommate payments
- **Payment Tracking**: Automatically detects Venmo payment confirmations and updates bill status
- **Web Dashboard**: Full-featured web interface for bill management and tracking
- **Scheduled Automation**: Runs automatically on the 5th of each month via EventBridge

## Architecture

- **AWS Lambda**: Serverless compute for bill processing logic
- **DynamoDB**: NoSQL database for bill storage
- **S3**: Secure storage for PDF bills
- **SES**: Email delivery service
- **App Runner**: Managed web application hosting
- **EventBridge**: Scheduled automation triggers
- **Secrets Manager**: Secure credential storage

## Web Dashboard Features

- View all processed bills with payment status
- Process new bills on-demand
- Check for payment confirmations
- Generate and send Venmo payment requests
- Download PDF summaries
- Track payment history

## Project Structure

```
.
├── cloudformation/         # Infrastructure as Code templates
├── config/                 # Configuration files
├── deployment/            # Deployment scripts
├── docs/                  # Documentation
├── lambda_package_final/  # Lambda function code
├── setup/                 # Setup utilities
├── src/                   # Core application logic
├── tests/                 # Test files
└── web-ui/               # Flask web application
```

## Setup

1. **AWS Configuration**
   - Configure AWS CLI with appropriate credentials
   - Deploy CloudFormation stack from `cloudformation/template.yaml`

2. **Gmail API Setup**
   - Enable Gmail API in Google Cloud Console
   - Create OAuth2 credentials
   - Store credentials in AWS Secrets Manager

3. **Deploy Lambda Function**
   ```bash
   cd lambda_package_final
   zip -r ../lambda_deployment.zip .
   aws lambda update-function-code --function-name pge-bill-automation-automation-dev --zip-file fileb://../lambda_deployment.zip
   ```

4. **Deploy Web Application**
   - App Runner automatically deploys from the `web-ui` directory
   - Access at: https://kyf5cqt8ci.us-west-2.awsapprunner.com

## Usage

### Web Interface
- Visit the dashboard to view bills and trigger actions
- Use "Process New Bills" to scan for new PG&E emails
- Click "Check for Payments" to update payment status

### Automatic Processing
- System runs automatically on the 5th of each month
- Processes new bills, generates PDFs, and sends notifications

## Security

- All credentials stored in AWS Secrets Manager
- Gmail OAuth tokens encrypted at rest
- DynamoDB encryption enabled
- S3 bucket with server-side encryption
- App Runner with HTTPS only

## Testing

Currently running in test mode with:
- Email notifications sent to configured test addresses
- SMS notifications disabled
- All actions logged but reversible

To switch to production mode, update the `test_mode` setting in Secrets Manager.

## Maintenance

- Lambda logs available in CloudWatch
- App Runner logs for web application debugging
- DynamoDB tables for bill and processing history
- Regular credential rotation recommended

## License

MIT License - See LICENSE file for details