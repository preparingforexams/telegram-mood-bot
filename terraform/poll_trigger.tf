resource "aws_cloudwatch_event_rule" "daily1" {
  name                = "${var.bot_name}-daily1"
  schedule_expression = "cron(1 ${var.target_hour - 2} * * ? *)"
}

resource "aws_cloudwatch_event_target" "reminder1" {
  rule = aws_cloudwatch_event_rule.daily1.name
  arn  = aws_lambda_function.handle_poll_trigger.arn
}

resource "aws_lambda_permission" "invoke_reminder1" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.handle_poll_trigger.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily1.arn
}

resource "aws_cloudwatch_event_rule" "daily2" {
  name                = "${var.bot_name}-daily2"
  schedule_expression = "cron(1 ${var.target_hour - 1} * * ? *)"
}

resource "aws_cloudwatch_event_target" "reminder2" {
  rule = aws_cloudwatch_event_rule.daily2.name
  arn  = aws_lambda_function.handle_poll_trigger.arn
}

resource "aws_lambda_permission" "invoke_reminder2" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.handle_poll_trigger.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily2.arn
}
