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
# Storage Account (required by AI Foundry Hub)
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
# Key Vault (required by AI Foundry Hub)
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
# AI Services (provides the cognitive endpoint for model deployments)
# ---------------------------------------------------------------------------

resource "azurerm_ai_services" "main" {
  name                = "ais-maf-cc"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku_name            = "S0"

  tags = {
    environment = var.environment
  }
}

# ---------------------------------------------------------------------------
# AI Foundry Hub
# ---------------------------------------------------------------------------

resource "azurerm_ai_foundry" "hub" {
  name                    = "hub-maf-cc"
  location                = azurerm_ai_services.main.location
  resource_group_name     = azurerm_resource_group.main.name
  storage_account_id      = azurerm_storage_account.hub.id
  key_vault_id            = azurerm_key_vault.hub.id
  application_insights_id = azurerm_application_insights.main.id

  identity {
    type = "SystemAssigned"
  }

  tags = {
    environment = var.environment
  }
}

# ---------------------------------------------------------------------------
# AI Foundry Project
# ---------------------------------------------------------------------------

resource "azurerm_ai_foundry_project" "main" {
  name               = "maf-contact-centre"
  location           = azurerm_ai_foundry.hub.location
  ai_services_hub_id = azurerm_ai_foundry.hub.id
  friendly_name      = "MAF Contact Centre"

  identity {
    type = "SystemAssigned"
  }

  tags = {
    environment = var.environment
  }
}

# ---------------------------------------------------------------------------
# GPT Model Deployment
# ---------------------------------------------------------------------------

resource "azurerm_cognitive_deployment" "gpt" {
  name                 = "gpt-53-chat"
  cognitive_account_id = azurerm_ai_services.main.id

  model {
    format  = "OpenAI"
    name    = var.model_name
    version = var.model_version
  }

  sku {
    name     = "GlobalStandard"
    capacity = var.model_capacity
  }
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
  scope                = azurerm_ai_services.main.id
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
