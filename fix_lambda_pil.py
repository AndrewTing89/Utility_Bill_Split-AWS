#!/usr/bin/env python3
"""
Fix PIL/Pillow in Lambda deployment package by installing Linux-compatible binaries
"""

import os
import shutil
import subprocess
from pathlib import Path

def create_lambda_package_with_pil():
    """Create clean Lambda package with Linux-compatible PIL"""
    
    # Paths
    project_dir = Path("/Users/ndting/Desktop/PGE Split AWS")
    old_package_dir = project_dir / "lambda_package"
    temp_dir = project_dir / "lambda_temp"
    new_package_dir = project_dir / "lambda_package_fixed"
    
    print("🔧 Creating Lambda package with Linux-compatible PIL...")
    
    # Remove old directories if they exist
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    if new_package_dir.exists():
        shutil.rmtree(new_package_dir)
    
    # Create temp directory for Linux pip install
    temp_dir.mkdir()
    
    # Install dependencies with Linux target
    print("📦 Installing dependencies for Linux x86_64...")
    
    # Create requirements.txt for the specific packages we need
    requirements = [
        "pillow==11.3.0",
        "reportlab==4.4.3", 
        "boto3",
        "google-api-python-client",
        "google-auth-oauthlib",
        "google-auth-httplib2",
        "requests",
        "python-dotenv",
        "email-validator",
        "simplejson"
    ]
    
    requirements_file = temp_dir / "requirements.txt"
    with open(requirements_file, 'w') as f:
        f.write('\n'.join(requirements))
    
    # Install with Linux platform target
    cmd = [
        "pip", "install", 
        "--target", str(temp_dir),
        "--platform", "linux_x86_64",
        "--only-binary=:all:",
        "--no-deps",
        "-r", str(requirements_file)
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Linux dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing Linux dependencies: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False
    
    # Install remaining dependencies normally (pure Python packages)
    pure_python_packages = [
        "google-api-core",
        "google-auth",
        "googleapis-common-protos",
        "uritemplate",
        "httplib2",
        "pyasn1",
        "pyasn1-modules",
        "cachetools",
        "rsa",
        "oauthlib",
        "requests-oauthlib",
        "charset-normalizer",
        "idna",
        "certifi",
        "urllib3",
        "python-dateutil",
        "six",
        "jmespath",
        "botocore",
        "s3transfer",
        "protobuf",
        "proto-plus",
        "pyparsing",
        "dnspython"
    ]
    
    for package in pure_python_packages:
        cmd = ["pip", "install", "--target", str(temp_dir), "--no-deps", package]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError:
            print(f"⚠️  Warning: Could not install {package}")
    
    # Create final package directory
    new_package_dir.mkdir()
    
    # Copy installed packages
    for item in temp_dir.iterdir():
        if item.is_dir() and not item.name.endswith('.dist-info'):
            shutil.copytree(item, new_package_dir / item.name)
        elif item.is_file() and item.suffix == '.py':
            shutil.copy2(item, new_package_dir)
    
    # Copy our application files
    app_files = [
        "lambda_handler.py",
        "gmail_processor_aws.py", 
        "pdf_generator_aws.py",
        "bill_automation.py"
    ]
    
    for file in app_files:
        src = project_dir / "src" / file
        if src.exists():
            shutil.copy2(src, new_package_dir)
        else:
            # Try in root directory
            src = project_dir / file
            if src.exists():
                shutil.copy2(src, new_package_dir)
    
    # Check if PIL is now properly installed
    pil_path = new_package_dir / "PIL"
    if pil_path.exists():
        print(f"✅ PIL module found at: {pil_path}")
        
        # Check for _imaging.so (the native extension)
        imaging_files = list(pil_path.glob("*imaging*"))
        if imaging_files:
            print(f"✅ Native imaging libraries: {[f.name for f in imaging_files]}")
        else:
            print("⚠️  No native imaging libraries found - PDF generation may fail")
    else:
        print("❌ PIL module not found in package")
        return False
    
    # Clean up temp directory
    shutil.rmtree(temp_dir)
    
    # Create deployment zip
    zip_file = project_dir / "lambda-deployment-pil-fixed.zip"
    if zip_file.exists():
        zip_file.unlink()
    
    print("📦 Creating deployment ZIP...")
    shutil.make_archive(str(zip_file.with_suffix('')), 'zip', str(new_package_dir))
    
    print(f"✅ Lambda package created: {zip_file}")
    print(f"📁 Package directory: {new_package_dir}")
    
    return True

if __name__ == "__main__":
    create_lambda_package_with_pil()