"""
PG&E Bill Automation Logic for AWS Lambda

This module contains the core automation logic adapted for AWS services:
- Uses DynamoDB instead of SQLite
- Uses SES instead of Mac Mail
- Uses S3 for PDF storage
- Uses Secrets Manager for credentials
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

# AWS clients
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
ses_client = boto3.client('ses')
secrets_client = boto3.client('secretsmanager')

logger = logging.getLogger(__name__)

# Environment variables
BILLS_TABLE = os.environ.get('BILLS_TABLE', 'pge-bills')
PROCESSING_LOG_TABLE = os.environ.get('PROCESSING_LOG_TABLE', 'pge-processing-log') 
PDF_BUCKET = os.environ.get('PDF_BUCKET', 'pge-bill-pdfs')
SECRETS_ARN = os.environ.get('SECRETS_ARN')


class AWSBillAutomation:
    """AWS-adapted bill automation system"""
    
    def __init__(self):
        self.bills_table = dynamodb.Table(BILLS_TABLE)
        self.log_table = dynamodb.Table(PROCESSING_LOG_TABLE)
        self.settings = self._load_settings()
        
    def _load_settings(self) -> Dict:
        """Load settings from AWS Secrets Manager"""
        try:
            if not SECRETS_ARN:
                raise ValueError("SECRETS_ARN not configured")
                
            response = secrets_client.get_secret_value(SecretId=SECRETS_ARN)
            return json.loads(response['SecretString'])
            
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            # Return default settings for development
            return {
                'gmail_user': 'andrewhting@gmail.com',
                'roommate_email': 'loushic@gmail.com',
                'my_email': 'andrewhting@gmail.com',
                'roommate_venmo': 'UshiLo',
                'my_venmo': 'andrewhting',
                'my_phone': '+19298884132',
                'roommate_split_ratio': 0.333333,
                'my_split_ratio': 0.666667,
                'test_mode': True,
                'enable_email_notifications': True,
                'enable_text_messaging': True
            }
    
    def process_latest_bills(self, days_back: int = 30) -> Dict:
        """
        Process new bills from Gmail
        
        Args:
            days_back: How many days back to search for bills
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"Processing bills from last {days_back} days")
        
        try:
            # Import Gmail processing for AWS Lambda
            from gmail_processor_aws import GmailProcessorAWS
            
            processor = GmailProcessorAWS(self.settings)
            return processor.process_bills(days_back=days_back)
            
        except Exception as e:
            logger.error(f"Error processing bills: {e}")
            return {
                'processed': 0,
                'duplicates': 0,
                'errors': 1,
                'new_bills': []
            }
    
    def generate_bill_pdf(self, bill_data: Dict) -> Optional[str]:
        """
        Generate PDF and upload to S3
        
        Args:
            bill_data: Bill information
            
        Returns:
            S3 URL of generated PDF or None if failed
        """
        try:
            from pdf_generator_aws import PDFGeneratorAWS
            
            generator = PDFGeneratorAWS()
            pdf_content = generator.generate_pdf(bill_data)
            
            if pdf_content:
                # Upload to S3
                due_date = bill_data['due_date'].replace('/', '-')
                s3_key = f"bills/{due_date}-pge-bill.pdf"
                
                s3_client.put_object(
                    Bucket=PDF_BUCKET,
                    Key=s3_key,
                    Body=pdf_content,
                    ContentType='application/pdf',
                    ServerSideEncryption='AES256'
                )
                
                s3_url = f"s3://{PDF_BUCKET}/{s3_key}"
                logger.info(f"PDF uploaded to S3: {s3_url}")
                return s3_url
                
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return None
    
    def send_email_notification(self, bill_data: Dict, pdf_s3_url: str, venmo_info: Dict) -> bool:
        """
        Send email notification via SES
        
        Args:
            bill_data: Bill information
            pdf_s3_url: S3 URL of PDF
            venmo_info: Venmo request information
            
        Returns:
            True if email sent successfully
        """
        try:
            if self.settings.get('test_mode', True):
                logger.info("TEST MODE: Email notification simulated")
                return True
                
            # Create email content
            subject = self._create_email_subject(bill_data)
            body_html, body_text = self._create_email_body(bill_data, venmo_info)
            
            # Get PDF from S3 for attachment
            pdf_content = self._get_pdf_from_s3(pdf_s3_url)
            
            # Send via SES
            response = ses_client.send_raw_email(
                Source=self.settings['my_email'],
                Destinations=[self.settings['roommate_email']],
                RawMessage={'Data': self._create_raw_email(
                    subject, body_html, body_text, pdf_content
                )}
            )
            
            logger.info(f"Email sent via SES: {response['MessageId']}")
            return True
            
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return False
    
    def send_sms_notification(self, venmo_url: str, bill_data: Dict) -> bool:
        """
        Send SMS notification via SNS
        
        Args:
            venmo_url: Venmo deep link
            bill_data: Bill information
            
        Returns:
            True if SMS sent successfully
        """
        try:
            if self.settings.get('test_mode', True):
                logger.info("TEST MODE: SMS notification simulated")
                return True
                
            import boto3
            sns_client = boto3.client('sns')
            
            roommate_portion = bill_data['roommate_portion']
            bill_month = datetime.strptime(bill_data['due_date'], '%m/%d/%Y').strftime('%B %Y')
            
            message = f"💰 PG&E Bill Split - {bill_month}\n"
            message += f"Request ${roommate_portion:.2f} from roommate\n"
            message += f"Venmo Link: {venmo_url}"
            
            response = sns_client.publish(
                PhoneNumber=self.settings['my_phone'],
                Message=message
            )
            
            logger.info(f"SMS sent via SNS: {response['MessageId']}")
            return True
            
        except Exception as e:
            logger.error(f"SMS sending failed: {e}")
            return False
    
    def log_processing_action(self, bill_id: str, action: str, details: str = None):
        """Log action to DynamoDB"""
        try:
            self.log_table.put_item(
                Item={
                    'bill_id': bill_id,
                    'timestamp': datetime.now().isoformat(),
                    'action': action,
                    'details': details or ''
                }
            )
        except Exception as e:
            logger.error(f"Failed to log action: {e}")
    
    def _create_email_subject(self, bill_data: Dict) -> str:
        """Create email subject line"""
        bill_month = datetime.strptime(bill_data['due_date'], '%m/%d/%Y').strftime('%B %Y')
        return f"PG&E Bill Split - {bill_month} (${bill_data['roommate_portion']:.2f})"
    
    def _create_email_body(self, bill_data: Dict, venmo_info: Dict) -> tuple:
        """Create HTML and text email body"""
        # Implementation would create the email body content
        # Similar to the existing email_notifier.py but for SES
        html_body = "Email content here..."
        text_body = "Email content here..."
        return html_body, text_body
    
    def _get_pdf_from_s3(self, s3_url: str) -> bytes:
        """Get PDF content from S3"""
        bucket = PDF_BUCKET
        key = s3_url.replace(f"s3://{bucket}/", "")
        
        response = s3_client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()
    
    def _create_raw_email(self, subject: str, html_body: str, text_body: str, pdf_content: bytes) -> bytes:
        """Create raw email with PDF attachment for SES"""
        # Implementation would create proper MIME email with attachment
        # This is a placeholder
        return b"Raw email content here..."


