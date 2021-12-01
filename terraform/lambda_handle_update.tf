resource "aws_lambda_function" "handle_update" {
  function_name = "${var.bot_name}-handleupdate"
  role          = aws_iam_role.lambda_role.arn
  runtime       = var.python_version
  handler       = "bot.handle_update"
  timeout       = 30

  filename         = "../code.zip"
  source_code_hash = filebase64sha256("../code.zip")

  layers = [aws_lambda_layer_version.main.arn]

  environment {
    variables = {
      TELEGRAM_TOKEN     = var.telegram_token,
      TARGET_HOUR        = var.target_hour,
      RESULT2_TABLE_NAME = aws_dynamodb_table.results2.name,
      GROUP_TABLE_NAME   = aws_dynamodb_table.groups.name
      USER_TABLE_NAME    = aws_dynamodb_table.users.name
    }
  }
}
