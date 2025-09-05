#!/bin/bash
# Production deployment script for FreshNutrients AI Chat API
# This script sets up the complete Azure infrastructure with proper networking

set -e

# Configuration
RESOURCE_GROUP="freshnutrients-rg"
LOCATION="East US"
CONTAINER_APP_ENV="freshnutrients-env"
CONTAINER_APP="freshnutrients-api"
SQL_SERVER="freshnutrients-sql"
SQL_DATABASE="FreshNutrientsDB"
VNET_NAME="freshnutrients-vnet"
SUBNET_NAME="container-apps-subnet"
SQL_SUBNET_NAME="sql-subnet"

echo "🚀 Deploying FreshNutrients AI Chat API to Azure Container Apps"

# 1. Create Resource Group
echo "📦 Creating resource group..."
az group create \
  --name $RESOURCE_GROUP \
  --location "$LOCATION"

# 2. Create Virtual Network for Private Networking
echo "🌐 Creating virtual network..."
az network vnet create \
  --resource-group $RESOURCE_GROUP \
  --name $VNET_NAME \
  --address-prefix 10.0.0.0/16 \
  --subnet-name $SUBNET_NAME \
  --subnet-prefix 10.0.1.0/24

# 3. Create SQL subnet for private endpoint
echo "🗄️ Creating SQL subnet..."
az network vnet subnet create \
  --resource-group $RESOURCE_GROUP \
  --vnet-name $VNET_NAME \
  --name $SQL_SUBNET_NAME \
  --address-prefix 10.0.2.0/24

# 4. Create Container Apps Environment with VNET integration
echo "🏗️ Creating Container Apps environment..."
az containerapp env create \
  --name $CONTAINER_APP_ENV \
  --resource-group $RESOURCE_GROUP \
  --location "$LOCATION" \
  --infrastructure-subnet-resource-id "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Network/virtualNetworks/$VNET_NAME/subnets/$SUBNET_NAME"

# 5. Create Azure SQL Server (if not exists)
echo "🗄️ Creating SQL Server..."
az sql server create \
  --name $SQL_SERVER \
  --resource-group $RESOURCE_GROUP \
  --location "$LOCATION" \
  --admin-user "sqladmin" \
  --admin-password "YourSecurePassword123!" \
  --enable-public-network false

# 6. Create SQL Database
echo "📊 Creating SQL Database..."
az sql db create \
  --resource-group $RESOURCE_GROUP \
  --server $SQL_SERVER \
  --name $SQL_DATABASE \
  --service-objective Basic

# 7. Create Private Endpoint for SQL Server
echo "🔒 Creating SQL Server private endpoint..."
az network private-endpoint create \
  --resource-group $RESOURCE_GROUP \
  --name "$SQL_SERVER-private-endpoint" \
  --vnet-name $VNET_NAME \
  --subnet $SQL_SUBNET_NAME \
  --private-connection-resource-id "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Sql/servers/$SQL_SERVER" \
  --group-ids sqlServer \
  --connection-name "$SQL_SERVER-connection"

# 8. Configure Private DNS Zone
echo "🌐 Configuring private DNS..."
az network private-dns zone create \
  --resource-group $RESOURCE_GROUP \
  --name "privatelink.database.windows.net"

az network private-dns link vnet create \
  --resource-group $RESOURCE_GROUP \
  --zone-name "privatelink.database.windows.net" \
  --name "$VNET_NAME-link" \
  --virtual-network $VNET_NAME \
  --registration-enabled false

# 9. Build and push container image
echo "🐳 Building and pushing container image..."
# Assuming you have Azure Container Registry set up
ACR_NAME="freshnutrientsacr"
az acr build --registry $ACR_NAME --image freshnutrients/chatbot-api:latest .

# 10. Deploy Container App
echo "🚀 Deploying Container App..."
az containerapp create \
  --name $CONTAINER_APP \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_APP_ENV \
  --image "$ACR_NAME.azurecr.io/freshnutrients/chatbot-api:latest" \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 10 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --env-vars \
    ENVIRONMENT=production \
    ENABLE_API_AUTH=true \
    ENABLE_RATE_LIMITING=true \
    ENABLE_HTTPS_REDIRECT=true \
    AZURE_SQL_SERVER="$SQL_SERVER.privatelink.database.windows.net" \
    AZURE_SQL_DATABASE=$SQL_DATABASE \
  --secrets \
    api-secret-key="$(openssl rand -base64 32)" \
    azure-sql-username="sqladmin" \
    azure-sql-password="YourSecurePassword123!" \
  --secret-env-vars \
    API_SECRET_KEY=api-secret-key \
    AZURE_SQL_USERNAME=azure-sql-username \
    AZURE_SQL_PASSWORD=azure-sql-password

echo "✅ Deployment complete!"
echo "🌐 Your API is available at: https://$CONTAINER_APP.$(az containerapp env show --name $CONTAINER_APP_ENV --resource-group $RESOURCE_GROUP --query properties.defaultDomain -o tsv)"
echo "🔑 API Key: $(az containerapp show --name $CONTAINER_APP --resource-group $RESOURCE_GROUP --query 'properties.configuration.secrets[?name==`api-secret-key`].value' -o tsv)"
