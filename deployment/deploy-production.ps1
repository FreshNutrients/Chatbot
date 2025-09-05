# PowerShell version of the production deployment script
# Production deployment script for FreshNutrients AI Chat API

param(
    [string]$ResourceGroup = "freshnutrients-rg",
    [string]$Location = "East US",
    [string]$ContainerAppEnv = "freshnutrients-env",
    [string]$ContainerApp = "freshnutrients-api",
    [string]$SqlServer = "freshnutrients-sql",
    [string]$SqlDatabase = "FreshNutrientsDB",
    [string]$VnetName = "freshnutrients-vnet",
    [string]$SubnetName = "container-apps-subnet",
    [string]$SqlSubnetName = "sql-subnet"
)

Write-Host "🚀 Deploying FreshNutrients AI Chat API to Azure Container Apps" -ForegroundColor Green

try {
    # 1. Create Resource Group
    Write-Host "📦 Creating resource group..." -ForegroundColor Blue
    az group create --name $ResourceGroup --location $Location

    # 2. Create Virtual Network
    Write-Host "🌐 Creating virtual network..." -ForegroundColor Blue
    az network vnet create `
        --resource-group $ResourceGroup `
        --name $VnetName `
        --address-prefix "10.0.0.0/16" `
        --subnet-name $SubnetName `
        --subnet-prefix "10.0.1.0/24"

    # 3. Create SQL subnet
    Write-Host "🗄️ Creating SQL subnet..." -ForegroundColor Blue
    az network vnet subnet create `
        --resource-group $ResourceGroup `
        --vnet-name $VnetName `
        --name $SqlSubnetName `
        --address-prefix "10.0.2.0/24"

    # 4. Get subscription ID
    $subscriptionId = az account show --query id -o tsv

    # 5. Create Container Apps Environment
    Write-Host "🏗️ Creating Container Apps environment..." -ForegroundColor Blue
    az containerapp env create `
        --name $ContainerAppEnv `
        --resource-group $ResourceGroup `
        --location $Location `
        --infrastructure-subnet-resource-id "/subscriptions/$subscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.Network/virtualNetworks/$VnetName/subnets/$SubnetName"

    # 6. Create SQL Server
    Write-Host "🗄️ Creating SQL Server..." -ForegroundColor Blue
    az sql server create `
        --name $SqlServer `
        --resource-group $ResourceGroup `
        --location $Location `
        --admin-user "sqladmin" `
        --admin-password "YourSecurePassword123!" `
        --enable-public-network false

    # 7. Create SQL Database
    Write-Host "📊 Creating SQL Database..." -ForegroundColor Blue
    az sql db create `
        --resource-group $ResourceGroup `
        --server $SqlServer `
        --name $SqlDatabase `
        --service-objective Basic

    # 8. Create Private Endpoint
    Write-Host "🔒 Creating SQL Server private endpoint..." -ForegroundColor Blue
    az network private-endpoint create `
        --resource-group $ResourceGroup `
        --name "$SqlServer-private-endpoint" `
        --vnet-name $VnetName `
        --subnet $SqlSubnetName `
        --private-connection-resource-id "/subscriptions/$subscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.Sql/servers/$SqlServer" `
        --group-ids sqlServer `
        --connection-name "$SqlServer-connection"

    # 9. Configure Private DNS
    Write-Host "🌐 Configuring private DNS..." -ForegroundColor Blue
    az network private-dns zone create `
        --resource-group $ResourceGroup `
        --name "privatelink.database.windows.net"

    az network private-dns link vnet create `
        --resource-group $ResourceGroup `
        --zone-name "privatelink.database.windows.net" `
        --name "$VnetName-link" `
        --virtual-network $VnetName `
        --registration-enabled false

    # 10. Generate API key (use a secure production key)
    $apiKey = "prod-fresh-nutrients-$(Get-Random -Minimum 1000 -Maximum 9999)-api-key"

    # 11. Deploy Container App
    Write-Host "🚀 Deploying Container App..." -ForegroundColor Blue
    az containerapp create `
        --name $ContainerApp `
        --resource-group $ResourceGroup `
        --environment $ContainerAppEnv `
        --image "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest" `
        --target-port 8000 `
        --ingress external `
        --min-replicas 1 `
        --max-replicas 10 `
        --cpu 1.0 `
        --memory "2.0Gi" `
        --env-vars `
            ENVIRONMENT=production `
            ENABLE_API_AUTH=true `
            ENABLE_RATE_LIMITING=true `
            ENABLE_HTTPS_REDIRECT=true `
            AZURE_SQL_SERVER="$SqlServer.privatelink.database.windows.net" `
            AZURE_SQL_DATABASE=$SqlDatabase `
        --secrets `
            api-secret-key=$apiKey `
            azure-sql-username="sqladmin" `
            azure-sql-password="YourSecurePassword123!" `
        --secret-env-vars `
            API_SECRET_KEY=api-secret-key `
            AZURE_SQL_USERNAME=azure-sql-username `
            AZURE_SQL_PASSWORD=azure-sql-password

    # Get the app URL
    $defaultDomain = az containerapp env show --name $ContainerAppEnv --resource-group $ResourceGroup --query properties.defaultDomain -o tsv
    
    Write-Host "✅ Deployment complete!" -ForegroundColor Green
    Write-Host "🌐 Your API is available at: https://$ContainerApp.$defaultDomain" -ForegroundColor Yellow
    Write-Host "🔑 API Key: $apiKey" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "💡 Next steps:" -ForegroundColor Cyan
    Write-Host "1. Build and push your Docker image to Azure Container Registry" -ForegroundColor White
    Write-Host "2. Update the container app with your image" -ForegroundColor White
    Write-Host "3. Configure your database schema" -ForegroundColor White
    Write-Host "4. Test the private endpoint connectivity" -ForegroundColor White

} catch {
    Write-Host "❌ Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
