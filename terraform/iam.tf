resource "aws_iam_group" "s3_bucket_access" {
  name = "s3-bucket-access"
}

resource "aws_iam_policy" "policy" {
  name        = "BucketAccessPolicy"
  description = "Policy to allow access to both S3 buckets"
  policy      = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:*"
      ],
      "Resource": [
        "${aws_s3_bucket.gdpr_input_bucket.arn}",              
        "${aws_s3_bucket.gdpr_input_bucket.arn}/*",  
        "${aws_s3_bucket.gdpr_processed_bucket.arn}",              
        "${aws_s3_bucket.gdpr_processed_bucket.arn}/*"  
      ]
    }
  ]
}
EOF
}

resource "aws_iam_group_policy_attachment" "s3_policy_attach" {
  group      = aws_iam_group.s3_bucket_access.name
  policy_arn = aws_iam_policy.policy.arn
}

resource "aws_iam_user" "example_user" {
  name = "example-user"
}

resource "aws_iam_user_group_membership" "user_membership" {
  user = aws_iam_user.example_user.name
  groups = [
    aws_iam_group.s3_bucket_access.name
  ]
}

resource "aws_iam_role" "lambda_role" {
  name = "lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com",
        },
      },
    ],
  })
}

resource "aws_iam_policy" "lambda_policy" {
  name        = "lambda-s3-access"
  description = "Policy to allow Lambda function access to S3 buckets"
  
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::${aws_s3_bucket.gdpr_processed_bucket.id}/*",   
        "arn:aws:s3:::${aws_s3_bucket.gdpr_processed_bucket.id}"      
      ]
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

