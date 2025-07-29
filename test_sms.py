import boto3

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
print(f"SMS sent! Message ID: {response['MessageId']}")