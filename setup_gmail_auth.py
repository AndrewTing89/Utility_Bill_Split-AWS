#!/usr/bin/env python3
"""
Gmail API Authentication Setup for AWS Lambda

This script:
1. Authenticates with Gmail API using OAuth2
2. Generates refresh token for long-term access
3. Stores credentials in AWS Secrets Manager
4. Tests Gmail API access
"""

import os
import json
import boto3
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scope - read-only access to Gmail
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# AWS Configuration
AWS_REGION = 'us-west-2'
SECRET_NAME = 'pge-bill-automation-secrets-dev'

def authenticate_gmail():
    """Authenticate with Gmail API and get refresh token"""
    print("🔐 Starting Gmail API authentication...")
    
    creds = None
    
    # Check if token file exists
    if os.path.exists('token.json'):
        print("📄 Found existing token.json, loading credentials...")
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no valid credentials available, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            print("🌐 Starting OAuth2 flow...")
            print("⚠️  This will open a browser window for authentication")
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        print("💾 Saving credentials to token.json...")
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds

def test_gmail_access(creds):
    """Test Gmail API access"""
    print("🧪 Testing Gmail API access...")
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        
        # Test: Get user profile
        profile = service.users().getProfile(userId='me').execute()
        print(f"✅ Gmail API working! Email: {profile['emailAddress']}")
        
        # Test: Search for PG&E emails
        print("🔍 Searching for recent PG&E emails...")
        results = service.users().messages().list(
            userId='me',
            q='from:pge.com OR from:pge-mail.com subject:"electric bill" OR subject:"statement"',
            maxResults=5
        ).execute()
        
        messages = results.get('messages', [])
        print(f"📧 Found {len(messages)} potential PG&E emails")
        
        return True
        
    except Exception as e:
        print(f"❌ Gmail API test failed: {e}")
        return False

def create_secrets_payload(creds, settings):
    """Create the secrets payload for AWS Secrets Manager"""
    return {
        # Gmail OAuth2 credentials
        "gmail_client_id": json.loads(open('credentials.json').read())['installed']['client_id'],
        "gmail_client_secret": json.loads(open('credentials.json').read())['installed']['client_secret'],
        "gmail_refresh_token": creds.refresh_token,
        "gmail_user": settings['gmail_user'],
        
        # User settings
        "my_email": settings['my_email'],
        "roommate_email": settings['roommate_email'],
        "my_phone": settings['my_phone'],
        "my_venmo": settings['my_venmo'],
        "roommate_venmo": settings['roommate_venmo'],
        
        # Feature flags
        "test_mode": True,  # Start in test mode
        "email_notifications": True,
        "pdf_generation": True,
        "text_messaging": True,
        "auto_open": False,
        
        # Split configuration
        "roommate_split": "33%",
        "my_split": "67%"
    }

def store_in_secrets_manager(secrets_payload):
    """Store credentials in AWS Secrets Manager"""
    print(f"🔒 Storing credentials in AWS Secrets Manager ({SECRET_NAME})...")
    
    try:
        secrets_client = boto3.client('secretsmanager', region_name=AWS_REGION)
        
        # Try to update existing secret first
        try:
            response = secrets_client.update_secret(
                SecretId=SECRET_NAME,
                SecretString=json.dumps(secrets_payload)
            )
            print(f"✅ Updated existing secret: {response['ARN']}")
            
        except secrets_client.exceptions.ResourceNotFoundException:
            # Create new secret if it doesn't exist
            response = secrets_client.create_secret(
                Name=SECRET_NAME,
                Description='PG&E Bill Split Automation - Gmail and user settings',
                SecretString=json.dumps(secrets_payload)
            )
            print(f"✅ Created new secret: {response['ARN']}")
            
        return response['ARN']
        
    except Exception as e:
        print(f"❌ Failed to store secrets: {e}")
        return None

def main():
    """Main setup process"""
    print("🚀 PG&E Bill Split - Gmail API Setup")
    print("=" * 50)
    
    # Step 1: Authenticate with Gmail
    creds = authenticate_gmail()
    if not creds:
        print("❌ Failed to authenticate with Gmail")
        return
    
    # Step 2: Test Gmail access
    if not test_gmail_access(creds):
        print("❌ Gmail API test failed")
        return
    
    # Step 3: Get user settings
    print("\n⚙️  Using default user settings:")
    
    settings = {
        'gmail_user': 'andrewhting@gmail.com',
        'my_email': 'andrewhting@gmail.com',
        'roommate_email': 'andrewhting@gmail.com',  # Start with your email for testing
        'my_phone': '+19298884132',
        'my_venmo': 'andrewhting',
        'roommate_venmo': 'UshiLo'
    }
    
    for key, value in settings.items():
        print(f"  {key}: {value}")
    
    # Step 4: Create secrets payload
    secrets_payload = create_secrets_payload(creds, settings)
    
    # Step 5: Store in AWS Secrets Manager
    secret_arn = store_in_secrets_manager(secrets_payload)
    if not secret_arn:
        return
    
    # Step 6: Update Lambda environment variables
    print("\n🔧 Updating Lambda function environment variables...")
    try:
        lambda_client = boto3.client('lambda', region_name=AWS_REGION)
        
        response = lambda_client.update_function_configuration(
            FunctionName='pge-bill-automation-automation-dev',
            Environment={
                'Variables': {
                    'SECRETS_ARN': secret_arn,
                    'BILLS_TABLE': 'pge-bill-automation-bills-dev',
                    'AWS_REGION': AWS_REGION
                }
            }
        )
        print("✅ Lambda environment variables updated")
        
    except Exception as e:
        print(f"⚠️  Could not update Lambda environment: {e}")
        print(f"📝 Please manually set SECRETS_ARN to: {secret_arn}")
    
    print("\n🎉 Gmail API setup complete!")
    print("=" * 50)
    print("✅ Gmail API authenticated")
    print("✅ Credentials stored in AWS Secrets Manager")
    print("✅ Lambda function configured")
    print("\n🧪 Next steps:")
    print("1. Test the 'Process New Bills' button in your web dashboard")
    print("2. Check the Lambda logs for any issues")
    print("3. Verify bills are being found and processed")

if __name__ == '__main__':
    main()