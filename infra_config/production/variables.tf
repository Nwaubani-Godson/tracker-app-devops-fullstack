variable "environment" {
  type    = string
  default = "production"
}

variable "my_ip" {
  description = "Restrict ssh access to this IP"
  type        = string
}


variable "instance_type" {
  type        = string
  description = "Instance type"
}

variable "key_name" {
  type        = string
  description = "SSH key name"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC"
}

variable "public_subnet_cidr" {
  type        = string
  description = "CIDR block for the public subnet"
}
