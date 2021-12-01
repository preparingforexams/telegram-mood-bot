resource "aws_lambda_function" "data" {
  function_name = "${var.bot_name}-data"
  role          = aws_iam_role.lambda_role.arn
  runtime       = var.python_version
  handler       = "data.handle_request"
  timeout       = 30

  filename         = "../code.zip"
  source_code_hash = filebase64sha256("../code.zip")

  layers = [aws_lambda_layer_version.main.arn]

  environment {
    variables = {
      USERS_TABLE        = aws_dynamodb_table.api_users.name
      USERS_TG_TABLE     = aws_dynamodb_table.api_users_tg.name
      BOT_USERS_TABLE    = aws_dynamodb_table.users.name
      RESULT2_TABLE_NAME = aws_dynamodb_table.results2.name
      GROUP_TABLE        = aws_dynamodb_table.groups.name
      KEYVALUE_TABLE     = aws_dynamodb_table.keyvalue.name
    }
  }
}
