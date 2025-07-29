#!/usr/bin/env python3
"""
Gmail Venmo Integration

Extends the Gmail processor to also check for Venmo payment confirmations
and automatically mark bills as paid when payments are detected.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List
from venmo_payment_detector import VenmoPaymentDetector

logger = logging.getLogger(__name__)

class GmailVenmoIntegration:
    """Integration class for processing both PG&E bills and Venmo payment confirmations"""
    
    def __init__(self, gmail_processor, settings: Dict):
        self.gmail_processor = gmail_processor
        self.settings = settings
        self.venmo_detector = VenmoPaymentDetector()
        
    def process_recent_emails(self, days_back: int = 30) -> Dict:
        """Process recent emails for both bills and payment confirmations"""
        
        result = {
            'bills_processed': 0,
            'payments_processed': 0,
            'bills_marked_paid': 0,
            'new_bills': [],
            'payment_confirmations': [],
            'errors': []
        }
        
        try:
            # First, process PG&E bills (existing functionality)
            bill_result = self.gmail_processor.process_bills(days_back=days_back)
            result['bills_processed'] = bill_result.get('processed', 0)
            result['new_bills'] = bill_result.get('new_bills', [])
            if bill_result.get('errors'):
                result['errors'].extend(bill_result['errors'])
            
            # Then, check for Venmo payment confirmations
            payment_result = self.check_venmo_payments(days_back=days_back)
            result['payments_processed'] = payment_result.get('emails_processed', 0)
            result['bills_marked_paid'] = payment_result.get('bills_updated', 0)
            result['payment_confirmations'] = payment_result.get('payments_found', [])
            if payment_result.get('errors'):
                result['errors'].extend(payment_result['errors'])
            
            logger.info(f"Email processing complete: {result['bills_processed']} bills, {result['payments_processed']} payment emails")
            return result
            
        except Exception as e:
            logger.error(f"Error in email processing: {e}")
            result['errors'].append(str(e))
            return result
    
    def check_venmo_payments(self, days_back: int = 30) -> Dict:
        """Check recent emails for Venmo payment confirmations"""
        
        result = {
            'success': True,
            'emails_processed': 0,
            'bills_updated': 0,
            'payments_found': [],
            'errors': []
        }
        
        try:
            # Build Gmail query for Venmo emails
            since_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
            
            # Search for emails from Venmo with payment confirmation keywords
            query_parts = [
                f'from:venmo@venmo.com',
                f'after:{since_date}',
                '"you charged"',
                '"money credited"'
            ]
            
            query = ' '.join(query_parts)
            logger.info(f"Searching for Venmo payments with query: {query}")
            
            # Get emails from Gmail
            emails = self.gmail_processor.search_emails(query, max_results=50)
            
            for email_data in emails:
                try:
                    result['emails_processed'] += 1
                    
                    # Process this email for payment confirmation
                    payment_result = self.venmo_detector.process_venmo_payment_email(email_data)
                    
                    if payment_result['success']:
                        result['bills_updated'] += payment_result.get('bills_updated', 0)
                        result['payments_found'].append({
                            'email_id': email_data.get('id'),
                            'payment_info': payment_result.get('payment_info'),
                            'message': payment_result.get('message')
                        })
                        logger.info(f"Payment confirmation processed: {payment_result['message']}")
                    else:
                        # Not an error - just not a matching payment
                        if "not a venmo payment" not in payment_result['message'].lower():
                            logger.debug(f"Payment processing result: {payment_result['message']}")
                
                except Exception as e:
                    logger.error(f"Error processing email {email_data.get('id', 'unknown')}: {e}")
                    result['errors'].append(f"Email processing error: {str(e)}")
            
            logger.info(f"Venmo payment check complete: {result['emails_processed']} emails, {result['bills_updated']} bills marked paid")
            return result
            
        except Exception as e:
            logger.error(f"Error checking Venmo payments: {e}")
            result['success'] = False
            result['errors'].append(str(e))
            return result
    
    def get_payment_status_summary(self) -> Dict:
        """Get summary of bill payment statuses"""
        
        try:
            # Query DynamoDB for bill statuses
            bills_table = self.venmo_detector.bills_table
            
            response = bills_table.scan()
            bills = response.get('Items', [])
            
            summary = {
                'total_bills': len(bills),
                'paid_bills': 0,
                'unpaid_bills': 0,
                'total_amount': 0.0,
                'paid_amount': 0.0,
                'outstanding_amount': 0.0
            }
            
            for bill in bills:
                amount = float(bill.get('roommate_portion', 0))
                summary['total_amount'] += amount
                
                if bill.get('payment_confirmed', False):
                    summary['paid_bills'] += 1
                    summary['paid_amount'] += amount
                else:
                    summary['unpaid_bills'] += 1
                    summary['outstanding_amount'] += amount
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting payment status summary: {e}")
            return {
                'total_bills': 0,
                'paid_bills': 0,
                'unpaid_bills': 0,
                'error': str(e)
            }

def test_venmo_integration():
    """Test the Venmo integration with mock data"""
    
    print("🧪 Testing Venmo Integration...")
    
    # Mock Gmail processor for testing
    class MockGmailProcessor:
        def process_bills(self, days_back=30):
            return {
                'processed': 1,
                'new_bills': [{'id': 'test_bill_123', 'amount': 288.15}],
                'errors': []
            }
        
        def search_emails(self, query, max_results=50):
            # Return mock Venmo email
            return [{
                'id': 'mock_venmo_email',
                'sender': 'venmo@venmo.com',
                'subject': 'Payment Notification',
                'body': '''
                You charged Ushi Lo
                PG&E bill split - 8/08/2025

                Transfer Date and Amount:
                Jul 29, 2025 PDT · private+ $96.05
                
                Money credited to your Venmo account.
                Payment ID: 1234567890123456789
                '''
            }]
    
    # Test settings
    settings = {
        'roommate_venmo': 'UshiLo',
        'my_email': 'test@example.com'
    }
    
    # Create integration
    mock_processor = MockGmailProcessor()
    integration = GmailVenmoIntegration(mock_processor, settings)
    
    # Test recent email processing
    result = integration.process_recent_emails(days_back=7)
    
    print(f"📊 Integration Test Results:")
    print(f"  • Bills processed: {result['bills_processed']}")
    print(f"  • Payment emails processed: {result['payments_processed']}")
    print(f"  • Bills marked as paid: {result['bills_marked_paid']}")
    print(f"  • Errors: {len(result['errors'])}")
    
    if result['errors']:
        print(f"  • Error details: {result['errors']}")

if __name__ == "__main__":
    test_venmo_integration()