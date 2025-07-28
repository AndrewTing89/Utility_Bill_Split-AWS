#!/bin/bash

# PG&E Bill Split Automation - Credentials Setup for AWS Lambda
#
# This script helps set up Gmail API credentials for AWS Lambda deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 PG&E Bill Split Automation - Credentials Setup${NC}"
echo -e "${BLUE}===================================================${NC}"
echo ""

# Check if local credentials exist
LOCAL_CREDS="../credentials.json"
LOCAL_TOKEN="../token.json"

if [ ! -f "$LOCAL_CREDS" ]; then
    echo -e "${RED}❌ Gmail credentials not found at: $LOCAL_CREDS${NC}"
    echo -e "${YELLOW}💡 Please ensure you have set up Gmail API credentials first.${NC}"
    echo -e "   Refer to the local setup documentation."
    exit 1
fi

echo -e "${GREEN}✅ Found local Gmail credentials${NC}"

# Check if token exists (user has authenticated locally)
if [ ! -f "$LOCAL_TOKEN" ]; then
    echo -e "${RED}❌ Gmail token not found at: $LOCAL_TOKEN${NC}"
    echo -e "${YELLOW}💡 Please authenticate locally first by running the local app.${NC}"
    echo -e "   This generates the token.json file needed for AWS."
    exit 1
fi

echo -e "${GREEN}✅ Found Gmail authentication token${NC}"
echo ""

# Process token for Lambda
echo -e "${YELLOW}📝 Processing credentials for Lambda...${NC}"

# Read the token file and create Lambda environment variable format
TOKEN_CONTENT=$(cat "$LOCAL_TOKEN")
CREDS_CONTENT=$(cat "$LOCAL_CREDS")

# Create environment variables file
ENV_FILE="lambda-env-vars.json"
cat > "$ENV_FILE" << EOF
{
  "Variables": {
    "GMAIL_CREDENTIALS": $(echo "$TOKEN_CONTENT" | jq -c .),
    "GMAIL_CLIENT_CONFIG": $(echo "$CREDS_CONTENT" | jq -c .)
  }
}
EOF

echo -e "${GREEN}✅ Created Lambda environment variables: $ENV_FILE${NC}"
echo ""

# Instructions for deployment
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo ""
echo -e "1. The Gmail credentials have been prepared for Lambda deployment"
echo -e "2. The credentials are saved in: ${BLUE}$ENV_FILE${NC}"
echo ""
echo -e "${YELLOW}⚠️  Security Note:${NC}"
echo -e "   • The $ENV_FILE contains sensitive credentials"
echo -e "   • Do NOT commit this file to version control"
echo -e "   • Consider using AWS Secrets Manager for production"
echo ""
echo -e "${YELLOW}🚀 To deploy with credentials:${NC}"
echo -e "   ${BLUE}./deploy.sh dev${NC}"
echo ""
echo -e "${GREEN}✨ Credentials setup completed!${NC}"

# Add to .gitignore if it exists
if [ -f "../.gitignore" ]; then
    if ! grep -q "lambda-env-vars.json" "../.gitignore"; then
        echo "lambda-env-vars.json" >> "../.gitignore"
        echo -e "${GREEN}✅ Added lambda-env-vars.json to .gitignore${NC}"
    fi
fi