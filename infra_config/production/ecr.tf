resource "aws_ecr_repository" "frontend" {
  name = "${var.environment}-frontend-repo"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${var.environment}-frontend-ecr"
  }
}

resource "aws_ecr_repository" "backend" {
  name = "${var.environment}-backend-repo"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${var.environment}-backend-ecr"
  }
}
