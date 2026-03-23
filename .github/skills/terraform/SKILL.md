---
name: terraform
description: >
  Plan, apply, validate, and troubleshoot Terraform infrastructure for the
  maf-contact-centre project on Azure.
---

# Terraform Skill

Use this skill when the user asks to run Terraform commands (plan, apply, destroy, validate, fmt), inspect infrastructure state, or troubleshoot Terraform errors for this project.

## Project context

- **Working directory**: `infra/` (all commands must run from this directory)
- **Backend**: Local state (`terraform.tfstate` in `infra/`)
- **Providers**: `azurerm` (~> 4.37), `azapi` (~> 2.0)
- **Variables file**: `infra/terraform.tfvars` (already populated)
- **Required CLI tools**: `terraform` (>= 1.10.0, < 2.0.0)
- **Authentication**: Azure CLI (`az login`) — must be authenticated before running commands

## Pre-flight checks

Before running any Terraform command:

1. Verify Terraform is installed: `terraform -version`
2. Verify Azure CLI authentication: `az account show`
3. Confirm `infra/terraform.tfvars` exists
4. If `infra/.terraform/` does not exist, run `terraform init` first

If any check fails, stop and tell the user what is missing and how to fix it.

## Commands

### terraform init

Run when `.terraform/` is missing or providers need updating.

```bash
cd infra && terraform init
```

### terraform fmt

Format all `.tf` files in `infra/`.

```bash
cd infra && terraform fmt
```

### terraform validate

Check configuration syntax and internal consistency.

```bash
cd infra && terraform validate
```

### terraform plan

Always save the plan to a file so `apply` uses the exact reviewed plan.

```bash
cd infra && terraform plan -out=main.tfplan
```

On success, summarise the planned changes (resources to add, change, destroy) for the user.
On failure, read the error output, diagnose the issue, and suggest a fix.

### terraform apply

Only apply a saved plan file — never run a bare `terraform apply`.

```bash
cd infra && terraform apply main.tfplan
```

After apply completes, show key outputs:

```bash
cd infra && terraform output
```

### terraform destroy

Always ask for explicit user confirmation before running destroy.

```bash
cd infra && terraform plan -destroy -out=destroy.tfplan
cd infra && terraform apply destroy.tfplan
```

### terraform output

Show current outputs from state.

```bash
cd infra && terraform output
```

## Error handling

- **Provider authentication errors**: Check `az account show` and suggest `az login`.
- **State lock errors**: Suggest `terraform force-unlock <LOCK_ID>` after confirming it is safe.
- **Provider version conflicts**: Suggest `terraform init -upgrade`.
- **Missing variable values**: Check `infra/terraform.tfvars` and `infra/variables.tf` for defaults.
- **API errors (Azure)**: Read the error message, check resource quotas, region availability, and naming constraints.

## Safety rules

- **Never** run `terraform apply` without a saved plan file.
- **Never** run `terraform destroy` without explicit user confirmation.
- **Never** display or log sensitive outputs (e.g., connection strings, keys).
- **Never** modify `terraform.tfvars` without asking the user first.
- **Never** commit `terraform.tfstate`, `.tfvars`, or `.terraform/` to git.

## Workflow

1. Run pre-flight checks.
2. Run `terraform init` if needed.
3. Run `terraform fmt` and `terraform validate` to catch issues early.
4. Run `terraform plan -out=main.tfplan` and summarise the changes.
5. Ask the user to confirm before applying.
6. Run `terraform apply main.tfplan`.
7. Show `terraform output` on success.
