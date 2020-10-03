resource "aws_lambda_function" "handle_tg_link" {
  function_name = "${var.bot_name}-handletglink"
  role          = aws_iam_role.lambda_role.arn
  runtime       = "python3.8"
  handler       = "link.handle_link"
  timeout       = 30

  filename         = "../code.zip"
  source_code_hash = filebase64sha256("../code.zip")

  layers = [aws_lambda_layer_version.main.arn]

  environment {
    variables = {
      ANDROID_PACKAGE_NAME = var.android_package_name
      FIREBASE_DOMAIN      = var.firebase_domain
      DEEP_LINK_DOMAIN = "${var.bot_name}.${var.cloudflare_infix}${var.cloudflare_zone_name}"
    }
  }
}
