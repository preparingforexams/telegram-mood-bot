resource "aws_api_gateway_rest_api" "api" {
  name = "telegram-${var.bot_name}"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_deployment" "deployment" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  stage_name  = "prod"

  triggers = {
    redeployment = sha1(join(",", tolist([
      jsonencode(aws_api_gateway_integration.handle_update),
      jsonencode(aws_api_gateway_integration.post_auth),
      jsonencode(aws_api_gateway_integration.get_auth),
      jsonencode(aws_api_gateway_integration.put_auth),
    ])))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.handle_update,
    aws_api_gateway_integration.post_auth,
    aws_api_gateway_integration.get_auth,
    aws_api_gateway_integration.put_auth
  ]
}

resource "aws_api_gateway_usage_plan" "whitelist" {
  name = "${var.bot_name}-whitelist"
  api_stages {
    api_id = aws_api_gateway_rest_api.api.id
    stage  = aws_api_gateway_deployment.deployment.stage_name
  }

  throttle_settings {
    burst_limit = 50
    rate_limit  = 10
  }
}

resource "aws_api_gateway_base_path_mapping" "api_domain" {
  api_id      = aws_api_gateway_rest_api.api.id
  domain_name = aws_api_gateway_domain_name.domain_name.domain_name
  stage_name  = aws_api_gateway_deployment.deployment.stage_name
}
