resource "aws_s3_bucket" "gdpr_input_bucket" {
  bucket_prefix =  "gdpr-input-"
  force_destroy = true
}

output "gdpr_bucket" {
  value = aws_s3_bucket.gdpr_input_bucket.id
}

