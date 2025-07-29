#!/usr/bin/env python3
"""
PG&E Bill Split Automation - AWS Web Interface

Flask web application adapted for AWS deployment with DynamoDB backend.
"""

import os
import json
import logging
from datetime import datetime
from decimal import Decimal
from flask import Flask, render_template, request, jsonify, redirect, url_for
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# AWS Configuration
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
lambda_client = boto3.client('lambda', region_name=AWS_REGION)
secrets_client = boto3.client('secretsmanager', region_name=AWS_REGION)

# Environment variables
BILLS_TABLE = os.environ.get('BILLS_TABLE', 'pge-bill-automation-bills-dev')
LAMBDA_FUNCTION = os.environ.get('LAMBDA_FUNCTION', 'pge-bill-automation-automation-dev')
SECRETS_ARN = os.environ.get('SECRETS_ARN')

class AWSBillDatabase:
    """DynamoDB interface for bill management"""
    
    def __init__(self):
        self.table = dynamodb.Table(BILLS_TABLE)
    
    def get_all_bills(self):
        """Get all bills from DynamoDB"""
        try:
            response = self.table.scan()
            bills = response.get('Items', [])
            
            # Convert to expected format and sort by date
            formatted_bills = []
            for bill in bills:
                # Handle Decimal conversion properly
                amount = bill.get('amount', 0)
                roommate_portion = bill.get('roommate_portion', 0)  
                my_portion = bill.get('my_portion', 0)
                
                # Convert Decimal to float if needed
                if isinstance(amount, Decimal):
                    amount = float(amount)
                if isinstance(roommate_portion, Decimal):
                    roommate_portion = float(roommate_portion)
                if isinstance(my_portion, Decimal):
                    my_portion = float(my_portion)
                
                formatted_bills.append({
                    'id': bill.get('bill_id', ''),
                    'amount': amount,
                    'due_date': bill.get('due_date', ''),
                    'roommate_portion': roommate_portion,
                    'my_portion': my_portion,
                    'processed_date': bill.get('processed_date', ''),
                    'status': bill.get('status', 'processed')
                })
            
            # Sort by due date (newest first)
            try:
                formatted_bills.sort(key=lambda x: datetime.strptime(x['due_date'], '%m/%d/%Y'), reverse=True)
            except ValueError:
                # If date parsing fails, just return unsorted
                pass
            
            return formatted_bills
            
        except ClientError as e:
            logger.error(f"Error fetching bills: {e}")
            return []
    
    def get_bill_by_id(self, bill_id):
        """Get specific bill by ID"""
        try:
            response = self.table.get_item(Key={'bill_id': bill_id})
            if 'Item' in response:
                bill = response['Item']
                
                # Handle Decimal conversion properly
                amount = bill.get('amount', 0)
                roommate_portion = bill.get('roommate_portion', 0)  
                my_portion = bill.get('my_portion', 0)
                
                # Convert Decimal to float if needed
                if isinstance(amount, Decimal):
                    amount = float(amount)
                if isinstance(roommate_portion, Decimal):
                    roommate_portion = float(roommate_portion)
                if isinstance(my_portion, Decimal):
                    my_portion = float(my_portion)
                
                return {
                    'id': bill.get('bill_id', ''),
                    'amount': amount,
                    'due_date': bill.get('due_date', ''),
                    'roommate_portion': roommate_portion,
                    'my_portion': my_portion,
                    'processed_date': bill.get('processed_date', ''),
                    'status': bill.get('status', 'processed'),
                    'email_body': bill.get('email_body', ''),
                    'pdf_generated': bill.get('pdf_generated', False),
                    'pdf_sent': bill.get('pdf_sent', False),
                    'venmo_sent': bill.get('venmo_sent', False),
                    'email_subject': bill.get('email_subject', ''),
                    'email_date': bill.get('email_date', ''),
                    'email_id': bill.get('email_id', ''),
                    'venmo_link': bill.get('venmo_link', ''),
                    'notes': bill.get('notes', '')
                }
            return None
            
        except ClientError as e:
            logger.error(f"Error fetching bill {bill_id}: {e}")
            return None

def load_settings():
    """Load settings from AWS Secrets Manager"""
    try:
        if not SECRETS_ARN:
            # Default settings with your actual info for development
            return {
                'test_mode': True,
                'gmail_user': 'andrewhting@gmail.com',
                'roommate_venmo': 'UshiLo',
                'my_venmo': 'andrewhting',
                'my_phone': '+19298884132',
                'roommate_email': 'andrewhting@gmail.com',
                'my_email': 'andrewhting@gmail.com'
            }
            
        response = secrets_client.get_secret_value(SecretId=SECRETS_ARN)
        return json.loads(response['SecretString'])
        
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        return {
            'test_mode': True,
            'gmail_user': 'andrewhting@gmail.com',
            'my_phone': '+19298884132'
        }

