# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------

data "azurerm_client_config" "current" {}

# ---------------------------------------------------------------------------
# Resource Group
# ---------------------------------------------------------------------------

resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    environment = var.environment
  }
}

# ---------------------------------------------------------------------------
# Storage Account
# ---------------------------------------------------------------------------

resource "azurerm_storage_account" "hub" {
  name                     = "stmafcc"
  location                 = azurerm_resource_group.main.location
  resource_group_name      = azurerm_resource_group.main.name
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = {
    environment = var.environment
  }
}

# ---------------------------------------------------------------------------
# Key Vault
# ---------------------------------------------------------------------------

resource "azurerm_key_vault" "hub" {
  name                     = "kv-maf-cc"
  location                 = azurerm_resource_group.main.location
  resource_group_name      = azurerm_resource_group.main.name
  tenant_id                = data.azurerm_client_config.current.tenant_id
  sku_name                 = "standard"
  purge_protection_enabled = true

  tags = {
    environment = var.environment
  }
}

# ---------------------------------------------------------------------------
# Observability — Log Analytics + Application Insights
# ---------------------------------------------------------------------------

resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-maf-cc"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = {
    environment = var.environment
  }
}

resource "azurerm_application_insights" "main" {
  name                = "appi-maf-cc"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"

  tags = {
    environment = var.environment
  }
}

# ---------------------------------------------------------------------------
# AI Foundry Resource (CognitiveServices account with project management)
# ---------------------------------------------------------------------------

resource "azapi_resource" "ai_foundry" {
  type                      = "Microsoft.CognitiveServices/accounts@2025-06-01"
  name                      = "ais-maf-cc"
  parent_id                 = azurerm_resource_group.main.id
  location                  = var.location
  schema_validation_enabled = false

  body = {
    kind = "AIServices"
    sku = {
      name = "S0"
    }
    identity = {
      type = "SystemAssigned"
    }
    properties = {
      disableLocalAuth       = false
      allowProjectManagement = true
      customSubDomainName    = "ais-maf-cc"
    }
  }

  tags = {
    environment = var.environment
  }

  response_export_values = ["properties.endpoint"]
}

# ---------------------------------------------------------------------------
# AI Foundry Project
# ---------------------------------------------------------------------------

resource "azapi_resource" "ai_foundry_project" {
  type                      = "Microsoft.CognitiveServices/accounts/projects@2025-06-01"
  name                      = "maf-contact-centre"
  parent_id                 = azapi_resource.ai_foundry.id
  location                  = var.location
  schema_validation_enabled = false

  body = {
    sku = {
      name = "S0"
    }
    identity = {
      type = "SystemAssigned"
    }
    properties = {
      displayName = "MAF Contact Centre"
      description = "MAF Contact Centre AI project"
    }
  }

  tags = {
    environment = var.environment
  }
}

# ---------------------------------------------------------------------------
# GPT Model Deployment
# ---------------------------------------------------------------------------

resource "azapi_resource" "gpt_deployment" {
  type      = "Microsoft.CognitiveServices/accounts/deployments@2025-06-01"
  name      = "gpt-53-chat"
  parent_id = azapi_resource.ai_foundry.id

  body = {
    sku = {
      name     = "GlobalStandard"
      capacity = var.model_capacity
    }
    properties = {
      model = {
        format  = "OpenAI"
        name    = var.model_name
        version = var.model_version
      }
    }
  }

  depends_on = [azapi_resource.ai_foundry]
}

# ---------------------------------------------------------------------------
# RBAC — grant the deploying user access to AI Foundry portal resources
# ---------------------------------------------------------------------------

resource "azurerm_role_assignment" "user_ai_developer" {
  scope                = azurerm_resource_group.main.id
  role_definition_name = "Azure AI Developer"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_role_assignment" "user_cognitive_openai_user" {
  scope                = azapi_resource.ai_foundry.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_role_assignment" "user_storage_blob_contributor" {
  scope                = azurerm_storage_account.hub.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_role_assignment" "user_keyvault_reader" {
  scope                = azurerm_key_vault.hub.id
  role_definition_name = "Key Vault Reader"
  principal_id         = data.azurerm_client_config.current.object_id
}
