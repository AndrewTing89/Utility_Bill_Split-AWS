#!/usr/bin/env python3
"""
Quick test of the AWS web UI locally
"""

import os
import sys
import boto3

# Set environment variables
os.environ['AWS_REGION'] = 'us-west-2'
os.environ['BILLS_TABLE'] = 'pge-bill-automation-bills-dev'
os.environ['LAMBDA_FUNCTION'] = 'pge-bill-automation-automation-dev'
os.environ['FLASK_ENV'] = 'development'
os.environ['PORT'] = '8080'

print("🧪 Testing PG&E Web UI - Local Development")
print("=" * 50)

# Test AWS connectivity
try:
    print("📡 Testing AWS connectivity...")
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
    table = dynamodb.Table('pge-bill-automation-bills-dev')
    
    # Try to scan the table
    response = table.scan(Limit=1)
    print(f"✅ DynamoDB connection successful")
    print(f"📊 Found {response.get('Count', 0)} bills in database")
    
except Exception as e:
    print(f"❌ AWS connection failed: {e}")

# Test Lambda connectivity
try:
    print("⚡ Testing Lambda connectivity...")
    lambda_client = boto3.client('lambda', region_name='us-west-2')
    
    response = lambda_client.get_function(
        FunctionName='pge-bill-automation-automation-dev'
    )
    print(f"✅ Lambda function found: {response['Configuration']['FunctionName']}")
    
except Exception as e:
    print(f"❌ Lambda connection failed: {e}")

print("\n🌐 Starting Flask web server...")
print("📱 Open your browser to: http://localhost:8080")
print("🔍 Press Ctrl+C to stop the server")
print()

# Import and run the Flask app
try:
    from app_aws import app
    app.run(host='0.0.0.0', port=8080, debug=True)
except KeyboardInterrupt:
    print("\n👋 Server stopped by user")
except Exception as e:
    print(f"❌ Server error: {e}")
    sys.exit(1)