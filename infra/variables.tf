variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
  default     = "aed60926-8bee-4a41-8892-55b523eb705f"
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

variable "model_name" {
  description = "OpenAI model name to deploy"
  type        = string
  default     = "gpt-5.3-chat"
}

variable "model_version" {
  description = "OpenAI model version string"
  type        = string
  default     = "2026-01-01"
}

variable "model_capacity" {
  description = "Model deployment capacity (thousands of tokens per minute)"
  type        = number
  default     = 30
}
