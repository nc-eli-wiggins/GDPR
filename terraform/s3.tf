resource "aws_s3_bucket" "gdpr_input_bucket" {
  bucket_prefix = "gdpr-input-"
  force_destroy = true
}

resource "aws_s3_bucket" "gdpr_processed_bucket" {
  bucket_prefix = "gdpr-processed-"
  force_destroy = true
}



output "gdpr_input_bucket" {
  value = aws_s3_bucket.gdpr_input_bucket.id
}

output "gdpr_processed_bucket" {
  value = aws_s3_bucket.gdpr_processed_bucket.id
}


