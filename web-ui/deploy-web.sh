#!/bin/bash

# Deploy Web UI to AWS App Runner
# This script builds and deploys the Flask web interface

set -e

# Configuration
PROJECT_NAME="pge-bill-automation"
ENVIRONMENT="dev"
AWS_REGION="us-west-2"
AWS_PROFILE="pge-automation"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🌐 PG&E Bill Split Web UI - AWS Deployment${NC}"
echo -e "${BLUE}=============================================${NC}"
echo ""

# Get stack outputs for environment variables
echo -e "${YELLOW}📊 Getting infrastructure information...${NC}"

BILLS_TABLE=$(aws --profile ${AWS_PROFILE} cloudformation describe-stacks \
    --stack-name "${PROJECT_NAME}-${ENVIRONMENT}" \
    --region "${AWS_REGION}" \
    --query 'Stacks[0].Outputs[?OutputKey==`BillsTableName`].OutputValue' \
    --output text)

LAMBDA_FUNCTION=$(aws --profile ${AWS_PROFILE} cloudformation describe-stacks \
    --stack-name "${PROJECT_NAME}-${ENVIRONMENT}" \
    --region "${AWS_REGION}" \
    --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunctionArn`].OutputValue' \
    --output text | cut -d':' -f7)

SECRETS_ARN=$(aws --profile ${AWS_PROFILE} cloudformation describe-stacks \
    --stack-name "${PROJECT_NAME}-${ENVIRONMENT}" \
    --region "${AWS_REGION}" \
    --query 'Stacks[0].Outputs[?OutputKey==`SecretsArn`].OutputValue' \
    --output text 2>/dev/null || echo "")

echo -e "Bills Table: ${BILLS_TABLE}"
echo -e "Lambda Function: ${LAMBDA_FUNCTION}"
echo -e "Secrets ARN: ${SECRETS_ARN}"
echo ""

# Create environment file for local testing
echo -e "${YELLOW}🔧 Creating environment configuration...${NC}"

cat > .env << EOF
# AWS Configuration
AWS_REGION=${AWS_REGION}
BILLS_TABLE=${BILLS_TABLE}
LAMBDA_FUNCTION=${LAMBDA_FUNCTION}
SECRETS_ARN=${SECRETS_ARN}

# Flask Configuration
FLASK_ENV=production
PORT=8080
SECRET_KEY=prod-secret-key-$(date +%s)
EOF

echo -e "${GREEN}✅ Environment configuration created${NC}"
echo ""

echo -e "${YELLOW}🧪 Testing web app locally...${NC}"
echo -e "You can now test the web app locally by running:"
echo -e "  ${BLUE}cd web-ui${NC}"
echo -e "  ${BLUE}pip install -r requirements.txt${NC}"
echo -e "  ${BLUE}source .env && python app_aws.py${NC}"
echo ""

echo -e "${YELLOW}📋 Manual App Runner Setup Steps:${NC}"
echo -e "1. Go to AWS App Runner Console: https://console.aws.amazon.com/apprunner/"
echo -e "2. Click 'Create service'"
echo -e "3. Choose 'Source code repository'"
echo -e "4. Connect to GitHub and select your repository"
echo -e "5. Branch: main"
echo -e "6. Use these configuration settings:"
echo ""
echo -e "   ${BLUE}Build settings:${NC}"
echo -e "     Build command: pip install -r web-ui/requirements.txt"
echo -e "     Start command: cd web-ui && python app_aws.py"
echo ""
echo -e "   ${BLUE}Environment variables:${NC}"
echo -e "     PORT=8080"
echo -e "     FLASK_ENV=production"
echo -e "     AWS_REGION=${AWS_REGION}"
echo -e "     BILLS_TABLE=${BILLS_TABLE}"
echo -e "     LAMBDA_FUNCTION=${LAMBDA_FUNCTION}"
echo -e "     SECRETS_ARN=${SECRETS_ARN}"
echo ""
echo -e "   ${BLUE}Instance configuration:${NC}"
echo -e "     CPU: 0.25 vCPU"
echo -e "     Memory: 0.5 GB"
echo ""
echo -e "7. Create and deploy!"
echo ""

echo -e "${GREEN}✨ Web UI deployment guide created!${NC}"
echo -e "💰 Expected cost: ~$5-10/month for App Runner"