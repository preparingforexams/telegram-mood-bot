terraform {
  backend "remote" {
    hostname = "app.terraform.io"

    workspaces {
      name = "mischebot"
    }
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.35.0"
    }

    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 3.25.0"
    }
  }
}

variable "cloudflare_token" {}

provider "cloudflare" {
  api_token = var.cloudflare_token
}

variable "aws_profile" {
  default = "default"
  type    = string
}

variable "aws_region" {
  default = "eu-central-1"
  type    = string
}

provider "aws" {
  profile = var.aws_profile
  region  = var.aws_region
}
