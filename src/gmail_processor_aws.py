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
        self.dynamodb = boto3.resource('dynamodb')
        self.bills_table = self.dynamodb.Table(os.environ.get('BILLS_TABLE', 'pge-bills'))
        
    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using credentials stored in Lambda
        
        Returns:
            True if authentication successful
        """
        try:
            # In Lambda, credentials should be stored as environment variables
            # or in a secure location like Secrets Manager
            creds_json = os.environ.get('GMAIL_CREDENTIALS')
            if not creds_json:
                logger.error("Gmail credentials not found in environment")
                return False
                
            creds_data = json.loads(creds_json)
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
            query = f'from:DoNotReply@billpay.pge.com subject:"Your PG&E bill is ready" after:{after_date} before:{before_date}'
            
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
    
    def _extract_bill_info(self, email_data: Dict) -> Optional[Dict]:
        """Extract bill information from email"""
        try:
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
            
            # Create bill info
            bill_info = {
                'id': f"pge_{due_date.replace('/', '_')}_{int(bill_amount * 100)}",
                'email_id': email_data['id'],
                'amount': bill_amount,
                'due_date': due_date,
                'roommate_portion': round(roommate_portion, 2),
                'my_portion': round(my_portion, 2),
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
                if payload.get('mimeType') == 'text/plain':
                    data = payload.get('body', {}).get('data')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8')
            
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
            # Check for existing bill with same amount and due date
            response = self.bills_table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('amount').eq(bill_info['amount']) & 
                                boto3.dynamodb.conditions.Attr('due_date').eq(bill_info['due_date'])
            )
            
            return len(response.get('Items', [])) > 0
            
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
            
            logger.info(f"Saved bill to DynamoDB: {bill_info['id']}")
            return bill_info
            
        except Exception as e:
            logger.error(f"Failed to save bill to DynamoDB: {e}")
            return None