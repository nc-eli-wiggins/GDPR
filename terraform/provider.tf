provider "aws" {
    region = "eu-west-2"
}

terraform { 
    required_providers {
      aws = {
        source = "hashicorp/aws"
        version = "5.66.0"
      }
    }


    backend "s3" {
      bucket = "tf-state-gdpr-obfuscator"
      key = "tf-state"
      region = "eu-west-2"
    }
}