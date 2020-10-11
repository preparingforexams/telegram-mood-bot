resource "aws_lambda_function" "data" {
  function_name = "${var.bot_name}-data"
  role          = aws_iam_role.lambda_role.arn
  runtime       = "python3.8"
  handler       = "data.handle_request"
  timeout       = 30

  filename         = "../code.zip"
  source_code_hash = filebase64sha256("../code.zip")

  layers = [aws_lambda_layer_version.main.arn]

  environment {
    variables = {
      USERS_TABLE     = aws_dynamodb_table.api_users.name,
      USERS_TG_TABLE  = aws_dynamodb_table.api_users_tg.name,
      BOT_USERS_TABLE = aws_dynamodb_table.users.name,
      KEYVALUE_TABLE  = aws_dynamodb_table.keyvalue.name
    }
  }
}
