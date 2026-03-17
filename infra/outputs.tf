output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "ai_hub_name" {
  description = "Name of the AI Foundry Hub"
  value       = azurerm_ai_foundry.hub.name
}

output "ai_project_name" {
  description = "Name of the AI Foundry Project"
  value       = azurerm_ai_foundry_project.main.name
}

output "ai_services_endpoint" {
  description = "Endpoint of the AI Services account"
  value       = azurerm_ai_services.main.endpoint
}

output "application_insights_connection_string" {
  description = "Connection string for Application Insights (use as APPLICATIONINSIGHTS_CONNECTION_STRING)"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.hub.vault_uri
}
