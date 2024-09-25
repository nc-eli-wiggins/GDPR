data "terraform_remote_state" "gdpr_state3" {
  backend = "s3"
  
  config = {
    bucket = "tf-state-gdpr-obfuscator"
    key    = "tf-state"
    region = "eu-west-2"
  }
}

resource "aws_s3_bucket_notification" "json_upload" {
  bucket = data.terraform_remote_state.gdpr_state3.outputs.gdpr_invocation_bucket

  lambda_function {
    lambda_function_arn = aws_lambda_function.my_lambda.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = ""
    filter_suffix       = ".json"
  }

  depends_on = [aws_lambda_permission.allow_s3_invocation]
}



resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.my_lambda.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${data.terraform_remote_state.gdpr_state3.outputs.gdpr_invocation_bucket}"
}
