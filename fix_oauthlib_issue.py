#!/usr/bin/env python3
"""
Fix oauthlib version compatibility issue
"""

import os
import shutil
import subprocess
from pathlib import Path

def fix_oauthlib_compatibility():
    """Fix oauthlib version compatibility issue"""
    
    project_dir = Path("/Users/ndting/Desktop/PGE Split AWS")
    final_package_dir = project_dir / "lambda_package_final"
    
    print("🔧 Fixing oauthlib compatibility issue...")
    
    # Remove old directory if exists
    if final_package_dir.exists():
        shutil.rmtree(final_package_dir)
    
    final_package_dir.mkdir()
    
    # Copy from the charset-fixed package as base
    base_package = project_dir / "lambda_package_charset_fixed"
    if base_package.exists():
        print("📦 Copying base package...")
        for item in base_package.iterdir():
            if item.is_dir():
                shutil.copytree(item, final_package_dir / item.name)
            else:
                shutil.copy2(item, final_package_dir)
    
    # Remove problematic oauth packages first
    oauth_dirs = ["oauthlib", "requests_oauthlib"]
    for oauth_dir in oauth_dirs:
        oauth_path = final_package_dir / oauth_dir
        if oauth_path.exists():
            print(f"🗑️  Removing {oauth_dir}")
            shutil.rmtree(oauth_path)
    
    # Remove related dist-info directories
    for item in final_package_dir.iterdir():
        if item.is_dir() and ("oauthlib" in item.name.lower() or "oauth" in item.name.lower()) and "dist-info" in item.name:
            print(f"🗑️  Removing {item.name}")
            shutil.rmtree(item)
    
    # Install compatible versions
    print("📦 Installing compatible OAuth packages...")
    
    # Install specific compatible versions
    oauth_packages = [
        "oauthlib==3.2.2",  # Known stable version
        "requests-oauthlib==1.3.1"  # Compatible with oauthlib 3.2.2
    ]
    
    for package in oauth_packages:
        cmd = ["pip", "install", "--target", str(final_package_dir), "--upgrade", package]
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing {package}: {e}")
            print(f"Stderr: {e.stderr}")
            return False
    
    # Verify installations
    oauthlib_path = final_package_dir / "oauthlib"
    requests_oauthlib_path = final_package_dir / "requests_oauthlib"
    
    if oauthlib_path.exists() and requests_oauthlib_path.exists():
        print("✅ OAuth packages installed successfully")
        
        # Check for SIGNATURE_HMAC in oauthlib
        rfc5849_path = oauthlib_path / "oauth1" / "rfc5849"
        if rfc5849_path.exists():
            print("✅ oauthlib.oauth1.rfc5849 module found")
            
            # Check __init__.py for SIGNATURE_HMAC
            init_file = rfc5849_path / "__init__.py"
            if init_file.exists():
                with open(init_file, 'r') as f:
                    content = f.read()
                    if "SIGNATURE_HMAC" in content:
                        print("✅ SIGNATURE_HMAC found in oauthlib")
                    else:
                        print("⚠️  SIGNATURE_HMAC not found - may still have issues")
            
        else:
            print("❌ oauthlib.oauth1.rfc5849 module not found")
            return False
    else:
        print("❌ OAuth packages not properly installed")
        return False
    
    # Create deployment zip
    zip_file = project_dir / "lambda-deployment-final.zip"
    if zip_file.exists():
        zip_file.unlink()
    
    print("📦 Creating final deployment ZIP...")
    shutil.make_archive(str(zip_file.with_suffix('')), 'zip', str(final_package_dir))
    
    file_size = zip_file.stat().st_size / (1024 * 1024)  # MB
    print(f"✅ Final Lambda package created: {zip_file}")
    print(f"📏 Package size: {file_size:.1f} MB")
    
    print("\n🎯 Summary of fixes applied:")
    print("  ✅ PIL/Pillow: Using Lambda Layer")
    print("  ✅ charset_normalizer: Fixed dependency")
    print("  ✅ oauthlib: Compatible versions installed")
    print("  ✅ requests-oauthlib: Compatible version installed")
    
    return True

if __name__ == "__main__":
    success = fix_oauthlib_compatibility()
    if success:
        print("\n🚀 Ready to deploy final Lambda package!")
    else:
        print("\n❌ Failed to fix oauthlib compatibility")