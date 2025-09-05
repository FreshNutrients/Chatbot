# Production Deployment Guide: Solving Azure SQL Firewall Issues

## 🎯 **The Problem & Solution**

**Problem:** Azure SQL firewall requires specific IP addresses, but production apps have dynamic IPs
**Solution:** Private endpoints + Azure Container Apps with VNET integration

## 🏗️ **Architecture Overview**

```
Internet → Azure Load Balancer → Container Apps (Private Network) → Private Endpoint → Azure SQL
```

**Benefits:**
- ✅ No firewall rules needed
- ✅ Encrypted private network traffic
- ✅ Auto-scaling containers
- ✅ Enterprise security
- ✅ No public SQL exposure

## 🚀 **Step-by-Step Deployment**

### **Phase 1: Prepare Local Environment**

1. **Install Azure CLI** (if not installed):
```powershell
# Download and install from: https://aka.ms/installazurecliwindows
az --version  # Verify installation
```

2. **Login to Azure**:
```powershell
az login
az account list --output table
az account set --subscription "Your-Subscription-ID"
```

3. **Verify Docker** (for image building):
```powershell
docker --version
```

### **Phase 2: Run Deployment Script**

```powershell
# Navigate to deployment folder
cd "c:\Users\Montg\Documents\Fresh nutrients\Chatbot\deployment"

# Run the deployment script
.\deploy-production.ps1 -ResourceGroup "freshnutrients-rg" -Location "East US"
```

### **Phase 3: Build and Deploy Your Application**

1. **Create Azure Container Registry** (for your custom image):
```powershell
az acr create --resource-group freshnutrients-rg --name freshnutrientsacr --sku Basic
az acr login --name freshnutrientsacr
```

2. **Build and push your image**:
```powershell
# Build the Docker image
docker build -t freshnutrientsacr.azurecr.io/chatbot-api:latest .

# Push to registry
docker push freshnutrientsacr.azurecr.io/chatbot-api:latest
```

3. **Update Container App with your image**:
```powershell
az containerapp update `
  --name freshnutrients-api `
  --resource-group freshnutrients-rg `
  --image freshnutrientsacr.azurecr.io/chatbot-api:latest
```

### **Phase 4: Configure Database**

1. **Connect via Private Endpoint**:
```powershell
# Your app will now connect to: freshnutrients-sql.privatelink.database.windows.net
# This resolves to a private IP (10.0.2.x) instead of public IP
```

2. **Set up database schema**:
```sql
-- Connect using Azure Data Studio or SQL Management Studio
-- Use private endpoint FQDN: freshnutrients-sql.privatelink.database.windows.net

CREATE TABLE conversations (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_message NVARCHAR(MAX) NOT NULL,
    bot_response NVARCHAR(MAX) NOT NULL,
    timestamp DATETIME2 DEFAULT GETUTCDATE(),
    session_id NVARCHAR(50)
);

CREATE TABLE products (
    id INT PRIMARY KEY IDENTITY(1,1),
    name NVARCHAR(255) NOT NULL,
    description NVARCHAR(MAX),
    price DECIMAL(10,2),
    nutritional_info NVARCHAR(MAX)
);
```

## 🔒 **Security Configuration**

### **Environment Variables (Automatically Set)**
```
ENVIRONMENT=production
ENABLE_API_AUTH=true
ENABLE_RATE_LIMITING=true
ENABLE_HTTPS_REDIRECT=true
AZURE_SQL_SERVER=freshnutrients-sql.privatelink.database.windows.net
AZURE_SQL_DATABASE=FreshNutrientsDB
```

### **API Authentication**
```powershell
# Get your API key from deployment output
$apiKey = "YOUR_GENERATED_API_KEY"

# Test authenticated request
$headers = @{
    "Authorization" = "Bearer $apiKey"
    "Content-Type" = "application/json"
}

$body = @{
    message = "What are your best protein sources?"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://freshnutrients-api.YOUR_DOMAIN/api/v1/chat" -Method POST -Headers $headers -Body $body
```

## 📊 **Monitoring & Management**

### **Admin Endpoints** (Require API Key)
```powershell
# Health check
Invoke-RestMethod -Uri "https://freshnutrients-api.YOUR_DOMAIN/admin/health" -Headers $headers

# Performance analytics
Invoke-RestMethod -Uri "https://freshnutrients-api.YOUR_DOMAIN/admin/analytics" -Headers $headers

# Error monitoring
Invoke-RestMethod -Uri "https://freshnutrients-api.YOUR_DOMAIN/admin/errors" -Headers $headers
```

### **Azure Monitor Integration**
```powershell
# Enable Application Insights
az monitor app-insights component create `
  --app freshnutrients-insights `
  --location "East US" `
  --resource-group freshnutrients-rg

# Get instrumentation key
az monitor app-insights component show `
  --app freshnutrients-insights `
  --resource-group freshnutrients-rg `
  --query instrumentationKey
```

## 🎛️ **Scaling Configuration**

### **Auto-scaling Rules**
```powershell
# Update scaling configuration
az containerapp update `
  --name freshnutrients-api `
  --resource-group freshnutrients-rg `
  --min-replicas 2 `
  --max-replicas 20 `
  --scale-rule-name cpu-scale `
  --scale-rule-type cpu `
  --scale-rule-metadata concurrentRequests=10
```

### **Performance Optimization**
```powershell
# Update resource allocation
az containerapp update `
  --name freshnutrients-api `
  --resource-group freshnutrients-rg `
  --cpu 2.0 `
  --memory 4.0Gi
```

## 🔧 **Troubleshooting**

### **Common Issues & Solutions**

1. **"Cannot connect to SQL Server"**
   - ✅ **Solution**: Private endpoint takes 5-10 minutes to propagate DNS
   - ✅ **Check**: `nslookup freshnutrients-sql.privatelink.database.windows.net`

2. **"Container App won't start"**
   - ✅ **Solution**: Check logs: `az containerapp logs show --name freshnutrients-api --resource-group freshnutrients-rg`

3. **"API returns 401 Unauthorized"**
   - ✅ **Solution**: Use the API key from deployment output in Authorization header

4. **"High response times"**
   - ✅ **Solution**: Scale up resources or increase replica count

### **Diagnostic Commands**
```powershell
# Check deployment status
az containerapp show --name freshnutrients-api --resource-group freshnutrients-rg --query properties.provisioningState

# View application logs
az containerapp logs show --name freshnutrients-api --resource-group freshnutrients-rg --follow

# Check private endpoint status
az network private-endpoint show --name freshnutrients-sql-private-endpoint --resource-group freshnutrients-rg
```

## 💰 **Cost Optimization**

### **Estimated Monthly Costs** (East US)
- **Container Apps**: ~$30-100/month (depends on usage)
- **Azure SQL Basic**: ~$5/month
- **Virtual Network**: ~$0 (basic usage)
- **Private Endpoint**: ~$7/month
- **Total**: ~$42-112/month

### **Cost-Saving Tips**
1. Use **Azure Dev/Test** pricing if applicable
2. Set **minimum replicas to 0** for dev environments
3. Use **Spot instances** for non-critical workloads
4. Monitor with **Azure Cost Management**

## 🎯 **Next Steps**

1. **Run the deployment script** ✅
2. **Test private endpoint connectivity** ✅
3. **Deploy your application image** ⏳
4. **Configure monitoring dashboards** ⏳
5. **Set up CI/CD pipeline** ⏳
6. **Load testing** ⏳

---

**🎉 Result**: Your application now has secure, scalable database access without firewall issues!
