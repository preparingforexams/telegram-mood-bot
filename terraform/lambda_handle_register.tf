resource "aws_lambda_function" "handle_register" {
  function_name = "${var.bot_name}-handleregister"
  role          = aws_iam_role.lambda_role.arn
  runtime       = "python3.8"
  handler       = "auth.handle_register"
  timeout       = 30

  filename         = "../code.zip"
  source_code_hash = filebase64sha256("../code.zip")

  layers = [aws_lambda_layer_version.main.arn]

  environment {
    variables = {
      USERS_TABLE    = aws_dynamodb_table.api_users.name,
      USERS_TG_TABLE = aws_dynamodb_table.api_users_tg.name,
      KEYVALUE_TABLE = aws_dynamodb_table.keyvalue.name
    }
  }
}
