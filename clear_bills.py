#!/usr/bin/env python3
"""
Clear all bills from DynamoDB for testing
"""

import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
table = dynamodb.Table('pge-bill-automation-bills-dev')

response = table.scan()
items = response.get('Items', [])

while 'LastEvaluatedKey' in response:
    response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
    items.extend(response.get('Items', []))

if not items:
    print("No bills to clear.")
else:
    print(f"Clearing {len(items)} bills...")
    
    for item in items:
        table.delete_item(Key={'bill_id': item['bill_id']})
        print(f"✓ Deleted: {item['bill_id']}")
    
    print(f"\n✅ Cleared {len(items)} bills from database!")