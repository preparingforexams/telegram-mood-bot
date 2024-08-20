terraform {
  required_version = "1.9.5"

  backend "s3" {
    region = "eu-central-1"
    bucket = "legacy-terraform-states"
    key    = "mischebot"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }

    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.4"
    }
  }
}

variable "cloudflare_token" {
  type = string
}

provider "cloudflare" {
  api_token = var.cloudflare_token
}

variable "aws_region" {
  default = "eu-central-1"
  type    = string
}

provider "aws" {
  region = var.aws_region
}
