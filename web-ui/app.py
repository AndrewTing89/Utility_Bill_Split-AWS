#!/usr/bin/env python3
"""
PG&E Bill Split Automation - Web Interface

A Flask web application for managing PG&E bill splitting with roommates.
Provides an intuitive dashboard for tracking bills, generating PDFs, 
creating Venmo requests, and managing email notifications.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from datetime import datetime
import logging
import traceback
from pathlib import Path

from src.bill_processor import BillProcessor
from src.database import BillDatabase
from src.pdf_generator import PDFGenerator
from src.venmo_links import VenmoLinkGenerator
from src.email_notifier import EmailNotifier
from src.gmail_parser import GmailParser
from src.scheduler import MacScheduler
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
app.secret_key = 'pge-bill-split-secret-key-change-in-production'

# Initialize components
db = BillDatabase()
processor = BillProcessor()
pdf_generator = PDFGenerator()
venmo_generator = VenmoLinkGenerator()
email_notifier = EmailNotifier()
scheduler = MacScheduler()


@app.route('/')
def dashboard():
    """Main dashboard showing recent bills and system status"""
    try:
        # Get system statistics
        stats = db.get_stats()
        
        # Get recent bills
        recent_bills = db.get_recent_bills(limit=5)
        
        # Get pending bills
        pending_bills = db.get_bills_by_status('pending')
        
        # Get processing log
        recent_activity = db.get_processing_log(limit=10)
        
        return render_template('dashboard.html',
                             stats=stats,
                             recent_bills=recent_bills,
                             pending_bills=pending_bills,
                             recent_activity=recent_activity,
                             test_mode=settings.TEST_MODE)
    
    except Exception as e:
        app.logger.error(f"Dashboard error: {e}")
        flash(f"Error loading dashboard: {e}", 'error')
        return render_template('error.html', error=str(e))


@app.route('/bills')
def bills_list():
    """List all bills with filtering and pagination"""
    try:
        # Get filter parameters
        status = request.args.get('status', 'all')
        limit = int(request.args.get('limit', 20))
        
        # Get bills based on filter
        if status == 'all':
            bills = db.get_recent_bills(limit=limit)
        else:
            bills = db.get_bills_by_status(status)[:limit]
        
        return render_template('bills.html',
                             bills=bills,
                             current_status=status)
    
    except Exception as e:
        app.logger.error(f"Bills list error: {e}")
        flash(f"Error loading bills: {e}", 'error')
        return redirect(url_for('dashboard'))


@app.route('/bill/<int:bill_id>')
def bill_detail(bill_id):
    """Show detailed information about a specific bill"""
    try:
        bill = db.get_bill_by_id(bill_id)
        if not bill:
            flash('Bill not found', 'error')
            return redirect(url_for('bills_list'))
        
        # Get processing log for this bill
        bill_log = db.get_processing_log(bill_id=bill_id, limit=20)
        
        return render_template('bill_detail.html',
                             bill=bill,
                             bill_log=bill_log)
    
    except Exception as e:
        app.logger.error(f"Bill detail error: {e}")
        flash(f"Error loading bill details: {e}", 'error')
        return redirect(url_for('bills_list'))


@app.route('/process-bills', methods=['POST'])
def process_bills():
    """Process new bills from Gmail"""
    try:
        # Authenticate Gmail
        if not processor.authenticate_gmail():
            return jsonify({
                'success': False,
                'message': 'Gmail authentication failed'
            })
        
        # Process bills
        days_back = int(request.form.get('days_back', 30))
        results = processor.process_latest_bills(days_back=days_back)
        
        message = f"Processed {results['processed']} new bills, {results['duplicates']} duplicates detected"
        if results['errors'] > 0:
            message += f", {results['errors']} errors"
        
        return jsonify({
            'success': True,
            'message': message,
            'results': results
        })
    
    except Exception as e:
        app.logger.error(f"Process bills error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error processing bills: {str(e)}'
        })


@app.route('/generate-pdf/<int:bill_id>', methods=['POST'])
def generate_pdf(bill_id):
    """Generate PDF for a specific bill"""
    try:
        bill = db.get_bill_by_id(bill_id)
        if not bill:
            return jsonify({'success': False, 'message': 'Bill not found'})
        
        # Get email content
        gmail = GmailParser()
        gmail.authenticate()
        email_content = gmail.get_email_content(bill['email_id'])
        
        if not email_content:
            return jsonify({'success': False, 'message': 'Could not retrieve email content'})
        
        # Generate PDF
        pdf_path = pdf_generator.generate_bill_pdf(bill, email_content['body'])
        
        if pdf_path:
            db.mark_pdf_generated(bill_id, pdf_path)
            return jsonify({
                'success': True,
                'message': 'PDF generated successfully',
                'pdf_path': pdf_path
            })
        else:
            return jsonify({'success': False, 'message': 'PDF generation failed'})
    
    except Exception as e:
        app.logger.error(f"Generate PDF error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/generate-venmo/<int:bill_id>', methods=['POST'])
def generate_venmo(bill_id):
    """Generate Venmo request link for a specific bill"""
    try:
        bill = db.get_bill_by_id(bill_id)
        if not bill:
            return jsonify({'success': False, 'message': 'Bill not found'})
        
        # Generate Venmo request
        auto_open = request.form.get('auto_open', 'false').lower() == 'true'
        result = venmo_generator.process_bill_venmo_request(bill, auto_open=auto_open)
        
        if result['success']:
            # Update database
            db.mark_venmo_sent(bill_id, result['venmo_url'])
            
            return jsonify({
                'success': True,
                'message': result['message'],
                'venmo_url': result['venmo_url'],
                'web_url': result['web_url'],
                'summary': result['summary']
            })
        else:
            return jsonify({'success': False, 'message': result['message']})
    
    except Exception as e:
        app.logger.error(f"Generate Venmo error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/send-email/<int:bill_id>', methods=['POST'])
def send_email(bill_id):
    """Send email notification for a specific bill"""
    try:
        bill = db.get_bill_by_id(bill_id)
        if not bill:
            return jsonify({'success': False, 'message': 'Bill not found'})
        
        if not bill['pdf_path'] or not Path(bill['pdf_path']).exists():
            return jsonify({'success': False, 'message': 'PDF not found - generate PDF first'})
        
        # Generate Venmo info for email
        venmo_result = venmo_generator.process_bill_venmo_request(bill, auto_open=False)
        if not venmo_result['success']:
            return jsonify({'success': False, 'message': 'Could not generate Venmo info'})
        
        # Send email
        success = email_notifier.send_bill_notification(bill, bill['pdf_path'], venmo_result)
        
        if success:
            db.mark_pdf_sent(bill_id)
            # Log the email send for tracking
            db.log_action(bill_id, f"Email sent to {settings.ROOMMATE_EMAIL}")
            return jsonify({
                'success': True,
                'message': 'Email sent successfully' if not settings.TEST_MODE else 'Email simulated (TEST_MODE)',
                'last_sent': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
            return jsonify({'success': False, 'message': 'Email sending failed'})
    
    except Exception as e:
        app.logger.error(f"Send email error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/test-email/<int:bill_id>', methods=['POST'])
def test_email(bill_id):
    """Test email functionality with debug information"""
    try:
        bill = db.get_bill_by_id(bill_id)
        if not bill:
            return jsonify({'success': False, 'message': 'Bill not found'})
        
        if not bill['pdf_path'] or not Path(bill['pdf_path']).exists():
            return jsonify({'success': False, 'message': 'PDF not found - generate PDF first'})
        
        # Generate Venmo info for email
        venmo_result = venmo_generator.process_bill_venmo_request(bill, auto_open=False)
        if not venmo_result['success']:
            return jsonify({'success': False, 'message': 'Could not generate Venmo info'})
        
        # Force email send with debug info
        app.logger.info(f"Testing email send to {settings.ROOMMATE_EMAIL}")
        success = email_notifier.send_bill_notification(bill, bill['pdf_path'], venmo_result)
        
        debug_info = {
            'recipient': settings.ROOMMATE_EMAIL,
            'sender': settings.MY_EMAIL,
            'pdf_exists': Path(bill['pdf_path']).exists(),
            'pdf_size': Path(bill['pdf_path']).stat().st_size if Path(bill['pdf_path']).exists() else 0,
            'test_mode': settings.TEST_MODE,
            'email_notifications_enabled': settings.ENABLE_EMAIL_NOTIFICATIONS
        }
        
        if success:
            db.log_action(bill_id, f"Test email sent to {settings.ROOMMATE_EMAIL}")
            return jsonify({
                'success': True,
                'message': 'Test email sent successfully',
                'debug_info': debug_info,
                'last_sent': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Test email failed',
                'debug_info': debug_info
            })
    
    except Exception as e:
        app.logger.error(f"Test email error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/download-pdf/<int:bill_id>')
def download_pdf(bill_id):
    """Download PDF for a specific bill"""
    try:
        bill = db.get_bill_by_id(bill_id)
        if not bill or not bill['pdf_path']:
            flash('PDF not found', 'error')
            return redirect(url_for('bill_detail', bill_id=bill_id))
        
        pdf_path = Path(bill['pdf_path'])
        if not pdf_path.exists():
            flash('PDF file not found on disk', 'error')
            return redirect(url_for('bill_detail', bill_id=bill_id))
        
        return send_file(pdf_path, as_attachment=True)
    
    except Exception as e:
        app.logger.error(f"Download PDF error: {e}")
        flash(f'Error downloading PDF: {e}', 'error')
        return redirect(url_for('bill_detail', bill_id=bill_id))


@app.route('/settings')
def settings_page():
    """Show application settings"""
    try:
        # Get current settings
        current_settings = {
            'gmail_user': settings.GMAIL_USER_EMAIL,
            'roommate_venmo': settings.ROOMMATE_VENMO,
            'roommate_phone': settings.ROOMMATE_PHONE,
            'my_venmo': settings.MY_VENMO_USERNAME,
            'my_phone': settings.MY_PHONE,
            'roommate_email': settings.ROOMMATE_EMAIL,
            'my_email': settings.MY_EMAIL,
            'roommate_split': f"{settings.ROOMMATE_SPLIT_RATIO:.1%}",
            'my_split': f"{settings.MY_SPLIT_RATIO:.1%}",
            'test_mode': settings.TEST_MODE,
            'auto_open': settings.ENABLE_AUTO_OPEN,
            'email_notifications': settings.ENABLE_EMAIL_NOTIFICATIONS,
            'pdf_generation': settings.ENABLE_PDF_GENERATION,
            'text_messaging': settings.ENABLE_TEXT_MESSAGING
        }
        
        # Get schedule status
        schedule_status = scheduler.get_schedule_status()
        
        return render_template('settings.html', 
                             settings=current_settings,
                             schedule_status=schedule_status)
    
    except Exception as e:
        app.logger.error(f"Settings page error: {e}")
        flash(f"Error loading settings: {e}", 'error')
        return redirect(url_for('dashboard'))


@app.route('/test-connection/<component>')
def test_connection(component):
    """Test connection for various components"""
    try:
        if component == 'gmail':
            gmail = GmailParser()
            gmail.authenticate()
            success = gmail.test_connection()
            message = "Gmail connection successful" if success else "Gmail connection failed"
        
        elif component == 'mail-app':
            success = email_notifier.test_mail_app_integration()
            message = "Mail app integration successful" if success else "Mail app integration failed"
        
        elif component == 'pdf':
            success = pdf_generator.test_pdf_generation()
            message = "PDF generation successful" if success else "PDF generation failed"
        
        elif component == 'venmo':
            success = venmo_generator.test_venmo_link_generation()
            message = "Venmo link generation successful" if success else "Venmo link generation failed"
        
        else:
            return jsonify({'success': False, 'message': 'Unknown component'})
        
        return jsonify({'success': success, 'message': message})
    
    except Exception as e:
        app.logger.error(f"Test connection error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/schedule/<action>', methods=['POST'])
def manage_schedule(action):
    """Manage automation schedule"""
    try:
        if action == 'install':
            success, message = scheduler.install_schedule()
            return jsonify({'success': success, 'message': message})
        
        elif action == 'uninstall':
            success, message = scheduler.uninstall_schedule()
            return jsonify({'success': success, 'message': message})
        
        elif action == 'test':
            success, output = scheduler.test_automation_script()
            return jsonify({
                'success': success, 
                'message': 'Automation test completed' if success else 'Automation test failed',
                'output': output
            })
        
        elif action == 'status':
            status = scheduler.get_schedule_status()
            return jsonify({'success': True, 'status': status})
        
        else:
            return jsonify({'success': False, 'message': 'Unknown action'})
    
    except Exception as e:
        app.logger.error(f"Schedule management error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/api/stats')
def api_stats():
    """API endpoint for dashboard statistics"""
    try:
        stats = db.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error="Page not found"), 404


@app.errorhandler(500)
def internal_error(error):
    app.logger.error('Server Error: %s', (error))
    return render_template('error.html', error="Internal server error"), 500


if __name__ == '__main__':
    print("🏠 PG&E Bill Split Automation - Web Interface")
    print("=" * 50)
    print(f"🔧 Test Mode: {'ENABLED' if settings.TEST_MODE else 'DISABLED'}")
    print(f"📧 Email Notifications: {'Enabled' if settings.ENABLE_EMAIL_NOTIFICATIONS else 'Disabled'}")
    print(f"💰 Split Ratio: {settings.ROOMMATE_SPLIT_RATIO:.1%} / {settings.MY_SPLIT_RATIO:.1%}")
    print("=" * 50)
    print("🌐 Starting web server...")
    print("📱 Open your browser to: http://localhost:5001")
    print("🔍 Press Ctrl+C to stop the server")
    print()
    
    # Ensure directories exist
    settings.ensure_directories()
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5001)