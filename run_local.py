#!/usr/bin/env python3
"""
Run the PG&E Bill Split app locally
"""

import os
import sys
import subprocess

# Change to project directory
project_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_dir)

print("🚀 Starting PG&E Bill Split App")
print("📱 Access at: http://localhost:8080")
print("Press Ctrl+C to stop\n")

# Run the Flask app
subprocess.run([sys.executable, "web-ui/app_aws.py"])