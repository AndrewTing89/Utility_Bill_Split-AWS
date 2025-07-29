#!/usr/bin/env python3
"""
Fix charset_normalizer dependency issue in Lambda package
"""

import os
import shutil
import subprocess
from pathlib import Path

def fix_charset_dependency():
    """Fix the charset_normalizer dependency issue"""
    
    project_dir = Path("/Users/ndting/Desktop/PGE Split AWS")
    fixed_package_dir = project_dir / "lambda_package_charset_fixed"
    
    print("🔧 Fixing charset_normalizer dependency...")
    
    # Remove old directory if exists
    if fixed_package_dir.exists():
        shutil.rmtree(fixed_package_dir)
    
    fixed_package_dir.mkdir()
    
    # Copy from the no-PIL package as base
    base_package = project_dir / "lambda_package_no_pil"
    if base_package.exists():
        print("📦 Copying base package...")
        for item in base_package.iterdir():
            if item.is_dir():
                shutil.copytree(item, fixed_package_dir / item.name)
            else:
                shutil.copy2(item, fixed_package_dir)
    
    # Install/reinstall charset_normalizer and chardet
    print("📦 Installing charset_normalizer and chardet...")
    
    charset_packages = ["charset_normalizer", "chardet"]
    
    for package in charset_packages:
        cmd = ["pip", "install", "--target", str(fixed_package_dir), "--upgrade", package]
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing {package}: {e}")
            print(f"Stderr: {e.stderr}")
    
    # Check for charset_normalizer installation
    charset_path = fixed_package_dir / "charset_normalizer"
    if charset_path.exists():
        print(f"✅ charset_normalizer found at: {charset_path}")
        
        # Check for native extensions
        native_files = list(charset_path.glob("*.so"))
        if native_files:
            print(f"✅ Native extensions: {[f.name for f in native_files]}")
        else:
            print("ℹ️  No native extensions (pure Python)")
    else:
        print("❌ charset_normalizer not found")
        return False
    
    # Check for chardet installation
    chardet_path = fixed_package_dir / "chardet"
    if chardet_path.exists():
        print(f"✅ chardet found at: {chardet_path}")
    else:
        print("⚠️  chardet not found (not critical)")
    
    # Verify urllib3 is present (another common issue)
    urllib3_path = fixed_package_dir / "urllib3"
    if urllib3_path.exists():
        print(f"✅ urllib3 found at: {urllib3_path}")
    else:
        print("⚠️  urllib3 not found, installing...")
        cmd = ["pip", "install", "--target", str(fixed_package_dir), "urllib3"]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✅ urllib3 installed")
        except subprocess.CalledProcessError:
            print("❌ Failed to install urllib3")
    
    # Create deployment zip
    zip_file = project_dir / "lambda-deployment-charset-fixed.zip"
    if zip_file.exists():
        zip_file.unlink()
    
    print("📦 Creating deployment ZIP...")
    shutil.make_archive(str(zip_file.with_suffix('')), 'zip', str(fixed_package_dir))
    
    file_size = zip_file.stat().st_size / (1024 * 1024)  # MB
    print(f"✅ Fixed Lambda package created: {zip_file}")
    print(f"📏 Package size: {file_size:.1f} MB")
    
    return True

if __name__ == "__main__":
    fix_charset_dependency()