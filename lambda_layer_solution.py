#!/usr/bin/env python3
"""
Use AWS Lambda Layer for PIL instead of bundling it in deployment package
"""

import json
import boto3
from pathlib import Path

def create_lambda_layer_deployment():
    """Create Lambda deployment without PIL and document layer solution"""
    
    project_dir = Path("/Users/ndting/Desktop/PGE Split AWS")
    
    print("🔧 Creating Lambda deployment using Layer approach for PIL...")
    print()
    
    # Known PIL Lambda layers for us-west-2
    pil_layers = {
        "us-west-2": {
            "pillow_layer": "arn:aws:lambda:us-west-2:770693421928:layer:Klayers-p312-pillow:1",
            "description": "Community-maintained Pillow layer for Python 3.12"
        }
    }
    
    print("📋 Available PIL Lambda Layers:")
    for region, layer_info in pil_layers.items():
        print(f"  Region: {region}")
        print(f"  Layer ARN: {layer_info['pillow_layer']}")
        print(f"  Description: {layer_info['description']}")
        print()
    
    # Create deployment configuration
    deployment_config = {
        "lambda_function": {
            "function_name": "pge-bill-automation-automation-dev",
            "runtime": "python3.12",
            "layers": [
                pil_layers["us-west-2"]["pillow_layer"]
            ],
            "deployment_package": "lambda-deployment-no-pil.zip"
        },
        "notes": [
            "PIL/Pillow is provided by Lambda Layer instead of deployment package",
            "This reduces deployment package size significantly",
            "Layer is maintained by the community and kept up to date",
            "If layer doesn't work, we can create our own or use Docker approach"
        ]
    }
    
    config_file = project_dir / "lambda_layer_config.json"
    with open(config_file, 'w') as f:
        json.dump(deployment_config, f, indent=2)
    
    print(f"💾 Configuration saved to: {config_file}")
    print()
    
    # Instructions for deployment
    instructions = """
🚀 Deployment Instructions:

1. Update Lambda function to use the PIL layer:
   aws lambda update-function-configuration \\
     --function-name pge-bill-automation-automation-dev \\
     --layers arn:aws:lambda:us-west-2:770693421928:layer:Klayers-p312-pillow:1

2. Deploy the lightweight package (without PIL):
   Create deployment package excluding PIL dependencies

3. Test PDF generation:
   The Lambda will now have access to PIL through the layer

🔍 Alternative Solutions if layer doesn't work:
- Create custom layer with PIL compiled for Lambda
- Use AWS SAM to build deployment package
- Use Docker with Lambda base image
"""
    
    print(instructions)
    
    # Create deployment package without PIL
    print("📦 Creating deployment package without PIL...")
    
    # Use existing lambda_package but exclude PIL-related files
    import shutil
    
    source_dir = project_dir / "lambda_package"
    target_dir = project_dir / "lambda_package_no_pil"
    
    if target_dir.exists():
        shutil.rmtree(target_dir)
    
    target_dir.mkdir()
    
    # Copy everything except PIL and Pillow
    exclude_patterns = ['pillow', 'PIL', 'Pillow', '_imaging']
    
    if source_dir.exists():
        for item in source_dir.iterdir():
            # Skip PIL-related items
            if any(pattern.lower() in item.name.lower() for pattern in exclude_patterns):
                print(f"  ⏭️  Skipping {item.name} (PIL-related)")
                continue
            
            if item.is_dir():
                shutil.copytree(item, target_dir / item.name)
            else:
                shutil.copy2(item, target_dir)
    
    # Create ZIP
    zip_file = project_dir / "lambda-deployment-no-pil.zip"
    if zip_file.exists():
        zip_file.unlink()
    
    shutil.make_archive(str(zip_file.with_suffix('')), 'zip', str(target_dir))
    
    file_size = zip_file.stat().st_size / (1024 * 1024)  # MB
    print(f"✅ Lightweight package created: {zip_file}")
    print(f"📏 Package size: {file_size:.1f} MB (much smaller without PIL)")
    
    return True

def update_lambda_with_layer():
    """Update Lambda function to use PIL layer"""
    
    try:
        lambda_client = boto3.client('lambda', region_name='us-west-2')
        
        function_name = 'pge-bill-automation-automation-dev'
        pil_layer_arn = 'arn:aws:lambda:us-west-2:770693421928:layer:Klayers-p312-pillow:1'
        
        print(f"🔄 Updating Lambda function {function_name}...")
        
        # Get current configuration
        response = lambda_client.get_function_configuration(FunctionName=function_name)
        current_layers = response.get('Layers', [])
        
        # Add PIL layer if not already present
        layer_arns = [layer['Arn'] for layer in current_layers]
        if pil_layer_arn not in layer_arns:
            layer_arns.append(pil_layer_arn)
            
            # Update function configuration
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Layers=layer_arns
            )
            
            print(f"✅ Added PIL layer to Lambda function")
        else:
            print(f"ℹ️  PIL layer already attached to function")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating Lambda: {e}")
        print("💡 You can update manually using AWS CLI or Console")
        return False

if __name__ == "__main__":
    create_lambda_layer_deployment()
    print("\n" + "="*60 + "\n")
    update_lambda_with_layer()