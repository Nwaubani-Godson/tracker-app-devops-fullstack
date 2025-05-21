# Reference the existing IAM role (created in staging)
data "aws_iam_role" "ec2_ecr_pull" {
  name = "ec2-ecr-pull-role"

  tags = local.common_tags
}

# Reference the existing instance profile
data "aws_iam_instance_profile" "ecr_profile" {
  name = "ec2-ecr-instance-profile"
}
