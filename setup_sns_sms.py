#!/usr/bin/env python3
"""
Setup AWS SNS for SMS notifications
"""

import boto3
import json
import sys

def setup_sns_sms():
    """Configure SNS for SMS notifications"""
    
    # Initialize SNS client
    sns_client = boto3.client('sns', region_name='us-west-2')
    
    print("=== AWS SNS SMS Setup ===")
    print()
    
    # Check SMS sandbox status
    try:
        response = sns_client.get_sms_sandbox_account_status()
        sandbox_status = response['IsInSandbox']
        
        if sandbox_status:
            print("⚠️  Your account is in SMS Sandbox mode")
            print("   - You can only send SMS to verified phone numbers")
            print("   - To send to any number, you need to request production access")
            print()
        else:
            print("✅ Your account has production SMS access")
            print()
    except Exception as e:
        print(f"❌ Error checking SMS sandbox status: {e}")
        return
    
    # Add phone number to sandbox (for testing)
    phone_number = '+19298884132'  # Your phone number
    
    if sandbox_status:
        print(f"Adding phone number to SMS sandbox: {phone_number}")
        try:
            response = sns_client.create_sms_sandbox_phone_number(
                PhoneNumber=phone_number,
                LanguageCode='en-US'
            )
            print(f"✅ Verification code sent to {phone_number}")
            print("   Check your phone for the verification code")
            
            # Get verification code from user
            verification_code = input("Enter the verification code: ")
            
            # Verify the phone number
            response = sns_client.verify_sms_sandbox_phone_number(
                PhoneNumber=phone_number,
                OneTimePassword=verification_code
            )
            print("✅ Phone number verified successfully!")
            
        except sns_client.exceptions.OptInRequired:
            print(f"✅ Phone number {phone_number} is already verified")
        except Exception as e:
            print(f"❌ Error adding phone number: {e}")
            return
    
    # Set SMS attributes for cost control
    print("\nSetting SMS attributes for cost control...")
    try:
        sns_client.set_sms_attributes(
            attributes={
                'MonthlySpendLimit': '5',  # $5 monthly limit
                'DefaultSMSType': 'Transactional',  # Reliable delivery
                'DefaultSenderID': 'PGEBill'  # Sender ID (not used in US)
            }
        )
        print("✅ SMS attributes configured")
    except Exception as e:
        print(f"❌ Error setting SMS attributes: {e}")
    
    # Create IAM policy for Lambda SNS access
    print("\nCreating IAM policy for Lambda SNS access...")
    
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "sns:Publish"
                ],
                "Resource": "*"
            }
        ]
    }
    
    with open('lambda-sns-policy.json', 'w') as f:
        json.dump(policy_document, f, indent=2)
    
    print("✅ Policy document created: lambda-sns-policy.json")
    print("\nNext steps:")
    print("1. Attach this policy to your Lambda role:")
    print("   aws iam put-role-policy --role-name pge-bill-automation-lambda-role-dev \\")
    print("     --policy-name SNSPublishPolicy \\")
    print("     --policy-document file://lambda-sns-policy.json")
    print()
    print("2. Update your code to enable SMS sending")
    print("3. Test with a manual trigger")
    
    # Test SMS sending
    print("\nWould you like to send a test SMS? (y/n): ", end='')
    if input().lower() == 'y':
        try:
            response = sns_client.publish(
                PhoneNumber=phone_number,
                Message='🎉 PG&E Bill SMS notifications are working! This is a test message.',
                MessageAttributes={
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'
                    }
                }
            )
            print(f"✅ Test SMS sent! Message ID: {response['MessageId']}")
        except Exception as e:
            print(f"❌ Error sending test SMS: {e}")

if __name__ == '__main__':
    setup_sns_sms()