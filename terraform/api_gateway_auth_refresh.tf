resource "aws_lambda_permission" "invoke_handle_refresh" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.handle_refresh.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*/*"
}


resource "aws_api_gateway_method" "get_auth" {
  rest_api_id      = aws_api_gateway_rest_api.api.id
  resource_id      = aws_api_gateway_resource.auth.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "get_auth" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.auth.id
  http_method             = aws_api_gateway_method.get_auth.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.handle_refresh.invoke_arn
}

resource "aws_api_gateway_integration_response" "get_auth" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.auth.id
  http_method = aws_api_gateway_method.get_auth.http_method
  status_code = aws_api_gateway_method_response.get_auth.status_code

  depends_on = [
    aws_api_gateway_integration.get_auth
  ]
}

resource "aws_api_gateway_method_response" "get_auth" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.auth.id
  http_method = aws_api_gateway_method.get_auth.http_method
  status_code = "200"
}
