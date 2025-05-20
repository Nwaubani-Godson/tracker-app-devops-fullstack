output "instance_public_ip" {
  description = "Public IP of the EC2 instance"
  value       = aws_instance.tracker_app_web_server
}

output "subnet_id" {
  value = aws_subnet.public.id
}

output "vpc_id" {
  value = aws_vpc.main.id
}

output "frontend_ecr_url" {
  value = aws_ecr_repository.frontend.repository_url
}

output "backend_ecr_url" {
  value = aws_ecr_repository.backend.repository_url
}

