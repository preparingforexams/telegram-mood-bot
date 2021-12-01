data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
resource "aws_lambda_function" "authorizer" {
  function_name = "${var.bot_name}-authorizer"
  role          = aws_iam_role.lambda_role.arn
  runtime       = var.python_version
  handler       = "auth.authorize_request"
  timeout       = 5

  filename         = "../code.zip"
  source_code_hash = filebase64sha256("../code.zip")

  layers = [aws_lambda_layer_version.main.arn]

  environment {
    variables = {
      KEYVALUE_TABLE = aws_dynamodb_table.keyvalue.name,
      API_RESOURCE   = "arn:aws:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${aws_api_gateway_rest_api.api.id}/*/*/"
    }
  }
}
