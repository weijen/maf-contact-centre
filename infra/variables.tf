variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "swedencentral"
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "rg-maf-contact-centre"
}

variable "environment" {
  description = "Environment tag (e.g. dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "model_deployment_name" {
  description = "Deployment name for the main model"
  type        = string
  default     = "gpt-54-mini"
}

variable "model_name" {
  description = "OpenAI model name to deploy"
  type        = string
  default     = "gpt-5.4-mini"
}

variable "model_version" {
  description = "OpenAI model version string"
  type        = string
  default     = "2026-03-17"
}

variable "model_capacity" {
  description = "Model deployment capacity (thousands of tokens per minute)"
  type        = number
  default     = 30
}

# ---------------------------------------------------------------------------
# Evaluator model variables
# ---------------------------------------------------------------------------

variable "eval_model_deployment_name" {
  description = "Deployment name for the evaluator model (Chat Completions API)"
  type        = string
  default     = "gpt-4o"
}

variable "eval_model_name" {
  description = "OpenAI model name for evaluations"
  type        = string
  default     = "gpt-4o"
}

variable "eval_model_version" {
  description = "OpenAI evaluator model version string"
  type        = string
  default     = "2024-08-06"
}

variable "eval_model_capacity" {
  description = "Evaluator model deployment capacity (thousands of tokens per minute)"
  type        = number
  default     = 50
}
