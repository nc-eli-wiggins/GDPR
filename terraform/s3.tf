resource "aws_s3_bucket" "gdpr_input_bucket" {
  bucket_prefix = "gdpr-input-"
  force_destroy = true
}

resource "aws_s3_bucket" "gdpr_processed_bucket" {
  bucket_prefix = "gdpr-processed-"
  force_destroy = true
}

resource "aws_s3_bucket" "gdpr_invocation_bucket" {
  bucket_prefix = "gdpr-invocation-"
  force_destroy = true
}


output "gdpr_input_bucket" {
  value = aws_s3_bucket.gdpr_input_bucket.id
}

output "gdpr_processed_bucket" {
  value = aws_s3_bucket.gdpr_processed_bucket.id
}

output "gdpr_invocation_bucket" {
  value = aws_s3_bucket.gdpr_invocation_bucket.id
}
# this must be ran 1st in stages using 
# terraform apply -target=aws_s3_bucket.gdpr_input_bucket -target=aws_s3_bucket.gdpr_processed_bucket -target=aws_s3_bucket.gdpr_invocation_bucket
# then run terraform apply

# might try to use workspaces, modules or depends on attribute

