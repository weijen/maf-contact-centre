output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "ai_foundry_name" {
  description = "Name of the AI Foundry resource"
  value       = azapi_resource.ai_foundry.name
}

output "ai_project_name" {
  description = "Name of the AI Foundry Project"
  value       = azapi_resource.ai_foundry_project.name
}

output "ai_services_endpoint" {
  description = "Endpoint of the AI Services account"
  value       = azapi_resource.ai_foundry.output.properties.endpoint
}

output "application_insights_connection_string" {
  description = "Connection string for Application Insights (use as APPLICATIONINSIGHTS_CONNECTION_STRING)"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

output "eval_deployment_name" {
  description = "Deployment name of the evaluator model"
  value       = azapi_resource.eval_deployment.name
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.hub.vault_uri
}
