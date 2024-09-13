resource "aws_iam_group" "s3_bucket_access" {
  name = "s3-bucket-access"
}

resource "aws_iam_policy" "policy" {
  name        = "BucketAccessPolicy"
  description = "Policy to allow access to S3 bucket"
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
        "${aws_s3_bucket.gdpr_input_bucket.arn}/*"             
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

# Example IAM user or role to attach the group
resource "aws_iam_user" "example_user" {
  name = "example-user"
}

resource "aws_iam_user_group_membership" "user_membership" {
  user = aws_iam_user.example_user.name
  groups = [
    aws_iam_group.s3_bucket_access.name
  ]
}
