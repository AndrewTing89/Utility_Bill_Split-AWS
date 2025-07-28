#!/usr/bin/env python3
"""
Basic tests for PG&E Bill Split Automation

Run with: python -m pytest tests/
"""

import unittest
import json
import os
from pathlib import Path

class TestConfiguration(unittest.TestCase):
    """Test configuration and setup"""
    
    def test_settings_file_exists(self):
        """Test that settings file exists"""
        settings_file = Path(__file__).parent.parent / "config" / "settings.json"
        self.assertTrue(settings_file.exists(), "settings.json should exist")
    
    def test_settings_valid_json(self):
        """Test that settings file is valid JSON"""
        settings_file = Path(__file__).parent.parent / "config" / "settings.json"
        with open(settings_file, 'r') as f:
            settings = json.load(f)
        
        # Check required fields
        required_fields = [
            'gmail_user', 'roommate_email', 'my_email',
            'roommate_venmo', 'my_venmo', 'my_phone',
            'roommate_split_ratio', 'my_split_ratio', 'test_mode'
        ]
        
        for field in required_fields:
            self.assertIn(field, settings, f"Required field '{field}' missing")
    
    def test_split_ratios_sum_to_one(self):
        """Test that split ratios sum to approximately 1.0"""
        settings_file = Path(__file__).parent.parent / "config" / "settings.json"
        with open(settings_file, 'r') as f:
            settings = json.load(f)
        
        total = settings['roommate_split_ratio'] + settings['my_split_ratio']
        self.assertAlmostEqual(total, 1.0, places=6, 
                              msg="Split ratios should sum to 1.0")

class TestRequirements(unittest.TestCase):
    """Test requirements and dependencies"""
    
    def test_requirements_file_exists(self):
        """Test that requirements.txt exists"""
        req_file = Path(__file__).parent.parent / "requirements.txt"
        self.assertTrue(req_file.exists(), "requirements.txt should exist")
    
    def test_requirements_has_key_packages(self):
        """Test that requirements includes key packages"""
        req_file = Path(__file__).parent.parent / "requirements.txt"
        with open(req_file, 'r') as f:
            content = f.read()
        
        key_packages = ['boto3', 'google-api-python-client', 'reportlab']
        for package in key_packages:
            self.assertIn(package, content, f"Package '{package}' should be in requirements")

class TestDeploymentFiles(unittest.TestCase):
    """Test deployment files and structure"""
    
    def test_lambda_handler_exists(self):
        """Test that lambda handler exists"""
        handler_file = Path(__file__).parent.parent / "src" / "lambda_handler.py"
        self.assertTrue(handler_file.exists(), "lambda_handler.py should exist")
    
    def test_cloudformation_template_exists(self):
        """Test that CloudFormation template exists"""
        cf_file = Path(__file__).parent.parent / "cloudformation" / "pge-automation-stack.yaml"
        self.assertTrue(cf_file.exists(), "CloudFormation template should exist")
    
    def test_deploy_script_executable(self):
        """Test that deploy script is executable"""
        deploy_script = Path(__file__).parent.parent / "deployment" / "deploy.sh"
        self.assertTrue(deploy_script.exists(), "deploy.sh should exist")
        self.assertTrue(os.access(deploy_script, os.X_OK), "deploy.sh should be executable")

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)