resource "aws_lambda_permission" "invoke_data_get_user_info" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.data_get_user_info.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*/*"
}

resource "aws_api_gateway_method" "data_get_user_info" {
  rest_api_id      = aws_api_gateway_rest_api.api.id
  resource_id      = aws_api_gateway_resource.data_me.id
  http_method      = "GET"
  authorization    = "CUSTOM"
  authorizer_id    = aws_api_gateway_authorizer.access.id
  api_key_required = true
}

resource "aws_api_gateway_integration" "data_get_user_info" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.data_me.id
  http_method             = aws_api_gateway_method.data_get_user_info.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.data_get_user_info.invoke_arn
}
