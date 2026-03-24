# Infrastructure Provisioning

This project uses **Terraform** to provision Azure AI Foundry resources in the `infra/` directory.

## Prerequisites

- [Terraform](https://www.terraform.io/downloads) >= 1.10 (available in the devcontainer)
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/) (available in the devcontainer)
- An Azure subscription with permissions to create resources (AI Account Owner or equivalent)

### Register required resource providers

```bash
az provider register --namespace 'Microsoft.CognitiveServices'
az provider register --namespace 'Microsoft.MachineLearningServices'
```

## Resources Provisioned

| Resource | Name | Purpose |
|---|---|---|
| Resource Group | `rg-maf-contact-centre` | Logical container |
| Storage Account | `stmafcc` | AI Foundry Hub dependency |
| Key Vault | `kv-maf-cc` | AI Foundry Hub dependency |
| Log Analytics Workspace | `log-maf-cc` | Application Insights backend |
| Application Insights | `appi-maf-cc` | Observability / tracing |
| AI Services | `ais-maf-cc` | Cognitive services endpoint |
| AI Foundry Hub | `hub-maf-cc` | Parent workspace |
| AI Foundry Project | `maf-contact-centre` | AI project |
| GPT-5.4-mini Deployment | `gpt-54-mini` | Model deployment (GlobalStandard) |

## Deployment Steps

### 1. Authenticate

```bash
az login --tenant <your-azure-tenant-id>
```

### 2. Set the subscription

```bash
export ARM_SUBSCRIPTION_ID="<your-azure-subscription-id>"
```

### 3. Configure variables (optional)

All variables have sensible defaults. To override, copy the example file:

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars as needed
```

### 4. Initialise and deploy

```bash
cd infra
terraform init
terraform plan -out main.tfplan
terraform apply main.tfplan
```

### 5. Retrieve outputs

```bash
terraform output
# To get the Application Insights connection string:
terraform output -raw application_insights_connection_string
```

Set `APPLICATIONINSIGHTS_CONNECTION_STRING` in your environment so `config.yaml` can resolve it:

```bash
export APPLICATIONINSIGHTS_CONNECTION_STRING=$(terraform -chdir=infra output -raw application_insights_connection_string)
```

## Tear Down

```bash
cd infra
terraform plan -destroy -out main.destroy.tfplan
terraform apply main.destroy.tfplan
```

## Variables Reference

| Variable | Default | Description |
|---|---|---|
| `subscription_id` | `aed60926-...` | Azure subscription ID |
| `location` | `swedencentral` | Azure region |
| `resource_group_name` | `rg-maf-contact-centre` | Resource group name |
| `environment` | `dev` | Environment tag |
| `model_deployment_name` | `gpt-54-mini` | Deployment name for the main model |
| `model_name` | `gpt-5.4-mini` | OpenAI model name |
| `model_version` | `2026-03-17` | Model version string |
| `model_capacity` | `30` | Capacity in K tokens/min |
