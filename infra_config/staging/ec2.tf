data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Owner ID for Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}


resource "aws_instance" "tracker_app_web_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  subnet_id     = var.public_subnet_cidr
  key_name      = var.key_name

  vpc_security_group_ids = [aws_security_group.tracker_app_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              apt-get update -y
              apt-get install -y docker.io docker-compose git
              systemctl enable docker
              systemctl start docker

              # Create app directory
              mkdir -p /home/ec2-user/tracker-app
              chown ec2-user:ec2-user /home/ec2-user/tracker-app
              EOF

  tags = merge(local.common_tags, {
    Name = "${var.environment}-tracker-app-server"
  })
}


resource "aws_security_group" "tracker_app_sg" {
  name        = "${var.environment}-tracker-app-sg"
  description = "Allow web traffic"
  vpc_id      = var.vpc_cidr

  tags = merge(local.common_tags, {
    Name = "${var.environment}-tracker-app-sg"
  })

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
