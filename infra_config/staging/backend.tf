terraform {
  backend "s3" {
    bucket         = "tasktracker-terraform-state"
    key            = "staging/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "tasktracker-terraform-locks"
    encrypt        = true
  }
}