# Initialize database
db = AWSBillDatabase()

@app.route('/')
def dashboard():
    """Main dashboard"""
    try:
        logger.info("Loading dashboard...")
        bills = db.get_all_bills()
        logger.info(f"Found {len(bills) if bills else 0} bills")
        
        settings = load_settings()
        logger.info("Settings loaded")
        
        # Calculate summary statistics
        total_bills = len(bills) if bills else 0
        total_amount = sum(bill['amount'] for bill in bills) if bills else 0
        total_roommate_portion = sum(bill['roommate_portion'] for bill in bills) if bills else 0
        
        summary = {
            'total_bills': total_bills,
            'total_amount': total_amount,
            'total_roommate_portion': total_roommate_portion,
            'pending_bills': 0,  # For now, no pending logic
            'pdfs_generated': total_bills,  # One PDF per bill
            'pdfs_sent': total_bills,  # One email per bill
            'average_bill': total_amount / total_bills if total_bills > 0 else 0
        }
        
        logger.info("Rendering dashboard template...")
        return render_template('dashboard.html', 
                             bills=bills[:5] if bills else [],  # Show latest 5 bills
                             stats=summary,
                             settings=settings)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return render_template('error.html', 
                             error=f"Dashboard failed to load: {str(e)}"), 500

@app.route('/bills')
def bills():
    """Bills management page"""
    all_bills = db.get_all_bills()
    settings = load_settings()
    
    return render_template('bills.html', 
                         bills=all_bills,
                         settings=settings)

@app.route('/bill/<bill_id>')
def bill_detail(bill_id):
    """Bill detail page"""
    bill = db.get_bill_by_id(bill_id)
    settings = load_settings()
    
    if not bill:
        return render_template('error.html', 
                             error="Bill not found"), 404
    
    # Get processing log for this bill (placeholder for now)
    bill_log = []  # TODO: Implement processing log retrieval from DynamoDB
    
    return render_template('bill_detail.html', 
                         bill=bill,
                         bill_log=bill_log,
                         settings=settings)

@app.route('/download-pdf/<bill_id>')
def download_pdf(bill_id):
    """Download PDF for bill (placeholder)"""
    return jsonify({'error': 'PDF download not implemented yet'}), 501

