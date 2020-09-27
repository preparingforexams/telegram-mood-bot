resource "aws_lambda_layer_version" "main" {
  filename   = "../layer.zip"
  layer_name = var.bot_name

  compatible_runtimes = ["python3.8"]

  lifecycle {
    create_before_destroy = true
  }
}
