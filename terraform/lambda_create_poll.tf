resource "aws_lambda_function" "handle_poll_trigger" {
  function_name = "${var.bot_name}-handle_poll_trigger"
  role          = aws_iam_role.lambda_role.arn
  runtime       = "python3.8"
  handler       = "bot.handle_poll_trigger"
  timeout       = 30

  filename         = "../code.zip"
  source_code_hash = filebase64sha256("../code.zip")

  layers = [aws_lambda_layer_version.main.arn]

  environment {
    variables = {
      TELEGRAM_TOKEN = var.telegram_token,
      TARGET_HOUR    = var.target_hour
    }
  }
}
