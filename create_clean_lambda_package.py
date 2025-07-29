#!/usr/bin/env python3
"""
Create a clean Lambda deployment package from scratch
"""

import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

def create_clean_lambda_package():
    """Create a clean Lambda deployment package"""
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        package_dir = Path(temp_dir) / "lambda_package"
        package_dir.mkdir()
        
        print(f"Creating package in: {package_dir}")
        
        # Install requirements to the package directory
        requirements_file = Path("/Users/ndting/Desktop/PGE Split AWS/requirements.txt")
        if requirements_file.exists():
            print("Installing requirements...")
            subprocess.run([
                "pip", "install", "-r", str(requirements_file),
                "-t", str(package_dir),
                "--no-deps"  # Don't install dependencies automatically
            ], check=True)
            
            # Install core dependencies that we know we need
            core_packages = [
                "boto3==1.39.15",
                "botocore==1.39.15", 
                "google-auth==2.40.3",
                "google-auth-oauthlib==1.2.2",
                "google-api-python-client==2.177.0",
                "requests==2.32.4",
                "oauthlib==3.3.1",
                "urllib3==2.5.0"
            ]
            
            for package in core_packages:
                print(f"Installing {package}...")
                subprocess.run([
                    "pip", "install", package,
                    "-t", str(package_dir),
                    "--upgrade"
                ], check=True)
        
        # Copy source files
        src_dir = Path("/Users/ndting/Desktop/PGE Split AWS/src")
        for src_file in src_dir.glob("*.py"):
            print(f"Copying {src_file.name}...")
            shutil.copy2(src_file, package_dir)
        
        # Create deployment ZIP
        zip_path = Path("/Users/ndting/Desktop/PGE Split AWS/lambda-deployment-clean.zip")
        print(f"Creating ZIP: {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(package_dir)
                    zipf.write(file_path, arcname)
        
        print(f"✅ Created clean Lambda package: {zip_path}")
        return zip_path

def deploy_to_lambda(zip_path):
    """Deploy the package to Lambda"""
    try:
        cmd = [
            "aws", "lambda", "update-function-code",
            "--function-name", "pge-bill-automation-automation-dev",
            "--zip-file", f"fileb://{zip_path}",
            "--region", "us-west-2"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Lambda deployment successful!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Lambda deployment failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

if __name__ == "__main__":
    print("Creating clean Lambda deployment package...")
    
    # Create package
    zip_path = create_clean_lambda_package()
    
    # Deploy to Lambda
    if deploy_to_lambda(zip_path):
        print("\n🎉 Clean Lambda deployment completed successfully!")
    else:
        print("\n❌ Deployment failed.")