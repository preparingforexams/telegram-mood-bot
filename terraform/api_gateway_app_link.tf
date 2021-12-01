resource "aws_api_gateway_resource" "app_link" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "app"
}

resource "aws_lambda_permission" "invoke_handle_app_link" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.handle_app_link.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*/*"
}

resource "aws_api_gateway_method" "handle_app_link" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.app_link.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "handle_app_link" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.app_link.id
  http_method             = aws_api_gateway_method.handle_app_link.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.handle_app_link.invoke_arn
}