# Plan: Provision Azure AI Foundry Project

## Problem Statement
Provision an Azure AI Foundry project named `maf-contact-centre` with a GPT-5.4-mini model deployment and Application Insights for observability. Subscription: `<your-azure-subscription-id>`.

## Proposed Approach
Use Infrastructure-as-Code to provision the following Azure resources:

### Resources to Provision
1. **Resource Group** — logical container for all resources
2. **Azure AI Hub** (formerly Azure AI resource) — parent resource for the AI project
3. **Azure AI Project** — `maf-contact-centre` project under the hub
4. **GPT-5.4-mini Model Deployment** — deployed within the AI project
5. **Application Insights** — for tracing/observability (already referenced in `config.yaml`)
6. **Log Analytics Workspace** — required backend for Application Insights
7. **Azure Storage Account** — required dependency for AI Hub
8. **Azure Key Vault** — required dependency for AI Hub

### Integration Points
- Wire Application Insights connection string into `config.yaml` (already templated as `${APPLICATIONINSIGHTS_CONNECTION_STRING}`)
- Output key values (endpoint, API keys, connection strings) for application configuration

## Todos
- `resource-group`: Create resource group resource definition
- `ai-hub`: Create Azure AI Hub resource definition (depends on resource-group, storage, keyvault)
- `ai-project`: Create Azure AI Foundry project resource definition (depends on ai-hub)
- `model-deployment`: Deploy GPT-5.4-mini model (depends on ai-project)
- `app-insights`: Create Application Insights + Log Analytics Workspace (depends on resource-group)
- `storage-account`: Create Storage Account for AI Hub (depends on resource-group)
- `key-vault`: Create Key Vault for AI Hub (depends on resource-group)
- `outputs`: Define outputs (endpoints, connection strings, keys)
- `documentation`: Document provisioning steps in docs/

## Decisions (Resolved)
- **IaC tool**: Terraform
- **Azure region**: `swedencentral`
- **Resource group**: New — `rg-maf-contact-centre`
- **Naming convention**: Azure standard with `maf-cc` prefix
  - AI Hub: `hub-maf-cc`
  - Storage Account: `stmafcc` (no hyphens — Azure requirement)
  - Key Vault: `kv-maf-cc`
  - Log Analytics: `log-maf-cc`
  - App Insights: `appi-maf-cc`
  - AI Project: `maf-contact-centre`
- **GPT-5.4-mini deployment**: GlobalStandard SKU (pay-per-use, no reserved capacity)
- **Environment tag**: `dev`
- **Additional tags**: None

## Notes
- `config.yaml` already references `${APPLICATIONINSIGHTS_CONNECTION_STRING}` — good to go
- No existing IaC in the repo — this will be net-new
- Storage Account and Key Vault are required dependencies for Azure AI Hub
