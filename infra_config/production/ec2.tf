# Fetch the latest Ubuntu 20.04 LTS AMI
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

# Application Server Resources
resource "aws_instance" "tracker_app_web_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  subnet_id     = aws_subnet.public.id
  key_name      = var.key_name

  vpc_security_group_ids = [aws_security_group.tracker_app_sg.id]

  iam_instance_profile = aws_iam_instance_profile.ec2_ecr_profile.name

  user_data = <<-EOF
            #!/bin/bash
            set -eux

            apt-get update -y
            apt-get install -y \
                docker.io \
                unzip \
                curl \
                jq \
                ca-certificates \
                gnupg \
                lsb-release

            systemctl enable docker
            systemctl start docker
            usermod -aG docker ubuntu

            # Install latest Docker Compose from GitHub
            sudo curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
            echo ">>> Docker Compose version:"
            docker-compose version

            # aws cli v2
            if ! command -v aws &>/dev/null; then
                curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
                unzip awscliv2.zip
                ./aws/install
                rm -rf awscliv2.zip aws
            fi

            mkdir -p /home/ubuntu/tracker-app
            chown ubuntu:ubuntu /home/ubuntu/tracker-app
        EOF

  tags = merge(local.common_tags, {
    Name = "${var.environment}-tracker-app-server"
  })
}

resource "aws_security_group" "tracker_app_sg" {
  name        = "${var.environment}-tracker-app-sg"
  description = "Allow web traffic"
  vpc_id      = aws_vpc.main.id

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

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow Prometheus to scrape metrics from app server
  ingress {
    from_port       = 9100
    to_port         = 9100
    protocol        = "tcp"
    security_groups = [aws_security_group.monitoring_sg.id] # allow only from monitoring server
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Monitoring Server Resources
resource "aws_security_group" "monitoring_sg" {
  name        = "${var.environment}-monitoring-sg"
  description = "Allow monitoring stack traffic"
  vpc_id      = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "${var.environment}-monitoring-sg"
  })


  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  # Prometheus
  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Alertmanager
  ingress {
    from_port   = 9093
    to_port     = 9093
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Grafana
  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Elasticsearch 
  ingress {
    from_port   = 9200
    to_port     = 9200
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Kibana 
  ingress {
    from_port   = 5601
    to_port     = 5601
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Node Exporter (for system metrics)
  ingress {
    from_port   = 9100
    to_port     = 9100
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


resource "aws_instance" "monitoring_server" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.monitoring_sg.id]
  key_name               = var.key_name
  iam_instance_profile   = aws_iam_instance_profile.ec2_ecr_profile.name

  user_data = <<-EOF
            #!/bin/bash
            set -eux

            apt-get update -y
            apt-get install -y \
                docker.io \
                unzip \
                curl \
                jq \
                ca-certificates \
                gnupg \
                lsb-release

            systemctl enable docker
            systemctl start docker
            usermod -aG docker ubuntu

            # Install latest Docker Compose
            sudo curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
            echo ">>> Docker Compose version:"
            docker-compose version

            # aws cli v2
            if ! command -v aws &>/dev/null; then
                curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
                unzip awscliv2.zip
                ./aws/install
                rm -rf awscliv2.zip aws
            fi

            mkdir -p /home/ubuntu/monitoring
            chown ubuntu:ubuntu /home/ubuntu/monitoring
        EOF

  tags = merge(local.common_tags, {
    Name = "${var.environment}-monitoring-server"
  })
}
