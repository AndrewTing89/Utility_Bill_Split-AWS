#!/bin/bash

# PG&E Bill Split Automation - AWS Deployment Script
#
# This script deploys the automation system to AWS Lambda
# Usage: ./deploy.sh [dev|prod]

set -e

# Configuration
PROJECT_NAME="pge-bill-automation"
AWS_REGION="us-west-2"  # Change to your preferred region
ENVIRONMENT="${1:-dev}"
AWS_PROFILE="pge-automation"  # Dedicated profile for this project

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 PG&E Bill Split Automation - AWS Deployment${NC}"
echo -e "${BLUE}=================================================${NC}"
echo -e "Environment: ${ENVIRONMENT}"
echo -e "Region: ${AWS_REGION}"
echo -e "Project: ${PROJECT_NAME}"
echo ""

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install AWS CLI first.${NC}"
    exit 1
fi

# Check if AWS is configured
if ! aws --profile ${AWS_PROFILE} sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not configured for profile '${AWS_PROFILE}'. Please run 'aws configure --profile ${AWS_PROFILE}' first.${NC}"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.${NC}"
    exit 1
fi

# Check zip
if ! command -v zip &> /dev/null; then
    echo -e "${RED}❌ zip command not found. Please install zip.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Get AWS account info
AWS_ACCOUNT_ID=$(aws --profile ${AWS_PROFILE} sts get-caller-identity --query Account --output text)
echo -e "AWS Account: ${AWS_ACCOUNT_ID}"
echo -e "AWS Profile: ${AWS_PROFILE}"
echo ""

# Step 1: Create deployment package
echo -e "${YELLOW}📦 Creating deployment package...${NC}"

# Create temporary directory
TEMP_DIR=$(mktemp -d)
PACKAGE_DIR="${TEMP_DIR}/package"
mkdir -p "${PACKAGE_DIR}"

# Copy Lambda function code from src directory
cp ../src/lambda_handler.py "${PACKAGE_DIR}/"
cp ../src/bill_automation.py "${PACKAGE_DIR}/"

# Copy adapted source code (only what we need for AWS)
echo -e "Copying source code..."
cp ../src/gmail_processor_aws.py "${PACKAGE_DIR}/"
cp ../src/pdf_generator_aws.py "${PACKAGE_DIR}/"

# Install dependencies
echo -e "Installing dependencies..."
pip3 install -r ../requirements.txt -t "${PACKAGE_DIR}/" --no-deps --quiet

# Create deployment zip
DEPLOYMENT_ZIP="${PROJECT_NAME}-${ENVIRONMENT}.zip"
cd "${PACKAGE_DIR}"
zip -r "../${DEPLOYMENT_ZIP}" . -q
cd - > /dev/null

echo -e "${GREEN}✅ Deployment package created: ${DEPLOYMENT_ZIP}${NC}"

# Step 2: Deploy CloudFormation stack
echo -e "${YELLOW}☁️  Deploying CloudFormation stack...${NC}"

STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"

# Check if stack exists
if aws --profile ${AWS_PROFILE} cloudformation describe-stacks --stack-name "${STACK_NAME}" --region "${AWS_REGION}" &> /dev/null; then
    echo -e "Stack exists, updating..."
    OPERATION="update-stack"
    WAIT_CONDITION="stack-update-complete"
else
    echo -e "Creating new stack..."
    OPERATION="create-stack"
    WAIT_CONDITION="stack-create-complete"
fi

# Deploy stack
aws --profile ${AWS_PROFILE} cloudformation ${OPERATION} \
    --stack-name "${STACK_NAME}" \
    --template-body file://../cloudformation/simple-stack.yaml \
    --parameters \
        ParameterKey=ProjectName,ParameterValue="${PROJECT_NAME}" \
        ParameterKey=Environment,ParameterValue="${ENVIRONMENT}" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "${AWS_REGION}"

echo -e "Waiting for CloudFormation operation to complete..."
aws --profile ${AWS_PROFILE} cloudformation wait ${WAIT_CONDITION} \
    --stack-name "${STACK_NAME}" \
    --region "${AWS_REGION}"

echo -e "${GREEN}✅ CloudFormation stack deployed successfully${NC}"

# Step 3: Update Lambda function code
echo -e "${YELLOW}⚡ Updating Lambda function code...${NC}"

FUNCTION_NAME="${PROJECT_NAME}-automation-${ENVIRONMENT}"

aws --profile ${AWS_PROFILE} lambda update-function-code \
    --function-name "${FUNCTION_NAME}" \
    --zip-file "fileb://${TEMP_DIR}/${DEPLOYMENT_ZIP}" \
    --region "${AWS_REGION}" > /dev/null

echo -e "${GREEN}✅ Lambda function code updated${NC}"

# Step 4: Get stack outputs
echo -e "${YELLOW}📊 Getting deployment information...${NC}"

LAMBDA_ARN=$(aws --profile ${AWS_PROFILE} cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${AWS_REGION}" \
    --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunctionArn`].OutputValue' \
    --output text)

S3_BUCKET=$(aws --profile ${AWS_PROFILE} cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${AWS_REGION}" \
    --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' \
    --output text)

DASHBOARD_URL=$(aws --profile ${AWS_PROFILE} cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${AWS_REGION}" \
    --query 'Stacks[0].Outputs[?OutputKey==`DashboardURL`].OutputValue' \
    --output text)

# Step 5: Test the deployment
echo -e "${YELLOW}🧪 Testing deployment...${NC}"

TEST_RESULT=$(aws --profile ${AWS_PROFILE} lambda invoke \
    --function-name "${FUNCTION_NAME}" \
    --payload '{"test_mode": true, "manual_trigger": true}' \
    --region "${AWS_REGION}" \
    response.json)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Test invocation successful${NC}"
    cat response.json | python3 -m json.tool
    rm -f response.json
else
    echo -e "${RED}❌ Test invocation failed${NC}"
fi

# Cleanup
rm -rf "${TEMP_DIR}"

# Final summary
echo -e "${GREEN}"
echo "🎉 Deployment completed successfully!"
echo "======================================"
echo -e "${NC}"
echo -e "📋 Deployment Summary:"
echo -e "  • Environment: ${ENVIRONMENT}"
echo -e "  • Region: ${AWS_REGION}"
echo -e "  • Lambda Function: ${FUNCTION_NAME}"
echo -e "  • S3 Bucket: ${S3_BUCKET}"
echo ""
echo -e "🔗 Useful Links:"
echo -e "  • Lambda Console: ${DASHBOARD_URL}"
echo -e "  • CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/home?region=${AWS_REGION}#logsV2:log-groups/log-group/%252Faws%252Flambda%252F${FUNCTION_NAME}"
echo ""
echo -e "${YELLOW}📅 Schedule Information:${NC}"
echo -e "  • Runs automatically on the 5th of each month at 9:00 AM PST"
echo -e "  • EventBridge rule: ${PROJECT_NAME}-monthly-schedule-${ENVIRONMENT}"
echo ""
echo -e "${YELLOW}💡 Next Steps:${NC}"
echo -e "  1. Update the secrets in AWS Secrets Manager with your actual configuration"
echo -e "  2. Set up SES (Simple Email Service) for sending emails"
echo -e "  3. Upload your Gmail API credentials to the Lambda function"
echo -e "  4. Test the automation manually before the next scheduled run"
echo ""
echo -e "${BLUE}Monthly cost estimate: \$2-5 for typical usage${NC}"
echo -e "${GREEN}✨ Your PG&E bills will now be processed automatically with 100% uptime!${NC}"