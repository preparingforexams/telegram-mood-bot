resource "aws_lambda_function" "handle_close_trigger" {
  function_name = "${var.bot_name}-handle_close_trigger"
  role          = aws_iam_role.lambda_role.arn
  runtime       = "python3.8"
  handler       = "bot.handle_close_trigger"
  timeout       = 30

  filename         = "../code.zip"
  source_code_hash = filebase64sha256("../code.zip")

  layers = [aws_lambda_layer_version.main.arn]

  environment {
    variables = {
      TELEGRAM_TOKEN = var.telegram_token,
      TARGET_HOUR    = var.target_hour,
      TABLE_NAME     = aws_dynamodb_table.keyvalue.name
    }
  }
}
