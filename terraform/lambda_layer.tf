resource "aws_lambda_layer_version" "main" {
  filename   = "../layer.zip"
  layer_name = var.bot_name

  compatible_runtimes = [var.python_version]

  lifecycle {
    create_before_destroy = true
  }
}
