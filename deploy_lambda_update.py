#!/usr/bin/env python3
"""
Script to update Lambda function with fixed Gmail authentication
"""

import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

def create_lambda_package():
    """Create updated Lambda deployment package"""
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        package_dir = Path(temp_dir) / "lambda_package"
        package_dir.mkdir()
        
        # Copy existing lambda_package contents (already has dependencies)
        existing_package = Path("/Users/ndting/Desktop/PGE Split AWS/lambda_package")
        if existing_package.exists():
            shutil.copytree(existing_package, package_dir, dirs_exist_ok=True)
        
        # Copy updated source files
        src_dir = Path("/Users/ndting/Desktop/PGE Split AWS/src")
        for src_file in src_dir.glob("*.py"):
            shutil.copy2(src_file, package_dir)
        
        # Create deployment ZIP
        zip_path = Path("/Users/ndting/Desktop/PGE Split AWS/lambda-deployment-updated.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(package_dir)
                    zipf.write(file_path, arcname)
        
        print(f"Created updated Lambda package: {zip_path}")
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
        print("Lambda deployment successful!")
        print(f"Function updated: {result.stdout}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Lambda deployment failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

if __name__ == "__main__":
    print("Creating updated Lambda package with fixed Gmail authentication...")
    
    # Create package
    zip_path = create_lambda_package()
    
    # Deploy to Lambda
    if deploy_to_lambda(zip_path):
        print("\n✅ Lambda function updated successfully!")
        print("The Gmail authentication issue should now be fixed.")
    else:
        print("\n❌ Lambda deployment failed.")