#!/usr/bin/env python3
"""
SES Email Sender for PG&E Bill Split notifications with screenshots
"""

import boto3
import json
import base64
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
from PIL import Image
import io

logger = logging.getLogger(__name__)

class SESEmailSender:
    """Send bill split notifications via SES with Venmo links and screenshots"""
    
    def __init__(self, region='us-west-2'):
        self.ses_client = boto3.client('sesv2', region_name=region)
        self.template_name = 'pge-bill-split-notification'
    
    def pdf_to_screenshot(self, pdf_data: bytes) -> Optional[bytes]:
        """Convert PDF to PNG screenshot for email attachment"""
        try:
            # For now, return None - we'll implement this after basic email works
            # TODO: Use pdf2image or similar to convert PDF to image
            logger.info("PDF to screenshot conversion not implemented yet")
            return None
            
        except Exception as e:
            logger.error(f"Error converting PDF to screenshot: {e}")
            return None
    
    def generate_venmo_link(self, bill_data: Dict[str, Any], settings: Dict[str, str]) -> str:
        """Generate Venmo payment request link"""
        
        roommate_venmo = settings.get('roommate_venmo', 'UshiLo')
        amount = float(bill_data.get('roommate_portion', 0))
        due_date = bill_data.get('due_date', 'Unknown')
        
        # Venmo deep link
        venmo_link = f"venmo://paycharge?txn=charge&recipients={roommate_venmo}&amount={amount:.2f}&note=PG%26E%20bill%20split%20-%20{due_date}"
        
        return venmo_link
    
    def send_bill_notification(
        self, 
        bill_data: Dict[str, Any], 
        settings: Dict[str, str],
        pdf_data: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """Send bill split notification email with Venmo link and screenshot"""
        
        try:
            # Extract data
            total_amount = float(bill_data.get('amount', 0))
            roommate_amount = float(bill_data.get('roommate_portion', 0))
            due_date = bill_data.get('due_date', 'Unknown')
            
            # Email addresses
            sender_email = settings.get('my_email', 'andrewhting@gmail.com')
            recipient_email = settings.get('roommate_email', 'andrewhting@gmail.com')  # Same for testing
            
            # Names
            sender_name = settings.get('my_name', 'Andrew')
            roommate_name = settings.get('roommate_name', 'Roommate')
            
            # Generate Venmo link
            venmo_link = self.generate_venmo_link(bill_data, settings)
            
            # Template data
            template_data = {
                'total_amount': f"{total_amount:.2f}",
                'roommate_amount': f"{roommate_amount:.2f}",
                'due_date': due_date,
                'bill_month': datetime.now().strftime('%B %Y'),
                'venmo_link': venmo_link,
                'sender_name': sender_name,
                'roommate_name': roommate_name,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Send email using template
            if pdf_data:
                # Convert PDF to screenshot
                screenshot_data = self.pdf_to_screenshot(pdf_data)
                result = self._send_email_with_attachment(
                    sender_email, recipient_email, template_data, screenshot_data
                )
            else:
                # Send without screenshot for now
                result = self._send_email_simple(sender_email, recipient_email, template_data)
            
            if result['success']:
                logger.info(f"Bill notification sent successfully to {recipient_email}")
                return {
                    'success': True,
                    'message': f'Email sent to {recipient_email}',
                    'message_id': result.get('message_id'),
                    'venmo_link': venmo_link
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error sending bill notification: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_email_simple(self, sender: str, recipient: str, template_data: Dict[str, str]) -> Dict[str, Any]:
        """Send email using SES template (without attachments)"""
        
        try:
            response = self.ses_client.send_email(
                FromEmailAddress=sender,
                Destination={
                    'ToAddresses': [recipient]
                },
                Content={
                    'Template': {
                        'TemplateName': self.template_name,
                        'TemplateData': json.dumps(template_data)
                    }
                }
            )
            
            return {
                'success': True,
                'message_id': response['MessageId']
            }
            
        except Exception as e:
            logger.error(f"Error sending simple email: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_email_with_attachment(
        self, 
        sender: str, 
        recipient: str, 
        template_data: Dict[str, str], 
        screenshot_data: Optional[bytes]
    ) -> Dict[str, Any]:
        """Send email with screenshot attachment (future implementation)"""
        
        # For now, fall back to simple email
        logger.info("Email with attachment not implemented yet, sending simple email")
        return self._send_email_simple(sender, recipient, template_data)
    
    def test_email_sending(self, settings: Dict[str, str]) -> Dict[str, Any]:
        """Test email sending with sample data"""
        
        # Sample bill data for testing
        test_bill_data = {
            'amount': 120.00,
            'roommate_portion': 40.00,
            'due_date': '08/15/2025',
            'bill_id': 'test-001'
        }
        
        logger.info("Sending test email...")
        return self.send_bill_notification(test_bill_data, settings)

if __name__ == "__main__":
    # Test the email sender
    logging.basicConfig(level=logging.INFO)
    
    sender = SESEmailSender()
    
    test_settings = {
        'my_email': 'andrewhting@gmail.com',
        'roommate_email': 'andrewhting@gmail.com',  # Same for testing
        'my_name': 'Andrew',
        'roommate_name': 'Roommate',
        'roommate_venmo': 'UshiLo'
    }
    
    result = sender.test_email_sending(test_settings)
    print(f"Test result: {result}")