# App Runner IAM Role Setup

## Step 1: Create the IAM Role

1. **Go to IAM Console**: https://console.aws.amazon.com/iam/
2. **Click "Roles"** in the left sidebar
3. **Click "Create role"**
4. **Select trusted entity**:
   - Choose **"AWS service"**
   - Select **"App Runner"** from the service list
   - Click **"Next"**

## Step 2: Create Custom Policy

1. **Click "Create policy"** (opens new tab)
2. **Click "JSON"** tab
3. **Paste this policy**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Scan",
        "dynamodb:Query"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-west-2:*:table/pge-bill-automation-bills-dev",
        "arn:aws:dynamodb:us-west-2:*:table/pge-bill-automation-bills-dev/index/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:us-west-2:*:function:pge-bill-automation-automation-dev"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:us-west-2:*:secret:pge-bill-automation-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::pge-bill-automation-pdfs-dev/*"
    }
  ]
}
```

4. **Click "Next"**
5. **Name**: `PGEBillSplitAppRunnerPolicy`
6. **Click "Create policy"**

## Step 3: Attach Policy to Role

1. **Go back to role creation tab**
2. **Search for**: `PGEBillSplitAppRunnerPolicy`
3. **Check the box** next to your policy
4. **Click "Next"**
5. **Role name**: `PGEBillSplitAppRunnerRole`
6. **Click "Create role"**

## Step 4: Use in App Runner

1. **In App Runner console**, at the security step
2. **Instance role**: Select `PGEBillSplitAppRunnerRole`
3. **Access role**: Use default (App Runner will create this)

## Alternative: Quick Setup

If you're comfortable with CLI, run this command:

```bash
cd "/Users/ndting/Desktop/PGE Split AWS"
aws iam create-role --role-name PGEBillSplitAppRunnerRole --assume-role-policy-document file://apprunner-trust-policy.json --profile pge-automation
aws iam put-role-policy --role-name PGEBillSplitAppRunnerRole --policy-name PGEBillSplitPolicy --policy-document file://apprunner-iam-policy.json --profile pge-automation
```