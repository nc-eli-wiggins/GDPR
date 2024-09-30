

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

resource "aws_iam_policy" "lambda_s3_policy" {
  name        = "lambda_s3_policy"
  description = "Policy to allow Lambda function access to S3 buckets"
  
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          "s3:DeleteObject",
          "logs:*"
        ],
        Resource = [
          "arn:aws:s3:::tf-state-gdpr-obfuscator/tf-state",
          "arn:aws:s3:::${data.terraform_remote_state.gdpr_state.outputs.gdpr_input_bucket}",              
          "arn:aws:s3:::${data.terraform_remote_state.gdpr_state.outputs.gdpr_input_bucket}/*",  
          "arn:aws:s3:::${data.terraform_remote_state.gdpr_state.outputs.gdpr_processed_bucket}",              
          "arn:aws:s3:::${data.terraform_remote_state.gdpr_state.outputs.gdpr_processed_bucket}/*",
          "arn:aws:s3:::${data.terraform_remote_state.gdpr_state.outputs.gdpr_invocation_bucket}",              
          "arn:aws:s3:::${data.terraform_remote_state.gdpr_state.outputs.gdpr_invocation_bucket}/*",
          "arn:aws:logs:eu-west-2:*:log-group:/aws/lambda/my_lambda_function:*"
          
        ]
      }
    ]
  })
}
resource "aws_lambda_permission" "allow_s3_invocation" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.my_lambda.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.gdpr_invocation_bucket.arn
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_s3_policy.arn
}

resource "aws_iam_user" "example_user" {
  name = "example-user"
}

resource "aws_iam_group" "s3_bucket_access" {
  name = "s3-bucket-access"
}

resource "aws_iam_user_group_membership" "user_membership" {
  user = aws_iam_user.example_user.name
  groups = [
    aws_iam_group.s3_bucket_access.name
  ]
}