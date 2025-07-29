#!/usr/bin/env python3
"""
Simple SNS SMS setup - Manual verification approach
"""

import boto3
import json
import sys

def setup_sns_simple():
    """Set up SNS for SMS with manual steps"""
    
    print("=== AWS SNS SMS Setup Guide ===")
    print()
    print("AWS SNS SMS requires manual setup through the console for SMS in sandbox mode.")
    print()
    print("Steps to enable SMS for Venmo notifications:")
    print()
    print("1. Go to AWS Console > SNS > Text messaging (SMS)")
    print("   https://us-west-2.console.aws.amazon.com/sns/v3/home?region=us-west-2#/mobile/text-messaging")
    print()
    print("2. Click 'Add phone number' in the Sandbox destination phone numbers section")
    print()
    print("3. Add your phone number: +19298884132")
    print()
    print("4. Enter the verification code sent to your phone")
    print()
    print("5. Once verified, we can send SMS to your number")
    print()
    
    # Create IAM policy for Lambda
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
    
    print("\n✅ IAM policy created: lambda-sns-policy.json")
    print()
    print("After verifying your phone number in the console, run this command to add SNS permissions:")
    print()
    print("AWS_PROFILE=pge-automation aws iam put-role-policy \\")
    print("  --role-name pge-bill-automation-lambda-role-dev \\")
    print("  --policy-name SNSPublishPolicy \\")
    print("  --policy-document file://lambda-sns-policy.json")
    print()
    
    # Create test SMS function
    print("Once setup is complete, you can test with this code:")
    print()
    test_code = '''import boto3

sns_client = boto3.client('sns', region_name='us-west-2')

response = sns_client.publish(
    PhoneNumber='+19298884132',
    Message='🎉 PG&E Bill SMS notifications are working!',
    MessageAttributes={
        'AWS.SNS.SMS.SMSType': {
            'DataType': 'String',
            'StringValue': 'Transactional'
        }
    }
)
print(f"SMS sent! Message ID: {response['MessageId']}")'''
    
    with open('test_sms.py', 'w') as f:
        f.write(test_code)
    
    print("✅ Test script created: test_sms.py")

if __name__ == '__main__':
    setup_sns_simple()