def run_monthly_automation(test_mode: bool = True) -> Dict:
    """
    Main automation function for Lambda
    
    Args:
        test_mode: Whether to run in test mode
        
    Returns:
        Dictionary with automation results
    """
    logger.info("Starting monthly automation")
    
    automation = AWSBillAutomation()
    
    # Override test mode if provided
    automation.settings['test_mode'] = test_mode
    
    results = {
        'bills_processed': 0,
        'pdfs_generated': 0,
        'emails_sent': 0,
        'sms_sent': 0,
        'errors': []
    }
    
    try:
        # Step 1: Process new bills
        bill_results = automation.process_latest_bills(days_back=30)
        
        # Step 2: Process each bill
        for bill_data in bill_results.get('new_bills', []):
            bill_id = bill_data['bill_id']
            
            try:
                # Generate PDF
                pdf_url = automation.generate_bill_pdf(bill_data)
                if pdf_url:
                    results['pdfs_generated'] += 1
                    automation.log_processing_action(bill_id, 'pdf_generated', pdf_url)
                
                # Generate Venmo info
                venmo_info = {
                    'venmo_url': f"venmo://paycharge?txn=charge&recipients={automation.settings['roommate_venmo']}&amount={bill_data['roommate_portion']:.2f}",
                    'summary': {
                        'roommate_owes': bill_data['roommate_portion'],
                        'payment_note': f"PG&E bill split - {bill_data['due_date']}"
                    }
                }
                
                # Send email notification
                if automation.send_email_notification(bill_data, pdf_url, venmo_info):
                    results['emails_sent'] += 1
                    automation.log_processing_action(bill_id, 'email_sent')
                
                # Send SMS notification
                if automation.send_sms_notification(venmo_info['venmo_url'], bill_data):
                    results['sms_sent'] += 1
                    automation.log_processing_action(bill_id, 'sms_sent')
                
                results['bills_processed'] += 1
                
            except Exception as e:
                error_msg = f"Error processing bill {bill_id}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        logger.info(f"Automation completed: {results}")
        return results
        
    except Exception as e:
        error_msg = f"Automation failed: {str(e)}"
        logger.error(error_msg)
        results['errors'].append(error_msg)
        return results