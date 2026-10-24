output "ecr_repository_url" {
  description = "Push your Docker image here."
  value       = aws_ecr_repository.app.repository_url
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster running the service."
  value       = aws_ecs_cluster.this.name
}

output "log_group" {
  description = "CloudWatch log group for application logs."
  value       = aws_cloudwatch_log_group.app.name
}
