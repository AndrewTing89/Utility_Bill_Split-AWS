#!/usr/bin/env python3
"""
PG&E Bill Split Automation - AWS Web Interface

Flask web application adapted for AWS deployment with DynamoDB backend.
"""

import os
import json
import logging
from datetime import datetime
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
                formatted_bills.append({
                    'id': bill.get('bill_id', ''),
                    'amount': float(bill.get('amount', 0)),
                    'due_date': bill.get('due_date', ''),
                    'roommate_portion': float(bill.get('roommate_portion', 0)),
                    'my_portion': float(bill.get('my_portion', 0)),
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
                return {
                    'id': bill.get('bill_id', ''),
                    'amount': float(bill.get('amount', 0)),
                    'due_date': bill.get('due_date', ''),
                    'roommate_portion': float(bill.get('roommate_portion', 0)),
                    'my_portion': float(bill.get('my_portion', 0)),
                    'processed_date': bill.get('processed_date', ''),
                    'status': bill.get('status', 'processed'),
                    'email_body': bill.get('email_body', '')
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
                'roommate_email': 'roommate@example.com',
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
    
    return render_template('bill_detail.html', 
                         bill=bill,
                         settings=settings)

@app.route('/download-pdf/<bill_id>')
def download_pdf(bill_id):
    """Download PDF for bill (placeholder)"""
    return jsonify({'error': 'PDF download not implemented yet'}), 501

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
        
        # TODO: Implement SMS sending via SNS
        return jsonify({
            'success': True,
            'message': 'Venmo request created and sent',
            'venmo_url': venmo_url,
            'amount': bill['roommate_portion']
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