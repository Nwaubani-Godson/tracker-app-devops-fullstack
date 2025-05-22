
# Task Tracker App – DevOps CI/CD Pipeline

This project demonstrates a CI/CD pipeline setup for a Task Tracker App using **Docker**, **GitHub Actions**, **Terraform**, and **AWS**.

## Features

1. Dockerized backend (FastAPI)  
2. Dockerized frontend (HTML + JavaScript)  
3. Docker Compose setup for local development  
4. GitHub Actions CI/CD pipeline  
5. Infrastructure provisioning with Terraform  
6. Application deployed to AWS EC2 instance  

## Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/Nwaubani-Godson/tracker-app-infra-deploy.git
cd Task_Tracker_App
```

### 2. Start the application locally

```bash
docker-compose up --build
```

### 3. Access the app

- Frontend: http://localhost:3500  
- Backend API: http://localhost:8000/tasks

## Infrastructure Provisioning (Terraform)

### 1. Navigate to Terraform directory

```bash
cd infra_config/staging
cd infra_cong/production
```

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Apply configuration to deploy EC2 instance on AWS

```bash
terraform plan
terraform apply
```

## CI/CD Pipeline – GitHub Actions

Pipeline files: `.github/workflows/ci-cd-staging.yaml` 
                `.github/workflows/ci-cd-prod.yaml`
