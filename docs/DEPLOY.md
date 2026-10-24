# Deploying to AWS Fargate

This walks through pushing the container image to AWS and running it on Fargate.
It assumes you have an AWS account, the AWS CLI configured (`aws configure`), Docker,
and Terraform installed.

> Cost note: ECR storage, CloudWatch logs, and a single small Fargate task are
> low-cost and largely free-tier eligible, but not always zero. Run
> `terraform destroy` when you are finished so nothing keeps running.

## 1. Provision the infrastructure

```bash
cd terraform
terraform init
terraform plan          # review the resources
terraform apply
```

Note the outputs, especially `ecr_repository_url`.

## 2. Build and push the image

```bash
# Log Docker in to ECR (replace region/account as needed)
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

# Build, tag, push
docker build -t uptime-monitor .
docker tag uptime-monitor:latest <ecr_repository_url>:latest
docker push <ecr_repository_url>:latest
```

## 3. Let ECS run it

The ECS service is configured with `desired_count = 1`, so once the image is in
ECR it will pull and run the task. Find the task's public IP in the ECS console
(or via the AWS CLI) and hit `http://<public-ip>:8000/docs`.

## 4. Tear it down

```bash
terraform destroy
```

## Notes for a real deployment

- Put an Application Load Balancer with HTTPS in front instead of exposing the task IP.
- Store any secrets in AWS Secrets Manager or SSM Parameter Store, not env vars in the task definition.
- Add auto-scaling policies based on CPU or the app's own metrics.
