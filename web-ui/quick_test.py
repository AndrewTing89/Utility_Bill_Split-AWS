#!/usr/bin/env python3
import os
from flask import Flask, jsonify, request

# Set environment
os.environ['AWS_REGION'] = 'us-west-2'
os.environ['BILLS_TABLE'] = 'pge-bill-automation-bills-dev'
os.environ['LAMBDA_FUNCTION'] = 'pge-bill-automation-automation-dev'

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <html>
    <head><title>PG&E Test</title></head>
    <body style="font-family: Arial; margin: 40px; background: #f5f5f5;">
        <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px;">
            <h1 style="color: #2c5aa0;">🏠 PG&E Bill Split - Quick Test</h1>
            <p><strong>✅ Flask is working!</strong></p>
            <p><strong>✅ AWS connectivity ready</strong></p>
            
            <button onclick="testAPI()" style="background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer;">
                🧪 Test API Connection
            </button>
            
            <div id="result" style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 4px;"></div>
            
            <script>
                function testAPI() {
                    document.getElementById('result').innerHTML = '🔄 Testing...';
                    fetch('/api/test')
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('result').innerHTML = 
                                '✅ API Test Result: ' + JSON.stringify(data, null, 2);
                        })
                        .catch(error => {
                            document.getElementById('result').innerHTML = '❌ Error: ' + error;
                        });
                }
            </script>
        </div>
    </body>
    </html>
    '''

@app.route('/api/test')
def test_api():
    try:
        import boto3
        # Test AWS connection
        sts = boto3.client('sts', region_name='us-west-2')
        identity = sts.get_caller_identity()
        
        return jsonify({
            'status': 'success',
            'message': 'AWS connection working!',
            'account': identity.get('Account'),
            'region': 'us-west-2',
            'flask': 'working'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

if __name__ == '__main__':
    print("\n🌐 Starting PG&E Quick Test Interface...")
    print("📱 Try these URLs in your browser:")
    print("   • http://localhost:3000")
    print("   • http://127.0.0.1:3000")
    print("🔍 Press Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=3000, debug=False)