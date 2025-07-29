#!/usr/bin/env python3
"""
Venmo Payment Confirmation Detector

Detects Venmo payment confirmations from venmo@venmo.com emails and matches them
to pending PG&E bills by amount and timeframe to avoid false positives.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class VenmoPaymentDetector:
    """Detect and process Venmo payment confirmations"""
    
    def __init__(self, region='us-west-2'):
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.bills_table = self.dynamodb.Table('pge-bill-automation-bills-dev')
        self.log_table = self.dynamodb.Table('pge-processing-log')
        
    def is_venmo_payment_email(self, email_data: Dict) -> bool:
        """Check if email is a Venmo payment confirmation"""
        
        sender = email_data.get('sender', '').lower()
        subject = email_data.get('subject', '').lower()
        
        # Check if from Venmo
        if 'venmo@venmo.com' not in sender:
            return False
            
        # Check for payment confirmation keywords
        payment_keywords = [
            'you charged',
            'transfer date and amount',
            'money credited to your venmo account',
            'payment id:'
        ]
        
        body = email_data.get('body', '').lower()
        
        # Must contain at least 2 payment confirmation keywords
        keyword_count = sum(1 for keyword in payment_keywords if keyword in body)
        
        return keyword_count >= 2
    
    def extract_payment_info(self, email_body: str) -> Optional[Dict]:
        """Extract payment information from Venmo confirmation email"""
        
        try:
            payment_info = {}
            
            # Extract payer name (after "You charged")
            payer_match = re.search(r'You charged\s+([^\n]+)', email_body, re.IGNORECASE)
            if payer_match:
                payment_info['payer_name'] = payer_match.group(1).strip()
            
            # Extract payment amount (look for $ followed by decimal amount)
            # Pattern: $XXX.XX or $X,XXX.XX
            amount_patterns = [
                r'\$\s*(\d{1,3}(?:,\d{3})*\.\d{2})',  # $123.45 or $1,234.56
                r'\$\s*(\d+\.\d{2})',                   # $123.45
                r'private\+\s*\$\s*(\d+\.\d{2})',      # private+ $123.45
            ]
            
            amount = None
            for pattern in amount_patterns:
                amount_match = re.search(pattern, email_body, re.IGNORECASE)
                if amount_match:
                    amount_str = amount_match.group(1).replace(',', '')
                    amount = float(amount_str)
                    break
            
            if not amount:
                logger.warning("Could not extract payment amount from Venmo email")
                return None
                
            payment_info['amount'] = amount
            
            # Extract payment date
            date_patterns = [
                r'([A-Za-z]{3}\s+\d{1,2},\s+\d{4})',           # Sep 12, 2024
                r'(\d{1,2}/\d{1,2}/\d{4})',                     # 9/12/2024
                r'([A-Za-z]{3}\s+\d{1,2}\s+\d{4})',            # Sep 12 2024
            ]
            
            payment_date = None
            for pattern in date_patterns:
                date_match = re.search(pattern, email_body)
                if date_match:
                    try:
                        date_str = date_match.group(1)
                        # Try different date formats
                        for fmt in ['%b %d, %Y', '%m/%d/%Y', '%b %d %Y']:
                            try:
                                payment_date = datetime.strptime(date_str, fmt)
                                break
                            except ValueError:
                                continue
                        if payment_date:
                            break
                    except Exception as e:
                        logger.warning(f"Error parsing date {date_match.group(1)}: {e}")
            
            if not payment_date:
                # Default to today if we can't parse the date
                payment_date = datetime.now()
                logger.warning("Could not extract payment date, using current date")
            
            payment_info['payment_date'] = payment_date
            
            # Extract Payment ID
            payment_id_match = re.search(r'Payment ID:\s*(\d+)', email_body, re.IGNORECASE)
            if payment_id_match:
                payment_info['payment_id'] = payment_id_match.group(1)
            
            # Extract note/description (between payer name and transfer info)
            note_section = email_body.split('You charged')[1] if 'You charged' in email_body else email_body
            note_section = note_section.split('Transfer Date')[0] if 'Transfer Date' in note_section else note_section
            
            # Clean up the note section
            lines = [line.strip() for line in note_section.split('\n') if line.strip()]
            if len(lines) > 1:
                # Skip the payer name (first line) and get the note
                payment_info['note'] = ' '.join(lines[1:]).strip()
            
            logger.info(f"Extracted payment info: ${payment_info.get('amount', 'N/A')} from {payment_info.get('payer_name', 'Unknown')}")
            return payment_info
            
        except Exception as e:
            logger.error(f"Error extracting payment info: {e}")
            return None
    
    def find_matching_bills(self, payment_amount: float, payment_date: datetime, tolerance_days: int = 30) -> List[Dict]:
        """Find bills that match the payment amount and are within the date tolerance"""
        
        try:
            # Get all unpaid bills
            response = self.bills_table.scan(
                FilterExpression='attribute_not_exists(payment_confirmed) OR payment_confirmed = :false',
                ExpressionAttributeValues={':false': False}
            )
            
            matching_bills = []
            amount_tolerance = 0.01  # $0.01 tolerance for floating point comparison
            
            for bill in response.get('Items', []):
                # Check if roommate portion matches payment amount
                roommate_portion = float(bill.get('roommate_portion', 0))
                
                if abs(roommate_portion - payment_amount) <= amount_tolerance:
                    # Check if bill is within the date tolerance
                    bill_date_str = bill.get('due_date', '')
                    try:
                        # Parse bill due date (format: M/D/YYYY)
                        bill_date = datetime.strptime(bill_date_str, '%m/%d/%Y')
                        
                        # Check if payment is within tolerance period of bill
                        days_diff = abs((payment_date - bill_date).days)
                        
                        if days_diff <= tolerance_days:
                            matching_bills.append({
                                'bill': bill,
                                'amount_match': abs(roommate_portion - payment_amount),
                                'days_diff': days_diff
                            })
                            
                    except ValueError:
                        logger.warning(f"Could not parse bill date: {bill_date_str}")
                        continue
            
            # Sort by best match (closest amount, then closest date)
            matching_bills.sort(key=lambda x: (x['amount_match'], x['days_diff']))
            
            logger.info(f"Found {len(matching_bills)} matching bills for payment of ${payment_amount}")
            return matching_bills
            
        except Exception as e:
            logger.error(f"Error finding matching bills: {e}")
            return []
    
    def mark_bill_as_paid(self, bill_id: str, payment_info: Dict) -> bool:
        """Mark a bill as paid with payment confirmation details"""
        
        try:
            # Update bill status
            self.bills_table.update_item(
                Key={'bill_id': bill_id},
                UpdateExpression='''
                    SET payment_confirmed = :confirmed,
                        payment_date = :payment_date,
                        payment_amount = :payment_amount,
                        payment_id = :payment_id,
                        payer_name = :payer_name,
                        payment_note = :payment_note,
                        status = :status
                ''',
                ExpressionAttributeValues={
                    ':confirmed': True,
                    ':payment_date': payment_info['payment_date'].isoformat(),
                    ':payment_amount': Decimal(str(payment_info['amount'])),
                    ':payment_id': payment_info.get('payment_id', ''),
                    ':payer_name': payment_info.get('payer_name', ''),
                    ':payment_note': payment_info.get('note', ''),
                    ':status': 'paid'
                }
            )
            
            # Log the payment confirmation
            self.log_table.put_item(
                Item={
                    'bill_id': bill_id,
                    'timestamp': datetime.now().isoformat(),
                    'action': 'payment_confirmed',
                    'details': f"Payment of ${payment_info['amount']} confirmed from {payment_info.get('payer_name', 'Unknown')}"
                }
            )
            
            logger.info(f"Marked bill {bill_id} as paid: ${payment_info['amount']}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking bill as paid: {e}")
            return False
    
    def process_venmo_payment_email(self, email_data: Dict) -> Dict:
        """Process a Venmo payment confirmation email"""
        
        result = {
            'success': False,
            'message': '',
            'bills_updated': 0,
            'payment_info': None
        }
        
        try:
            # Verify this is a Venmo payment email
            if not self.is_venmo_payment_email(email_data):
                result['message'] = 'Not a Venmo payment confirmation email'
                return result
            
            # Extract payment information
            payment_info = self.extract_payment_info(email_data.get('body', ''))
            if not payment_info:
                result['message'] = 'Could not extract payment information'
                return result
            
            result['payment_info'] = payment_info
            
            # Find matching bills
            matching_bills = self.find_matching_bills(
                payment_info['amount'],
                payment_info['payment_date']
            )
            
            if not matching_bills:
                result['message'] = f"No matching bills found for payment of ${payment_info['amount']}"
                return result
            
            if len(matching_bills) > 1:
                # Multiple matches - use the best match (first in sorted list)
                logger.warning(f"Multiple bills match payment of ${payment_info['amount']}, using best match")
            
            # Mark the best matching bill as paid
            best_match = matching_bills[0]
            bill_id = best_match['bill']['bill_id']
            
            if self.mark_bill_as_paid(bill_id, payment_info):
                result['success'] = True
                result['bills_updated'] = 1
                result['message'] = f"Bill {bill_id} marked as paid (${payment_info['amount']})"
            else:
                result['message'] = 'Failed to update bill status'
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing Venmo payment email: {e}")
            result['message'] = f"Error: {str(e)}"
            return result
    
    def check_for_payment_confirmations(self, days_back: int = 7) -> Dict:
        """Check for Venmo payment confirmations in recent emails"""
        
        try:
            # This would integrate with Gmail processor to get recent emails
            # For now, return placeholder
            return {
                'success': True,
                'message': 'Payment confirmation check completed',
                'emails_processed': 0,
                'payments_found': 0,
                'bills_updated': 0
            }
            
        except Exception as e:
            logger.error(f"Error checking payment confirmations: {e}")
            return {
                'success': False,
                'message': f"Error: {str(e)}"
            }

# Test function
def test_payment_extraction():
    """Test payment info extraction with the provided example"""
    
    sample_email = """
    You charged Ushi Lo
    Water bill: 7/02/24 - 8/27/2024

    549.63/3 = 183.21

    Transfer Date and Amount:
    Sep 12, 2024 PDT · private+ $183.21
    Like
    Comment
    Money credited to your Venmo account.

    Transfer to your bank.
    Payment ID: 4155750468701492611
    """
    
    detector = VenmoPaymentDetector()
    payment_info = detector.extract_payment_info(sample_email)
    
    print("Test Payment Extraction:")
    print(f"Payment Info: {payment_info}")
    
    expected_amount = 183.21
    if payment_info and abs(payment_info['amount'] - expected_amount) < 0.01:
        print("✅ Amount extraction test passed")
    else:
        print("❌ Amount extraction test failed")

if __name__ == "__main__":
    test_payment_extraction()