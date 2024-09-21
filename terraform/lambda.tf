resource "aws_lambda_function" "my_lambda" {
    filename         = data.archive_file.upload_zip.output_path
    function_name    = "my_lambda_function"
    role             = aws_iam_role.lambda_role.arn
    handler          = "upload.handler"
    runtime          = "python3.8"  # check (works so far)
    source_code_hash = filebase64sha256(data.archive_file.upload_zip.output_path)

environment {
    variables = {
    EXAMPLE_ENV_VAR = "value"
    }
}
}