"""
Gmail API processor adapted for AWS Lambda

This module handles Gmail API authentication and email parsing
optimized for the Lambda environment with proper error handling.
"""

import os
import json
import logging
import base64
import re
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

import boto3
from botocore.exceptions import ClientError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailProcessorAWS:
    """Gmail processor adapted for AWS Lambda environment"""
    
    def __init__(self, settings: Dict):
        self.settings = settings
        self.service = None
        self.dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        self.bills_table = self.dynamodb.Table(os.environ.get('BILLS_TABLE', 'pge-bill-automation-bills-dev'))
        
    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using credentials from Secrets Manager
        
        Returns:
            True if authentication successful
        """
        try:
            # Get Gmail credentials from settings (loaded from Secrets Manager)
            client_id = self.settings.get('gmail_client_id')
            client_secret = self.settings.get('gmail_client_secret') 
            refresh_token = self.settings.get('gmail_refresh_token')
            
            if not all([client_id, client_secret, refresh_token]):
                logger.error("Gmail credentials not found in settings")
                return False
                
            # Create credentials from OAuth2 data
            creds_data = {
                'client_id': client_id,
                'client_secret': client_secret,
                'refresh_token': refresh_token,
                'type': 'authorized_user'
            }
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
            
            # Refresh if needed
            if not creds.valid:
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    logger.error("Gmail credentials expired and cannot be refreshed")
                    return False
            
            # Build the service
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail API authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Gmail authentication failed: {e}")
            return False
    
    def process_bills(self, days_back: int = 30) -> Dict:
        """
        Process PG&E bills from Gmail
        
        Args:
            days_back: How many days back to search
            
        Returns:
            Dictionary with processing results
        """
        if not self.authenticate():
            return {
                'processed': 0,
                'duplicates': 0, 
                'errors': 1,
                'new_bills': []
            }
        
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Search for PG&E emails
            emails = self._search_pge_emails(start_date, end_date)
            logger.info(f"Found {len(emails)} PG&E emails to process")
            
            results = {
                'processed': 0,
                'duplicates': 0,
                'errors': 0,
                'new_bills': []
            }
            
            for email_data in emails:
                try:
                    bill_info = self._extract_bill_info(email_data)
                    if bill_info:
                        # Check for duplicates
                        if self._is_duplicate_bill(bill_info):
                            results['duplicates'] += 1
                            logger.info(f"Skipping duplicate bill for {bill_info['due_date']}")
                            continue
                        
                        # Save to DynamoDB
                        saved_bill = self._save_bill_to_db(bill_info)
                        if saved_bill:
                            results['new_bills'].append(saved_bill)
                            results['processed'] += 1
                            logger.info(f"Processed new bill: ${bill_info['amount']} due {bill_info['due_date']}")
                        
                except Exception as e:
                    logger.error(f"Error processing email {email_data.get('id', 'unknown')}: {e}")
                    results['errors'] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to process bills: {e}")
            return {
                'processed': 0,
                'duplicates': 0,
                'errors': 1,
                'new_bills': []
            }
    
    def _search_pge_emails(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Search for PG&E bill emails in date range"""
        try:
            # Format dates for Gmail search
            after_date = start_date.strftime('%Y/%m/%d')
            before_date = end_date.strftime('%Y/%m/%d')
            
            # Search query for PG&E bills  
            query = f'from:DoNotReply@billpay.pge.com after:{after_date} before:{before_date}'
            logger.info(f"Gmail search query: {query}")
            
            # Search emails
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=50
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                try:
                    # Get full message details
                    email_detail = self.service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()
                    
                    emails.append(email_detail)
                    
                except HttpError as e:
                    logger.warning(f"Could not fetch email {message['id']}: {e}")
                    continue
            
            return emails
            
        except Exception as e:
            logger.error(f"Gmail search failed: {e}")
            return []
    
    def _is_bill_statement(self, email_data: Dict) -> bool:
        """Check if email is actually a bill statement (not payment confirmation, etc)"""
        try:
            # Get email headers
            headers = email_data.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            
            # Check subject line
            if 'Energy Statement is Ready' not in subject:
                return False
            
            # Get email body to check content
            body = self._get_email_body(email_data)
            if not body:
                return False
            
            # Check for bill statement indicators
            bill_indicators = [
                'paperless bill',
                'is now available',
                'statement balance'
            ]
            
            # Check for payment confirmation indicators (should NOT be present)
            payment_indicators = [
                'payment has been processed',
                'Confirmation Number',
                'Date of Payment',
                'Payment Amount',
                'We thank you for being',
                'previously scheduled recurring payment'
            ]
            
            # Must have at least one bill indicator
            has_bill_indicator = any(indicator.lower() in body.lower() for indicator in bill_indicators)
            
            # Must NOT have payment indicators
            has_payment_indicator = any(indicator.lower() in body.lower() for indicator in payment_indicators)
            
            return has_bill_indicator and not has_payment_indicator
            
        except Exception as e:
            logger.error(f"Error checking if email is bill statement: {e}")
            return False
    
    def _extract_bill_info(self, email_data: Dict) -> Optional[Dict]:
        """Extract bill information from email"""
        try:
            # First check if this is actually a bill statement
            if not self._is_bill_statement(email_data):
                logger.info("Email is not a bill statement, skipping")
                return None
            
            # Get email body
            body = self._get_email_body(email_data)
            if not body:
                return None
            
            # Extract bill amount
            amount_pattern = r'\$(\d+\.\d{2})'
            amount_matches = re.findall(amount_pattern, body)
            
            if not amount_matches:
                logger.warning("Could not find bill amount in email")
                return None
            
            # PG&E emails typically have the total amount as the largest value
            bill_amount = max([float(amount) for amount in amount_matches])
            
            # Extract due date
            due_date = self._extract_due_date(body)
            if not due_date:
                logger.warning("Could not find due date in email")
                return None
            
            # Calculate splits
            roommate_ratio = self.settings.get('roommate_split_ratio', 0.333333)
            my_ratio = self.settings.get('my_split_ratio', 0.666667)
            
            roommate_portion = bill_amount * roommate_ratio
            my_portion = bill_amount * my_ratio
            
            # Create bill info (convert floats to Decimal for DynamoDB)
            bill_id = f"pge_{due_date.replace('/', '_')}_{int(bill_amount * 100)}"
            bill_info = {
                'bill_id': bill_id,
                'email_id': email_data['id'],
                'amount': Decimal(str(round(bill_amount, 2))),
                'due_date': due_date,
                'roommate_portion': Decimal(str(round(roommate_portion, 2))),
                'my_portion': Decimal(str(round(my_portion, 2))),
                'email_body': body,
                'processed_date': datetime.now().isoformat(),
                'status': 'processed'
            }
            
            return bill_info
            
        except Exception as e:
            logger.error(f"Failed to extract bill info: {e}")
            return None
    
    def _get_email_body(self, email_data: Dict) -> Optional[str]:
        """Extract email body from Gmail message"""
        try:
            payload = email_data.get('payload', {})
            
            # Check if it's multipart
            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain':
                        data = part.get('body', {}).get('data')
                        if data:
                            return base64.urlsafe_b64decode(data).decode('utf-8')
                    elif part.get('mimeType') == 'text/html':
                        data = part.get('body', {}).get('data')
                        if data:
                            # For HTML, we'll use it as backup
                            html_content = base64.urlsafe_b64decode(data).decode('utf-8')
                            # Strip HTML tags for text processing
                            import re
                            return re.sub('<[^<]+?>', '', html_content)
            else:
                # Single part message
                data = payload.get('body', {}).get('data')
                if data:
                    content = base64.urlsafe_b64decode(data).decode('utf-8')
                    if payload.get('mimeType') == 'text/html':
                        # Strip HTML tags
                        import re
                        return re.sub('<[^<]+?>', '', content)
                    else:
                        return content
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract email body: {e}")
            return None
    
    def _extract_due_date(self, body: str) -> Optional[str]:
        """Extract due date from email body"""
        try:
            # Common date patterns in PG&E emails
            patterns = [
                r'due.{0,20}(\d{1,2}/\d{1,2}/\d{4})',  # due on MM/DD/YYYY
                r'(\d{1,2}/\d{1,2}/\d{4}).{0,20}due',  # MM/DD/YYYY due
                r'by.{0,20}(\d{1,2}/\d{1,2}/\d{4})',   # by MM/DD/YYYY
                r'(\d{1,2}/\d{1,2}/\d{4})'             # any MM/DD/YYYY
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, body, re.IGNORECASE)
                if matches:
                    # Return the first valid date found
                    for date_str in matches:
                        try:
                            # Validate date format
                            datetime.strptime(date_str, '%m/%d/%Y')
                            return date_str
                        except ValueError:
                            continue
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract due date: {e}")
            return None
    
    def _is_duplicate_bill(self, bill_info: Dict) -> bool:
        """Check if bill already exists in DynamoDB"""
        try:
            # Check for existing bill with same bill_id (more reliable than amount/date)
            response = self.bills_table.get_item(
                Key={'bill_id': bill_info['bill_id']}
            )
            
            return 'Item' in response
            
        except Exception as e:
            logger.error(f"Failed to check for duplicate: {e}")
            return False
    
    def _save_bill_to_db(self, bill_info: Dict) -> Optional[Dict]:
        """Save bill to DynamoDB"""
        try:
            # Add timestamp
            bill_info['created_at'] = datetime.now().isoformat()
            bill_info['updated_at'] = datetime.now().isoformat()
            
            # Save to DynamoDB
            self.bills_table.put_item(Item=bill_info)
            
            logger.info(f"Saved bill to DynamoDB: {bill_info['bill_id']}")
            return bill_info
            
        except Exception as e:
            logger.error(f"Failed to save bill to DynamoDB: {e}")
            return None
    
    def search_emails(self, query: str, max_results: int = 50) -> List[Dict]:
        """
        Search emails with a custom Gmail query
        
        Args:
            query: Gmail search query
            max_results: Maximum number of results to return
            
        Returns:
            List of email data dictionaries
        """
        try:
            if not self.service:
                if not self.authenticate():
                    return []
            
            logger.info(f"Searching emails with query: {query}")
            
            # Search emails
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                try:
                    # Get full message details
                    email_detail = self.service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()
                    
                    emails.append(email_detail)
                    
                except HttpError as e:
                    logger.warning(f"Could not fetch email {message['id']}: {e}")
                    continue
            
            logger.info(f"Found {len(emails)} emails matching query")
            return emails
            
        except Exception as e:
            logger.error(f"Email search failed: {e}")
            return []