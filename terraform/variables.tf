variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "us-east-1"
}

variable "app_name" {
  description = "Name used for all resources."
  type        = string
  default     = "uptime-monitor"
}

variable "app_port" {
  description = "Port the container listens on."
  type        = number
  default     = 8000
}
