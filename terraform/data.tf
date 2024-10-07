data "aws_caller_identity" "current" {}

data "aws_region" "current" {}


data "terraform_remote_state" "gdpr_state" {
  backend = "s3"

  config = {
    bucket = "tf-state-gdpr-obfuscator-test"  
    key    = "tf-state"                  
    region = "eu-west-2"                 
  }
}


data "archive_file" "upload_zip" {
  type        = "zip"
  source_file = "${path.module}/../src/utils/processing2.py"
  output_path = "${path.module}/../upload.zip"
}


resource "aws_s3_object" "lambda_code" {
  bucket = data.terraform_remote_state.gdpr_state.outputs.gdpr_input_bucket  
  key    = "upload.zip"
  source = data.archive_file.upload_zip.output_path
}

