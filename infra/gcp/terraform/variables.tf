variable "project_id" {
  description = "Existing GCP project with billing enabled. Terraform does not create or attach billing."
  type        = string
}

variable "region" {
  description = "Deployment region."
  type        = string
  default     = "us-central1"
}

variable "api_image" {
  description = "Immutable Artifact Registry image URI for the API."
  type        = string
}

variable "worker_image" {
  description = "Immutable Artifact Registry image URI for the worker."
  type        = string
}

