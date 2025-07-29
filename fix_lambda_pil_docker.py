#!/usr/bin/env python3
"""
Fix PIL/Pillow in Lambda deployment using Docker to create Linux-compatible package
"""

import os
import shutil
import subprocess
from pathlib import Path

def create_lambda_package_with_docker():
    """Create Lambda package using Docker for Linux compatibility"""
    
    project_dir = Path("/Users/ndting/Desktop/PGE Split AWS")
    package_dir = project_dir / "lambda_package_docker"
    
    print("🐳 Creating Lambda package with Docker for Linux compatibility...")
    
    # Remove old directory if it exists
    if package_dir.exists():
        shutil.rmtree(package_dir)
    
    package_dir.mkdir()
    
    # Create requirements.txt
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
    
    requirements_file = package_dir / "requirements.txt"
    with open(requirements_file, 'w') as f:
        f.write('\n'.join(requirements))
    
    # Create Dockerfile for building the package
    dockerfile_content = """FROM public.ecr.aws/lambda/python:3.12

# Copy requirements
COPY requirements.txt /tmp/

# Install dependencies to /tmp/lambda-package
RUN pip install -r /tmp/requirements.txt -t /tmp/lambda-package

# Copy application files would go here (we'll add them manually after)

# Create output directory
RUN mkdir -p /output

# Copy the installed packages to output
CMD cp -r /tmp/lambda-package/* /output/
"""
    
    dockerfile_path = package_dir / "Dockerfile"
    with open(dockerfile_path, 'w') as f:
        f.write(dockerfile_content)
    
    print("📦 Building Docker image...")
    
    # Build Docker image
    build_cmd = [
        "docker", "build", 
        "-t", "lambda-pil-builder",
        str(package_dir)
    ]
    
    try:
        result = subprocess.run(build_cmd, check=True, capture_output=True, text=True, cwd=str(package_dir))
        print("✅ Docker image built successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error building Docker image: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ Docker not found. Please install Docker Desktop first.")
        print("📋 Alternative: Use AWS Lambda Layer for PIL")
        return False
    
    # Run container to extract packages
    print("📦 Extracting packages from Docker container...")
    
    deps_dir = package_dir / "deps"
    deps_dir.mkdir(exist_ok=True)
    
    run_cmd = [
        "docker", "run",
        "--rm",
        "-v", f"{deps_dir}:/output",
        "lambda-pil-builder"
    ]
    
    try:
        subprocess.run(run_cmd, check=True, capture_output=True, text=True)
        print("✅ Dependencies extracted successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error extracting dependencies: {e}")
        return False
    
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
            shutil.copy2(src, deps_dir)
        else:
            # Try in root directory or lambda_package
            for possible_dir in [project_dir, project_dir / "lambda_package"]:
                src = possible_dir / file
                if src.exists():
                    shutil.copy2(src, deps_dir)
                    break
    
    # Check if PIL was installed correctly
    pil_path = deps_dir / "PIL"
    if pil_path.exists():
        print(f"✅ PIL module found at: {pil_path}")
        
        # Check for native libraries
        native_libs = list(pil_path.glob("*.so"))
        if native_libs:
            print(f"✅ Native libraries found: {[lib.name for lib in native_libs]}")
        else:
            print("⚠️  No .so files found in PIL directory")
            
        # Specifically check for _imaging
        imaging_path = pil_path / "_imaging.cpython-312-x86_64-linux-gnu.so"
        if imaging_path.exists():
            print("✅ _imaging native library found for Linux")
        else:
            print("⚠️  _imaging native library not found")
    else:
        print("❌ PIL module not found")
        return False
    
    # Create deployment zip
    zip_file = project_dir / "lambda-deployment-docker-pil.zip"
    if zip_file.exists():
        zip_file.unlink()
    
    print("📦 Creating deployment ZIP...")
    shutil.make_archive(str(zip_file.with_suffix('')), 'zip', str(deps_dir))
    
    print(f"✅ Lambda package created: {zip_file}")
    print(f"📁 Package directory: {deps_dir}")
    
    # Clean up Docker image
    cleanup_cmd = ["docker", "rmi", "lambda-pil-builder"]
    try:
        subprocess.run(cleanup_cmd, check=True, capture_output=True, text=True)
        print("🧹 Docker image cleaned up")
    except subprocess.CalledProcessError:
        print("⚠️  Could not clean up Docker image")
    
    return True

if __name__ == "__main__":
    success = create_lambda_package_with_docker()
    if not success:
        print("\n💡 Alternative solution: Use AWS Lambda Layer for PIL/Pillow")
        print("   Or try manual installation with manylinux wheels")