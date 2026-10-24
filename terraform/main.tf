# Infrastructure as Code for AWS.
#
# This provisions the pieces needed to run the container on AWS Fargate:
#   - an ECR repository to hold the Docker image
#   - a CloudWatch log group for centralized logs
#   - an ECS cluster + Fargate task/service behind the default VPC
#
# It is written to be readable and safe to `terraform plan` for review. Applying
# it will create real (mostly free-tier-eligible) AWS resources, so read the
# README before running `terraform apply`.

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# --- Container registry -----------------------------------------------------
resource "aws_ecr_repository" "app" {
  name                 = var.app_name
  image_tag_mutability = "IMMUTABLE" # tags can't be overwritten -> reproducible deploys

  image_scanning_configuration {
    scan_on_push = true # scan images for CVEs automatically (security)
  }
}

# --- Logs -------------------------------------------------------------------
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.app_name}"
  retention_in_days = 14
}

# --- ECS cluster ------------------------------------------------------------
resource "aws_ecs_cluster" "this" {
  name = "${var.app_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled" # extra CloudWatch metrics for the cluster
  }
}
