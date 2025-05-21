resource "aws_iam_role" "ec2_ecr_pull" {
  name = "ec2-ecr-pull-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "ec2.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecr_readonly_attach" {
  role       = aws_iam_role.ec2_ecr_pull.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}


resource "aws_iam_instance_profile" "ec2_ecr_profile" {
  name = "ec2-ecr-instance-profile"
  role = aws_iam_role.ec2_ecr_pull.name

  tags = merge(local.common_tags, {
    Name = "${var.environment}-tracker-app"
  })
}