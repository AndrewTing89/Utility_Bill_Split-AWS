#!/usr/bin/env python3
"""
Fix PIL/Pillow by downloading Linux wheels manually
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
import urllib.request
import zipfile

def download_linux_wheels():
    """Download Linux-compatible wheels for PIL and ReportLab"""
    
    project_dir = Path("/Users/ndting/Desktop/PGE Split AWS")
    wheels_dir = project_dir / "linux_wheels"
    package_dir = project_dir / "lambda_package_manual"
    
    print("🔄 Downloading Linux-compatible wheels...")
    
    # Clean up directories
    if wheels_dir.exists():
        shutil.rmtree(wheels_dir)
    if package_dir.exists():
        shutil.rmtree(package_dir)
    
    wheels_dir.mkdir()
    package_dir.mkdir()
    
    # URLs for Linux x86_64 wheels (Python 3.12)
    wheels_to_download = [
        "https://files.pythonhosted.org/packages/b8/7d/90b4e2b2e2c3a2caaa0bfadf8b0095a654a623c39a1aa87dd14b2b6e7e68/pillow-11.3.0-cp312-cp312-linux_x86_64.whl",
        "https://files.pythonhosted.org/packages/72/6f/8c82a38cd9b5e6e6816b1ad2dd80ffcf0bb901ad8b4c0ecc5bfc10e5abefc/reportlab-4.4.3-cp312-cp312-linux_x86_64.whl"
    ]
    
    downloaded_wheels = []
    
    for wheel_url in wheels_to_download:
        wheel_name = wheel_url.split('/')[-1]
        wheel_path = wheels_dir / wheel_name
        
        print(f"📥 Downloading {wheel_name}...")
        
        try:
            urllib.request.urlretrieve(wheel_url, wheel_path)
            downloaded_wheels.append(wheel_path)
            print(f"✅ Downloaded {wheel_name}")
        except Exception as e:
            print(f"❌ Failed to download {wheel_name}: {e}")
            continue
    
    # Extract wheels
    print("📦 Extracting wheels...")
    
    for wheel_path in downloaded_wheels:
        print(f"🔄 Extracting {wheel_path.name}...")
        
        with zipfile.ZipFile(wheel_path, 'r') as zip_ref:
            # Extract to temp directory first
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_ref.extractall(temp_dir)
                
                # Copy only the actual package directories (not .dist-info)
                temp_path = Path(temp_dir)
                for item in temp_path.iterdir():
                    if item.is_dir() and not item.name.endswith('.dist-info'):
                        dest_path = package_dir / item.name
                        if dest_path.exists():
                            shutil.rmtree(dest_path)
                        shutil.copytree(item, dest_path)
                        print(f"  ✅ Extracted {item.name}")
    
    # Install pure Python dependencies normally
    print("📦 Installing pure Python dependencies...")
    
    pure_python_deps = [
        "boto3", "botocore", "s3transfer", "jmespath",
        "google-api-python-client", "google-auth", "google-auth-oauthlib", 
        "google-auth-httplib2", "google-api-core", "googleapis-common-protos",
        "requests", "urllib3", "certifi", "charset-normalizer", "idna",
        "python-dotenv", "email-validator", "simplejson",
        "uritemplate", "httplib2", "pyasn1", "pyasn1-modules", 
        "cachetools", "rsa", "oauthlib", "requests-oauthlib",
        "python-dateutil", "six", "protobuf", "proto-plus", 
        "pyparsing", "dnspython"
    ]
    
    for dep in pure_python_deps:
        cmd = ["pip", "install", "--target", str(package_dir), "--no-deps", dep]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Warning: Could not install {dep}")
    
    # Copy our application files
    app_files = [
        "lambda_handler.py",
        "gmail_processor_aws.py", 
        "pdf_generator_aws.py",
        "bill_automation.py"
    ]
    
    for file in app_files:
        # Try different source locations
        for src_dir in [project_dir / "src", project_dir, project_dir / "lambda_package"]:
            src = src_dir / file
            if src.exists():
                shutil.copy2(src, package_dir)
                print(f"✅ Copied {file}")
                break
        else:
            print(f"⚠️  Could not find {file}")
    
    # Verify PIL installation
    pil_path = package_dir / "PIL"
    if pil_path.exists():
        print(f"✅ PIL module found at: {pil_path}")
        
        # Check for _imaging.so
        imaging_files = list(pil_path.glob("*imaging*.so"))
        if imaging_files:
            print(f"✅ Native imaging libraries: {[f.name for f in imaging_files]}")
        else:
            print("⚠️  No native imaging libraries found")
            
        # List PIL contents
        pil_contents = [f.name for f in pil_path.iterdir()]
        print(f"📋 PIL contents: {pil_contents[:10]}...")  # First 10 items
        
    else:
        print("❌ PIL module not found")
        return False
    
    # Create deployment zip
    zip_file = project_dir / "lambda-deployment-manual-pil.zip"
    if zip_file.exists():
        zip_file.unlink()
    
    print("📦 Creating deployment ZIP...")
    shutil.make_archive(str(zip_file.with_suffix('')), 'zip', str(package_dir))
    
    file_size = zip_file.stat().st_size / (1024 * 1024)  # MB
    print(f"✅ Lambda package created: {zip_file}")
    print(f"📏 Package size: {file_size:.1f} MB")
    print(f"📁 Package directory: {package_dir}")
    
    if file_size > 50:
        print("⚠️  Warning: Package is large. Consider using Lambda layers for dependencies.")
    
    # Clean up wheels directory
    shutil.rmtree(wheels_dir)
    
    return True

if __name__ == "__main__":
    download_linux_wheels()