#!/bin/bash

# Azure Container Apps deployment script for FreshNutrients ChatBot
# This script deploys the chatbot API to Azure Container Apps

set -e

# Configuration
RESOURCE_GROUP="freshnutrients-rg"
LOCATION="eastus"
CONTAINER_APP_ENV="freshnutrients-env"
CONTAINER_APP_NAME="freshnutrients-chatbot"
ACR_NAME="freshnutrientsacr"
IMAGE_NAME="freshnutrients-chatbot"
IMAGE_TAG="latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Azure Container Apps deployment...${NC}"

# Check if Azure CLI is logged in
if ! az account show > /dev/null 2>&1; then
    echo -e "${RED}❌ Not logged in to Azure CLI. Please run 'az login' first.${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Current Azure account:${NC}"
az account show --query "{subscriptionId:id, name:name, user:user.name}" -o table

# Create resource group if it doesn't exist
echo -e "${YELLOW}🔧 Creating resource group...${NC}"
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION \
    --output table

# Create Azure Container Registry if it doesn't exist
echo -e "${YELLOW}🔧 Creating Azure Container Registry...${NC}"
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Basic \
    --admin-enabled true \
    --output table

# Build and push Docker image
echo -e "${YELLOW}🔨 Building and pushing Docker image...${NC}"
az acr build \
    --registry $ACR_NAME \
    --image $IMAGE_NAME:$IMAGE_TAG \
    --file Dockerfile \
    .

# Create Container Apps environment
echo -e "${YELLOW}🔧 Creating Container Apps environment...${NC}"
az containerapp env create \
    --name $CONTAINER_APP_ENV \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --output table

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query loginServer -o tsv)

# Deploy container app
echo -e "${YELLOW}🚀 Deploying container app...${NC}"
az containerapp create \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment $CONTAINER_APP_ENV \
    --image "$ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG" \
    --target-port 8000 \
    --ingress 'external' \
    --registry-server $ACR_LOGIN_SERVER \
    --min-replicas 1 \
    --max-replicas 5 \
    --cpu 0.5 \
    --memory 1.0Gi \
    --env-vars \
        ENVIRONMENT=production \
        API_HOST=0.0.0.0 \
        API_PORT=8000 \
        ENABLE_API_AUTH=true \
        ENABLE_RATE_LIMITING=true \
        ENABLE_HTTPS_REDIRECT=true \
    --output table

# Get the app URL
APP_URL=$(az containerapp show \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    -o tsv)

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🌐 Your app is available at: https://$APP_URL${NC}"
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "1. Configure secrets using Azure Key Vault"
echo "2. Set up custom domain and SSL certificate"
echo "3. Configure monitoring and alerts"
echo "4. Test the API endpoints"

# Test health endpoint
echo -e "${YELLOW}🔍 Testing health endpoint...${NC}"
if curl -f "https://$APP_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Health check passed!${NC}"
else
    echo -e "${RED}❌ Health check failed. Check logs with:${NC}"
    echo "az containerapp logs show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP"
fi
