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
secrets_client = boto3.client('secretsmanager')

logger = logging.getLogger(__name__)

# Environment variables
BILLS_TABLE = os.environ.get('BILLS_TABLE', 'pge-bills')
PROCESSING_LOG_TABLE = os.environ.get('PROCESSING_LOG_TABLE', 'pge-processing-log') 
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
    
    
    def send_sms_notification(self, venmo_url: str, bill_data: Dict) -> bool:
        """
        Send SMS notification via Gmail SMTP to email-to-SMS gateway
        
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
                
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from datetime import datetime
            
            # Get SMS credentials from settings
            gmail_user = self.settings.get('gmail_user')
            gmail_app_password = self.settings.get('gmail_app_password')
            sms_gateway = self.settings.get('sms_gateway')
            
            if not gmail_user or not gmail_app_password or not sms_gateway:
                logger.error("SMS credentials not configured in settings")
                return False
            
            roommate_portion = bill_data['roommate_portion']
            total_amount = bill_data.get('amount', bill_data.get('total_amount', 0))
            bill_month = datetime.strptime(bill_data['due_date'], '%m/%d/%Y').strftime('%B %Y')
            
            # Include total amount in message - shortened for SMS
            message_body = f"PG&E {bill_month}\nTotal: ${total_amount:.2f}\nPay: ${roommate_portion:.2f}\n{venmo_url}"
            
            # Send to both SMS gateways for better reliability
            sms_gateways = [sms_gateway, '9298884132@mypixmessages.com']
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(gmail_user, gmail_app_password)
            
            # Send SMS to gateways
            for gateway in sms_gateways:
                msg = MIMEText(message_body)
                msg['From'] = gmail_user
                msg['To'] = gateway
                msg['Subject'] = ''  # Empty subject for SMS
                
                try:
                    server.send_message(msg)
                    logger.info(f"SMS sent via email-to-SMS gateway: {gateway}")
                except Exception as e:
                    logger.warning(f"Failed to send to {gateway}: {e}")
            
            # Also send email to andrewhting@gmail.com
            try:
                email_msg = MIMEMultipart()
                email_msg['From'] = gmail_user
                email_msg['To'] = 'andrewhting@gmail.com'
                email_msg['Subject'] = f'PG&E Bill Split - {bill_month}'
                
                email_body = f"""
                <html>
                <head>
                    <style>
                        .venmo-button {{
                            display: inline-block;
                            background-color: #3D95CE;
                            color: white !important;
                            padding: 12px 24px;
                            text-decoration: none;
                            border-radius: 5px;
                            font-weight: bold;
                            font-size: 16px;
                            margin: 10px 0;
                        }}
                        .venmo-button:hover {{
                            background-color: #2b7bb0;
                        }}
                        body {{
                            font-family: Arial, sans-serif;
                        }}
                    </style>
                </head>
                <body>
                    <h2>PG&E Bill Split - {bill_month}</h2>
                    <p><strong>Total Bill Amount:</strong> ${total_amount:.2f}</p>
                    <p><strong>Roommate's Share:</strong> ${roommate_portion:.2f}</p>
                    <p><strong>Due Date:</strong> {bill_data['due_date']}</p>
                    <br>
                    
                    <p><a href="{venmo_url}" class="venmo-button">Charge on Venmo</a></p>
                    
                    <p><strong>If the button doesn't work, copy this link:</strong></p>
                    <p style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; word-break: break-all;">
                        {venmo_url}
                    </p>
                    
                    <hr style="margin-top: 20px;">
                    <p style="color: #666; font-size: 14px;">
                        This will charge <strong>{self.settings.get('roommate_venmo')}</strong> for ${roommate_portion:.2f}<br>
                        Note: ${roommate_portion:.2f} ({roommate_portion/total_amount*100:.1f}%) of total ${total_amount:.2f}
                    </p>
                </body>
                </html>
                """
                
                email_msg.attach(MIMEText(email_body, 'html'))
                server.send_message(email_msg)
                logger.info("Email notification sent to andrewhting@gmail.com")
                
            except Exception as e:
                logger.error(f"Failed to send email notification: {e}")
            
            server.quit()
            
            logger.info(f"Notifications sent via SMS gateways and email")
            
            # Update bill record with SMS sent status and timestamp
            try:
                current_time = datetime.now().isoformat()
                self.bills_table.update_item(
                    Key={'bill_id': bill_data['bill_id']},
                    UpdateExpression='SET sms_sent = :val, sms_sent_at = :sent_at, updated_at = :updated',
                    ExpressionAttributeValues={
                        ':val': True,
                        ':sent_at': current_time,
                        ':updated': current_time
                    }
                )
            except Exception as e:
                logger.warning(f"Could not update SMS status: {e}")
            
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
    
    
    def check_venmo_payments(self, days_back: int = 30) -> Dict:
        """
        Check for Venmo payment confirmations and mark bills as paid
        
        Args:
            days_back: How many days back to search for payment confirmations
            
        Returns:
            Dictionary with payment check results
        """
        try:
            from venmo_payment_detector import VenmoPaymentDetector
            from gmail_processor_aws import GmailProcessorAWS
            
            # Initialize Gmail processor and Venmo detector
            gmail_processor = GmailProcessorAWS(self.settings)
            if not gmail_processor.authenticate():
                return {
                    'payments_found': 0,
                    'bills_updated': 0,
                    'errors': ['Gmail authentication failed']
                }
            
            venmo_detector = VenmoPaymentDetector()
            
            # Search for Venmo payment emails
            since_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
            query = f'from:venmo@venmo.com after:{since_date} "you charged"'
            
            logger.info(f"Searching for Venmo payments: {query}")
            
            # Search for Venmo emails directly
            venmo_emails = gmail_processor.search_emails(query, max_results=50)
            
            results = {
                'payments_found': 0,
                'bills_updated': 0,
                'errors': []
            }
            
            # Process each Venmo email
            for email_data in venmo_emails:
                try:
                    payment_result = venmo_detector.process_venmo_payment_email(email_data)
                    
                    if payment_result['success']:
                        results['payments_found'] += 1
                        results['bills_updated'] += payment_result.get('bills_updated', 0)
                        logger.info(f"Payment processed: {payment_result['message']}")
                    
                except Exception as e:
                    logger.error(f"Error processing Venmo email: {e}")
                    results['errors'].append(str(e))
            
            logger.info(f"Venmo payment check complete: {results['payments_found']} payments found, {results['bills_updated']} bills updated")
            return results
            
        except Exception as e:
            logger.error(f"Venmo payment check failed: {e}")
            return {
                'payments_found': 0,
                'bills_updated': 0,
                'errors': [str(e)]
            }


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
        'sms_sent': 0,
        'payments_found': 0,
        'bills_updated': 0,
        'errors': []
    }
    
    try:
        # Step 1: Process new bills
        bill_results = automation.process_latest_bills(days_back=30)
        
        # Step 2: Process each bill
        for bill_data in bill_results.get('new_bills', []):
            bill_id = bill_data['bill_id']
            
            try:
                # Generate Venmo info - use HTTPS URL for better email compatibility
                venmo_username = automation.settings['roommate_venmo']
                amount = bill_data['roommate_portion']
                total = bill_data.get('amount', 0)
                
                # Create a cleaner note with line breaks
                note = f"Balance--${amount:.2f}\nTotal--${total:.2f}\nDue--{bill_data['due_date']}"
                # URL encode the note properly
                import urllib.parse
                encoded_note = urllib.parse.quote(note)
                
                # Use Venmo's web URL which redirects to app on mobile
                venmo_info = {
                    'venmo_url': f"https://venmo.com/{venmo_username}?txn=charge&amount={amount:.2f}&note={encoded_note}",
                    'summary': {
                        'roommate_owes': bill_data['roommate_portion'],
                        'payment_note': note
                    }
                }
                
                # Send SMS notification
                if automation.send_sms_notification(venmo_info['venmo_url'], bill_data):
                    results['sms_sent'] += 1
                    automation.log_processing_action(bill_id, 'sms_sent')
                
                results['bills_processed'] += 1
                
            except Exception as e:
                error_msg = f"Error processing bill {bill_id}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        # Step 3: Check for Venmo payments
        try:
            payment_results = automation.check_venmo_payments()
            results['payments_found'] = payment_results.get('payments_found', 0)
            results['bills_updated'] = payment_results.get('bills_updated', 0)
            if payment_results.get('errors'):
                results['errors'].extend(payment_results['errors'])
        except Exception as e:
            error_msg = f"Payment check failed: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        logger.info(f"Automation completed: {results}")
        return results
        
    except Exception as e:
        error_msg = f"Automation failed: {str(e)}"
        logger.error(error_msg)
        results['errors'].append(error_msg)
        return results