#!/usr/bin/env python3
"""
Start the Flask server for testing
"""

import os
import sys

# Set environment variables
os.environ['AWS_REGION'] = 'us-west-2'
os.environ['BILLS_TABLE'] = 'pge-bill-automation-bills-dev'
os.environ['LAMBDA_FUNCTION'] = 'pge-bill-automation-automation-dev'
os.environ['FLASK_ENV'] = 'development'
os.environ['PORT'] = '8080'

print("🌐 Starting PG&E Bill Split Web UI...")
print("📱 Open your browser to: http://localhost:8080")
print("🔍 Press Ctrl+C to stop the server")
print()

try:
    from app_aws import app
    app.run(host='127.0.0.1', port=8080, debug=False, use_reloader=False)
except KeyboardInterrupt:
    print("\n👋 Server stopped")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)