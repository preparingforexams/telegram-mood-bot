resource "aws_cloudwatch_event_rule" "closer" {
  name                = "${var.bot_name}-closer"
  schedule_expression = "cron(0 1 * * ? *)"
}

resource "aws_cloudwatch_event_target" "closer" {
  rule = aws_cloudwatch_event_rule.closer.name
  arn  = aws_lambda_function.handle_close_trigger.arn
}

resource "aws_lambda_permission" "invoke_closer" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.handle_close_trigger.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.closer.arn
}
