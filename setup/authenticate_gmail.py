#!/usr/bin/env python3
"""
Gmail API Authentication Setup

This script helps you authenticate with Gmail API and creates the token.json
file needed for AWS Lambda deployment.

Run this script once to set up Gmail authentication before deploying to AWS.
"""

import os
import sys
import json
from pathlib import Path

# Add the parent directory to path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    print("❌ Missing required packages. Please install dependencies:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def main():
    """Authenticate with Gmail API and save credentials"""
    print("🔐 PG&E Bill Split - Gmail API Authentication")
    print("=" * 50)
    print()
    
    # Check for credentials file
    creds_file = Path(__file__).parent.parent / "credentials.json"
    token_file = Path(__file__).parent.parent / "token.json"
    
    if not creds_file.exists():
        print("❌ credentials.json not found!")
        print()
        print("Please follow these steps:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing")
        print("3. Enable Gmail API")
        print("4. Create OAuth 2.0 credentials")
        print("5. Download credentials as 'credentials.json'")
        print("6. Place credentials.json in the root directory")
        print()
        return False
    
    print("✅ Found credentials.json")
    
    creds = None
    
    # Load existing token if it exists
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
        print("✅ Found existing token.json")
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired credentials...")
            try:
                creds.refresh(Request())
                print("✅ Credentials refreshed successfully")
            except Exception as e:
                print(f"❌ Failed to refresh credentials: {e}")
                creds = None
        
        if not creds:
            print("🌐 Starting OAuth flow...")
            print("Your browser will open for Gmail authentication.")
            print("Please sign in and authorize the application.")
            print()
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(creds_file), SCOPES
            )
            creds = flow.run_local_server(port=0)
            print("✅ Authentication successful!")
    
    # Save the credentials for the next run
    with open(token_file, 'w') as token:
        token.write(creds.to_json())
    print(f"✅ Saved credentials to {token_file}")
    
    # Test the credentials
    print("🧪 Testing Gmail API access...")
    try:
        service = build('gmail', 'v1', credentials=creds)
        
        # Test by getting user profile
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile.get('emailAddress')
        
        print(f"✅ Gmail API test successful!")
        print(f"📧 Authenticated as: {email_address}")
        
        # Test search for PG&E emails
        print("🔍 Testing PG&E email search...")
        results = service.users().messages().list(
            userId='me',
            q='from:DoNotReply@billpay.pge.com',
            maxResults=5
        ).execute()
        
        messages = results.get('messages', [])
        print(f"📬 Found {len(messages)} PG&E emails in your account")
        
        if len(messages) == 0:
            print("⚠️  No PG&E emails found. Make sure you have received bills from DoNotReply@billpay.pge.com")
        
    except HttpError as e:
        print(f"❌ Gmail API test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    print()
    print("🎉 Gmail authentication setup complete!")
    print()
    print("Next steps:")
    print("1. Update config/settings.json with your information")
    print("2. Run: cd deployment && ./deploy.sh dev")
    print("3. Test the deployment thoroughly before enabling production mode")
    print()
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)