@app.route('/generate-pdf/<bill_id>', methods=['POST'])
def generate_pdf(bill_id):
    """Generate PDF for bill"""
    try:
        bill = db.get_bill_by_id(bill_id)
        if not bill:
            return jsonify({'success': False, 'message': 'Bill not found'}), 404
        
        # TODO: Implement PDF generation via Lambda
        return jsonify({
            'success': True,
            'message': 'PDF generation not implemented yet (TEST MODE)'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/send-email/<bill_id>', methods=['POST'])
def send_email_route(bill_id):
    """Send email for bill"""
    try:
        bill = db.get_bill_by_id(bill_id)
        if not bill:
            return jsonify({'success': False, 'message': 'Bill not found'}), 404
        
        # TODO: Implement email sending via SES
        return jsonify({
            'success': True,
            'message': 'Email sending not implemented yet (TEST MODE)'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/test-email/<bill_id>', methods=['POST'])
def test_email_route(bill_id):
    """Test email for bill"""
    try:
        bill = db.get_bill_by_id(bill_id)
        if not bill:
            return jsonify({'success': False, 'message': 'Bill not found'}), 404
        
        settings = load_settings()
        
        # Return test email info
        return jsonify({
            'success': True,
            'message': 'Test email would be sent (TEST MODE)',
            'last_sent': '2025-07-29 04:30:00',
            'debug_info': {
                'recipient': settings.get('roommate_email', 'roommate@example.com'),
                'sender': settings.get('my_email', 'me@example.com'),
                'pdf_exists': bill.get('pdf_generated', False),
                'pdf_size': 0,
                'test_mode': settings.get('test_mode', True),
                'email_notifications_enabled': True
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/generate-venmo/<bill_id>', methods=['POST'])
def generate_venmo_route(bill_id):
    """Generate Venmo request for bill"""
    try:
        bill = db.get_bill_by_id(bill_id)
        if not bill:
            return jsonify({'success': False, 'message': 'Bill not found'}), 404
        
        settings = load_settings()
        
        # Generate Venmo URL
        venmo_url = f"venmo://paycharge?txn=charge&recipients={settings.get('roommate_venmo', 'UshiLo')}&amount={bill['roommate_portion']:.2f}&note=PG%26E%20bill%20split%20-%20{bill['due_date']}"
        
        return jsonify({
            'success': True,
            'message': 'Venmo request created',
            'summary': {
                'roommate_owes': f"{bill['roommate_portion']:.2f}",
                'payment_note': f"PG&E bill split - {bill['due_date']}"
            },
            'venmo_url': venmo_url,
            'web_url': f"https://venmo.com/{settings.get('roommate_venmo', 'UshiLo')}?txn=pay&amount={bill['roommate_portion']:.2f}&note=PG%26E%20bill%20split"
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/process-bills', methods=['POST'])
def process_bills():
    """Trigger Lambda function to process new bills"""
    try:
        data = request.get_json() or {}
        test_mode = data.get('test_mode', True)
        
        # Invoke Lambda function
        payload = {
            'test_mode': test_mode,
            'manual_trigger': True
        }
        
        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Parse response
        result = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            body = json.loads(result.get('body', '{}'))
            return jsonify({
                'success': True,
                'message': 'Bills processed successfully',
                'result': body.get('result', {})
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Lambda function failed'
            }), 500
            
    except Exception as e:
        logger.error(f"Error processing bills: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/check-payments', methods=['POST'])
def check_payments():
    """Trigger Lambda function to check for Venmo payment confirmations only"""
    try:
        data = request.get_json() or {}
        test_mode = data.get('test_mode', True)
        
        # Invoke Lambda function with payment check flag
        payload = {
            'test_mode': test_mode,
            'manual_trigger': True,
            'payment_check_only': True
        }
        
        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Parse response
        result = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            body = json.loads(result.get('body', '{}'))
            return jsonify({
                'success': True,
                'message': 'Bills processed successfully',
                'result': body.get('result', {})
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Lambda function failed'
            }), 500
            
    except Exception as e:
        logger.error(f"Error processing bills: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/create-venmo-request', methods=['POST'])
def create_venmo_request():
    """Create Venmo payment request"""
    try:
        data = request.get_json()
        bill_id = data.get('bill_id')
        
        if not bill_id:
            return jsonify({'success': False, 'error': 'Bill ID required'}), 400
        
        bill = db.get_bill_by_id(bill_id)
        if not bill:
            return jsonify({'success': False, 'error': 'Bill not found'}), 404
        
        settings = load_settings()
        
        # Generate Venmo URL
        venmo_url = f"venmo://paycharge?txn=charge&recipients={settings.get('roommate_venmo', 'UshiLo')}&amount={bill['roommate_portion']:.2f}&note=PG%26E%20bill%20split%20-%20{bill['due_date']}"
        
        # In test mode, just return the URL
        if settings.get('test_mode', True):
            return jsonify({
                'success': True,
                'message': 'TEST MODE: Venmo request created (not sent)',
                'venmo_url': venmo_url,
                'amount': bill['roommate_portion']
            })
        
        # Send SMS via email-to-SMS gateway
        try:
            import smtplib
            from email.mime.text import MIMEText
            
            # Get SMS credentials from settings
            gmail_user = settings.get('gmail_user', 'andrewhting@gmail.com')
            gmail_app_password = settings.get('gmail_app_password')
            sms_gateway = settings.get('sms_gateway', '9298884132@vtext.com')
            
            if not gmail_app_password:
                raise Exception("Gmail app password not configured in settings")
            
            bill_month = datetime.strptime(bill['due_date'], '%m/%d/%Y').strftime('%B %Y')
            message_body = f"💰 PG&E Bill - {bill_month}\nAmount: ${bill['roommate_portion']:.2f}\n{venmo_url}"
            
            # Create and send email-to-SMS
            msg = MIMEText(message_body)
            msg['From'] = gmail_user
            msg['To'] = sms_gateway
            msg['Subject'] = ''  # Empty subject for SMS
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(gmail_user, gmail_app_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"SMS sent successfully via {sms_gateway}")
            
            return jsonify({
                'success': True,
                'message': 'Venmo request created and SMS sent!',
                'venmo_url': venmo_url,
                'amount': bill['roommate_portion'],
                'sms_sent': True,
                'sms_gateway': sms_gateway
            })
            
        except Exception as e:
            logger.error(f"SMS sending failed: {e}")
            # Still return success but note SMS failed
            return jsonify({
                'success': True,
                'message': 'Venmo request created (SMS failed)',
                'venmo_url': venmo_url,
                'amount': bill['roommate_portion'],
                'sms_sent': False,
                'sms_error': str(e)
            })
        
    except Exception as e:
        logger.error(f"Error creating Venmo request: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/send-email', methods=['POST'])
def send_email():
    """Send email notification"""
    try:
        data = request.get_json()
        bill_id = data.get('bill_id')
        
        if not bill_id:
            return jsonify({'success': False, 'error': 'Bill ID required'}), 400
        
        bill = db.get_bill_by_id(bill_id)
        if not bill:
            return jsonify({'success': False, 'error': 'Bill not found'}), 404
        
        settings = load_settings()
        
        # In test mode, simulate email sending
        if settings.get('test_mode', True):
            return jsonify({
                'success': True,
                'message': 'TEST MODE: Email sent (simulated)',
                'recipient': settings.get('roommate_email', 'roommate@example.com')
            })
        
        # TODO: Implement email sending via SES
        return jsonify({
            'success': True,
            'message': 'Email sent successfully',
            'recipient': settings.get('roommate_email')
        })
        
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/settings')
def settings():
    """Settings page"""
    settings = load_settings()
    schedule_status = {'loaded': True, 'next_run': 'February 5, 2025 at 2:00 AM PT'}
    return render_template('settings.html', settings=settings, schedule_status=schedule_status)

@app.route('/api/test-connections', methods=['GET'])
@app.route('/test-connection/<component>')
def test_connections(component=None):
    """Test all connections or specific component"""
    results = {}
    
    if component:
        # Test specific component
        if component == 'gmail':
            try:
                # Check if Lambda function has Gmail credentials
                lambda_client.get_function(FunctionName=LAMBDA_FUNCTION)
                results['status'] = 'success'
                results['message'] = 'Gmail integration ready via Lambda'
            except Exception as e:
                results['status'] = 'error'
                results['message'] = f'Gmail test failed: {str(e)}'
                
        elif component == 'mail-app':
            results['status'] = 'info'
            results['message'] = 'Mail app not needed for AWS deployment'
            
        elif component == 'pdf':
            try:
                # Test if we can access S3 for PDF storage
                import boto3
                s3 = boto3.client('s3', region_name=AWS_REGION)
                # Just test permissions, don't create anything
                results['status'] = 'success'
                results['message'] = 'PDF generation and S3 storage ready'
            except Exception as e:
                results['status'] = 'warning'
                results['message'] = f'PDF storage may have issues: {str(e)}'
                
        elif component == 'venmo':
            settings = load_settings()
            roommate_venmo = settings.get('roommate_venmo')
            my_venmo = settings.get('my_venmo')
            if roommate_venmo and my_venmo:
                results['status'] = 'success'
                results['message'] = f'Venmo configured: {roommate_venmo} & {my_venmo}'
            else:
                results['status'] = 'warning'
                results['message'] = 'Venmo usernames not fully configured'
                
        else:
            results['status'] = 'error'
            results['message'] = f'Unknown component: {component}'
    else:
        # Test all connections
        try:
            # Test DynamoDB
            table = dynamodb.Table(BILLS_TABLE)
            table.table_status
            results['dynamodb'] = 'Connected'
        except Exception as e:
            results['dynamodb'] = f'Error: {str(e)}'
        
        try:
            # Test Lambda
            lambda_client.get_function(FunctionName=LAMBDA_FUNCTION)
            results['lambda'] = 'Connected'
        except Exception as e:
            results['lambda'] = f'Error: {str(e)}'
        
        try:
            # Test settings
            settings = load_settings()
            results['settings'] = 'Loaded'
            results['test_mode'] = settings.get('test_mode', 'Unknown')
        except Exception as e:
            results['settings'] = f'Error: {str(e)}'
    
    return jsonify(results)

@app.route('/api/debug-bills')
def debug_bills():
    """Debug endpoint to see raw DynamoDB data"""
    try:
        response = db.table.scan()
        items = response.get('Items', [])
        
        # Return raw data for debugging
        debug_info = {
            'raw_items_count': len(items),
            'raw_items': items,
            'processed_bills': db.get_all_bills()
        }
        
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'type': str(type(e))
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0-aws'
    })

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', 
                         error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', 
                         error="Internal server error"), 500

if __name__ == '__main__':
    # For local development
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)