#!/usr/bin/env python3
"""
Simple test interface for PG&E automation
"""

import os
import json
import boto3
from flask import Flask, jsonify, render_template_string

# Set environment
os.environ['AWS_REGION'] = 'us-west-2'
os.environ['BILLS_TABLE'] = 'pge-bill-automation-bills-dev'
os.environ['LAMBDA_FUNCTION'] = 'pge-bill-automation-automation-dev'

app = Flask(__name__)

# AWS clients
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
lambda_client = boto3.client('lambda', region_name='us-west-2')

# Simple HTML template
SIMPLE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>PG&E Bill Split - Test Interface</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; color: #2c5aa0; }
        .btn { background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #0056b3; }
        .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 4px; margin: 10px 0; }
        .error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 4px; margin: 10px 0; }
        .info { background: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; padding: 15px; border-radius: 4px; margin: 10px 0; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat-card { background: #f8f9fa; padding: 20px; border-radius: 4px; text-align: center; }
        .stat-number { font-size: 24px; font-weight: bold; color: #007bff; }
        .bills-list { margin-top: 20px; }
        .bill-item { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 4px; border-left: 4px solid #007bff; }
        #result { margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 PG&E Bill Split Automation</h1>
            <p>AWS Test Interface</p>
        </div>
        
        <div class="info">
            <strong>Status:</strong> Connected to AWS<br>
            <strong>Bills Table:</strong> {{ bills_table }}<br>
            <strong>Lambda Function:</strong> {{ lambda_function }}<br>
            <strong>Total Bills:</strong> {{ total_bills }}
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{{ total_bills }}</div>
                <div>Total Bills</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${{ "%.2f"|format(total_amount) }}</div>
                <div>Total Amount</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${{ "%.2f"|format(roommate_total) }}</div>
                <div>Roommate Total</div>
            </div>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <button class="btn" onclick="processBills()">🔄 Process New Bills</button>
            <button class="btn" onclick="testLambda()">⚡ Test Lambda Function</button>
            <button class="btn" onclick="refreshPage()">📊 Refresh Data</button>
        </div>
        
        <div id="result"></div>
        
        {% if bills %}
        <div class="bills-list">
            <h3>Recent Bills</h3>
            {% for bill in bills %}
            <div class="bill-item">
                <strong>Amount:</strong> ${{ "%.2f"|format(bill.amount) }} 
                <strong>Due:</strong> {{ bill.due_date }}
                <strong>Roommate Owes:</strong> ${{ "%.2f"|format(bill.roommate_portion) }}
                <strong>Status:</strong> {{ bill.status }}
                <br>
                <button class="btn" onclick="createVenmoRequest('{{ bill.id }}', {{ bill.roommate_portion }})">💰 Create Venmo Request</button>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>

    <script>
        function showResult(message, type = 'info') {
            const result = document.getElementById('result');
            result.innerHTML = `<div class="${type}">${message}</div>`;
        }
        
        function processBills() {
            showResult('🔄 Processing bills from Gmail...', 'info');
            fetch('/api/process-bills', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({test_mode: true}) })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showResult(`✅ ${data.message}<br>Result: ${JSON.stringify(data.result)}`, 'success');
                        setTimeout(() => location.reload(), 2000);
                    } else {
                        showResult(`❌ Error: ${data.error}`, 'error');
                    }
                })
                .catch(error => showResult(`❌ Error: ${error}`, 'error'));
        }
        
        function testLambda() {
            showResult('⚡ Testing Lambda function...', 'info');
            fetch('/api/test-lambda', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showResult(`✅ Lambda test successful!<br>${data.message}`, 'success');
                    } else {
                        showResult(`❌ Lambda test failed: ${data.error}`, 'error');
                    }
                })
                .catch(error => showResult(`❌ Error: ${error}`, 'error'));
        }
        
        function createVenmoRequest(billId, amount) {
            showResult(`💰 Creating Venmo request for $${amount.toFixed(2)}...`, 'info');
            fetch('/api/create-venmo-request', { 
                method: 'POST', 
                headers: {'Content-Type': 'application/json'}, 
                body: JSON.stringify({bill_id: billId}) 
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showResult(`✅ ${data.message}<br>Venmo URL: ${data.venmo_url}`, 'success');
                    } else {
                        showResult(`❌ Error: ${data.error}`, 'error');
                    }
                })
                .catch(error => showResult(`❌ Error: ${error}`, 'error'));
        }
        
        function refreshPage() {
            location.reload();
        }
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    """Simple dashboard"""
    try:
        # Get bills from DynamoDB
        table = dynamodb.Table('pge-bill-automation-bills-dev')
        response = table.scan()
        bills = response.get('Items', [])
        
        # Calculate stats
        total_bills = len(bills)
        total_amount = sum(float(bill.get('amount', 0)) for bill in bills)
        roommate_total = sum(float(bill.get('roommate_portion', 0)) for bill in bills)
        
        # Format bills for display
        formatted_bills = []
        for bill in bills:
            formatted_bills.append({
                'id': bill.get('bill_id', ''),
                'amount': float(bill.get('amount', 0)),
                'due_date': bill.get('due_date', ''),
                'roommate_portion': float(bill.get('roommate_portion', 0)),
                'status': bill.get('status', 'processed')
            })
        
        return render_template_string(SIMPLE_TEMPLATE, 
                                    bills_table='pge-bill-automation-bills-dev',
                                    lambda_function='pge-bill-automation-automation-dev',
                                    total_bills=total_bills,
                                    total_amount=total_amount,
                                    roommate_total=roommate_total,
                                    bills=formatted_bills[:5])
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/api/process-bills', methods=['POST'])
def process_bills():
    """Trigger Lambda to process bills"""
    try:
        response = lambda_client.invoke(
            FunctionName='pge-bill-automation-automation-dev',
            InvocationType='RequestResponse',
            Payload=json.dumps({'test_mode': True, 'manual_trigger': True})
        )
        
        result = json.loads(response['Payload'].read())
        if response['StatusCode'] == 200:
            body = json.loads(result.get('body', '{}'))
            return jsonify({
                'success': True,
                'message': 'Bills processed successfully',
                'result': body.get('result', {})
            })
        else:
            return jsonify({'success': False, 'error': 'Lambda function failed'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/test-lambda', methods=['POST'])
def test_lambda():
    """Test Lambda function"""
    try:
        response = lambda_client.invoke(
            FunctionName='pge-bill-automation-automation-dev',
            InvocationType='RequestResponse',
            Payload=json.dumps({'test_mode': True})
        )
        
        if response['StatusCode'] == 200:
            return jsonify({'success': True, 'message': 'Lambda function is working!'})
        else:
            return jsonify({'success': False, 'error': f'Status code: {response["StatusCode"]}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/create-venmo-request', methods=['POST'])
def create_venmo_request():
    """Create Venmo request"""
    try:
        data = request.get_json()
        bill_id = data.get('bill_id')
        
        # Get bill from DynamoDB
        table = dynamodb.Table('pge-bill-automation-bills-dev')
        response = table.get_item(Key={'bill_id': bill_id})
        
        if 'Item' not in response:
            return jsonify({'success': False, 'error': 'Bill not found'})
        
        bill = response['Item']
        roommate_portion = float(bill.get('roommate_portion', 0))
        
        # Generate Venmo URL
        venmo_url = f"venmo://paycharge?txn=charge&recipients=UshiLo&amount={roommate_portion:.2f}&note=PG%26E%20bill%20split"
        
        return jsonify({
            'success': True,
            'message': 'TEST MODE: Venmo request created (not sent)',
            'venmo_url': venmo_url,
            'amount': roommate_portion
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/health')
def health():
    """Health check"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print("🌐 Starting Simple PG&E Test Interface...")
    print("📱 Open your browser to: http://localhost:8080")
    print("🔍 Press Ctrl+C to stop")
    print()
    app.run(host='127.0.0.1', port=8080, debug=False)